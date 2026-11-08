"""
Driving Adapter: Jobs & Preemption HTTP API (`api/routes/jobs.py`).
Handles:
- `POST /api/v1/jobs`: Job Submission Ingress, Idempotency & Queue Cap (Stories 9.1, 1.1, 1.2, 3.1, 3.3)
- `GET /api/v1/jobs/{job_id}`: Transparent Decision Citations & Uniform 404 RBAC (Stories 4.1, 4.3)
- `POST /api/v1/scheduler/preempt`: Dynamic Priority Queue Preemption Cascade (Stories 9.5, 4.2)
"""

from typing import Optional
from fastapi import APIRouter, Header, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from domain.entities import DomainError, JobEntity, JobState
from dto import (
    ErrorBodyDTO,
    ExplanationDTO,
    JobSubmissionRequestDTO,
)

router = APIRouter()


class PreemptionDispatchRequest(BaseModel):
    job_id: Optional[str] = None
    actor_id: str = "student-kavita"
    priority: int = 10
    granted_priority: str = "THESIS"
    model_id: str = "llama-3-8b-thesis"
    gpu_slots_requested: int = 1
    required_vram_gb: int = 24
    sim_instant: str = "2026-10-18T23:10:00-05:00"


def _domain_error_response(exc: DomainError, sim_iso: str) -> JSONResponse:
    err_dto = ErrorBodyDTO(
        error_code=exc.error_code,
        message=exc.message,
        http_status=exc.http_status,
        retryable=exc.retryable,
        occurred_at=sim_iso,
        explanation=ExplanationDTO(
            rule_id=exc.rule_id,
            summary=exc.message,
            observed_values=exc.observed_values,
            thresholds=exc.thresholds,
            citations=list(exc.citations) if exc.citations else [exc.rule_id],
        ),
    )
    return JSONResponse(status_code=exc.http_status, content=err_dto.model_dump())


@router.post("/api/v1/jobs", status_code=201)
async def submit_job_endpoint(payload: JobSubmissionRequestDTO, request: Request):
    submission_service = request.app.state.submission_service
    clock = request.app.state.clock
    repo = request.app.state.repo
    sim_dt = clock.now()

    try:
        existed_before = repo.get_job_by_idempotency_key(payload.idempotency_key) is not None
        res = submission_service.submit_job(payload, at=sim_dt)
        status_code = 200 if existed_before else 201
        return JSONResponse(status_code=status_code, content=res.model_dump())
    except DomainError as exc:
        return _domain_error_response(exc, sim_dt.isoformat())


@router.get("/api/v1/jobs/{job_id}")
async def get_job_endpoint(
    job_id: str,
    request: Request,
    x_actor_id: str = Header(default="student-kavita"),
    x_actor_role: str = Header(default="STUDENT"),
):
    board_service = request.app.state.board_service
    clock = request.app.state.clock
    is_admin = x_actor_role.upper() in ("LAB_ADMIN", "ADMIN", "OPERATOR")

    try:
        data = board_service.get_job_for_actor(
            job_id=job_id,
            requesting_actor_id=x_actor_id,
            is_admin=is_admin,
        )
        return JSONResponse(status_code=200, content=data)
    except DomainError as exc:
        return _domain_error_response(exc, clock.now_iso())


@router.post("/api/v1/scheduler/preempt")
async def preempt_job_endpoint(payload: PreemptionDispatchRequest, request: Request):
    """
    Story 9.5 & Story 4.2 endpoint:
    Submits or evaluates a high-priority thesis fine-tuning job against a saturated night window,
    atomically preempting the lowest-priority earliest-checkpointed exploration job.
    """
    repo = request.app.state.repo
    board_service = request.app.state.board_service
    clock = request.app.state.clock

    try:
        with repo.atomic_transaction() as cur:
            target_id = payload.job_id
            if not target_id or repo.get_job(target_id) is None:
                target_id = payload.job_id or repo.next_sequence_id("JOB-THESIS", "jobs", "job_id")
                cur.execute(
                    """
                    INSERT OR IGNORE INTO jobs (
                        job_id, state, actor_id, idempotency_key, payload_digest,
                        gpu_slots_requested, required_vram_gb, checkpoint_interval_minutes,
                        estimated_duration_s, image_digest, model_id, model_version,
                        storage_request_bytes, submitted_at, effective_priority, granted_priority
                    ) VALUES (
                        ?, 'QUEUED_PENDING_WINDOW', ?, ?, ?,
                        ?, ?, 15, 7200, ?, ?, '1.0', 2048, ?, ?, ?
                    )
                    """,
                    (
                        target_id,
                        payload.actor_id,
                        f"idemp-{target_id}",
                        "e" * 64,
                        payload.gpu_slots_requested,
                        payload.required_vram_gb,
                        "sha256:" + "f" * 64,
                        payload.model_id,
                        payload.sim_instant,
                        payload.priority,
                        payload.granted_priority,
                    ),
                )

        outcome = board_service.execute_priority_preemption(
            challenger_job_id=target_id,
            sim_instant=payload.sim_instant,
        )
        status_code = 200 if outcome["preempted"] or outcome["challenger_state"] == "RUNNING" else 409
        return JSONResponse(status_code=status_code, content=outcome)
    except DomainError as exc:
        return _domain_error_response(exc, clock.now_iso())
