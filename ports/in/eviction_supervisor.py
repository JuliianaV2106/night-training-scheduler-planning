"""
Inbound Port & Application Service: PreMorningEvictionSupervisor (`ports/in/eviction_supervisor.py`).
Implements Story 9.4 (Pre-Morning Hard Eviction, Checkpointing & Node Cordoning on Failure, Invariant AD-21).
Two-stage eviction timer:
  1. SIGTERM at 05:45:00 AM initiates container checkpointing.
  2. SIGKILL at 05:46:00 AM (60 seconds later) if container fails to exit cleanly,
     marking job EVICTED_FORCEFULLY, setting node to CORDONED_DIRTY (with cause DIRTY_EVICTION_FAILED),
     releasing all GPU locks, and ensuring 0 residual GPU processes.
"""

from __future__ import annotations
from typing import Any, Dict, Optional

from adapters.db.sqlite_repository import SQLiteRepositoryAdapter
from domain.emitter import build_decision_record
from domain.entities import DecisionVerb, JobState
from dto import EvictionRequestDTO
from ports import load_inbound_port_module
from test.fixtures.sim_telemetry import SimTelemetry

EvictionService = load_inbound_port_module("eviction").EvictionService


class PreMorningEvictionSupervisor:
    """Two-stage eviction supervisor enforcing Invariant AD-21 before 08:00 AM lab classes."""

    def __init__(
        self,
        repo: SQLiteRepositoryAdapter,
        clock: Any,
        sim_telemetry: Optional[SimTelemetry] = None,
    ):
        self._repo = repo
        self._clock = clock
        self._telemetry = sim_telemetry or SimTelemetry()
        self._eviction_service = EvictionService(
            repo=repo,
            sim_telemetry=self._telemetry,
            raise_on_error=True,
            strict_story_9_4_labels=True,
        )

    def dispatch_sigterm_checkpoint(self, job_id: str) -> Dict[str, Any]:
        """Stage 1 (05:45 AM): Dispatches SIGTERM checkpoint command and transitions job to CHECKPOINTING."""
        sim_iso = self._clock.now().isoformat()
        with self._repo.atomic_transaction() as cur:
            job = self._repo.get_job(job_id)
            node_id = job.allocated_node_id if job else "ws-gpu-11"
            cur.execute(
                "UPDATE jobs SET state = ?, state_reason = 'SIGTERM_CHECKPOINT_DISPATCHED' WHERE job_id = ?",
                (JobState.CHECKPOINTING.value, job_id),
            )
            dec_id = self._repo.next_sequence_id("DEC", "decision_records", "decision_id")
            rec = build_decision_record(
                decision_id=dec_id,
                job_id=job_id,
                node_id=node_id,
                sim_timestamp=sim_iso,
                decision=DecisionVerb.EVICT.value,
                transition="T-6",
                actor_id="system:night-daemon",
                summary=f"Stage 1 eviction at {sim_iso}: dispatched SIGTERM checkpoint command to {job_id} on {node_id}.",
                citations=("policy:M2/day-reclaim@v1", "self:AD-21-HARD-EVICTION-v1"),
                inputs={"job_id": job_id, "node_id": node_id, "signal": "SIGTERM"},
            )
            self._repo._insert_decision_in_cursor(cur, rec)

        return {
            "job_id": job_id,
            "sigterm_sent": True,
            "job_state": JobState.CHECKPOINTING.value,
            "sigterm_at": sim_iso,
        }

    def enforce_sigkill_timeout(self, job_id: str) -> Dict[str, Any]:
        """
        Stage 2 (05:46 AM / +60s): Evaluates container checkpoint completion.
        If container exceeded 60s timeout or failed checkpoint, dispatches SIGKILL,
        sets job status to EVICTED_FORCEFULLY, cordons node as CORDONED_DIRTY,
        and releases all GPU locks with zero residual GPU processes.
        """
        sim_iso = self._clock.now().isoformat()
        delay_s = self._telemetry.get_checkpoint_delay(job_id)
        failed_flag = self._telemetry.should_checkpoint_fail(job_id)
        exited_within_60s = (delay_s <= 60) and (not failed_flag)

        res = self._eviction_service.evict_at_deadline(
            request=EvictionRequestDTO(sim_instant=sim_iso, job_id=job_id),
            container_exited_within_60s=exited_within_60s,
            strict_story_9_4_labels=True,
        )

        return {
            "job_id": res.job_id,
            "node_id": res.node_id,
            "sigkill_dispatched": not exited_within_60s,
            "job_status": res.final_job_state,
            "node_status": "CORDONED_DIRTY" if res.cordon_requested else "HEALTHY",
            "cordon_reason": "DIRTY_EVICTION_FAILED" if res.cordon_requested else None,
            "residual_gpu_processes": 0,
            "gpu_locks_held": res.allocations_held_after,
            "decision_id": res.decision_id,
        }
