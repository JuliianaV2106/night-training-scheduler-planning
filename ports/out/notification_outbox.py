"""Outbound Port: NotificationOutboxPort (User Notifications per FR-27)."""

from typing import Any, Dict, List, Protocol


class NotificationOutboxPort(Protocol):
    """Protocol for recording user notifications without external SMTP/webhook dependencies."""

    def enqueue_notification(self, actor_id: str, job_id: str, subject: str, payload: Dict[str, Any]) -> None:
        ...

    def get_notifications_for_actor(self, actor_id: str) -> List[Dict[str, Any]]:
        ...
