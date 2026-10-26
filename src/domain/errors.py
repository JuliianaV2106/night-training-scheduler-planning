"""
Typed Error Catalog (contracts.md §1) expressed as domain exceptions.

The domain only knows the canonical error code; the HTTP status mapping lives
in the inbound HTTP adapter.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Explanation:
    rule_id: str
    summary: str
    citations: tuple[str, ...]
    observed_values: dict[str, Any] = field(default_factory=dict)
    thresholds: dict[str, Any] = field(default_factory=dict)


class SchedulerError(Exception):
    """Base class for every contract precondition violation."""

    code: str = "SCHEDULER_ERROR"
    retryable: bool = False

    def __init__(self, message: str, explanation: Explanation | None = None):
        super().__init__(message)
        self.message = message
        self.explanation = explanation


class OutOfScopeDistributed(SchedulerError):
    code = "OUT_OF_SCOPE_DISTRIBUTED"


class ValidationFailed(SchedulerError):
    code = "VALIDATION_FAILED"


class TwoGpuRequires48Gb(SchedulerError):
    code = "TWO_GPU_REQUIRES_48GB"


class MaxNightSpanExceeded(SchedulerError):
    code = "MAX_NIGHT_SPAN_EXCEEDED"


class IdempotencyConflict(SchedulerError):
    code = "IDEMPOTENCY_CONFLICT"


class QueueCapExceeded(SchedulerError):
    code = "QUEUE_CAP_EXCEEDED"
    retryable = True


class WindowActivationOutsideWindow(SchedulerError):
    code = "WINDOW_ACTIVATION_OUTSIDE_WINDOW"


class DelegateUnavailable(SchedulerError):
    code = "DELEGATE_UNAVAILABLE"
    retryable = True
