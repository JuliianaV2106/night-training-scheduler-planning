"""
Mandatory Test Fixture: db
Provides an ephemeral in-memory SQLite database migrated from migrations/ (same path as production).
"""

import sqlite3

from src.adapters.outbound.sqlite_repository import connect


def create_in_memory_db() -> sqlite3.Connection:
    """Creates an in-memory SQLite connection migrated with every migration script."""
    return connect(":memory:")
