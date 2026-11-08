"""
Flow A (ATDD-First) Verification Suite:
Story 9.4: Pre-Morning Hard Eviction, Checkpointing & Node Cordoning on Failure
Module 9: Night Training Scheduler
Invariant AD-21: Zero student training jobs may persist past 06:00:00.
Nodes with failed checkpoints must be cordoned as DIRTY_EVICTION_FAILED / CORDONED_DIRTY.

BDD Scenario:
  Scenario: Hanging training job killed and node cordoned before morning classes
    Given an active LoRA training job on node "ws-gpu-11" at 05:45 AM
    When the scheduler dispatches a SIGTERM checkpoint command
    And the container fails to exit within 60 seconds
    Then the scheduler dispatches a SIGKILL, marking job status "EVICTED_FORCEFULLY"
    And sets node "ws-gpu-11" status to "CORDONED_DIRTY"
    And ensures zero residual GPU processes remain running
"""

import pytest
from adapters.db.sqlite_repository import SQLiteRepositoryAdapter
from ports import load_inbound_port_module


class TestStory94HardEvictionATDD:
    """Flow A ATDD-First test suite for Story 9.4 (Invariant AD-21)."""

    def test_hanging_training_job_killed_and_node_cordoned_before_morning_classes(
        self, db, fake_clock, sim_telemetry
    ):
        """
        Verifies the two-stage eviction timer (SIGTERM at 05:45, SIGKILL at 05:46 if un-halted)
        and node cordoning (CORDONED_DIRTY) with zero residual GPU processes.
        """
        repo = SQLiteRepositoryAdapter(db)
        cursor = db.cursor()

        # Given an active LoRA training job on node "ws-gpu-11" at 05:45 AM
        job_id = "JOB-LORA-94"
        node_id = "ws-gpu-11"
        cursor.execute(
            """
            INSERT INTO jobs (
                job_id, state, actor_id, idempotency_key, payload_digest,
                gpu_slots_requested, required_vram_gb, checkpoint_interval_minutes,
                estimated_duration_s, image_digest, model_id, model_version,
                storage_request_bytes, submitted_at, allocated_node_id
            ) VALUES (
                ?, 'RUNNING', 'student-kavita', 'idemp-lora-94', ?,
                1, 24, 15, 14400, ?, 'llama-3-8b-lora', '1.0', 2048,
                '2026-10-18T22:00:00-05:00', ?
            )
            """,
            (job_id, "a" * 64, "sha256:" + "b" * 64, node_id),
        )
        cursor.execute(
            "UPDATE gpu_slots SET allocated_job_id = ?, held_since = '2026-10-18T22:00:00-05:00' WHERE node_id = ?",
            (job_id, node_id),
        )
        db.commit()

        PreMorningEvictionSupervisor = load_inbound_port_module("eviction_supervisor").PreMorningEvictionSupervisor
        supervisor = PreMorningEvictionSupervisor(
            repo=repo,
            clock=fake_clock,
            sim_telemetry=sim_telemetry,
        )

        # Stage 1: At 05:45:00 AM, scheduler dispatches SIGTERM checkpoint command
        fake_clock.jump_to("2026-10-19T05:45:00-05:00")
        stage1 = supervisor.dispatch_sigterm_checkpoint(job_id=job_id)
        assert stage1["sigterm_sent"] is True
        assert stage1["job_state"] == "CHECKPOINTING"
        assert stage1["sigterm_at"] == "2026-10-19T05:45:00-05:00"

        # Simulate hanging checkpoint container (> 60 seconds without exit)
        sim_telemetry.inject_checkpoint_delay(job_id, delay_s=95)
        fake_clock.advance(seconds=60)  # Clock is now 05:46:00 AM

        # Stage 2: At 05:46:00 AM, container failed to exit within 60 seconds -> SIGKILL
        stage2 = supervisor.enforce_sigkill_timeout(job_id=job_id)

        # Then the scheduler dispatches a SIGKILL, marking job status "EVICTED_FORCEFULLY"
        assert stage2["sigkill_dispatched"] is True
        assert stage2["job_status"] == "EVICTED_FORCEFULLY"

        # And sets node "ws-gpu-11" status to "CORDONED_DIRTY"
        assert stage2["node_status"] == "CORDONED_DIRTY"
        assert stage2["cordon_reason"] == "DIRTY_EVICTION_FAILED"

        # And ensures zero residual GPU processes remain running
        assert stage2["residual_gpu_processes"] == 0
        assert stage2["gpu_locks_held"] == 0

        # Verify physical database invariants
        cursor.execute("SELECT state, state_reason FROM jobs WHERE job_id = ?", (job_id,))
        job_row = cursor.fetchone()
        assert job_row[0] == "EVICTED_FORCEFULLY"
        assert job_row[1] == "DIRTY_EVICTION_FAILED"

        cursor.execute("SELECT status FROM nodes WHERE node_id = ?", (node_id,))
        node_row = cursor.fetchone()
        assert node_row[0] == "CORDONED_DIRTY"

        cursor.execute("SELECT allocated_job_id FROM gpu_slots WHERE node_id = ?", (node_id,))
        slot_row = cursor.fetchone()
        assert slot_row[0] is None
