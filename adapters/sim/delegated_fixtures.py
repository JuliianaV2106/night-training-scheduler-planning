"""
Driven Adapter: DelegatedFixturesAdapter (In-Process M1–M8 Fixtures per PRD §5, FR-6).
Provides deterministic responses for Module 1 (Identity/RBAC), Module 2 (Policy/Priority),
Module 5 (Model Catalog), and Module 8 (Token/GPU Quota).
"""

from typing import Any, Dict, Set
from domain.entities import DomainError


class DelegatedFixturesAdapter:
    """Deterministic in-process simulator for peer modules M1, M2, M3, M5, M8."""

    def __init__(self):
        self._unavailable_modules: Set[str] = set()
        self._unauthorized_actors: Set[str] = {"user-unauthorized", "guest-001"}
        self._deprecated_models: Set[str] = {"deprecated-model-v0", "banned-llm"}
        self._quota_exhausted_actors: Set[str] = {"student-over-quota"}
        self._actor_roles: Dict[str, Dict[str, Any]] = {
            "student-kavita": {"role": "STUDENT", "granted_priority": "THESIS", "effective_priority": 150},
            "dr-chen": {"role": "LAB_ADMIN", "granted_priority": "URGENT", "effective_priority": 200},
            "operator-ines": {"role": "LAB_ADMIN", "granted_priority": "URGENT", "effective_priority": 200},
        }

    def set_module_unavailable(self, module_name: str, unavailable: bool = True) -> None:
        if unavailable:
            self._unavailable_modules.add(module_name)
        else:
            self._unavailable_modules.discard(module_name)

    def verify_actor_entitlement(self, actor_id: str) -> Dict[str, Any]:
        if "M1" in self._unavailable_modules or "M2" in self._unavailable_modules:
            mod = "M1" if "M1" in self._unavailable_modules else "M2"
            raise DomainError(
                error_code="DELEGATE_UNAVAILABLE",
                message=f"Delegated module '{mod}' is unavailable. Automatic fail-closed policy applied citing self:DELEGATE-UNAVAILABLE-v1.",
                http_status=503,
                retryable=True,
                rule_id="self:DELEGATE-UNAVAILABLE-v1",
                citations=("self:DELEGATE-UNAVAILABLE-v1",),
            )
        if actor_id in self._unauthorized_actors:
            # Per AD-8: return 404 Not Found to prevent enumeration oracle
            raise DomainError(
                error_code="ENTITLEMENT_DENIED",
                message=f"Resource not found or unauthorized access attempt for actor '{actor_id}'.",
                http_status=404,
                retryable=False,
                rule_id="policy:M1/rbac-uniform-404@v1",
                citations=("policy:M1/rbac-uniform-404@v1", "self:AD-8-UNIFORM-404-v1"),
            )
        return self._actor_roles.get(
            actor_id,
            {"role": "STUDENT", "granted_priority": "NORMAL", "effective_priority": 100},
        )

    def verify_model_catalog(self, model_id: str, model_version: str) -> bool:
        if "M5" in self._unavailable_modules:
            raise DomainError(
                error_code="DELEGATE_UNAVAILABLE",
                message="Delegated module 'M5' is unavailable. Automatic fail-closed policy applied citing self:DELEGATE-UNAVAILABLE-v1.",
                http_status=503,
                retryable=True,
                rule_id="self:DELEGATE-UNAVAILABLE-v1",
                citations=("self:DELEGATE-UNAVAILABLE-v1",),
            )
        if model_id in self._deprecated_models:
            raise DomainError(
                error_code="MODEL_NOT_FOUND",
                message=f"Model identifier '{model_id}' version '{model_version}' does not exist or is deprecated in catalog.",
                http_status=422,
                retryable=False,
                rule_id=f"catalog:M5/{model_id}@{model_version}",
                citations=(f"catalog:M5/{model_id}@{model_version}",),
            )
        return True

    def verify_quota_budget(self, actor_id: str, gpu_slots: int) -> bool:
        if "M8" in self._unavailable_modules:
            raise DomainError(
                error_code="DELEGATE_UNAVAILABLE",
                message="Delegated module 'M8' is unavailable. Automatic fail-closed policy applied citing self:DELEGATE-UNAVAILABLE-v1.",
                http_status=503,
                retryable=True,
                rule_id="self:DELEGATE-UNAVAILABLE-v1",
                citations=("self:DELEGATE-UNAVAILABLE-v1",),
            )
        if actor_id in self._quota_exhausted_actors:
            raise DomainError(
                error_code="VALIDATION_FAILED",
                message=f"Actor '{actor_id}' has exhausted nightly GPU quota in Module 8.",
                http_status=422,
                retryable=False,
                rule_id="quota:M8/night-budget@v1",
                citations=("quota:M8/night-budget@v1",),
            )
        return True
