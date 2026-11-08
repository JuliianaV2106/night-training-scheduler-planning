"""
Driven Adapter: InMemoryOutboxAdapter (User Notifications per FR-27, Story 2.2).
"""

from typing import Any, Dict, List


class InMemoryOutboxAdapter:
    """Stores user notifications in memory for deterministic verification."""

    def __init__(self):
        self._messages: List[Dict[str, Any]] = []

    def enqueue_notification(
        self,
        actor_id: str,
        job_id: str,
        subject: str,
        payload: Dict[str, Any],
    ) -> None:
        self._messages.append(
            {
                "actor_id": actor_id,
                "job_id": job_id,
                "subject": subject,
                "payload": dict(payload),
            }
        )

    def get_notifications_for_actor(self, actor_id: str) -> List[Dict[str, Any]]:
        return [m for m in self._messages if m["actor_id"] == actor_id]

    def get_notifications_for_job(self, job_id: str) -> List[Dict[str, Any]]:
        return [m for m in self._messages if m["job_id"] == job_id]

    def all_notifications(self) -> List[Dict[str, Any]]:
        return list(self._messages)
