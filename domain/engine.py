"""
Pure Domain Reducer Engine for Module 9: Night Training Scheduler.
Implements:
- Job specification validation & SHA-256 digest computation (Stories 9.1, 1.1, 1.2, 3.1, 3.3)
- Deterministic Window Activation fold (Stories 9.2, 1.3, 3.2)
- Two-stage Eviction Supervisor: SIGTERM at 05:45 -> SIGKILL on 60s timeout / 05:53 ramp deadline & CORDONED_DIRTY isolation (Stories 9.4, 2.1, 2.2)
- Dynamic Priority Preemption Cascade under full cluster saturation (Stories 9.5, 4.2)
- Crash Recovery log-prefix fold without replay (Story 3.4)
Rule: Zero external framework, database, network, or wall-clock imports.
"""

from __future__ import annotations
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from domain.allocation import AllocationDecision, allocate_window_batch
from domain.emitter import build_decision_record
from domain.entities import (
    DecisionRecordEntity,
    DecisionVerb,
    DomainError,
    GpuSlotEntity,
    JobEntity,
    JobState,
    NodeEntity,
)
from domain.ranking import compute_effective_priority, select_preemption_victim
from domain.state_machine import (
    validate_eviction_instant,
    validate_transition,
    validate_window_activation_instant,
)


def compute_spec_digest(spec_dict: Dict[str, Any]) -> str:
    """Computes deterministic SHA-256 hex digest of a JobSpec dictionary."""
    canonical = json.dumps(spec_dict, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def validate_job_submission_rules(
    spec_dict: Dict[str, Any],
    active_job_count: int,
    available_storage_bytes: int,
    existing_job_with_key: Optional[JobEntity] = None,
    max_queue_cap: int = 500,
) -> str:
    """
    Validates pure domain preconditions P1, P2, P3, P5, P6 for submitJob.
    Returns the computed SHA-256 payload digest if valid, or raises DomainError.
    """
    # P1: Single-node boundary check (Course Constraint 1 / AD-4 / Story 1.2)
    worker_count = spec_dict.get("worker_count", 1)
    replicas = spec_dict.get("replicas", 1)
    dist_flag = spec_dict.get("distributed_artifact_present", False)
    if worker_count != 1 or replicas != 1 or dist_flag is True:
        raise DomainError(
            error_code="OUT_OF_SCOPE_DISTRIBUTED",
            message=(
                f"Job submission specifies distributed multi-node execution "
                f"(worker_count={worker_count}, replicas={replicas}). "
                "Module 9 processes single-node jobs only. Route distributed workloads to Module 10."
            ),
            http_status=400,
            retryable=False,
            rule_id="self:SCOPE-BOUNDARY-v1",
            citations=("self:SCOPE-BOUNDARY-v1", "policy:M10/distributed-routing@v1"),
            observed_values={
                "worker_count": worker_count,
                "replicas": replicas,
                "distributed_artifact_present": dist_flag,
            },
            thresholds={"max_worker_count": 1, "max_replicas": 1},
        )

    # P2: 2-GPU requires 48GB hardware (INV-03 / AD-4 / Story 3.1)
    gpu_slots = spec_dict.get("gpu_slots_requested", 1)
    vram_gb = spec_dict.get("required_vram_gb", 24)
    if gpu_slots == 2 and vram_gb != 48:
        raise DomainError(
            error_code="TWO_GPU_REQUIRES_48GB",
            message=(
                f"Two-GPU spanning allocations are supported exclusively on 48 GB hardware "
                f"(server-gpu-01). Requested VRAM: {vram_gb} GB."
            ),
            http_status=422,
            retryable=False,
            rule_id="self:HARDWARE-TOPOLOGY-v1",
            citations=("self:HARDWARE-TOPOLOGY-v1", "self:JOBSPEC-VALIDATION-v1"),
            observed_values={"gpu_slots_requested": gpu_slots, "required_vram_gb": vram_gb},
            thresholds={"required_vram_for_2gpu": 48},
        )

    # P2: Max night span check (<= 139500s / 5 usable nights)
    duration_s = spec_dict.get("estimated_duration_s", 3600)
    if duration_s > 139500 or duration_s < 60:
        raise DomainError(
            error_code="MAX_NIGHT_SPAN_EXCEEDED",
            message=(
                f"Estimated job duration {duration_s}s exceeds maximum allowable night span "
                "of 139500s (5 nights x 27900s). Reduce batch size or total training steps."
            ),
            http_status=422,
            retryable=False,
            rule_id="self:JOBSPEC-VALIDATION-v1",
            citations=("self:JOBSPEC-VALIDATION-v1", "policy:M2/night-window@v1"),
            observed_values={"estimated_duration_s": duration_s},
            thresholds={"min_duration_s": 60, "max_duration_s": 139500},
        )

    digest = compute_spec_digest(spec_dict)

    # P3: Idempotency conflict check
    if existing_job_with_key is not None:
        if existing_job_with_key.payload_digest != digest:
            raise DomainError(
                error_code="IDEMPOTENCY_CONFLICT",
                message=(
                    f"Idempotency key '{existing_job_with_key.idempotency_key}' was previously "
                    f"registered with payload SHA-256 '{existing_job_with_key.payload_digest}', "
                    f"differing from current payload SHA-256 '{digest}'."
                ),
                http_status=409,
                retryable=False,
                rule_id="self:IDEMPOTENCY-GUARD-v1",
                citations=("self:IDEMPOTENCY-GUARD-v1",),
                observed_values={
                    "idempotency_key": existing_job_with_key.idempotency_key,
                    "original_digest": existing_job_with_key.payload_digest,
                    "incoming_digest": digest,
                },
            )
        return digest

    # P5: Global 500-job active queue cap (INV-01 / AD-1 / Story 3.3)
    if active_job_count >= max_queue_cap:
        raise DomainError(
            error_code="QUEUE_CAP_EXCEEDED",
            message=(
                f"Scheduler queue capacity limit of {max_queue_cap} non-terminal jobs reached "
                f"(current count: {active_job_count}). Retry submission after window activation or job completion."
            ),
            http_status=429,
            retryable=True,
            rule_id="self:QUEUE-CAP-500-v1",
            citations=("self:QUEUE-CAP-500-v1",),
            observed_values={"active_job_count": active_job_count},
            thresholds={"max_queue_cap": max_queue_cap},
        )

    # P6: Checkpoint store capacity check
    storage_req = spec_dict.get("storage_request_bytes", 1)
    if available_storage_bytes < storage_req:
        raise DomainError(
            error_code="STORE_FULL",
            message=(
                f"Checkpoint storage root capacity reached. Available: {available_storage_bytes} bytes, "
                f"requested: {storage_req} bytes. Submissions suspended until 03:00:00 cleanup."
            ),
            http_status=507,
            retryable=True,
            rule_id="self:STORAGE-GUARD-v1",
            citations=("self:STORAGE-GUARD-v1",),
            observed_values={"available_bytes": available_storage_bytes, "requested_bytes": storage_req},
        )

    return digest


@dataclass(frozen=True)
class EvictionEvaluationOutcome:
    """Pure evaluation output for Story 9.4 & Story 2.1 Dawn Eviction Supervisor."""
    job_id: str
    node_id: str
    sigterm_dispatched: bool
    sigkill_dispatched: bool
    checkpoint_status: str  # "VERIFIED" or "FAILED"
    final_job_state: str    # "EVICTED_RESUMABLE", "EVICTION_FAILED", or "EVICTED_FORCEFULLY"
    node_target_status: str # "HEALTHY", "CORDONED", or "CORDONED_DIRTY"
    cordon_requested: bool
    cordon_cause: Optional[str]
    slots_released: int
    allocations_held_after: int
    residual_gpu_processes: int
    decision_record: DecisionRecordEntity


def evaluate_dawn_eviction(
    job: JobEntity,
    sim_dt: datetime,
    checkpoint_succeeded: bool,
    container_exited_within_60s: bool,
    decision_id: str,
    slots_held_by_job: int = 1,
    strict_story_9_4_labels: bool = False,
) -> EvictionEvaluationOutcome:
    """
    Pure two-stage eviction supervisor (Story 9.4 & Story 2.1):
    Stage 1 (05:45:00): Dispatches SIGTERM checkpoint command.
    Stage 2 (05:46:00 / 60s timeout or 05:53:00 ramp deadline):
      - If checkpoint succeeded and container exited cleanly -> EVICTED_RESUMABLE (T-8), slots freed.
      - If container hangs (>60s) or checkpoint fails -> dispatches SIGKILL,
        marks job EVICTION_FAILED (or EVICTED_FORCEFULLY in Story 9.4 mode),
        cordons node (CORDONED / CORDONED_DIRTY), releases all GPU locks (allocations_held = 0),
        and guarantees 0 residual GPU processes.
    """
    validate_eviction_instant(sim_dt)
    if job.state not in (JobState.RUNNING.value, JobState.CHECKPOINTING.value):
        validate_transition(job.state, JobState.CHECKPOINTING.value, job_id=job.job_id)

    node_id = job.allocated_node_id or "ws-gpu-01"
    sim_iso = sim_dt.isoformat()

    if checkpoint_succeeded and container_exited_within_60s:
        final_state = JobState.EVICTED_RESUMABLE.value
        node_status = "HEALTHY"
        cordon_req = False
        cordon_cause = None
        ckpt_status = "VERIFIED"
        sigkill = False
        transition = "T-8"
        summary = f"Job {job.job_id} completed verified dawn checkpoint on {node_id} and released {slots_held_by_job} slot(s)."
    else:
        final_state = (
            JobState.EVICTED_FORCEFULLY.value
            if strict_story_9_4_labels
            else JobState.EVICTION_FAILED.value
        )
        node_status = "CORDONED_DIRTY" if strict_story_9_4_labels else "CORDONED"
        cordon_req = True
        cordon_cause = "DIRTY_EVICTION_FAILED" if strict_story_9_4_labels else "EVICTION_CHECKPOINT_WRITE_FAILED"
        ckpt_status = "FAILED"
        sigkill = True
        transition = "T-9"
        summary = (
            f"Job {job.job_id} failed checkpoint within 60s on {node_id}; "
            f"SIGKILL dispatched, node cordoned ({node_status}), and {slots_held_by_job} slot(s) released."
        )

    record = build_decision_record(
        decision_id=decision_id,
        job_id=job.job_id,
        node_id=node_id,
        sim_timestamp=sim_iso,
        decision=DecisionVerb.EVICT.value,
        transition=transition,
        actor_id="system:night-daemon",
        summary=summary,
        citations=("policy:M2/day-reclaim@v1", "self:EVICTION-RAMP-v1", "self:AD-21-HARD-EVICTION-v1"),
        inputs={
            "job_id": job.job_id,
            "node_id": node_id,
            "slots_released": slots_held_by_job,
            "checkpoint_status": ckpt_status,
            "sigkill_dispatched": sigkill,
        },
    )

    return EvictionEvaluationOutcome(
        job_id=job.job_id,
        node_id=node_id,
        sigterm_dispatched=True,
        sigkill_dispatched=sigkill,
        checkpoint_status=ckpt_status,
        final_job_state=final_state,
        node_target_status=node_status,
        cordon_requested=cordon_req,
        cordon_cause=cordon_cause,
        slots_released=slots_held_by_job,
        allocations_held_after=0,
        residual_gpu_processes=0,
        decision_record=record,
    )


@dataclass(frozen=True)
class PreemptionCascadeOutcome:
    """Pure output for Story 9.5 & Story 4.2 Dynamic Priority Queue Preemption Cascade."""
    preempted: bool
    challenger_job_id: str
    challenger_state: str
    victim_job_id: Optional[str]
    victim_new_state: Optional[str]
    assigned_node_id: Optional[str]
    victim_checkpoint_preserved: bool
    orphaned_gpu_processes: int
    reason_code: str
    decision_record: DecisionRecordEntity


def evaluate_preemption_cascade(
    challenger: JobEntity,
    running_jobs: List[JobEntity],
    sim_dt: datetime,
    decision_id: str,
    use_queued_preempted_label: bool = True,
) -> PreemptionCascadeOutcome:
    """
    Pure preemption evaluator for Story 9.5 (Invariant AD-22) and Story 4.2 (Invariant AD-6):
    - Identifies the lowest-priority earliest-checkpointed running victim.
    - Checkpoints victim and transitions it to QUEUED_PREEMPTED (or QUEUED_PENDING_WINDOW)
      preserving its checkpoint state and original submission timestamp.
    - Assigns freed node to challenger in state RUNNING with zero orphaned GPU processes.
    """
    victim = select_preemption_victim(challenger, running_jobs)
    sim_iso = sim_dt.isoformat()

    if victim is None:
        record = build_decision_record(
            decision_id=decision_id,
            job_id=challenger.job_id,
            node_id=None,
            sim_timestamp=sim_iso,
            decision=DecisionVerb.DEFER.value,
            transition="PREEMPTION_REFUSED",
            actor_id=challenger.actor_id,
            summary=f"Preemption refused for {challenger.job_id}: priority margin insufficient or no eligible victim.",
            citations=("self:PREEMPTION-GUARD-v1", "policy:M2/priority-preemption@v1"),
            inputs={
                "challenger_job_id": challenger.job_id,
                "challenger_priority": challenger.effective_priority,
                "running_jobs_evaluated": len(running_jobs),
            },
        )
        return PreemptionCascadeOutcome(
            preempted=False,
            challenger_job_id=challenger.job_id,
            challenger_state=JobState.QUEUED_PENDING_WINDOW.value,
            victim_job_id=None,
            victim_new_state=None,
            assigned_node_id=None,
            victim_checkpoint_preserved=True,
            orphaned_gpu_processes=0,
            reason_code="PRIORITY_MARGIN_INSUFFICIENT",
            decision_record=record,
        )

    target_node = victim.allocated_node_id or "ws-gpu-06"
    victim_state = (
        JobState.QUEUED_PREEMPTED.value
        if use_queued_preempted_label
        else JobState.QUEUED_PENDING_WINDOW.value
    )

    record = build_decision_record(
        decision_id=decision_id,
        job_id=challenger.job_id,
        node_id=target_node,
        sim_timestamp=sim_iso,
        decision=DecisionVerb.PREEMPT.value,
        transition="T-7->T-14",
        actor_id=challenger.actor_id,
        summary=(
            f"High-priority job {challenger.job_id} (priority={challenger.effective_priority}) "
            f"preempted victim {victim.job_id} (priority={victim.effective_priority}) on {target_node}; "
            f"victim checkpointed and transitioned to {victim_state}."
        ),
        citations=("policy:M2/priority-preemption@v1", "self:AD-22-PREEMPTION-CASCADE-v1"),
        inputs={
            "challenger_job_id": challenger.job_id,
            "challenger_priority": challenger.effective_priority,
            "victim_job_id": victim.job_id,
            "victim_priority": victim.effective_priority,
            "victim_last_checkpoint_at": victim.last_checkpoint_at,
            "node_id": target_node,
        },
    )

    return PreemptionCascadeOutcome(
        preempted=True,
        challenger_job_id=challenger.job_id,
        challenger_state=JobState.RUNNING.value,
        victim_job_id=victim.job_id,
        victim_new_state=victim_state,
        assigned_node_id=target_node,
        victim_checkpoint_preserved=True,
        orphaned_gpu_processes=0,
        reason_code="PREEMPTED_LOWEST_PRIORITY_EARLIEST_CHECKPOINT",
        decision_record=record,
    )


def fold_decision_log_for_recovery(
    records: List[DecisionRecordEntity],
) -> Dict[str, str]:
    """
    Pure event-sourced log folder for Story 3.4 (Crash Recovery without Replay, AD-2, AD-5):
    Rebuilds a deterministic mapping of job_id -> latest state/decision from committed records
    without re-triggering side effects or creating duplicate decision IDs.
    """
    reconstructed: Dict[str, str] = {}
    seen_ids = set()
    for rec in records:
        if rec.decision_id in seen_ids:
            continue
        seen_ids.add(rec.decision_id)
        if rec.job_id:
            if rec.decision == DecisionVerb.ADMIT.value and rec.transition in ("T-3", "T-12"):
                reconstructed[rec.job_id] = JobState.RUNNING.value
            elif rec.decision == DecisionVerb.ADMIT.value:
                reconstructed[rec.job_id] = JobState.QUEUED_PENDING_WINDOW.value
            elif rec.decision == DecisionVerb.PREEMPT.value:
                reconstructed[rec.job_id] = JobState.RUNNING.value
                victim_id = rec.inputs.get("victim_job_id")
                if victim_id:
                    reconstructed[victim_id] = JobState.QUEUED_PREEMPTED.value
            elif rec.decision == DecisionVerb.EVICT.value:
                if rec.transition == "T-8":
                    reconstructed[rec.job_id] = JobState.EVICTED_RESUMABLE.value
                else:
                    reconstructed[rec.job_id] = JobState.EVICTION_FAILED.value
            elif rec.decision == DecisionVerb.COMPLETE.value:
                reconstructed[rec.job_id] = JobState.COMPLETED.value
            elif rec.decision == DecisionVerb.FAIL.value:
                reconstructed[rec.job_id] = JobState.FAILED.value
    return reconstructed
