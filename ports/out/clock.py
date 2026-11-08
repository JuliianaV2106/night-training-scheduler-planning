"""Outbound Port: ClockPort (Deterministic Time Injection per AD-1, NFR-1)."""

from datetime import datetime
from typing import Protocol


class ClockPort(Protocol):
    """Protocol for deterministic time injection."""

    def now(self) -> datetime:
        """Returns current simulated instant with America/Bogota (-05:00) offset."""
        ...

    def advance(self, seconds: int = 1) -> datetime:
        """Advances simulated clock by `seconds`."""
        ...

    def jump_to(self, target_iso: str) -> datetime:
        """Jumps simulated clock forward to `target_iso`."""
        ...
