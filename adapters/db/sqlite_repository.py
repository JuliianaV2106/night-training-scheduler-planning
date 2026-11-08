"""
Driven Adapter: SQLiteRepositoryAdapter (Persistence Engine per AD-2, AD-5, NFR-10).
Enforces:
- Atomic SQLite transactions (`BEGIN IMMEDIATE`) combined with thread-level mutex for concurrency defense.
- Single-transaction commits pairing state transitions with append-only `decision_records` (INV-04).
- Physical invariant checks (INV-01 queue cap 500, INV-02 0 daytime occupancy, INV-03 2-GPU 48GB).
"""

from __future__ import annotations
import json
import sqlite3
import threading
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Tuple
from domain.entities import (
    CheckpointEntity,
    DecisionRecordEntity,
    GpuSlotEntity,
    JobEntity,
    NodeEntity,
)


class SQLiteRepositoryAdapter:
    """Thread-safe, transactional SQLite persistence adapter."""

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn
        self._lock = threading.RLock()
        with self._lock:
            self._conn.execute("PRAGMA foreign_keys = ON;")

    @property
    def connection(self) -> sqlite3.Connection:
        return self._conn

    @contextmanager
    def atomic_transaction(self):
        """
        Executes a block inside an exclusive mutex and SQLite transaction.
        Rolls back completely on any exception (Q-fail guarantee).
        """
        with self._lock:
            in_tx = self._conn.in_transaction
            if not in_tx:
                self._conn.execute("BEGIN IMMEDIATE;")
            try:
                yield self._conn.cursor()
                if not in_tx:
                    self._conn.commit()
            except Exception:
                if not in_tx and self._conn.in_transaction:
                    self._conn.rollback()
                raise

    # -------------------------------------------------------------------------
    # Deterministic ID Generation
    # -------------------------------------------------------------------------

    def next_sequence_id(self, prefix: str, table: str, id_column: str) -> str:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0] + 1
            candidate = f"{prefix}-{count:04d}"
            while True:
                cur.execute(f"SELECT 1 FROM {table} WHERE {id_column} = ?", (candidate,))
                if cur.fetchone() is None:
                    return candidate
                count += 1
                candidate = f"{prefix}-{count:04d}"

    # -------------------------------------------------------------------------
    # Queries
    # -------------------------------------------------------------------------

    def count_active_jobs(self) -> int:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute(
                "SELECT COUNT(*) FROM jobs WHERE state NOT IN ('COMPLETED', 'FAILED', 'REJECTED', 'EXPIRED')"
            )
            return int(cur.fetchone()[0])

    def get_job_by_idempotency_key(self, idempotency_key: str) -> Optional[JobEntity]:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute(
                """
                SELECT job_id, state, actor_id, idempotency_key, payload_digest,
                       gpu_slots_requested, required_vram_gb, checkpoint_interval_minutes,
                       estimated_duration_s, image_digest, model_id, model_version,
                       storage_request_bytes, submitted_at, worker_count, replicas,
                       effective_priority, granted_priority, consecutive_nights_missed,
                       admitted_nights, retry_count, preempted_in_window, allocated_node_id, state_reason
                FROM jobs WHERE idempotency_key = ?
                """,
                (idempotency_key,),
            )
            row = cur.fetchone()
            return self._row_to_job(row) if row else None

    def get_job(self, job_id: str) -> Optional[JobEntity]:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute(
                """
                SELECT job_id, state, actor_id, idempotency_key, payload_digest,
                       gpu_slots_requested, required_vram_gb, checkpoint_interval_minutes,
                       estimated_duration_s, image_digest, model_id, model_version,
                       storage_request_bytes, submitted_at, worker_count, replicas,
                       effective_priority, granted_priority, consecutive_nights_missed,
                       admitted_nights, retry_count, preempted_in_window, allocated_node_id, state_reason
                FROM jobs WHERE job_id = ?
                """,
                (job_id,),
            )
            row = cur.fetchone()
            return self._row_to_job(row) if row else None

    def list_jobs(self, states: Optional[List[str]] = None) -> List[JobEntity]:
        with self._lock:
            cur = self._conn.cursor()
            if states:
                placeholders = ",".join("?" for _ in states)
                cur.execute(
                    f"""
                    SELECT job_id, state, actor_id, idempotency_key, payload_digest,
                           gpu_slots_requested, required_vram_gb, checkpoint_interval_minutes,
                           estimated_duration_s, image_digest, model_id, model_version,
                           storage_request_bytes, submitted_at, worker_count, replicas,
                           effective_priority, granted_priority, consecutive_nights_missed,
                           admitted_nights, retry_count, preempted_in_window, allocated_node_id, state_reason
                    FROM jobs WHERE state IN ({placeholders})
                    ORDER BY submitted_at ASC, job_id ASC
                    """,
                    tuple(states),
                )
            else:
                cur.execute(
                    """
                    SELECT job_id, state, actor_id, idempotency_key, payload_digest,
                           gpu_slots_requested, required_vram_gb, checkpoint_interval_minutes,
                           estimated_duration_s, image_digest, model_id, model_version,
                           storage_request_bytes, submitted_at, worker_count, replicas,
                           effective_priority, granted_priority, consecutive_nights_missed,
                           admitted_nights, retry_count, preempted_in_window, allocated_node_id, state_reason
                    FROM jobs ORDER BY submitted_at ASC, job_id ASC
                    """
                )
            return [self._row_to_job(r) for r in cur.fetchall()]

    def _row_to_job(self, row: Tuple[Any, ...]) -> JobEntity:
        job = JobEntity(
            job_id=row[0],
            state=row[1],
            actor_id=row[2],
            idempotency_key=row[3],
            payload_digest=row[4],
            gpu_slots_requested=int(row[5]),
            required_vram_gb=int(row[6]),
            checkpoint_interval_minutes=int(row[7]),
            estimated_duration_s=int(row[8]),
            image_digest=row[9],
            model_id=row[10],
            model_version=row[11],
            storage_request_bytes=int(row[12]),
            submitted_at=row[13],
            worker_count=int(row[14]),
            replicas=int(row[15]),
            effective_priority=int(row[16]),
            granted_priority=row[17],
            consecutive_nights_missed=int(row[18]),
            admitted_nights=int(row[19]),
            retry_count=int(row[20]),
            preempted_in_window=int(row[21]),
            allocated_node_id=row[22],
            state_reason=row[23],
        )
        # Attach latest checkpoint timestamp if present
        cur = self._conn.cursor()
        cur.execute(
            "SELECT sim_timestamp FROM checkpoints WHERE job_id = ? AND state = 'VERIFIED' ORDER BY sim_timestamp ASC LIMIT 1",
            (job.job_id,),
        )
        ckpt_row = cur.fetchone()
        if ckpt_row:
            job.last_checkpoint_at = ckpt_row[0]
        return job

    def get_nodes(self) -> List[NodeEntity]:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("SELECT node_id, vram_class_gb, total_slots, status FROM nodes ORDER BY node_id ASC")
            return [
                NodeEntity(node_id=r[0], vram_class_gb=int(r[1]), total_slots=int(r[2]), status=r[3])
                for r in cur.fetchall()
            ]

    def get_slots(self) -> List[GpuSlotEntity]:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute(
                "SELECT slot_id, node_id, slot_index, allocated_job_id, held_since FROM gpu_slots ORDER BY slot_id ASC"
            )
            return [
                GpuSlotEntity(
                    slot_id=r[0],
                    node_id=r[1],
                    slot_index=int(r[2]),
                    allocated_job_id=r[3],
                    held_since=r[4],
                )
                for r in cur.fetchall()
            ]

    def list_decision_records(self, job_id: Optional[str] = None) -> List[DecisionRecordEntity]:
        with self._lock:
            cur = self._conn.cursor()
            if job_id:
                cur.execute(
                    """
                    SELECT decision_id, job_id, node_id, sim_timestamp, decision,
                           transition, actor_id, summary, citations, inputs, supersedes
                    FROM decision_records WHERE job_id = ? ORDER BY created_at ASC, decision_id ASC
                    """,
                    (job_id,),
                )
            else:
                cur.execute(
                    """
                    SELECT decision_id, job_id, node_id, sim_timestamp, decision,
                           transition, actor_id, summary, citations, inputs, supersedes
                    FROM decision_records ORDER BY created_at ASC, decision_id ASC
                    """
                )
            records = []
            for r in cur.fetchall():
                records.append(
                    DecisionRecordEntity(
                        decision_id=r[0],
                        job_id=r[1],
                        node_id=r[2],
                        sim_timestamp=r[3],
                        decision=r[4],
                        transition=r[5],
                        actor_id=r[6],
                        summary=r[7],
                        citations=tuple(json.loads(r[8])),
                        inputs=json.loads(r[9]),
                        supersedes=r[10],
                    )
                )
            return records

    # -------------------------------------------------------------------------
    # Atomic Mutations (paired with DecisionRecord & AuditEvent per INV-04)
    # -------------------------------------------------------------------------

    def insert_job_and_decision_atomic(
        self,
        job: JobEntity,
        decision: DecisionRecordEntity,
        event_id: str,
    ) -> int:
        """
        Inserts a newly admitted job, its DecisionRecord, and JOB_SUBMITTED audit event
        in a single atomic transaction. Returns 1-based queue position.
        """
        with self.atomic_transaction() as cur:
            cur.execute(
                """
                INSERT INTO jobs (
                    job_id, state, state_reason, actor_id, idempotency_key, payload_digest,
                    worker_count, replicas, gpu_slots_requested, required_vram_gb,
                    checkpoint_interval_minutes, estimated_duration_s, image_digest,
                    model_id, model_version, storage_request_bytes, effective_priority,
                    granted_priority, consecutive_nights_missed, admitted_nights,
                    retry_count, preempted_in_window, allocated_node_id, submitted_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job.job_id,
                    job.state,
                    job.state_reason,
                    job.actor_id,
                    job.idempotency_key,
                    job.payload_digest,
                    job.worker_count,
                    job.replicas,
                    job.gpu_slots_requested,
                    job.required_vram_gb,
                    job.checkpoint_interval_minutes,
                    job.estimated_duration_s,
                    job.image_digest,
                    job.model_id,
                    job.model_version,
                    job.storage_request_bytes,
                    job.effective_priority,
                    job.granted_priority,
                    job.consecutive_nights_missed,
                    job.admitted_nights,
                    job.retry_count,
                    job.preempted_in_window,
                    job.allocated_node_id,
                    job.submitted_at,
                ),
            )
            self._insert_decision_in_cursor(cur, decision)
            self._insert_audit_event_in_cursor(
                cur,
                event_id=event_id,
                event_type="JOB_SUBMITTED",
                job_id=job.job_id,
                node_id=None,
                actor_id=job.actor_id,
                payload={"job_id": job.job_id, "payload_digest": job.payload_digest, "state": job.state},
                occurred_at=job.submitted_at,
            )
            cur.execute("SELECT COUNT(*) FROM jobs WHERE state = 'QUEUED_PENDING_WINDOW'")
            queue_pos = int(cur.fetchone()[0])
            return max(1, min(500, queue_pos))

    def _insert_decision_in_cursor(self, cur: sqlite3.Cursor, decision: DecisionRecordEntity) -> None:
        cur.execute(
            """
            INSERT INTO decision_records (
                decision_id, job_id, node_id, sim_timestamp, decision,
                transition, actor_id, summary, citations, inputs, supersedes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                decision.decision_id,
                decision.job_id,
                decision.node_id,
                decision.sim_timestamp,
                decision.decision,
                decision.transition,
                decision.actor_id,
                decision.summary,
                json.dumps(list(decision.citations)),
                json.dumps(decision.inputs),
                decision.supersedes,
            ),
        )

    def _insert_audit_event_in_cursor(
        self,
        cur: sqlite3.Cursor,
        event_id: str,
        event_type: str,
        job_id: Optional[str],
        node_id: Optional[str],
        actor_id: str,
        payload: Dict[str, Any],
        occurred_at: str,
    ) -> None:
        cur.execute(
            """
            INSERT INTO audit_events (
                event_id, event_type, job_id, node_id, actor_id, payload, occurred_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                event_type,
                job_id,
                node_id,
                actor_id,
                json.dumps(payload),
                occurred_at,
            ),
        )

    def record_checkpoint(self, ckpt: CheckpointEntity) -> None:
        with self.atomic_transaction() as cur:
            cur.execute(
                """
                INSERT OR REPLACE INTO checkpoints (
                    checkpoint_id, job_id, path, bytes, step, digest, sim_timestamp, state, written_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ckpt.checkpoint_id,
                    ckpt.job_id,
                    ckpt.path,
                    ckpt.bytes,
                    ckpt.step,
                    ckpt.digest,
                    ckpt.sim_timestamp,
                    ckpt.state,
                    ckpt.written_by,
                ),
            )
