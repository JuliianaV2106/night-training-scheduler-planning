"""
SQLite driven adapter implementing SchedulerRepositoryPort.

Schema source of truth: migrations/001_night_training_scheduler_schema.sql.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from src.domain.entities import ADMISSIBLE_STATES, TERMINAL_STATES, Job, JobSpec, JobState, Node, Placement
from src.ports.outbound import AuditEvent, DecisionRecord

logger = logging.getLogger(__name__)

MIGRATIONS_DIR = Path(__file__).resolve().parents[3] / "migrations"

_TERMINAL = tuple(s.value for s in TERMINAL_STATES)
_ADMISSIBLE = tuple(s.value for s in ADMISSIBLE_STATES)


def connect(database_path: str) -> sqlite3.Connection:
    """Opens the database and applies pending migrations (tracked through PRAGMA user_version)."""
    if database_path != ":memory:":
        Path(database_path).parent.mkdir(parents=True, exist_ok=True)
    # The HTTP adapter serialises all calls on one event loop; the connection is shared by design.
    conn = sqlite3.connect(database_path, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON;")
    apply_migrations(conn)
    return conn


def apply_migrations(conn: sqlite3.Connection) -> None:
    current = conn.execute("PRAGMA user_version").fetchone()[0]
    for script in sorted(MIGRATIONS_DIR.glob("[0-9][0-9][0-9]_*.sql")):
        version = int(script.name[:3])
        if version > current:
            logger.info("Applying migration %s", script.name)
            conn.executescript(script.read_text(encoding="utf-8"))
            conn.execute(f"PRAGMA user_version = {version}")
    conn.commit()


class SqliteSchedulerRepository:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    @contextmanager
    def transaction(self) -> Iterator[None]:
        try:
            yield
            self._conn.commit()
        except BaseException:
            self._conn.rollback()
            raise

    # --- jobs -----------------------------------------------------------------

    def find_job_by_idempotency_key(self, key: str) -> Job | None:
        row = self._conn.execute(
            f"SELECT {_JOB_COLUMNS} FROM jobs WHERE idempotency_key = ?", (key,)
        ).fetchone()
        return _row_to_job(row) if row else None

    def count_active_jobs(self) -> int:
        placeholders = ",".join("?" * len(_TERMINAL))
        return self._conn.execute(
            f"SELECT COUNT(*) FROM jobs WHERE state NOT IN ({placeholders})", _TERMINAL
        ).fetchone()[0]

    def next_job_id(self) -> str:
        highest = self._conn.execute(
            "SELECT MAX(CAST(substr(job_id, 5) AS INTEGER)) FROM jobs "
            "WHERE job_id GLOB 'JOB-[0-9][0-9][0-9][0-9]'"
        ).fetchone()[0]
        return f"JOB-{(highest or 0) + 1:04d}"

    def queue_position(self, job_id: str) -> int:
        """1-based FIFO position among queued jobs (submission order, then job_id)."""
        return self._conn.execute(
            """
            SELECT COUNT(*) FROM jobs q, jobs me
            WHERE me.job_id = ? AND q.state = 'QUEUED_PENDING_WINDOW'
              AND (q.submitted_at < me.submitted_at
                   OR (q.submitted_at = me.submitted_at AND q.job_id <= me.job_id))
            """,
            (job_id,),
        ).fetchone()[0] or 1

    def insert_job(self, job: Job, spec: JobSpec) -> None:
        self._conn.execute(
            """
            INSERT INTO jobs (
                job_id, state, actor_id, idempotency_key, payload_digest, worker_count, replicas,
                gpu_slots_requested, required_vram_gb, checkpoint_interval_minutes,
                estimated_duration_s, image_digest, model_id, model_version,
                storage_request_bytes, effective_priority, submitted_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job.job_id, job.state.value, job.actor_id, job.idempotency_key, job.payload_digest,
                spec.worker_count, spec.replicas, spec.gpu_slots_requested, spec.required_vram_gb,
                spec.checkpoint_interval_minutes, spec.estimated_duration_s, spec.image_digest,
                spec.model_id, spec.model_version, spec.storage_request_bytes,
                job.effective_priority, job.submitted_at.isoformat(),
            ),
        )

    def list_admissible_jobs(self) -> list[Job]:
        placeholders = ",".join("?" * len(_ADMISSIBLE))
        rows = self._conn.execute(
            f"SELECT {_JOB_COLUMNS} FROM jobs WHERE state IN ({placeholders})", _ADMISSIBLE
        ).fetchall()
        return [_row_to_job(r) for r in rows]

    def mark_job_running(self, job_id: str, node_id: str) -> None:
        placeholders = ",".join("?" * len(_ADMISSIBLE))
        cursor = self._conn.execute(
            f"""
            UPDATE jobs SET state = 'RUNNING', allocated_node_id = ?, admitted_nights = admitted_nights + 1
            WHERE job_id = ? AND state IN ({placeholders})
            """,
            (node_id, job_id, *_ADMISSIBLE),
        )
        if cursor.rowcount != 1:
            raise RuntimeError(f"Job {job_id} changed state during activation; aborting transaction")

    # --- fleet ----------------------------------------------------------------

    def list_nodes(self) -> list[Node]:
        rows = self._conn.execute(
            """
            SELECT n.node_id, n.vram_class_gb, n.status, s.slot_id, s.allocated_job_id
            FROM nodes n JOIN gpu_slots s ON s.node_id = n.node_id
            ORDER BY n.node_id, s.slot_index
            """
        ).fetchall()
        nodes: dict[str, Node] = {}
        for node_id, vram, status, slot_id, job_id in rows:
            node = nodes.setdefault(node_id, Node(node_id=node_id, vram_class_gb=vram, status=status))
            node.slots[slot_id] = job_id
        return list(nodes.values())

    def allocate_slots(self, placement: Placement, held_since: str) -> None:
        for slot_id in placement.slot_ids:
            cursor = self._conn.execute(
                "UPDATE gpu_slots SET allocated_job_id = ?, held_since = ? "
                "WHERE slot_id = ? AND allocated_job_id IS NULL",
                (placement.job_id, held_since, slot_id),
            )
            if cursor.rowcount != 1:
                raise RuntimeError(f"Slot {slot_id} is no longer free; aborting transaction")

    # --- logs -----------------------------------------------------------------

    def append_decision(self, record: DecisionRecord) -> None:
        self._conn.execute(
            """
            INSERT INTO decision_records (
                decision_id, job_id, node_id, sim_timestamp, decision, transition,
                actor_id, summary, citations, inputs
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.decision_id, record.job_id, record.node_id, record.sim_timestamp,
                record.decision, record.transition, record.actor_id, record.summary,
                json.dumps(record.citations), json.dumps(record.inputs),
            ),
        )

    def append_audit_event(self, event: AuditEvent) -> None:
        self._conn.execute(
            """
            INSERT INTO audit_events (event_id, event_type, job_id, node_id, actor_id, payload, occurred_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.event_id, event.event_type, event.job_id, event.node_id,
                event.actor_id, json.dumps(event.payload), event.occurred_at,
            ),
        )

    def find_audit_event(self, event_id: str) -> AuditEvent | None:
        row = self._conn.execute(
            "SELECT event_id, event_type, job_id, node_id, actor_id, payload, occurred_at "
            "FROM audit_events WHERE event_id = ?",
            (event_id,),
        ).fetchone()
        if row is None:
            return None
        return AuditEvent(*row[:5], payload=json.loads(row[5]), occurred_at=row[6])


_JOB_COLUMNS = (
    "job_id, state, actor_id, idempotency_key, payload_digest, gpu_slots_requested, "
    "required_vram_gb, submitted_at, effective_priority, consecutive_nights_missed, allocated_node_id"
)


def _row_to_job(row: tuple) -> Job:
    return Job(
        job_id=row[0],
        state=JobState(row[1]),
        actor_id=row[2],
        idempotency_key=row[3],
        payload_digest=row[4],
        gpu_slots_requested=row[5],
        required_vram_gb=row[6],
        submitted_at=datetime.fromisoformat(row[7]),
        effective_priority=row[8],
        consecutive_nights_missed=row[9],
        last_node_id=row[10],
    )
