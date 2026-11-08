"""Outbound Port: IdGeneratorPort (Deterministic Sequential ID Factory per AD-1, FR-1)."""

from typing import Protocol


class IdGeneratorPort(Protocol):
    """Protocol for generating deterministic identifiers."""

    def next_job_id(self) -> str:
        ...

    def next_decision_id(self) -> str:
        ...

    def next_activation_id(self) -> str:
        ...

    def next_checkpoint_id(self) -> str:
        ...

    def next_cordon_id(self) -> str:
        ...

    def next_event_id(self) -> str:
        ...
