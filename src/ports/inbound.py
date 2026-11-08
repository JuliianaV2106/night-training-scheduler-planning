"""
Inbound ports (use-case contracts). Signatures use DTOs and primitives only.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from src.ports.dto import (
    JobSubmissionRequestDTO,
    JobSubmissionResponseDTO,
    WindowActivationRequestDTO,
    WindowActivationResultDTO,
)


@dataclass(frozen=True)
class SubmissionOutcome:
    response: JobSubmissionResponseDTO
    created: bool  # False on an idempotent replay (HTTP 200 instead of 201)


class JobSubmissionPort(Protocol):
    def submit(self, request: JobSubmissionRequestDTO, at: datetime | None = None) -> SubmissionOutcome: ...

    def submit_job(
        self, request: JobSubmissionRequestDTO, at: datetime | None = None
    ) -> JobSubmissionResponseDTO: ...


class WindowActivationPort(Protocol):
    def activate_window(self, request: WindowActivationRequestDTO) -> WindowActivationResultDTO: ...
