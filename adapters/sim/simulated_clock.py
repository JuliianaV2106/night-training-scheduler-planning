"""
Driven Adapter: SimulatedClockAdapter (Ports & Adapters timekeeper per AD-1, NFR-1, FR-28).
Supports deterministic advancing, jumping, and fast-forward time-warp multipliers (1x, 10x, 60x, 1440x)
with zero wall-clock sleeps.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

CAMPUS_TZ = timezone(timedelta(hours=-5), name="America/Bogota")


class SimulatedClockAdapter:
    """Deterministic timekeeper implementing ClockPort."""

    def __init__(self, initial_iso: str = "2026-10-18T14:00:00-05:00", speed_multiplier: int = 1):
        self._current_time = datetime.fromisoformat(initial_iso)
        self._speed_multiplier = speed_multiplier

    @property
    def speed_multiplier(self) -> int:
        return self._speed_multiplier

    def set_speed(self, multiplier: int) -> int:
        if multiplier not in (1, 10, 60, 1440):
            raise ValueError(f"Unsupported time-warp multiplier: {multiplier}")
        self._speed_multiplier = multiplier
        return self._speed_multiplier

    def now(self) -> datetime:
        return self._current_time

    def now_iso(self) -> str:
        return self._current_time.isoformat()

    def advance(self, seconds: int = 1) -> datetime:
        self._current_time += timedelta(seconds=seconds)
        return self._current_time

    def jump_to(self, target_iso: str) -> datetime:
        target = datetime.fromisoformat(target_iso)
        if target < self._current_time:
            raise ValueError(f"Cannot jump backwards in time from {self._current_time} to {target}")
        self._current_time = target
        return self._current_time

    def set_time(self, target_iso: str) -> datetime:
        """Sets clock to exact ISO timestamp (used by simulation reset / time-warp controls)."""
        self._current_time = datetime.fromisoformat(target_iso)
        return self._current_time
