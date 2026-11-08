"""Outbound Port: DecisionLogPort (Append-Only Decision Record Log per AD-2, AD-3)."""

from typing import List, Protocol
from domain.entities import DecisionRecordEntity


class DecisionLogPort(Protocol):
    """Protocol for appending and reading durable DecisionRecord rows."""

    def append_decision(self, record: DecisionRecordEntity) -> None:
        ...

    def list_decisions(self, job_id: str = None) -> List[DecisionRecordEntity]:
        ...
