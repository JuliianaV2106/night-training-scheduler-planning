"""
Interface Stubs for Module 9: Night Training Scheduler
In accordance with the Solutioning Stop-Point Rule:
No production logic is written. All methods raise NotImplementedError so that
the ATDD suite runs RED for the right reason.
"""

from typing import Optional
from datetime import datetime
from dto import (
    JobSpecDTO,
    JobSubmissionRequestDTO,
    JobSubmissionResponseDTO,
    WindowActivationRequestDTO,
    WindowActivationResultDTO,
    EvictionRequestDTO,
    EvictionResultDTO,
)


class JobSubmissionServiceStub:
    """Inbound Port Stub: Job Submission Use-Case."""

    def submit_job(
        self,
        request: JobSubmissionRequestDTO,
        at: Optional[datetime] = None
    ) -> JobSubmissionResponseDTO:
        """
        Validates job spec, checks idempotency & queue caps, persists job.
        Raises NotImplementedError per Unit 4 Solutioning Stop-Point Rule.
        """
        raise NotImplementedError("JobSubmissionService.submit_job() production logic is not implemented in Unit 4.")


class WindowActivationServiceStub:
    """Inbound Port Stub: Window Lifecycle Activation Use-Case."""

    def activate_window(
        self,
        request: WindowActivationRequestDTO
    ) -> WindowActivationResultDTO:
        """
        Calculates deterministic Admission Order and allocates GPU slots.
        Raises NotImplementedError per Unit 4 Solutioning Stop-Point Rule.
        """
        raise NotImplementedError("WindowActivationService.activate_window() production logic is not implemented in Unit 4.")


class EvictionServiceStub:
    """Inbound Port Stub: Dawn Eviction & Deadline Kill Use-Case."""

    def evict_at_deadline(
        self,
        request: EvictionRequestDTO
    ) -> EvictionResultDTO:
        """
        Executes 05:45:00 checkpoint ramp and 05:53:00 SIGKILL/cordon.
        Raises NotImplementedError per Unit 4 Solutioning Stop-Point Rule.
        """
        raise NotImplementedError("EvictionService.evict_at_deadline() production logic is not implemented in Unit 4.")
