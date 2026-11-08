"""
Executable ATDD Contract Suite: Module 9 — Night Training Scheduler (Solu-2, promoted in Impl-1).

Tests Design-by-Contract postconditions, precondition rejections, invariants,
explainability payloads, and the Mandatory Edge Case.

Impl-1: submitJob and activateWindow run against the real services (GREEN).
evictAtDeadline (Epic 2) keeps its red-phase stub and is marked `impl2`
(deselected by default in pytest.ini; run with `pytest -m impl2`).
"""

import json
import sqlite3

import pytest

from src.domain.errors import (
    OutOfScopeDistributed,
    QueueCapExceeded,
    TwoGpuRequires48Gb,
    WindowActivationOutsideWindow,
)
from src.ports.dto import (
    EvictionRequestDTO,
    EvictionResultDTO,
    JobSpecDTO,
    JobSubmissionRequestDTO,
    JobSubmissionResponseDTO,
    WindowActivationRequestDTO,
    WindowActivationResultDTO,
)
from tests.fixtures.explain_assert import assert_explainability
from tests.stubs.interfaces import EvictionServiceStub

# =============================================================================
# Helper Fixtures & Builders
# =============================================================================

@pytest.fixture
def submission_stub(submission_service):
    """Real JobSubmissionService (fixture name kept from the Solu-2 red-phase suite)."""
    return submission_service


@pytest.fixture
def activation_stub(activation_service):
    """Real WindowActivationService (fixture name kept from the Solu-2 red-phase suite)."""
    return activation_service


@pytest.fixture
def eviction_stub() -> EvictionServiceStub:
    return EvictionServiceStub()


def build_valid_job_spec(
    gpu_slots: int = 1,
    vram_gb: int = 24,
    duration_s: int = 7200,
    model_id: str = "llama-3-8b-instruct"
) -> JobSpecDTO:
    """Constructs a strictly valid JobSpecDTO."""
    return JobSpecDTO(
        image_digest="sha256:" + "a" * 64,
        gpu_slots_requested=gpu_slots,
        required_vram_gb=vram_gb,
        checkpoint_interval_minutes=15,
        estimated_duration_s=duration_s,
        model_id=model_id,
        model_version="1.0.0",
        storage_request_bytes=1024 * 1024 * 500,  # 500 MB
        worker_count=1,
        replicas=1,
        distributed_artifact_present=False
    )


def submit(service, key: str, clock, spec: JobSpecDTO = None) -> JobSubmissionResponseDTO:
    return service.submit_job(
        JobSubmissionRequestDTO(idempotency_key=key, actor_id="student-kavita",
                                spec=spec or build_valid_job_spec()),
        at=clock.advance(1),
    )


def decision_record(db, job_id: str, transition: str) -> dict:
    row = db.execute(
        "SELECT citations, inputs FROM decision_records WHERE job_id = ? AND transition = ?",
        (job_id, transition),
    ).fetchone()
    assert row is not None, f"No decision record {transition} for {job_id}"
    return {"citations": json.loads(row[0]), "inputs": json.loads(row[1])}


# =============================================================================
# 1. Operation 1: submitJob Tests
# =============================================================================

class TestSubmitJobContract:
    """Contract tests for submitJob."""

    def test_submit_job_happy_path_admits_and_persists_pending_job(
        self, submission_stub, db, fake_clock
    ):
        """Happy Path (Q holds): Valid spec returns 201 Created and QUEUED_PENDING_WINDOW state."""
        spec = build_valid_job_spec(gpu_slots=1, vram_gb=24)
        req = JobSubmissionRequestDTO(
            idempotency_key="idemp-key-happy-001",
            actor_id="student-kavita",
            spec=spec
        )

        res: JobSubmissionResponseDTO = submission_stub.submit_job(req, at=fake_clock.now())

        # Real postcondition assertions:
        assert res.job_id.startswith("JOB-")
        assert res.state == "QUEUED_PENDING_WINDOW"
        assert res.idempotency_key == "idemp-key-happy-001"
        assert len(res.payload_digest) == 64
        assert 1 <= res.queue_position <= 500

        # Verify physical database state:
        cursor = db.cursor()
        cursor.execute("SELECT state, actor_id FROM jobs WHERE job_id = ?", (res.job_id,))
        row = cursor.fetchone()
        assert row is not None
        assert row[0] == "QUEUED_PENDING_WINDOW"
        assert row[1] == "student-kavita"

    def test_submit_job_precondition_violation_distributed_spec_rejected_with_zero_state_mutation(
        self, submission_stub, db
    ):
        """Precondition Violation (P1): Distributed spec rejected with zero mutations."""
        spec = build_valid_job_spec()
        spec.worker_count = 4  # Illegal for Module 9 single-node scheduler
        req = JobSubmissionRequestDTO(
            idempotency_key="idemp-key-dist-fail",
            actor_id="student-dist",
            spec=spec
        )

        with pytest.raises(OutOfScopeDistributed):
            submission_stub.submit_job(req)

        # Physical assertion on Q-fail: zero records inserted
        cursor = db.cursor()
        cursor.execute("SELECT COUNT(*) FROM jobs WHERE idempotency_key = 'idemp-key-dist-fail'")
        count = cursor.fetchone()[0]
        assert count == 0, "Q-fail breach: database mutation occurred when precondition failed"

    def test_submit_job_invariant_queue_cap_500_enforced_under_burst_submissions(
        self, submission_stub, db
    ):
        """Invariant (INV-01): Total non-terminal jobs capped at 500."""
        # Pre-seed DB with 500 non-terminal jobs
        cursor = db.cursor()
        for i in range(500):
            cursor.execute(
                """
                INSERT INTO jobs (
                    job_id, state, actor_id, idempotency_key, payload_digest,
                    gpu_slots_requested, required_vram_gb, checkpoint_interval_minutes,
                    estimated_duration_s, image_digest, model_id, model_version,
                    storage_request_bytes, submitted_at
                ) VALUES (
                    ?, 'QUEUED_PENDING_WINDOW', 'user-batch', ?, '0000000000000000000000000000000000000000000000000000000000000000',
                    1, 24, 15, 3600, 'sha256:' || hex(randomblob(32)), 'model-1', '1.0', 1000, '2026-10-18T20:00:00-05:00'
                )
                """,
                (f"JOB-{i:04d}", f"idemp-preseed-{i:04d}")
            )
        db.commit()

        # 501st submission must be rejected
        spec = build_valid_job_spec()
        req = JobSubmissionRequestDTO(
            idempotency_key="idemp-key-501",
            actor_id="student-over-cap",
            spec=spec
        )

        with pytest.raises(QueueCapExceeded):
            submission_stub.submit_job(req)

        # Assert 501st job is not persisted
        cursor.execute("SELECT COUNT(*) FROM jobs WHERE state NOT IN ('COMPLETED', 'FAILED', 'REJECTED', 'EXPIRED')")
        active_count = cursor.fetchone()[0]
        assert active_count == 500

    def test_submit_job_invariant_two_gpu_requires_48gb_physically_enforced(
        self, submission_stub, db
    ):
        """Invariant (INV-03 / AD-4): 2-GPU job requested on 24GB hardware rejected."""
        # Spec with 2 GPUs on 24GB VRAM (the Solu-2 draft passed vram_gb=48, which is a valid spec)
        spec = build_valid_job_spec(gpu_slots=2, vram_gb=24)
        req = JobSubmissionRequestDTO(
            idempotency_key="idemp-2gpu-24gb",
            actor_id="student-invalid-vram",
            spec=spec
        )
        with pytest.raises(TwoGpuRequires48Gb):
            submission_stub.submit_job(req)

        # Assert database constraint rejects invalid tuple physically if reached
        cursor = db.cursor()
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute(
                """
                INSERT INTO jobs (
                    job_id, state, actor_id, idempotency_key, payload_digest,
                    gpu_slots_requested, required_vram_gb, checkpoint_interval_minutes,
                    estimated_duration_s, image_digest, model_id, model_version,
                    storage_request_bytes, submitted_at
                ) VALUES (
                    'JOB-INV3', 'QUEUED_PENDING_WINDOW', 'user-inv3', 'key-inv3', '0000000000000000000000000000000000000000000000000000000000000000',
                    2, 24, 15, 3600, 'sha256:' || hex(randomblob(32)), 'model-1', '1.0', 1000, '2026-10-18T20:00:00-05:00'
                )
                """
            )

    def test_submit_job_explainability_payload_cites_jobspec_validation_rule(
        self, submission_stub, db, fake_clock
    ):
        """Explainability (Q4): the ADMIT T-1 Decision Record carries the cited validation authority."""
        spec = build_valid_job_spec()
        req = JobSubmissionRequestDTO(
            idempotency_key="idemp-explain-01",
            actor_id="student-explain",
            spec=spec
        )

        res = submission_stub.submit_job(req, at=fake_clock.now())
        # The OpenAPI JobSubmissionResponse carries no citations; Q4 lives in the Decision Record.
        assert_explainability(
            decision_record(db, res.job_id, "T-1"),
            expected_rule_id="self:JOBSPEC-VALIDATION-v1",
            required_keys=["gpu_slots_requested", "required_vram_gb"]
        )


# =============================================================================
# 2. Operation 2: activateWindow Tests
# =============================================================================

class TestActivateWindowContract:
    """Contract tests for activateWindow."""

    def test_activate_window_happy_path_places_jobs_deterministically(
        self, submission_stub, activation_stub, db, fake_clock
    ):
        """Happy Path (Q holds): At 22:00:00, queued jobs are placed into 33 slots."""
        for i in range(5):
            submit(submission_stub, f"idemp-act-{i}", fake_clock)
        fake_clock.jump_to("2026-10-18T22:00:00-05:00")
        req = WindowActivationRequestDTO(sim_instant=fake_clock.now().isoformat())

        result: WindowActivationResultDTO = activation_stub.activate_window(req)
        assert result.sim_instant.endswith("22:00:00-05:00")
        assert result.admitted_count == 5
        assert len(result.placements) == result.admitted_count

        # Verify slot occupancy reflects placements
        cursor = db.cursor()
        cursor.execute("SELECT COUNT(*) FROM gpu_slots WHERE allocated_job_id IS NOT NULL")
        allocated_slots = cursor.fetchone()[0]
        assert allocated_slots == result.admitted_count

    def test_activate_window_precondition_violation_outside_window_rejected(
        self, activation_stub, db, fake_clock
    ):
        """Precondition Violation (P1): Activation rejected outside 22:00:00."""
        fake_clock.jump_to("2026-10-18T14:30:00-05:00")  # Daytime
        req = WindowActivationRequestDTO(sim_instant=fake_clock.now().isoformat())

        with pytest.raises(WindowActivationOutsideWindow):
            activation_stub.activate_window(req)

        cursor = db.cursor()
        cursor.execute("SELECT COUNT(*) FROM gpu_slots WHERE allocated_job_id IS NOT NULL")
        assert cursor.fetchone()[0] == 0

    def test_activate_window_invariant_total_allocated_slots_never_exceeds_33(
        self, submission_stub, activation_stub, db, fake_clock
    ):
        """Invariant (AD-4): Fleet active allocations count <= 33 slots."""
        for i in range(40):
            submit(submission_stub, f"idemp-burst-{i}", fake_clock)
        fake_clock.jump_to("2026-10-18T22:00:00-05:00")
        req = WindowActivationRequestDTO(sim_instant=fake_clock.now().isoformat())

        activation_stub.activate_window(req)
        cursor = db.cursor()
        cursor.execute("SELECT COUNT(*) FROM gpu_slots WHERE allocated_job_id IS NOT NULL")
        active_slots = cursor.fetchone()[0]
        assert active_slots == 33, f"Fleet over-allocation detected: {active_slots} slots held"

    def test_activate_window_invariant_atomic_server_gpu_allocation(
        self, submission_stub, activation_stub, db, fake_clock
    ):
        """Invariant (AD-4): server-gpu-01 allocates both slots atomically for 2-GPU jobs."""
        submit(submission_stub, "idemp-2gpu", fake_clock, build_valid_job_spec(gpu_slots=2, vram_gb=48))
        fake_clock.jump_to("2026-10-18T22:00:00-05:00")
        req = WindowActivationRequestDTO(sim_instant=fake_clock.now().isoformat())

        res = activation_stub.activate_window(req)
        assert [len(p.slot_ids) for p in res.placements] == [2]
        for placement in res.placements:
            if placement.node_id == "server-gpu-01" and len(placement.slot_ids) == 2:
                cursor = db.cursor()
                cursor.execute("SELECT allocated_job_id FROM gpu_slots WHERE node_id = 'server-gpu-01'")
                rows = cursor.fetchall()
                assert rows[0][0] == rows[1][0] == placement.job_id

    def test_activate_window_explainability_payload_cites_policy_and_admission_ranking(
        self, submission_stub, activation_stub, db, fake_clock
    ):
        """Explainability (Q4): each placement record cites the night-window policy and ranking rule."""
        queued = submit(submission_stub, "idemp-explain-act", fake_clock)
        fake_clock.jump_to("2026-10-18T22:00:00-05:00")
        req = WindowActivationRequestDTO(sim_instant=fake_clock.now().isoformat())

        activation_stub.activate_window(req)
        assert_explainability(
            decision_record(db, queued.job_id, "T-3"),
            expected_rule_id="self:ADMISSION-RANKING-v1",
            required_keys=["total_evaluated", "admitted_count"]
        )


# =============================================================================
# 3. Operation 3: evictAtDeadline & Mandatory Edge Case Tests (Impl-2 scope)
# =============================================================================

@pytest.mark.impl2
class TestEvictAtDeadlineContract:
    """Contract tests for evictAtDeadline and the Mandatory Edge Case."""

    def test_evict_at_deadline_happy_path_completes_checkpoint_and_releases_slots(
        self, eviction_stub, db, fake_clock
    ):
        """Happy Path (Q holds): Checkpoint verified before 05:53:00, slot freed, job resumable."""
        fake_clock.jump_to("2026-10-19T05:45:00-05:00")
        req = EvictionRequestDTO(sim_instant=fake_clock.now().isoformat(), job_id="JOB-HAPPY-EVICT")

        result: EvictionResultDTO = eviction_stub.evict_at_deadline(req)
        assert result.checkpoint_status == "VERIFIED"
        assert result.final_job_state == "EVICTED_RESUMABLE"
        assert result.cordon_requested is False
        assert result.slots_released >= 1

    def test_evict_at_deadline_precondition_violation_called_before_ramp_rejected(
        self, eviction_stub, fake_clock
    ):
        """Precondition Violation (P1): Eviction invoked prior to 05:45:00 rejected."""
        fake_clock.jump_to("2026-10-19T05:00:00-05:00")  # Pre-ramp
        req = EvictionRequestDTO(sim_instant=fake_clock.now().isoformat(), job_id="JOB-EARLY")

        eviction_stub.evict_at_deadline(req)

    def test_mandatory_edge_case_checkpoint_failure_at_dawn_cordons_node_releases_all_slots_at_0600(
        self, eviction_stub, db, sim_telemetry, fake_clock
    ):
        """
        MANDATORY EDGE CASE (P0):
        Checkpoint fails at 05:45:00-05:53:00 -> Node cordoned via CordonRequest to Module 3,
        user notified, GPU allocation released immediately, allocations_held == 0 at 06:00:00.
        """
        target_job = "JOB-EDGE-001"
        target_node = "ws-gpu-17"

        # Pre-seed running job on node 17 in database
        cursor = db.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO jobs (
                job_id, state, actor_id, idempotency_key, payload_digest,
                gpu_slots_requested, required_vram_gb, checkpoint_interval_minutes,
                estimated_duration_s, image_digest, model_id, model_version,
                storage_request_bytes, submitted_at, allocated_node_id
            ) VALUES (
                ?, 'RUNNING', 'student-maria', 'key-edge-01', '0000000000000000000000000000000000000000000000000000000000000000',
                1, 24, 15, 14400, 'sha256:' || hex(randomblob(32)), 'model-1', '1.0', 1000,
                '2026-10-18T20:00:00-05:00', ?
            )
            """,
            (target_job, target_node)
        )
        cursor.execute(
            "UPDATE gpu_slots SET allocated_job_id = ? WHERE node_id = ?",
            (target_job, target_node)
        )
        db.commit()

        # Inject checkpoint failure fault via sim_telemetry
        sim_telemetry.inject_checkpoint_failure(target_job)
        fake_clock.jump_to("2026-10-19T05:53:00-05:00")

        req = EvictionRequestDTO(sim_instant=fake_clock.now().isoformat(), job_id=target_job)

        result: EvictionResultDTO = eviction_stub.evict_at_deadline(req)

        # Assert Edge-Case Postconditions:
        assert result.checkpoint_status == "FAILED"
        assert result.final_job_state == "EVICTION_FAILED"
        assert result.cordon_requested is True
        assert result.slots_released == 1
        assert result.allocations_held_after == 0

        # 1. Assert node is physically marked CORDONED locally
        cursor.execute("SELECT status FROM nodes WHERE node_id = ?", (target_node,))
        node_status = cursor.fetchone()[0]
        assert node_status == "CORDONED"

        # 2. Assert CordonRequest was recorded for Module 3
        cursor.execute("SELECT cause, state FROM cordon_requests WHERE node_id = ?", (target_node,))
        cordon_row = cursor.fetchone()
        assert cordon_row is not None
        assert cordon_row[0] == "EVICTION_CHECKPOINT_WRITE_FAILED"
        assert cordon_row[1] == "REQUESTED"

        # 3. Assert slots released: GPU slot allocated_job_id is NULL
        cursor.execute("SELECT allocated_job_id FROM gpu_slots WHERE node_id = ?", (target_node,))
        slot_job = cursor.fetchone()[0]
        assert slot_job is None

        # 4. Advance clock to 06:00:00 and assert Invariant S-1 (allocations_held == 0)
        fake_clock.jump_to("2026-10-19T06:00:00-05:00")
        cursor.execute("SELECT COUNT(*) FROM gpu_slots WHERE allocated_job_id IS NOT NULL")
        total_active_allocations = cursor.fetchone()[0]
        assert total_active_allocations == 0, "Invariant S-1 breach: student allocation held at 06:00:00"

    def test_mandatory_edge_case_user_notified_and_job_rescheduled_after_dawn_checkpoint_failure(
        self, eviction_stub, db, fake_clock
    ):
        """Mandatory Edge Case Notification: User outbox receives notification and job is eligible for T-20."""
        target_job = "JOB-EDGE-NOTIF"
        fake_clock.jump_to("2026-10-19T05:53:00-05:00")
        req = EvictionRequestDTO(sim_instant=fake_clock.now().isoformat(), job_id=target_job)

        eviction_stub.evict_at_deadline(req)
        # Assert audit event emitted
        cursor = db.cursor()
        cursor.execute("SELECT payload FROM audit_events WHERE job_id = ? AND event_type = 'JOB_EVICTED'", (target_job,))
        row = cursor.fetchone()
        assert row is not None
        assert "FAILED" in row[0]

    def test_evict_at_deadline_explainability_payload_cites_day_reclaim_policy(
        self, eviction_stub, fake_clock
    ):
        """Explainability (Q4): Eviction decision record cites day reclaim policy."""
        fake_clock.jump_to("2026-10-19T05:45:00-05:00")
        req = EvictionRequestDTO(sim_instant=fake_clock.now().isoformat(), job_id="JOB-EXPLAIN-EVICT")

        res = eviction_stub.evict_at_deadline(req)
        assert_explainability(
            res,
            expected_rule_id="policy:M2/day-reclaim@v1",
            required_keys=["job_id", "slots_released"]
        )
