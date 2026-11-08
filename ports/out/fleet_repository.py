"""Outbound Port: FleetRepositoryPort (Node, Slot & Job Store Interface per AD-4)."""

from typing import List, Optional, Protocol
from domain.entities import GpuSlotEntity, JobEntity, NodeEntity


class FleetRepositoryPort(Protocol):
    """Persistence interface for nodes, GPU slots, and training jobs."""

    def get_nodes(self) -> List[NodeEntity]:
        ...

    def get_slots(self) -> List[GpuSlotEntity]:
        ...

    def get_job(self, job_id: str) -> Optional[JobEntity]:
        ...

    def get_job_by_idempotency_key(self, idempotency_key: str) -> Optional[JobEntity]:
        ...

    def count_active_jobs(self) -> int:
        ...
