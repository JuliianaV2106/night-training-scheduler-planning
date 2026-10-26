"""
Pytest configuration registering mandatory fixtures (clock, fleet, telemetry, db) and the API client.
"""

import pytest
from fastapi.testclient import TestClient

from src.adapters.outbound.sqlite_repository import SqliteSchedulerRepository
from src.application.job_submission import JobSubmissionService
from src.application.window_activation import WindowActivationService
from src.main import create_app
from tests.fixtures.db import create_in_memory_db
from tests.fixtures.fake_clock import FakeClock
from tests.fixtures.seed_fleet import get_plan2_seed_fleet
from tests.fixtures.sim_telemetry import SimTelemetry


@pytest.fixture
def fake_clock() -> FakeClock:
    """Yields a deterministic simulated clock (daytime submission instant by default)."""
    return FakeClock(initial_iso="2026-10-18T14:30:00-05:00")


@pytest.fixture
def seed_fleet() -> dict:
    """Yields the canonical 32-node, 33-slot fleet profile."""
    return get_plan2_seed_fleet()


@pytest.fixture
def sim_telemetry() -> SimTelemetry:
    """Yields a scriptable fault injector."""
    telemetry = SimTelemetry()
    yield telemetry
    telemetry.reset()


@pytest.fixture
def db():
    """Yields an ephemeral in-memory SQLite database migrated with the 001 schema."""
    conn = create_in_memory_db()
    yield conn
    conn.close()


@pytest.fixture
def repository(db) -> SqliteSchedulerRepository:
    return SqliteSchedulerRepository(db)


@pytest.fixture
def submission_service(repository, fake_clock) -> JobSubmissionService:
    return JobSubmissionService(repository, fake_clock)


@pytest.fixture
def activation_service(repository) -> WindowActivationService:
    return WindowActivationService(repository)


@pytest.fixture
def client(db, fake_clock) -> TestClient:
    """HTTP client over the real composition root, backed by the in-memory database."""
    with TestClient(create_app(db, fake_clock), raise_server_exceptions=False) as c:
        yield c
