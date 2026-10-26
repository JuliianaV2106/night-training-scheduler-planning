"""
Mandatory Test Fixture: fake_clock
Provides deterministic, advanceable time without real sleep (NFR-1, NFR-7).
"""

from datetime import datetime, timedelta, timezone

# America/Bogota is UTC-05:00 permanently (no Daylight Saving Time)
CAMPUS_TZ = timezone(timedelta(hours=-5), name="America/Bogota")


class FakeClock:
    """Deterministic, advanceable simulated clock."""

    def __init__(self, initial_iso: str = "2026-10-18T21:59:00-05:00"):
        self._current_time = datetime.fromisoformat(initial_iso)

    def now(self) -> datetime:
        """Returns current simulated instant with America/Bogota offset."""
        return self._current_time

    def advance(self, seconds: int = 1) -> datetime:
        """Advances simulated time deterministically."""
        self._current_time += timedelta(seconds=seconds)
        return self._current_time

    def jump_to(self, target_iso: str) -> datetime:
        """Jumps simulated time to target instant."""
        target = datetime.fromisoformat(target_iso)
        if target < self._current_time:
            raise ValueError(f"Cannot jump backwards in time from {self._current_time} to {target}")
        self._current_time = target
        return self._current_time
