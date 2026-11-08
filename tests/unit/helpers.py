"""Shared request builders for the HTTP-level story tests."""

from typing import Any

JOBS_URL = "/api/v1/jobs"
ACTIVATE_URL = "/api/v1/window/activate"
WINDOW_OPEN = "2026-10-18T22:00:00-05:00"
ERROR_BODY_KEYS = {"error_code", "message", "http_status", "retryable", "occurred_at"}


def job_payload(key: str, actor: str = "student-kavita", **spec_overrides: Any) -> dict:
    spec = {
        "image_digest": "sha256:" + "a" * 64,
        "gpu_slots_requested": 1,
        "required_vram_gb": 24,
        "checkpoint_interval_minutes": 15,
        "estimated_duration_s": 7200,
        "model_id": "llama-3-8b-instruct",
        "model_version": "1.0.0",
        "storage_request_bytes": 500 * 1024 * 1024,
        "worker_count": 1,
        "replicas": 1,
        "distributed_artifact_present": False,
    }
    spec.update(spec_overrides)
    return {"idempotency_key": key, "actor_id": actor, "spec": spec}


def count_jobs(db) -> int:
    return db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
