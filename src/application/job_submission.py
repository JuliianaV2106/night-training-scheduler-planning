"""
submitJob use case (Stories 1.1 and 1.2) — contracts.md §2.1.

Orchestrates pure domain checks and the repository inside one transaction.
"""

from __future__ import annotations

import logging
from datetime import datetime

from src.domain.entities import Job, JobSpec, JobState
from src.domain.errors import Explanation, IdempotencyConflict
from src.domain.policies import (
    POLICY_NIGHT_WINDOW,
    RULE_JOBSPEC,
    check_queue_capacity,
    check_single_node_scope,
    check_spec_ranges,
    next_window_date,
    payload_digest,
)
from src.ports.dto import JobSubmissionRequestDTO, JobSubmissionResponseDTO
from src.ports.inbound import SubmissionOutcome
from src.ports.outbound import AuditEvent, ClockPort, DecisionRecord, SchedulerRepositoryPort

logger = logging.getLogger(__name__)


class JobSubmissionService:
    def __init__(self, repository: SchedulerRepositoryPort, clock: ClockPort):
        self._repo = repository
        self._clock = clock

    def submit_job(
        self, request: JobSubmissionRequestDTO, at: datetime | None = None
    ) -> JobSubmissionResponseDTO:
        return self.submit(request, at).response

    def submit(self, request: JobSubmissionRequestDTO, at: datetime | None = None) -> SubmissionOutcome:
        at = at or self._clock.now()
        spec = JobSpec(**request.spec.model_dump())

        # P1 then P2: pure checks run before any read or write (Q-fail: zero mutation).
        check_single_node_scope(spec)
        check_spec_ranges(spec)
        digest = payload_digest(spec)

        with self._repo.transaction():
            existing = self._repo.find_job_by_idempotency_key(request.idempotency_key)
            if existing is not None:
                return SubmissionOutcome(self._replay(existing, request, digest, at), created=False)

            check_queue_capacity(self._repo.count_active_jobs())

            job = Job(
                job_id=self._repo.next_job_id(),
                state=JobState.QUEUED_PENDING_WINDOW,
                actor_id=request.actor_id,
                idempotency_key=request.idempotency_key,
                payload_digest=digest,
                gpu_slots_requested=spec.gpu_slots_requested,
                required_vram_gb=spec.required_vram_gb,
                submitted_at=at,
            )
            self._repo.insert_job(job, spec)
            self._repo.append_decision(self._admission_record(job, spec, at))
            self._repo.append_audit_event(
                AuditEvent(
                    event_id=f"EVT-JOB_SUBMITTED-{job.job_id}",
                    event_type="JOB_SUBMITTED",
                    job_id=job.job_id,
                    node_id=None,
                    actor_id=job.actor_id,
                    payload={"job_id": job.job_id, "actor_id": job.actor_id,
                             "sim_timestamp": at.isoformat(), "payload_digest": digest},
                    occurred_at=at.isoformat(),
                )
            )
            position = self._repo.queue_position(job.job_id)

        logger.info("Job %s admitted to queue at position %d for actor %s", job.job_id, position, job.actor_id)
        return SubmissionOutcome(self._response(job, at, position), created=True)

    def _replay(
        self, existing: Job, request: JobSubmissionRequestDTO, digest: str, at: datetime
    ) -> JobSubmissionResponseDTO:
        """P3: same key + same digest returns the original job; a differing digest is a conflict."""
        if existing.payload_digest != digest:
            raise IdempotencyConflict(
                f"Idempotency key '{request.idempotency_key}' was previously registered with payload "
                f"SHA-256 '{existing.payload_digest}', differing from current payload SHA-256 '{digest}'.",
                Explanation(
                    rule_id=RULE_JOBSPEC,
                    summary="Idempotency key reused with a different payload.",
                    citations=(RULE_JOBSPEC,),
                    observed_values={"incoming_digest": digest},
                    thresholds={"original_digest": existing.payload_digest},
                ),
            )
        logger.info("Idempotent replay of %s for key %s", existing.job_id, request.idempotency_key)
        return self._response(existing, existing.submitted_at, self._repo.queue_position(existing.job_id))

    @staticmethod
    def _response(job: Job, admitted_at: datetime, position: int) -> JobSubmissionResponseDTO:
        return JobSubmissionResponseDTO(
            job_id=job.job_id,
            idempotency_key=job.idempotency_key,
            payload_digest=job.payload_digest,
            admitted_at=admitted_at.isoformat(),
            queue_position=position,
            estimated_first_window=next_window_date(admitted_at).isoformat(),
        )

    @staticmethod
    def _admission_record(job: Job, spec: JobSpec, at: datetime) -> DecisionRecord:
        """Q2/Q4: one ADMIT T-1 record citing validation, night-window and catalog authorities."""
        return DecisionRecord(
            decision_id=f"DEC-{job.job_id}-T-1",
            job_id=job.job_id,
            node_id=None,
            sim_timestamp=at.isoformat(),
            decision="ADMIT",
            transition="T-1",
            actor_id=job.actor_id,
            summary="Job specification validated and queued for the next night window.",
            citations=[RULE_JOBSPEC, POLICY_NIGHT_WINDOW, f"catalog:M5/{spec.model_id}@{spec.model_version}"],
            inputs={
                "gpu_slots_requested": spec.gpu_slots_requested,
                "required_vram_gb": spec.required_vram_gb,
                "checkpoint_interval_minutes": spec.checkpoint_interval_minutes,
                "estimated_duration_s": spec.estimated_duration_s,
                "payload_digest": job.payload_digest,
            },
        )
