"""
Pure domain entities for the Night Training Scheduler (Module 9).

Standard library only (dataclasses, enum, datetime types). No framework,
database or clock access is allowed in this package (INV-07).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class JobState(str, Enum):
    REJECTED = "REJECTED"
    QUEUED_PENDING_WINDOW = "QUEUED_PENDING_WINDOW"
    RUNNING = "RUNNING"
    CHECKPOINTING = "CHECKPOINTING"
    EVICTED_RESUMABLE = "EVICTED_RESUMABLE"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    EVICTION_FAILED = "EVICTION_FAILED"
    EXPIRED = "EXPIRED"


TERMINAL_STATES = frozenset(
    {JobState.COMPLETED, JobState.FAILED, JobState.REJECTED, JobState.EXPIRED}
)

# States a job may be admitted from at Window Activation (T-3 fresh, T-12 resume).
ADMISSIBLE_STATES = {
    JobState.QUEUED_PENDING_WINDOW: "T-3",
    JobState.EVICTED_RESUMABLE: "T-12",
}


@dataclass(frozen=True)
class JobSpec:
    image_digest: str
    gpu_slots_requested: int
    required_vram_gb: int
    checkpoint_interval_minutes: int
    estimated_duration_s: int
    model_id: str
    model_version: str
    storage_request_bytes: int
    worker_count: int = 1
    replicas: int = 1
    distributed_artifact_present: bool = False


@dataclass(frozen=True)
class Job:
    job_id: str
    state: JobState
    actor_id: str
    idempotency_key: str
    payload_digest: str
    gpu_slots_requested: int
    required_vram_gb: int
    submitted_at: datetime
    effective_priority: int = 100
    consecutive_nights_missed: int = 0
    last_node_id: str | None = None


@dataclass(frozen=True)
class Node:
    node_id: str
    vram_class_gb: int
    status: str
    # slot_id -> allocated job_id (None when free), ordered by slot_index
    slots: dict[str, str | None] = field(default_factory=dict)

    @property
    def free_slot_ids(self) -> list[str]:
        return [slot_id for slot_id, job_id in self.slots.items() if job_id is None]

    @property
    def allocations_held(self) -> int:
        return len({job_id for job_id in self.slots.values() if job_id is not None})


@dataclass(frozen=True)
class Placement:
    job_id: str
    node_id: str
    slot_ids: tuple[str, ...]
    vram_class_gb: int
    transition: str
    rank: int
    prior_node_preferred: bool
    won_on: str  # AD-4 key that decided the node: prior_node | lowest_allocations_held | node_id_asc | only_candidate
    candidates_considered: int


@dataclass(frozen=True)
class Deferral:
    job_id: str
    transition: str  # T-4a or T-4b
    reason_code: str  # NO_ELIGIBLE_NODE or CAPACITY_EXHAUSTED
    rank: int
