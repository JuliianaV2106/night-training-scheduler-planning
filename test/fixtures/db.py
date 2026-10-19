"""
Mandatory Test Fixture: db
Provides an ephemeral in-memory SQLite database initialized from 001_night_training_scheduler_schema.sql.
"""

import sqlite3
from pathlib import Path


def create_in_memory_db() -> sqlite3.Connection:
    """Creates in-memory SQLite connection migrated with the full schema."""
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON;")

    schema_path = Path(__file__).parent.parent.parent / "planning" / "detailed-design" / "schemas" / "001_night_training_scheduler_schema.sql"
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found at {schema_path}")

    schema_sql = schema_path.read_text(encoding="utf-8")
    conn.executescript(schema_sql)
    conn.commit()
    return conn
