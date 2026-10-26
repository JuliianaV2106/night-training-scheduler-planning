"""
Submission preconditions (submitJob P1, P2, P5) and night-window time rules.

Pure functions: every instant is passed in by the caller (ClockPort), never read here.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict
from datetime import date, datetime, time, timedelta

from src.domain.entities import JobSpec
from src.domain.errors import (
    Explanation,
    MaxNightSpanExceeded,
    OutOfScopeDistributed,
    QueueCapExceeded,
    TwoGpuRequires48Gb,
    ValidationFailed,
)

QUEUE_CAP = 500
MAX_NIGHT_SPAN_S = 139_500  # 5 nights x 27 900 s usable (PRD A-21)
WINDOW_OPEN = time(22, 0, 0)
ACTIVATION_TOLERANCE_S = 2
IMAGE_DIGEST_RE = re.compile(r"^sha256:[a-f0-9]{64}$")

RULE_SCOPE = "self:SCOPE-BOUNDARY-v1"
RULE_JOBSPEC = "self:JOBSPEC-VALIDATION-v1"
RULE_QUEUE_CAP = "self:QUEUE-DEPTH-CAP-v1"
RULE_RANKING = "self:ADMISSION-RANKING-v1"
POLICY_NIGHT_WINDOW = "policy:M2/night-window@v1"


def payload_digest(spec: JobSpec) -> str:
    """SHA-256 over the canonical (sorted-key, compact) JSON form of the spec."""
    canonical = json.dumps(asdict(spec), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def check_single_node_scope(spec: JobSpec) -> None:
    """P1: Module 9 only schedules single-node jobs (Story 1.2)."""
    if spec.worker_count != 1 or spec.replicas != 1 or spec.distributed_artifact_present:
        raise OutOfScopeDistributed(
            f"Job submission specifies distributed multi-node execution "
            f"(worker_count={spec.worker_count}, replicas={spec.replicas}). "
            f"Module 9 processes single-node jobs only. Route distributed workloads to Module 10.",
            Explanation(
                rule_id=RULE_SCOPE,
                summary="Distributed specification is out of Module 9 scope; route to Module 10.",
                citations=(RULE_SCOPE,),
                observed_values={
                    "worker_count": spec.worker_count,
                    "replicas": spec.replicas,
                    "distributed_artifact_present": spec.distributed_artifact_present,
                },
                thresholds={"worker_count": 1, "replicas": 1, "distributed_artifact_present": False},
            ),
        )


def _field_failure(field_name: str, observed: object, constraint: str) -> ValidationFailed:
    return ValidationFailed(
        f"Job specification field '{field_name}' failed validation rule '{RULE_JOBSPEC}': "
        f"observed value '{observed}', required threshold '{constraint}'.",
        Explanation(
            rule_id=RULE_JOBSPEC,
            summary=f"Field '{field_name}' is outside its contract range.",
            citations=(RULE_JOBSPEC,),
            observed_values={field_name: observed},
            thresholds={field_name: constraint},
        ),
    )


def check_spec_ranges(spec: JobSpec) -> None:
    """P2: type and range checks. Re-asserted here so the domain never trusts the adapter."""
    if not IMAGE_DIGEST_RE.match(spec.image_digest):
        raise _field_failure("image_digest", spec.image_digest, "^sha256:[a-f0-9]{64}$")
    if spec.gpu_slots_requested not in (1, 2):
        raise _field_failure("gpu_slots_requested", spec.gpu_slots_requested, "{1, 2}")
    if spec.required_vram_gb not in (24, 48):
        raise _field_failure("required_vram_gb", spec.required_vram_gb, "{24, 48}")
    if spec.gpu_slots_requested == 2 and spec.required_vram_gb != 48:
        raise TwoGpuRequires48Gb(
            "Two-GPU spanning allocations are supported exclusively on 48 GB hardware "
            f"(server-gpu-01). Requested VRAM: {spec.required_vram_gb} GB.",
            Explanation(
                rule_id=RULE_JOBSPEC,
                summary="A 2-GPU job must request the 48 GB class (AD-4, INV-03).",
                citations=(RULE_JOBSPEC,),
                observed_values={"gpu_slots_requested": 2, "required_vram_gb": spec.required_vram_gb},
                thresholds={"required_vram_gb": 48},
            ),
        )
    if not 1 <= spec.checkpoint_interval_minutes <= 30:
        raise _field_failure("checkpoint_interval_minutes", spec.checkpoint_interval_minutes, "[1, 30]")
    if spec.estimated_duration_s > MAX_NIGHT_SPAN_S:
        raise MaxNightSpanExceeded(
            f"Estimated job duration {spec.estimated_duration_s}s exceeds maximum allowable night span "
            f"of {MAX_NIGHT_SPAN_S}s (5 nights x 27900s). Reduce batch size or total training steps.",
            Explanation(
                rule_id=RULE_JOBSPEC,
                summary="Estimated duration exceeds the Max Night Span.",
                citations=(RULE_JOBSPEC,),
                observed_values={"estimated_duration_s": spec.estimated_duration_s},
                thresholds={"estimated_duration_s": MAX_NIGHT_SPAN_S},
            ),
        )
    if spec.estimated_duration_s < 60:
        raise _field_failure("estimated_duration_s", spec.estimated_duration_s, "[60, 139500]")
    if spec.storage_request_bytes <= 0:
        raise _field_failure("storage_request_bytes", spec.storage_request_bytes, "> 0")


def check_queue_capacity(active_jobs: int) -> None:
    """P5 / INV-01: at most 500 non-terminal jobs."""
    if active_jobs >= QUEUE_CAP:
        raise QueueCapExceeded(
            f"Scheduler queue capacity limit of {QUEUE_CAP} non-terminal jobs reached "
            f"(current count: {active_jobs}). Retry submission after window activation or job completion.",
            Explanation(
                rule_id=RULE_QUEUE_CAP,
                summary="Queue depth cap reached.",
                citations=(RULE_QUEUE_CAP,),
                observed_values={"active_jobs": active_jobs},
                thresholds={"queue_cap": QUEUE_CAP},
            ),
        )


def next_window_date(at: datetime) -> date:
    """Date of the next 22:00:00 Window Activation at or after `at`."""
    if at.timetz().replace(tzinfo=None) < WINDOW_OPEN:
        return at.date()
    return at.date() + timedelta(days=1)


def is_activation_instant(at: datetime) -> bool:
    """activateWindow P1: time component is 22:00:00 within +/- 2 simulated seconds."""
    opening = datetime.combine(at.date(), WINDOW_OPEN, tzinfo=at.tzinfo)
    candidates = (opening, opening + timedelta(days=1))
    return any(abs((at - c).total_seconds()) <= ACTIVATION_TOLERANCE_S for c in candidates)
