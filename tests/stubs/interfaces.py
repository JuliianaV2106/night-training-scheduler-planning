"""
Interface stub for the Epic 2 eviction use case (Impl-2 scope).

Submission and Window Activation stubs were replaced by the real services in Impl-1;
this stub keeps the Epic 2 contract tests RED for the right reason until Impl-2.
"""

from src.ports.dto import EvictionRequestDTO, EvictionResultDTO


class EvictionServiceStub:
    """Inbound Port Stub: Dawn Eviction & Deadline Kill Use-Case."""

    def evict_at_deadline(self, request: EvictionRequestDTO) -> EvictionResultDTO:
        raise NotImplementedError("EvictionService.evict_at_deadline() is scheduled for Impl-2.")
