"""
Pytest configuration registering mandatory fixtures and configuring paths.
"""

import sys
from pathlib import Path
import pytest

root_dir = Path(__file__).parent.parent
schemas_dir = root_dir / "planning" / "detailed-design" / "schemas"

if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))
if str(schemas_dir) not in sys.path:
    sys.path.insert(0, str(schemas_dir))

from test.fixtures.fake_clock import FakeClock
from test.fixtures.seed_fleet import get_plan2_seed_fleet
from test.fixtures.sim_telemetry import SimTelemetry
from test.fixtures.db import create_in_memory_db


@pytest.fixture
def fake_clock() -> FakeClock:
    """Yields a deterministic simulated clock."""
    return FakeClock(initial_iso="2026-10-18T21:59:00-05:00")


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
