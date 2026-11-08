"""
Production Interface Wiring for Module 9: Night Training Scheduler.
In Impl-2, the stubs from Unit 4 are backed by the real hexagonal services
(`JobSubmissionService`, `WindowActivationService`, `EvictionService`) connected
to the SQLite database fixture, simulated clock, and telemetry fault injector.
"""

from typing import Optional
from datetime import datetime
import sqlite3

from adapters.db.sqlite_repository import SQLiteRepositoryAdapter
from adapters.sim.simulated_clock import SimulatedClockAdapter
from dto import (
    JobSpecDTO,
    JobSubmissionRequestDTO,
    JobSubmissionResponseDTO,
    WindowActivationRequestDTO,
    WindowActivationResultDTO,
    EvictionRequestDTO,
    EvictionResultDTO,
)
from ports import load_inbound_port_module
from test.fixtures.db import create_in_memory_db
from test.fixtures.sim_telemetry import SimTelemetry

EvictionService = load_inbound_port_module("eviction").EvictionService
JobSubmissionService = load_inbound_port_module("job_submission").JobSubmissionService
WindowActivationService = load_inbound_port_module("window_activation").WindowActivationService


class JobSubmissionServiceStub:
    """Inbound Port Production Wrapper: Job Submission Use-Case."""

    def __init__(self, db_conn: Optional[sqlite3.Connection] = None, clock=None):
        conn = db_conn or create_in_memory_db()
        self._repo = SQLiteRepositoryAdapter(conn)
        self._service = JobSubmissionService(repo=self._repo, clock=clock, raise_on_error=False)

    def submit_job(
        self,
        request: JobSubmissionRequestDTO,
        at: Optional[datetime] = None,
    ) -> Optional[JobSubmissionResponseDTO]:
        return self._service.submit_job(request=request, at=at)


class WindowActivationServiceStub:
    """Inbound Port Production Wrapper: Window Lifecycle Activation Use-Case."""

    def __init__(self, db_conn: Optional[sqlite3.Connection] = None):
        conn = db_conn or create_in_memory_db()
        self._repo = SQLiteRepositoryAdapter(conn)
        self._service = WindowActivationService(repo=self._repo, raise_on_error=False)

    def activate_window(
        self,
        request: WindowActivationRequestDTO,
    ) -> Optional[WindowActivationResultDTO]:
        return self._service.activate_window(request=request)


class EvictionServiceStub:
    """Inbound Port Production Wrapper: Dawn Eviction & Deadline Kill Use-Case."""

    def __init__(
        self,
        db_conn: Optional[sqlite3.Connection] = None,
        sim_telemetry: Optional[SimTelemetry] = None,
    ):
        conn = db_conn or create_in_memory_db()
        self._repo = SQLiteRepositoryAdapter(conn)
        self._service = EvictionService(
            repo=self._repo,
            sim_telemetry=sim_telemetry,
            raise_on_error=False,
        )

    def evict_at_deadline(
        self,
        request: EvictionRequestDTO,
    ) -> Optional[EvictionResultDTO]:
        return self._service.evict_at_deadline(request=request)
