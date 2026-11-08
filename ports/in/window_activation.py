"""
Inbound Port & Application Service: WindowActivationService (`ports/in/window_activation.py`).
Implements Contract 2 (`activateWindow`), Stories 9.2, 1.3, 3.1, 3.2, 4.1.
"""

from __future__ import annotations
from datetime import datetime
from typing import List, Optional

from adapters.db.sqlite_repository import SQLiteRepositoryAdapter
from domain.allocation import allocate_window_batch
from domain.emitter import build_decision_record
from domain.entities import DecisionVerb, DomainError, JobState
from domain.state_machine import validate_window_activation_instant
from dto import (
    ExplanationDTO,
    PlacementDTO,
    WindowActivationRequestDTO,
    WindowActivationResultDTO,
)


class WindowActivationService:
    """Use-Case handler for 22:00:00 Night Window Activation and 33-slot placement."""

    def __init__(self, repo: SQLiteRepositoryAdapter, raise_on_error: bool = False):
        self._repo = repo
        self._raise_on_error = raise_on_error

    def activate_window(
        self,
        request: WindowActivationRequestDTO,
    ) -> Optional[WindowActivationResultDTO]:
        sim_dt = datetime.fromisoformat(request.sim_instant)
        sim_iso = sim_dt.isoformat()

        try:
            validate_window_activation_instant(sim_dt)

            with self._repo.atomic_transaction() as cur:
                candidates = self._repo.list_jobs(
                    states=[
                        JobState.QUEUED_PENDING_WINDOW.value,
                        JobState.QUEUED_PREEMPTED.value,
                        JobState.EVICTED_RESUMABLE.value,
                        JobState.EVICTION_FAILED.value,
                    ]
                )
                nodes = self._repo.get_nodes()
                slots = self._repo.get_slots()

                decisions = allocate_window_batch(
                    candidate_jobs=candidates,
                    nodes=nodes,
                    slots=slots,
                    sim_instant=sim_iso,
                )

                placements: List[PlacementDTO] = []
                admitted_count = 0
                deferred_count = 0

                for dec in decisions:
                    decision_id = self._repo.next_sequence_id("DEC", "decision_records", "decision_id")
                    if dec.admitted and dec.node_id:
                        admitted_count += 1
                        cur.execute(
                            """
                            UPDATE jobs
                            SET state = 'RUNNING',
                                allocated_node_id = ?,
                                admitted_nights = admitted_nights + 1,
                                consecutive_nights_missed = 0,
                                preempted_in_window = 0
                            WHERE job_id = ?
                            """,
                            (dec.node_id, dec.job_id),
                        )
                        for slot_id in dec.slot_ids:
                            cur.execute(
                                "UPDATE gpu_slots SET allocated_job_id = ?, held_since = ? WHERE slot_id = ?",
                                (dec.job_id, sim_iso, slot_id),
                            )

                        d_rec = build_decision_record(
                            decision_id=decision_id,
                            job_id=dec.job_id,
                            node_id=dec.node_id,
                            sim_timestamp=sim_iso,
                            decision=DecisionVerb.ADMIT.value,
                            transition=dec.transition,
                            actor_id="system:night-daemon",
                            summary=f"Placed job {dec.job_id} onto {dec.node_id} ({', '.join(dec.slot_ids)}).",
                            citations=("policy:M2/night-window@v1", "self:ADMISSION-RANKING-v1"),
                            inputs={
                                "job_id": dec.job_id,
                                "node_id": dec.node_id,
                                "slot_ids": list(dec.slot_ids),
                                "transition": dec.transition,
                            },
                        )
                        self._repo._insert_decision_in_cursor(cur, d_rec)

                        placements.append(
                            PlacementDTO(
                                job_id=dec.job_id,
                                node_id=dec.node_id,
                                slot_ids=list(dec.slot_ids),
                                vram_class_gb=dec.vram_class_gb or 24,
                                transition=dec.transition if dec.transition in ("T-3", "T-12") else "T-3",
                                decision_id=decision_id,
                            )
                        )
                    else:
                        deferred_count += 1
                        cur.execute(
                            """
                            UPDATE jobs
                            SET state = 'QUEUED_PENDING_WINDOW',
                                state_reason = ?,
                                consecutive_nights_missed = consecutive_nights_missed + 1
                            WHERE job_id = ?
                            """,
                            (dec.reason_code, dec.job_id),
                        )
                        d_rec = build_decision_record(
                            decision_id=decision_id,
                            job_id=dec.job_id,
                            node_id=None,
                            sim_timestamp=sim_iso,
                            decision=DecisionVerb.DEFER.value,
                            transition=dec.transition,
                            actor_id="system:night-daemon",
                            summary=f"Deferred job {dec.job_id} ({dec.reason_code}).",
                            citations=("policy:M2/night-window@v1", "self:ADMISSION-RANKING-v1"),
                            inputs={"job_id": dec.job_id, "reason_code": dec.reason_code},
                        )
                        self._repo._insert_decision_in_cursor(cur, d_rec)

                activation_id = self._repo.next_sequence_id("ACT", "audit_events", "event_id")
                citations = ["policy:M2/night-window@v1", "self:ADMISSION-RANKING-v1"]
                summary_inputs = {
                    "total_evaluated": len(candidates),
                    "admitted_count": admitted_count,
                    "deferred_count": deferred_count,
                }
                self._repo._insert_audit_event_in_cursor(
                    cur,
                    event_id=activation_id,
                    event_type="WINDOW_ACTIVATED",
                    job_id=None,
                    node_id=None,
                    actor_id="system:night-daemon",
                    payload=summary_inputs,
                    occurred_at=sim_iso,
                )

                return WindowActivationResultDTO(
                    activation_id=activation_id,
                    sim_instant=sim_iso,
                    total_evaluated=len(candidates),
                    admitted_count=admitted_count,
                    deferred_count=deferred_count,
                    placements=placements,
                    citations=citations,
                    inputs=summary_inputs,
                    explanation=ExplanationDTO(
                        rule_id="self:ADMISSION-RANKING-v1",
                        summary=f"Activated night window at {sim_iso}: admitted {admitted_count} of {len(candidates)} candidate jobs.",
                        observed_values=summary_inputs,
                        thresholds={"max_fleet_slots": 33},
                        citations=citations,
                    ),
                )
        except DomainError:
            if self._raise_on_error:
                raise
            return None
