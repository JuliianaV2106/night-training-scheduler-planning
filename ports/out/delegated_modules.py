"""Outbound Port: DelegatedModulesPort (Simulated M1, M2, M3, M4, M5, M8 Fixtures per PRD §5)."""

from typing import Dict, Any, Protocol


class DelegatedModulesPort(Protocol):
    """Protocol for querying simulated peer modules in standalone mode."""

    def verify_actor_entitlement(self, actor_id: str) -> Dict[str, Any]:
        """Queries Module 1 & Module 2 for role and granted priority tier."""
        ...

    def verify_model_catalog(self, model_id: str, model_version: str) -> bool:
        """Queries Module 5 catalog fixture."""
        ...

    def verify_quota_budget(self, actor_id: str, gpu_slots: int) -> bool:
        """Queries Module 8 quota fixture."""
        ...
