"""
Settings loaded from environment variables (see .env.example) and validated at startup.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Settings:
    database_path: str
    sim_start_instant: str
    log_level: str

    @classmethod
    def from_env(cls) -> Settings:
        settings = cls(
            database_path=os.getenv("DATABASE_PATH", "data/scheduler.db"),
            sim_start_instant=os.getenv("SIM_START_INSTANT", "2026-10-18T14:30:00-05:00"),
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        )
        settings.validate()
        return settings

    def validate(self) -> None:
        try:
            instant = datetime.fromisoformat(self.sim_start_instant)
        except ValueError as exc:
            raise ValueError(f"SIM_START_INSTANT is not ISO-8601: {self.sim_start_instant!r}") from exc
        if instant.tzinfo is None:
            raise ValueError("SIM_START_INSTANT must include the -05:00 offset (America/Bogota)")
        if self.log_level not in logging.getLevelNamesMapping():
            raise ValueError(f"LOG_LEVEL is not a valid logging level: {self.log_level!r}")
        if not self.database_path:
            raise ValueError("DATABASE_PATH must not be empty")
