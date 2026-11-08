"""
Outbound ports (driven contracts). Implemented by adapters in src/adapters/outbound.
"""

from __future__ import annotations

from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol

from src.domain.entities import Job, JobSpec, Node, Placement


class ClockPort(Protocol):
    """Single source of simulated time (AD-1). Always America/Bogota (-05:00)."""

    def now(self) -> datetime: ...


@dataclass(frozen=True)
class DecisionRecord:
    decision_id: str
    job_id: str | None
    node_id: str | None
    sim_timestamp: str
    decision: str
    transition: str | None
    actor_id: str
    summary: str
    citations: list[str]
    inputs: dict[str, Any]


@dataclass(frozen=True)
class AuditEvent:
    event_id: str
    event_type: str
    job_id: str | None
    node_id: str | None
    actor_id: str
    payload: dict[str, Any]
    occurred_at: str


class SchedulerRepositoryPort(Protocol):
    """Persistence for jobs, fleet slots, decision records and audit events."""

    def transaction(self) -> AbstractContextManager[None]:
        """All writes inside the block commit atomically or not at all (AD-2, INV-04)."""
        ...

    # --- jobs -------------------------------------------------------------
    def find_job_by_idempotency_key(self, key: str) -> Job | None: ...

    def count_active_jobs(self) -> int: ...

    def next_job_id(self) -> str: ...

    def queue_position(self, job_id: str) -> int: ...

    def insert_job(self, job: Job, spec: JobSpec) -> None: ...

    def list_admissible_jobs(self) -> list[Job]: ...

    def mark_job_running(self, job_id: str, node_id: str) -> None: ...

    # --- fleet ------------------------------------------------------------
    def list_nodes(self) -> list[Node]: ...

    def allocate_slots(self, placement: Placement, held_since: str) -> None: ...

    # --- logs -------------------------------------------------------------
    def append_decision(self, record: DecisionRecord) -> None: ...

    def append_audit_event(self, event: AuditEvent) -> None: ...

    def find_audit_event(self, event_id: str) -> AuditEvent | None: ...
