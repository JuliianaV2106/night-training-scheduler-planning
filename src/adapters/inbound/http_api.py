"""
FastAPI driving adapter. Routes and status codes follow docs/contracts/openapi.yaml exactly.

Only this module knows about HTTP; it translates DTOs in and domain errors out.
"""

from __future__ import annotations

from fastapi import APIRouter, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.domain.errors import Explanation, SchedulerError
from src.domain.policies import RULE_JOBSPEC
from src.ports.dto import (
    ErrorBodyDTO,
    ExplanationDTO,
    JobSubmissionRequestDTO,
    JobSubmissionResponseDTO,
    WindowActivationRequestDTO,
    WindowActivationResultDTO,
)
from src.ports.inbound import JobSubmissionPort, WindowActivationPort
from src.ports.outbound import ClockPort

API_PREFIX = "/api/v1"

HTTP_STATUS_BY_CODE = {
    "OUT_OF_SCOPE_DISTRIBUTED": 400,
    "WINDOW_ACTIVATION_OUTSIDE_WINDOW": 400,
    "IDEMPOTENCY_CONFLICT": 409,
    "VALIDATION_FAILED": 422,
    "TWO_GPU_REQUIRES_48GB": 422,
    "MAX_NIGHT_SPAN_EXCEEDED": 422,
    "QUEUE_CAP_EXCEEDED": 429,
    "DELEGATE_UNAVAILABLE": 503,
}


def build_router(submission: JobSubmissionPort, activation: WindowActivationPort, clock: ClockPort) -> APIRouter:
    router = APIRouter(prefix=API_PREFIX)

    # Handlers are async on purpose: every request runs on the single event-loop thread,
    # which serialises access to the scheduler state (single writer, contracts.md §2.1).

    @router.post("/jobs", response_model=JobSubmissionResponseDTO, status_code=201,
                 responses={200: {"model": JobSubmissionResponseDTO}})
    async def submit_job(body: JobSubmissionRequestDTO):
        outcome = submission.submit(body)
        if outcome.created:
            return outcome.response
        return JSONResponse(status_code=200, content=outcome.response.model_dump())

    @router.post("/window/activate", response_model=WindowActivationResultDTO)
    async def activate_window(body: WindowActivationRequestDTO):
        return activation.activate_window(body)

    @router.get("/health")
    async def health():
        return {"status": "HEALTHY", "sim_instant": clock.now().isoformat(), "pacer_rate": 1}

    return router


def _error_body(code: str, message: str, retryable: bool, occurred_at: str,
                explanation: Explanation | None) -> JSONResponse:
    status = HTTP_STATUS_BY_CODE.get(code, 500)
    body = ErrorBodyDTO(
        error_code=code,
        message=message,
        http_status=status,
        retryable=retryable,
        occurred_at=occurred_at,
        explanation=ExplanationDTO(
            rule_id=explanation.rule_id,
            summary=explanation.summary,
            observed_values=explanation.observed_values,
            thresholds=explanation.thresholds,
            citations=list(explanation.citations),
        ) if explanation else None,
    )
    return JSONResponse(status_code=status, content=body.model_dump(exclude_none=True))


def install_error_handlers(app: FastAPI, clock: ClockPort) -> None:
    @app.exception_handler(SchedulerError)
    async def scheduler_error(_: Request, exc: SchedulerError) -> JSONResponse:
        return _error_body(exc.code, exc.message, exc.retryable, clock.now().isoformat(), exc.explanation)

    @app.exception_handler(RequestValidationError)
    async def request_validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        """Pydantic schema failures become the contract's VALIDATION_FAILED / MAX_NIGHT_SPAN_EXCEEDED body."""
        first = exc.errors()[0]
        field = ".".join(str(p) for p in first["loc"] if p != "body")
        code = "VALIDATION_FAILED"
        if field.endswith("estimated_duration_s") and first["type"] == "less_than_equal":
            code = "MAX_NIGHT_SPAN_EXCEEDED"
        message = f"Job specification field '{field}' failed validation rule '{RULE_JOBSPEC}': {first['msg']}."
        explanation = Explanation(
            rule_id=RULE_JOBSPEC,
            summary=first["msg"],
            citations=(RULE_JOBSPEC,),
            observed_values={field: first.get("input")},
            thresholds={field: {k: str(v) for k, v in first.get("ctx", {}).items()}},
        )
        return _error_body(code, message, False, clock.now().isoformat(), explanation)

    @app.exception_handler(Exception)
    async def unexpected(_: Request, exc: Exception) -> JSONResponse:
        return _error_body("INTERNAL_ERROR", "Unexpected scheduler failure; the transaction was rolled back.",
                           False, clock.now().isoformat(), None)
