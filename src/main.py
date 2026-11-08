"""
Composition root: wires adapters to ports and builds the FastAPI application.

Run with: uvicorn src.main:build_from_env --factory --port 8000
"""

from __future__ import annotations

import logging
import sqlite3

from fastapi import FastAPI

from src.adapters.inbound.http_api import build_router, install_error_handlers
from src.adapters.outbound.simulated_clock import SimulatedClock
from src.adapters.outbound.sqlite_repository import SqliteSchedulerRepository, connect
from src.application.job_submission import JobSubmissionService
from src.application.window_activation import EXPECTED_NODES, EXPECTED_SLOTS, WindowActivationService
from src.config import Settings
from src.ports.outbound import ClockPort


def verify_fleet_seed(conn: sqlite3.Connection) -> None:
    """Startup dependency check: the migrated fleet must be 32 nodes / 33 GPU slots."""
    nodes = conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
    slots = conn.execute("SELECT COUNT(*) FROM gpu_slots").fetchone()[0]
    if (nodes, slots) != (EXPECTED_NODES, EXPECTED_SLOTS):
        raise RuntimeError(f"Fleet seed mismatch: {nodes} nodes / {slots} slots, expected 32 / 33")


def create_app(conn: sqlite3.Connection, clock: ClockPort) -> FastAPI:
    verify_fleet_seed(conn)
    repository = SqliteSchedulerRepository(conn)
    app = FastAPI(
        title="Module 9 — Night Training Scheduler API",
        version="1.0.0",
        description="Single-node night training scheduling for the Academic AI Compute Fabric.",
    )
    app.include_router(
        build_router(JobSubmissionService(repository, clock), WindowActivationService(repository), clock)
    )
    install_error_handlers(app, clock)
    return app


def build_from_env() -> FastAPI:
    settings = Settings.from_env()
    logging.basicConfig(level=settings.log_level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    return create_app(connect(settings.database_path), SimulatedClock(settings.sim_start_instant))

