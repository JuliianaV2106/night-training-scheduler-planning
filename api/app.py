"""
FastAPI Application Factory for Module 9: Night Training Scheduler (`api/app.py`).
Wires hexagonal Driving Adapters (`api/routes/*`) to Inbound Ports (`ports/in/*`)
and Driven Adapters (`adapters/db/*`, `adapters/sim/*`).
"""

from typing import Optional
from pathlib import Path
import sqlite3
import sys
from fastapi import FastAPI

_ROOT_DIR = Path(__file__).parent.parent
_SCHEMAS_DIR = _ROOT_DIR / "planning" / "detailed-design" / "schemas"
for _p in (str(_ROOT_DIR), str(_SCHEMAS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from adapters.db.sqlite_repository import SQLiteRepositoryAdapter
from adapters.sim.delegated_fixtures import DelegatedFixturesAdapter
from adapters.sim.filesystem_checkpoint_store import FilesystemCheckpointStoreAdapter
from adapters.sim.in_memory_outbox import InMemoryOutboxAdapter
from adapters.sim.simulated_clock import SimulatedClockAdapter
from api.routes import auth, board, health, jobs, simulations
from ports import load_inbound_port_module
from test.fixtures.db import create_in_memory_db
from test.fixtures.sim_telemetry import SimTelemetry

PreemptionAndBoardService = load_inbound_port_module("board_query").PreemptionAndBoardService
EvictionService = load_inbound_port_module("eviction").EvictionService
JobSubmissionService = load_inbound_port_module("job_submission").JobSubmissionService
SimulationControlService = load_inbound_port_module("simulation_control").SimulationControlService
WindowActivationService = load_inbound_port_module("window_activation").WindowActivationService


def create_app(
    db_conn: Optional[sqlite3.Connection] = None,
    initial_iso: str = "2026-10-18T14:00:00-05:00",
) -> FastAPI:
    app = FastAPI(
        title="Module 9 — Night Training Scheduler",
        version="2.0.0",
        description="Academic AI Compute Fabric — Single-Node Night Training Scheduler",
    )

    if db_conn is None:
        conn = sqlite3.connect(":memory:", check_same_thread=False)
        conn.execute("PRAGMA foreign_keys = ON;")
        from pathlib import Path
        schema_path = (
            Path(__file__).parent.parent
            / "planning"
            / "detailed-design"
            / "schemas"
            / "001_night_training_scheduler_schema.sql"
        )
        conn.executescript(schema_path.read_text(encoding="utf-8"))
        conn.commit()
    else:
        conn = db_conn

    repo = SQLiteRepositoryAdapter(conn)
    clock = SimulatedClockAdapter(initial_iso=initial_iso)
    delegates = DelegatedFixturesAdapter()
    ckpt_store = FilesystemCheckpointStoreAdapter()
    outbox = InMemoryOutboxAdapter()
    telemetry = SimTelemetry()

    submission_service = JobSubmissionService(
        repo=repo,
        clock=clock,
        delegates=delegates,
        checkpoint_store=ckpt_store,
        raise_on_error=True,
    )
    window_service = WindowActivationService(repo=repo, raise_on_error=True)
    eviction_service = EvictionService(
        repo=repo,
        sim_telemetry=telemetry,
        checkpoint_store=ckpt_store,
        outbox=outbox,
        raise_on_error=True,
    )
    board_service = PreemptionAndBoardService(repo=repo, checkpoint_store=ckpt_store)
    simulation_service = SimulationControlService(
        repo=repo,
        clock=clock,
        window_service=window_service,
        eviction_service=eviction_service,
    )

    app.state.repo = repo
    app.state.clock = clock
    app.state.delegates = delegates
    app.state.checkpoint_store = ckpt_store
    app.state.outbox = outbox
    app.state.telemetry = telemetry
    app.state.submission_service = submission_service
    app.state.window_service = window_service
    app.state.eviction_service = eviction_service
    app.state.board_service = board_service
    app.state.simulation_service = simulation_service

    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(jobs.router)
    app.include_router(simulations.router)
    app.include_router(board.router)

    return app


app = create_app()
