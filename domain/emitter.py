"""
Fail-Closed Explainability Decision Record Emitter for Module 9: Night Training Scheduler.
Enforces AD-3: Every automated state transition must carry non-empty authority citations
and observed input parameters, or fail closed before committing.
Zero external I/O or wall-clock imports.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Sequence
from domain.entities import DecisionRecordEntity, DomainError


def build_decision_record(
    decision_id: str,
    sim_timestamp: str,
    decision: str,
    actor_id: str,
    summary: str,
    citations: Sequence[str],
    inputs: Dict[str, Any],
    job_id: Optional[str] = None,
    node_id: Optional[str] = None,
    transition: Optional[str] = None,
    supersedes: Optional[str] = None,
) -> DecisionRecordEntity:
    """
    Constructs a verified DecisionRecordEntity.
    Fails closed if citations is empty or contains blank rule identifiers (AD-3).
    """
    cleaned_citations: List[str] = [c.strip() for c in citations if c and c.strip()]
    if not cleaned_citations:
        raise DomainError(
            error_code="EXPLAINABILITY_CITATION_MISSING",
            message="Fail-closed guard (AD-3): DecisionRecord cannot be emitted with empty citations.",
            http_status=500,
            retryable=False,
            rule_id="self:EXPLAINABILITY-FAIL-CLOSED-v1",
            citations=("self:EXPLAINABILITY-FAIL-CLOSED-v1",),
        )

    if not summary or not summary.strip():
        raise DomainError(
            error_code="EXPLAINABILITY_SUMMARY_MISSING",
            message="Fail-closed guard (AD-3): DecisionRecord summary must be non-empty.",
            http_status=500,
            retryable=False,
            rule_id="self:EXPLAINABILITY-FAIL-CLOSED-v1",
            citations=("self:EXPLAINABILITY-FAIL-CLOSED-v1",),
        )

    return DecisionRecordEntity(
        decision_id=decision_id,
        job_id=job_id,
        node_id=node_id,
        sim_timestamp=sim_timestamp,
        decision=decision,
        transition=transition,
        actor_id=actor_id,
        summary=summary.strip(),
        citations=tuple(cleaned_citations),
        inputs=dict(inputs),
        supersedes=supersedes,
    )
