"""
activateWindow use case (Story 1.3) — contracts.md §2.2.

Reads a snapshot, runs the pure placement fold, and commits every transition,
slot allocation and Decision Record in a single transaction (AD-2, INV-04).
"""

from __future__ import annotations

import logging
from datetime import datetime

from src.domain.entities import Deferral, Placement
from src.domain.errors import DelegateUnavailable, Explanation, WindowActivationOutsideWindow
from src.domain.policies import POLICY_NIGHT_WINDOW, RULE_RANKING, is_activation_instant
from src.domain.scheduling import plan_window
from src.ports.dto import PlacementDTO, WindowActivationRequestDTO, WindowActivationResultDTO
from src.ports.outbound import AuditEvent, DecisionRecord, SchedulerRepositoryPort

logger = logging.getLogger(__name__)

SYSTEM_ACTOR = "system:night-daemon"
EXPECTED_NODES = 32
EXPECTED_SLOTS = 33


class WindowActivationService:
    def __init__(self, repository: SchedulerRepositoryPort):
        self._repo = repository

    def activate_window(self, request: WindowActivationRequestDTO) -> WindowActivationResultDTO:
        try:
            at = datetime.fromisoformat(request.sim_instant)
        except ValueError:
            at = None
        if at is None or at.tzinfo is None or not is_activation_instant(at):
            raise WindowActivationOutsideWindow(
                f"Window activation invoked at invalid simulated instant '{request.sim_instant}'. "
                f"Window activation occurs strictly at 22:00:00.",
                Explanation(
                    rule_id=POLICY_NIGHT_WINDOW,
                    summary="Activation is only valid at 22:00:00 (+/- 2 s).",
                    citations=(POLICY_NIGHT_WINDOW,),
                    observed_values={"sim_instant": request.sim_instant},
                    thresholds={"activation_time": "22:00:00", "tolerance_s": 2},
                ),
            )

        activation_id = f"ACT-{at.date().strftime('%Y%m%d')}"
        event_id = f"EVT-WINDOW_ACTIVATED-{activation_id}"

        with self._repo.transaction():
            # Idempotency: a repeated activation for the same night returns the recorded result.
            previous = self._repo.find_audit_event(event_id)
            if previous is not None:
                logger.info("Window %s already activated; returning recorded result", activation_id)
                return WindowActivationResultDTO.model_validate(previous.payload)

            nodes = self._repo.list_nodes()
            if len(nodes) != EXPECTED_NODES or sum(len(n.slots) for n in nodes) != EXPECTED_SLOTS:
                raise DelegateUnavailable(
                    "Delegated module 'M3 fleet' is unavailable. Automatic fail-closed policy applied "
                    "citing self:DELEGATE-UNAVAILABLE-v1."
                )
            candidates = self._repo.list_admissible_jobs()
            placements, deferrals = plan_window(candidates, nodes)

            sim_ts = at.isoformat()
            summary_inputs = {
                "total_evaluated": len(candidates),
                "admitted_count": len(placements),
                "deferred_count": len(deferrals),
            }
            for p in placements:
                self._repo.allocate_slots(p, held_since=sim_ts)
                self._repo.mark_job_running(p.job_id, p.node_id)
                self._repo.append_decision(self._placement_record(activation_id, p, sim_ts, summary_inputs))
            for d in deferrals:
                self._repo.append_decision(self._deferral_record(activation_id, d, sim_ts, summary_inputs))

            result = WindowActivationResultDTO(
                activation_id=activation_id,
                sim_instant=sim_ts,
                total_evaluated=len(candidates),
                admitted_count=len(placements),
                deferred_count=len(deferrals),
                placements=[
                    PlacementDTO(
                        job_id=p.job_id,
                        node_id=p.node_id,
                        slot_ids=list(p.slot_ids),
                        vram_class_gb=p.vram_class_gb,
                        transition=p.transition,
                        decision_id=self._decision_id(activation_id, p.job_id),
                    )
                    for p in placements
                ],
            )
            self._repo.append_audit_event(
                AuditEvent(
                    event_id=event_id,
                    event_type="WINDOW_ACTIVATED",
                    job_id=None,
                    node_id=None,
                    actor_id=SYSTEM_ACTOR,
                    payload=result.model_dump(),
                    occurred_at=sim_ts,
                )
            )

        logger.info(
            "Window %s activated: %d evaluated, %d admitted, %d deferred",
            activation_id, result.total_evaluated, result.admitted_count, result.deferred_count,
        )
        return result

    @staticmethod
    def _decision_id(activation_id: str, job_id: str) -> str:
        return f"DEC-{activation_id}-{job_id}"

    def _placement_record(
        self, activation_id: str, p: Placement, sim_ts: str, summary_inputs: dict
    ) -> DecisionRecord:
        return DecisionRecord(
            decision_id=self._decision_id(activation_id, p.job_id),
            job_id=p.job_id,
            node_id=p.node_id,
            sim_timestamp=sim_ts,
            decision="ADMIT",
            transition=p.transition,
            actor_id=SYSTEM_ACTOR,
            summary=f"Admission rank {p.rank} placed on {p.node_id} ({', '.join(p.slot_ids)}).",
            citations=[POLICY_NIGHT_WINDOW, RULE_RANKING],
            inputs={
                **summary_inputs,
                "rank": p.rank,
                "node_tiebreak": ["prior_node", "lowest_allocations_held", "node_id_asc"],
                "won_on": p.won_on,
                "candidates_considered": p.candidates_considered,
                "prior_node_preferred": p.prior_node_preferred,
            },
        )

    def _deferral_record(
        self, activation_id: str, d: Deferral, sim_ts: str, summary_inputs: dict
    ) -> DecisionRecord:
        return DecisionRecord(
            decision_id=self._decision_id(activation_id, d.job_id),
            job_id=d.job_id,
            node_id=None,
            sim_timestamp=sim_ts,
            decision="DEFER",
            transition=d.transition,
            actor_id=SYSTEM_ACTOR,
            summary=f"Admission rank {d.rank} deferred: {d.reason_code}.",
            citations=[POLICY_NIGHT_WINDOW, RULE_RANKING],
            inputs={**summary_inputs, "rank": d.rank, "reason_code": d.reason_code},
        )
