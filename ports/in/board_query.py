"""
Inbound Port & Application Service: PreemptionAndBoardService (`ports/in/board_query.py`).
Implements:
- Story 9.5 & Story 4.2: Dynamic Priority Queue Preemption Cascade under full cluster saturation (31 nodes)
- Story 4.1: Transparent Decision Records & Explanation DTO citations on Status Board
- Story 4.3: Uniform HTTP 404 Access Control & Identity Redaction (AD-8)
"""

from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List, Optional

from adapters.db.sqlite_repository import SQLiteRepositoryAdapter
from adapters.sim.filesystem_checkpoint_store import FilesystemCheckpointStoreAdapter
from domain.engine import evaluate_preemption_cascade
from domain.entities import DomainError, JobEntity, JobState


class PreemptionAndBoardService:
    """Use-Case handler for priority preemption cascades, board state queries, and RBAC 404 isolation."""

    def __init__(
        self,
        repo: SQLiteRepositoryAdapter,
        checkpoint_store: Optional[FilesystemCheckpointStoreAdapter] = None,
    ):
        self._repo = repo
        self._checkpoint_store = checkpoint_store or FilesystemCheckpointStoreAdapter()

    def execute_priority_preemption(
        self,
        challenger_job_id: str,
        sim_instant: str = "2026-10-18T23:10:00-05:00",
        use_queued_preempted_label: bool = True,
    ) -> Dict[str, Any]:
        """
        Executes atomic priority preemption cascade under heavy contention (Story 9.5 & Story 4.2).
        Protected by SQLite `BEGIN IMMEDIATE` + mutex lock so simultaneous high-priority requests
        never select or overwrite the same victim node concurrently.
        """
        sim_dt = datetime.fromisoformat(sim_instant)
        with self._repo.atomic_transaction() as cur:
            challenger = self._repo.get_job(challenger_job_id)
            if challenger is None:
                raise DomainError(
                    error_code="ENTITLEMENT_DENIED",
                    message=f"Job '{challenger_job_id}' not found.",
                    http_status=404,
                    retryable=False,
                    rule_id="self:AD-8-UNIFORM-404-v1",
                    citations=("self:AD-8-UNIFORM-404-v1",),
                )

            # Check if there is already a free eligible slot before preempting
            slots = self._repo.get_slots()
            nodes = {n.node_id: n for n in self._repo.get_nodes()}
            free_matching = [
                s
                for s in slots
                if s.allocated_job_id is None
                and nodes[s.node_id].status in ("HEALTHY", "IDLE")
                and nodes[s.node_id].vram_class_gb == challenger.required_vram_gb
            ]
            if len(free_matching) >= challenger.gpu_slots_requested:
                chosen_slot = free_matching[0]
                cur.execute(
                    "UPDATE jobs SET state = 'RUNNING', allocated_node_id = ? WHERE job_id = ?",
                    (chosen_slot.node_id, challenger.job_id),
                )
                cur.execute(
                    "UPDATE gpu_slots SET allocated_job_id = ?, held_since = ? WHERE slot_id = ?",
                    (challenger.job_id, sim_instant, chosen_slot.slot_id),
                )
                return {
                    "preempted": False,
                    "challenger_job_id": challenger.job_id,
                    "challenger_state": "RUNNING",
                    "victim_job_id": None,
                    "victim_new_state": None,
                    "assigned_node_id": chosen_slot.node_id,
                    "reason_code": "PLACED_ON_FREE_SLOT",
                    "orphaned_gpu_processes": 0,
                }

            running_jobs = self._repo.list_jobs(states=[JobState.RUNNING.value])
            decision_id = self._repo.next_sequence_id("DEC", "decision_records", "decision_id")

            outcome = evaluate_preemption_cascade(
                challenger=challenger,
                running_jobs=running_jobs,
                sim_dt=sim_dt,
                decision_id=decision_id,
                use_queued_preempted_label=use_queued_preempted_label,
            )

            self._repo._insert_decision_in_cursor(cur, outcome.decision_record)

            if not outcome.preempted or outcome.victim_job_id is None or outcome.assigned_node_id is None:
                return {
                    "preempted": False,
                    "challenger_job_id": outcome.challenger_job_id,
                    "challenger_state": outcome.challenger_state,
                    "victim_job_id": None,
                    "victim_new_state": None,
                    "assigned_node_id": None,
                    "reason_code": outcome.reason_code,
                    "orphaned_gpu_processes": 0,
                }

            # 1. Write preemption checkpoint for victim (Invariant AD-22)
            ckpt_id = self._repo.next_sequence_id("CKP", "checkpoints", "checkpoint_id")
            ckpt = self._checkpoint_store.write_verified_checkpoint(
                checkpoint_id=ckpt_id,
                job_id=outcome.victim_job_id,
                step=50,
                sim_timestamp=sim_instant,
                written_by="preemption",
            )
            cur.execute(
                """
                INSERT OR REPLACE INTO checkpoints (
                    checkpoint_id, job_id, path, bytes, step, digest, sim_timestamp, state, written_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ckpt.checkpoint_id,
                    ckpt.job_id,
                    ckpt.path,
                    ckpt.bytes,
                    ckpt.step,
                    ckpt.digest,
                    ckpt.sim_timestamp,
                    ckpt.state,
                    ckpt.written_by,
                ),
            )

            # 2. Transition victim to QUEUED_PREEMPTED (preserving checkpoint & original submitted_at)
            cur.execute(
                """
                UPDATE jobs
                SET state = ?,
                    state_reason = 'PREEMPTED_BY_HIGHER_PRIORITY',
                    preempted_in_window = 1,
                    allocated_node_id = NULL
                WHERE job_id = ?
                """,
                (outcome.victim_new_state, outcome.victim_job_id),
            )

            # 3. Reassign GPU slot atomically from victim to challenger
            cur.execute(
                """
                UPDATE gpu_slots
                SET allocated_job_id = ?, held_since = ?
                WHERE node_id = ? AND allocated_job_id = ?
                """,
                (challenger.job_id, sim_instant, outcome.assigned_node_id, outcome.victim_job_id),
            )

            # 4. Transition challenger to RUNNING on the victim's node
            cur.execute(
                """
                UPDATE jobs
                SET state = 'RUNNING',
                    state_reason = 'ADMITTED_VIA_PREEMPTION',
                    allocated_node_id = ?,
                    admitted_nights = admitted_nights + 1
                WHERE job_id = ?
                """,
                (outcome.assigned_node_id, challenger.job_id),
            )

            event_id = self._repo.next_sequence_id("EVT", "audit_events", "event_id")
            self._repo._insert_audit_event_in_cursor(
                cur,
                event_id=event_id,
                event_type="JOB_PREEMPTED",
                job_id=challenger.job_id,
                node_id=outcome.assigned_node_id,
                actor_id=challenger.actor_id,
                payload={
                    "challenger_job_id": challenger.job_id,
                    "victim_job_id": outcome.victim_job_id,
                    "victim_new_state": outcome.victim_new_state,
                    "assigned_node_id": outcome.assigned_node_id,
                    "checkpoint_id": ckpt_id,
                    "orphaned_gpu_processes": 0,
                },
                occurred_at=sim_instant,
            )

            return {
                "preempted": True,
                "challenger_job_id": challenger.job_id,
                "challenger_state": outcome.challenger_state,
                "victim_job_id": outcome.victim_job_id,
                "victim_new_state": outcome.victim_new_state,
                "assigned_node_id": outcome.assigned_node_id,
                "checkpoint_id": ckpt_id,
                "reason_code": outcome.reason_code,
                "orphaned_gpu_processes": 0,
                "citations": list(outcome.decision_record.citations),
            }

    def get_job_for_actor(self, job_id: str, requesting_actor_id: str, is_admin: bool = False) -> Dict[str, Any]:
        """
        Story 4.3 (AD-8 Uniform 404 Access Control & Identity Redaction):
        Returns full job details + citations if owner or admin.
        If job does not exist OR belongs to another student, returns byte-identical 404 DomainError
        (never 403 Forbidden) and records an audit event.
        """
        uniform_404_msg = "Requested training job resource was not found."
        job = self._repo.get_job(job_id)

        if job is None or (not is_admin and job.actor_id != requesting_actor_id):
            with self._repo.atomic_transaction() as cur:
                evt_id = self._repo.next_sequence_id("EVT", "audit_events", "event_id")
                self._repo._insert_audit_event_in_cursor(
                    cur,
                    event_id=evt_id,
                    event_type="UNAUTHORIZED_OR_MISSING_JOB_QUERY",
                    job_id=None,
                    node_id=None,
                    actor_id=requesting_actor_id,
                    payload={"queried_resource": "redacted", "status_returned": 404},
                    occurred_at="2026-10-18T22:00:00-05:00",
                )
            raise DomainError(
                error_code="ENTITLEMENT_DENIED",
                message=uniform_404_msg,
                http_status=404,
                retryable=False,
                rule_id="policy:M1/rbac-uniform-404@v1",
                citations=("policy:M1/rbac-uniform-404@v1", "self:AD-8-UNIFORM-404-v1"),
            )

        decisions = self._repo.list_decision_records(job_id=job.job_id)
        latest_citations = list(decisions[-1].citations) if decisions else ["self:JOBSPEC-VALIDATION-v1"]

        return {
            "job_id": job.job_id,
            "state": job.state,
            "actor_id": job.actor_id,
            "allocated_node_id": job.allocated_node_id,
            "effective_priority": job.effective_priority,
            "granted_priority": job.granted_priority,
            "gpu_slots_requested": job.gpu_slots_requested,
            "required_vram_gb": job.required_vram_gb,
            "model_id": job.model_id,
            "citations": latest_citations,
            "decisions": [
                {
                    "decision_id": d.decision_id,
                    "decision": d.decision,
                    "transition": d.transition,
                    "summary": d.summary,
                    "citations": list(d.citations),
                    "inputs": d.inputs,
                }
                for d in decisions
            ],
        }
