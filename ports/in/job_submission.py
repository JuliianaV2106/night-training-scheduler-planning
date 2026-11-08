"""
Inbound Port & Application Service: JobSubmissionService (`ports/in/job_submission.py`).
Implements Contract 1 (`submitJob`), Stories 9.1, 1.1, 1.2, 3.1, 3.3, 4.1, 4.3.
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional

from adapters.db.sqlite_repository import SQLiteRepositoryAdapter
from adapters.sim.delegated_fixtures import DelegatedFixturesAdapter
from adapters.sim.filesystem_checkpoint_store import FilesystemCheckpointStoreAdapter
from adapters.sim.simulated_clock import SimulatedClockAdapter
from domain.emitter import build_decision_record
from domain.engine import validate_job_submission_rules
from domain.entities import DecisionVerb, DomainError, JobEntity, JobState
from dto import (
    ExplanationDTO,
    JobSubmissionRequestDTO,
    JobSubmissionResponseDTO,
)


class JobSubmissionService:
    """Use-Case handler for single-node job submission, validation, and idempotency."""

    def __init__(
        self,
        repo: SQLiteRepositoryAdapter,
        clock: Optional[SimulatedClockAdapter] = None,
        delegates: Optional[DelegatedFixturesAdapter] = None,
        checkpoint_store: Optional[FilesystemCheckpointStoreAdapter] = None,
        raise_on_error: bool = False,
    ):
        self._repo = repo
        self._clock = clock or SimulatedClockAdapter()
        self._delegates = delegates or DelegatedFixturesAdapter()
        self._checkpoint_store = checkpoint_store or FilesystemCheckpointStoreAdapter()
        self._raise_on_error = raise_on_error

    def submit_job(
        self,
        request: JobSubmissionRequestDTO,
        at: Optional[datetime] = None,
    ) -> Optional[JobSubmissionResponseDTO]:
        sim_dt = at or self._clock.now()
        sim_iso = sim_dt.isoformat()
        spec_dict = request.spec.model_dump()

        try:
            # Fast-path read check for already-persisted idempotency key (avoids BEGIN IMMEDIATE write lock on replays)
            existing_fast = self._repo.get_job_by_idempotency_key(request.idempotency_key)
            if existing_fast is not None:
                validate_job_submission_rules(
                    spec_dict=spec_dict,
                    active_job_count=0,
                    available_storage_bytes=self._checkpoint_store.available_bytes(),
                    existing_job_with_key=existing_fast,
                )
                citations = [
                    "self:JOBSPEC-VALIDATION-v1",
                    "policy:M2/night-window@v1",
                    f"catalog:M5/{existing_fast.model_id}@{existing_fast.model_version}",
                ]
                inputs = {
                    "gpu_slots_requested": existing_fast.gpu_slots_requested,
                    "required_vram_gb": existing_fast.required_vram_gb,
                    "worker_count": existing_fast.worker_count,
                }
                return JobSubmissionResponseDTO(
                    job_id=existing_fast.job_id,
                    state="QUEUED_PENDING_WINDOW",
                    idempotency_key=existing_fast.idempotency_key,
                    payload_digest=existing_fast.payload_digest,
                    admitted_at=existing_fast.submitted_at,
                    queue_position=1,
                    estimated_first_window=sim_dt.strftime("%Y-%m-%d"),
                    citations=citations,
                    inputs=inputs,
                    explanation=ExplanationDTO(
                        rule_id="self:JOBSPEC-VALIDATION-v1",
                        summary=f"Idempotent replay for {existing_fast.job_id}.",
                        observed_values=inputs,
                        thresholds={"max_queue_cap": 500},
                        citations=citations,
                    ),
                )

            with self._repo.atomic_transaction():
                existing = self._repo.get_job_by_idempotency_key(request.idempotency_key)
                active_count = self._repo.count_active_jobs()
                avail_bytes = self._checkpoint_store.available_bytes()

                digest = validate_job_submission_rules(
                    spec_dict=spec_dict,
                    active_job_count=active_count,
                    available_storage_bytes=avail_bytes,
                    existing_job_with_key=existing,
                )

                # Double-checked lock inside atomic_transaction if another thread inserted between fast-path and lock
                if existing is not None:
                    citations = [
                        "self:JOBSPEC-VALIDATION-v1",
                        "policy:M2/night-window@v1",
                        f"catalog:M5/{existing.model_id}@{existing.model_version}",
                    ]
                    inputs = {
                        "gpu_slots_requested": existing.gpu_slots_requested,
                        "required_vram_gb": existing.required_vram_gb,
                        "worker_count": existing.worker_count,
                    }
                    return JobSubmissionResponseDTO(
                        job_id=existing.job_id,
                        state="QUEUED_PENDING_WINDOW",
                        idempotency_key=existing.idempotency_key,
                        payload_digest=existing.payload_digest,
                        admitted_at=existing.submitted_at,
                        queue_position=1,
                        estimated_first_window=sim_dt.strftime("%Y-%m-%d"),
                        citations=citations,
                        inputs=inputs,
                        explanation=ExplanationDTO(
                            rule_id="self:JOBSPEC-VALIDATION-v1",
                            summary=f"Idempotent replay for {existing.job_id}.",
                            observed_values=inputs,
                            thresholds={"max_queue_cap": 500},
                            citations=citations,
                        ),
                    )

                # Verify delegated fixtures (M1, M2, M5, M8)
                entitlement = self._delegates.verify_actor_entitlement(request.actor_id)
                self._delegates.verify_model_catalog(request.spec.model_id, request.spec.model_version)
                self._delegates.verify_quota_budget(request.actor_id, request.spec.gpu_slots_requested)

                job_id = self._repo.next_sequence_id("JOB", "jobs", "job_id")
                decision_id = self._repo.next_sequence_id("DEC", "decision_records", "decision_id")
                event_id = self._repo.next_sequence_id("EVT", "audit_events", "event_id")

                citations = [
                    "self:JOBSPEC-VALIDATION-v1",
                    "policy:M2/night-window@v1",
                    f"catalog:M5/{request.spec.model_id}@{request.spec.model_version}",
                ]
                inputs = {
                    "gpu_slots_requested": request.spec.gpu_slots_requested,
                    "required_vram_gb": request.spec.required_vram_gb,
                    "worker_count": request.spec.worker_count,
                    "estimated_duration_s": request.spec.estimated_duration_s,
                }

                job_entity = JobEntity(
                    job_id=job_id,
                    state=JobState.QUEUED_PENDING_WINDOW.value,
                    actor_id=request.actor_id,
                    idempotency_key=request.idempotency_key,
                    payload_digest=digest,
                    gpu_slots_requested=request.spec.gpu_slots_requested,
                    required_vram_gb=request.spec.required_vram_gb,
                    checkpoint_interval_minutes=request.spec.checkpoint_interval_minutes,
                    estimated_duration_s=request.spec.estimated_duration_s,
                    image_digest=request.spec.image_digest,
                    model_id=request.spec.model_id,
                    model_version=request.spec.model_version,
                    storage_request_bytes=request.spec.storage_request_bytes,
                    submitted_at=sim_iso,
                    worker_count=request.spec.worker_count,
                    replicas=request.spec.replicas,
                    effective_priority=entitlement["effective_priority"],
                    granted_priority=entitlement["granted_priority"],
                )

                decision_record = build_decision_record(
                    decision_id=decision_id,
                    job_id=job_id,
                    node_id=None,
                    sim_timestamp=sim_iso,
                    decision=DecisionVerb.ADMIT.value,
                    transition="T-1",
                    actor_id=request.actor_id,
                    summary=f"Admitted single-node job {job_id} to pending night queue.",
                    citations=citations,
                    inputs=inputs,
                )

                queue_pos = self._repo.insert_job_and_decision_atomic(
                    job=job_entity,
                    decision=decision_record,
                    event_id=event_id,
                )

                return JobSubmissionResponseDTO(
                    job_id=job_id,
                    state="QUEUED_PENDING_WINDOW",
                    idempotency_key=request.idempotency_key,
                    payload_digest=digest,
                    admitted_at=sim_iso,
                    queue_position=queue_pos,
                    estimated_first_window=sim_dt.strftime("%Y-%m-%d"),
                    citations=citations,
                    inputs=inputs,
                    explanation=ExplanationDTO(
                        rule_id="self:JOBSPEC-VALIDATION-v1",
                        summary=decision_record.summary,
                        observed_values=inputs,
                        thresholds={"max_queue_cap": 500, "max_worker_count": 1},
                        citations=citations,
                    ),
                )
        except DomainError:
            if self._raise_on_error:
                raise
            return None
