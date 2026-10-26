"""
Simulated clock driven adapter (AD-1): never reads the host clock.

The instant is fixed by SIM_START_INSTANT; the pacer that advances it is Impl-2 scope.
"""

from __future__ import annotations

from datetime import datetime, timedelta


class SimulatedClock:
    def __init__(self, initial_iso: str):
        start = datetime.fromisoformat(initial_iso)
        if start.utcoffset() != timedelta(hours=-5):
            raise ValueError(f"Simulated instant must carry the America/Bogota offset -05:00: {initial_iso}")
        self._now = start

    def now(self) -> datetime:
        return self._now

