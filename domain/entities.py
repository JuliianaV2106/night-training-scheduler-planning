"""
Core Domain Entities for Module 9: Night Training Scheduler.
Rule: Zero external framework, database, network, or wall-clock imports.
Uses only Python standard library dataclasses, Enum, and typing.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any


class JobState(str, Enum):
    """Canonical job states from PRD §4 and Annex Stories 9.4–9.6."""
    REJECTED = "REJECTED"
    QUEUED_PENDING_WINDOW = "QUEUED_PENDING_WINDOW"
    QUEUED_PREEMPTED = "QUEUED_PREEMPTED"
    RUNNING = "RUNNING"
    CHECKPOINTING = "CHECKPOINTING"
    EVICTED_RESUMABLE = "EVICTED_RESUMABLE"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    EVICTION_FAILED = "EVICTION_FAILED"
    EVICTED_FORCEFULLY = "EVICTED_FORCEFULLY"
    EXPIRED = "EXPIRED"


class NodeStatus(str, Enum):
    """Canonical node states from PRD and Annex Story 9.4."""
    HEALTHY = "HEALTHY"
    IDLE = "IDLE"
    DRAINING = "DRAINING"
    CORDONED = "CORDONED"
    CORDONED_DIRTY = "CORDONED_DIRTY"
    DIRTY_EVICTION_FAILED = "DIRTY_EVICTION_FAILED"
    RESERVED = "RESERVED"


class PriorityTier(str, Enum):
    """Priority tiers granted by Module 2 Policy Engine."""
    EXPLORATION = "EXPLORATION"
    NORMAL = "NORMAL"
    THESIS = "THESIS"
    URGENT = "URGENT"


class DecisionVerb(str, Enum):
    """Decision Record verbs from 001_night_training_scheduler_schema.sql."""
    ADMIT = "ADMIT"
    DEFER = "DEFER"
    PREEMPT = "PREEMPT"
    EVICT = "EVICT"
    FAIL = "FAIL"
    COMPLETE = "COMPLETE"
    REJECT = "REJECT"


@dataclass
class DomainError(Exception):
    """Pure domain error carrying canonical error code, HTTP status, and citation."""
    error_code: str
    message: str
    http_status: int
    retryable: bool
    rule_id: str = "self:JOBSPEC-VALIDATION-v1"
    citations: Tuple[str, ...] = ("self:JOBSPEC-VALIDATION-v1",)
    observed_values: Dict[str, Any] = field(default_factory=dict)
    thresholds: Dict[str, Any] = field(default_factory=dict)


@dataclass
class JobEntity:
    """Pure in-memory domain representation of a Training Job."""
    job_id: str
    state: str
    actor_id: str
    idempotency_key: str
    payload_digest: str
    gpu_slots_requested: int
    required_vram_gb: int
    checkpoint_interval_minutes: int
    estimated_duration_s: int
    image_digest: str
    model_id: str
    model_version: str
    storage_request_bytes: int
    submitted_at: str
    worker_count: int = 1
    replicas: int = 1
    effective_priority: int = 100
    granted_priority: str = "NORMAL"
    consecutive_nights_missed: int = 0
    admitted_nights: int = 0
    retry_count: int = 0
    preempted_in_window: int = 0
    allocated_node_id: Optional[str] = None
    state_reason: Optional[str] = None
    last_checkpoint_at: Optional[str] = None
    sigterm_sent_at: Optional[str] = None


@dataclass
class NodeEntity:
    """Pure in-memory domain representation of a Compute Node."""
    node_id: str
    vram_class_gb: int
    total_slots: int
    status: str = "HEALTHY"


@dataclass
class GpuSlotEntity:
    """Pure in-memory domain representation of a physical GPU slot."""
    slot_id: str
    node_id: str
    slot_index: int
    allocated_job_id: Optional[str] = None
    held_since: Optional[str] = None


@dataclass(frozen=True)
class DecisionRecordEntity:
    """Append-only Decision Record per AD-2 and AD-3."""
    decision_id: str
    job_id: Optional[str]
    node_id: Optional[str]
    sim_timestamp: str
    decision: str
    transition: Optional[str]
    actor_id: str
    summary: str
    citations: Tuple[str, ...]
    inputs: Dict[str, Any]
    supersedes: Optional[str] = None


@dataclass(frozen=True)
class CheckpointEntity:
    """Durable checkpoint metadata per AD-7."""
    checkpoint_id: str
    job_id: str
    path: str
    bytes: int
    step: int
    digest: str
    sim_timestamp: str
    state: str
    written_by: str
