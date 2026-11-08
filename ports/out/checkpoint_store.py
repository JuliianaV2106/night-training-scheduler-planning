"""Outbound Port: CheckpointStorePort (AD-7 5-Step Protocol Store)."""

from typing import Optional, Protocol
from domain.entities import CheckpointEntity


class CheckpointStorePort(Protocol):
    """Protocol for writing and verifying durable job checkpoints."""

    def available_bytes(self) -> int:
        ...

    def write_verified_checkpoint(
        self,
        checkpoint_id: str,
        job_id: str,
        step: int,
        sim_timestamp: str,
        written_by: str = "ramp",
    ) -> CheckpointEntity:
        ...

    def verify_checkpoint_integrity(self, checkpoint_id: str) -> bool:
        ...
