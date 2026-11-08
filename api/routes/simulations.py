"""
Driving Adapter: Simulation & Time-Warp Control API (`api/routes/simulations.py`).
Handles:
- `POST /api/v1/simulation/time-warp`: Accelerates clock ticks and triggers 22:00 / 06:00 transitions (Story 9.6)
- `POST /api/v1/simulation/seed-board`: Seeds initial Kanban board state for E2E verification
- `POST /api/v1/window/activate`: Triggers 22:00:00 window activation
- `POST /api/v1/eviction/deadline`: Triggers dawn eviction ramp / hard kill
"""

from typing import Optional
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from domain.entities import DomainError
from dto import EvictionRequestDTO, WindowActivationRequestDTO

router = APIRouter()


class TimeWarpRequest(BaseModel):
    target_time: Optional[str] = None
    speed_multiplier: Optional[int] = None
    advance_seconds: Optional[int] = None


class SeedBoardRequest(BaseModel):
    initial_time: str = "2026-10-18T14:00:00-05:00"
    queued_jobs_count: int = 5


@router.post("/api/v1/simulation/time-warp")
def time_warp_endpoint(payload: TimeWarpRequest, request: Request):
    sim_service = request.app.state.simulation_service
    snapshot = sim_service.time_warp(
        target_time_hhmm=payload.target_time,
        speed_multiplier=payload.speed_multiplier,
        advance_seconds=payload.advance_seconds,
    )
    return JSONResponse(status_code=200, content=snapshot)


@router.post("/api/v1/simulation/seed-board")
def seed_board_endpoint(payload: SeedBoardRequest, request: Request):
    """Seeds deterministic initial state for Story 9.6 (5 queued jobs at simulated time 14:00)."""
    repo = request.app.state.repo
    clock = request.app.state.clock
    sim_service = request.app.state.simulation_service

    clock.set_time(payload.initial_time)
    with repo.atomic_transaction() as cur:
        cur.execute("DELETE FROM audit_events")
        cur.execute("DELETE FROM cordon_requests")
        cur.execute("DELETE FROM checkpoints")
        cur.execute("DELETE FROM decision_records")
        cur.execute("UPDATE gpu_slots SET allocated_job_id = NULL, held_since = NULL")
        cur.execute("DELETE FROM jobs")
        cur.execute("UPDATE nodes SET status = 'HEALTHY'")

        for i in range(1, payload.queued_jobs_count + 1):
            job_id = f"JOB-KANBAN-{i:02d}"
            cur.execute(
                """
                INSERT INTO jobs (
                    job_id, state, actor_id, idempotency_key, payload_digest,
                    gpu_slots_requested, required_vram_gb, checkpoint_interval_minutes,
                    estimated_duration_s, image_digest, model_id, model_version,
                    storage_request_bytes, submitted_at, effective_priority, granted_priority
                ) VALUES (
                    ?, 'QUEUED_PENDING_WINDOW', 'student-kavita', ?, ?,
                    1, 24, 15, ?, ?, ?, '1.0', 1024, ?, ?, 'THESIS'
                )
                """,
                (
                    job_id,
                    f"idemp-kanban-{i:02d}",
                    f"{i:064d}",
                    14400 if i <= 3 else 43200,  # First 3 complete in 1 night; 2 evict resumable at 06:00
                    "sha256:" + f"{i:064x}",
                    f"llama-3-8b-ft-{i:02d}",
                    payload.initial_time,
                    150 - i,
                ),
            )
    return JSONResponse(status_code=200, content=sim_service.get_board_snapshot())
