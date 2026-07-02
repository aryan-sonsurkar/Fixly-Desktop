from typing import Any

from app.core.logging import get_logger
from app.repositories.notification_repository import NotificationRepository

logger = get_logger(__name__)

NOTIFICATION_TYPES = [
    "assignment_reminder", "deadline_alert", "exam_reminder",
    "pomodoro_finished", "daily_briefing", "email_sync",
    "ocr_completed", "document_processed", "ai_recommendation",
]


class NotificationService:
    def __init__(self) -> None:
        self.repository = NotificationRepository()

    async def notify(self, user_id: str, ntype: str, title: str, message: str, data: dict[str, Any] | None = None) -> dict[str, Any]:  # noqa: E501
        if ntype not in NOTIFICATION_TYPES:
            raise ValueError(f"Invalid notification type: {ntype}")
        return await self.repository.create(user_id, {
            "type": ntype,
            "title": title,
            "message": message,
            "metadata": data or {},
        })

    async def list_notifications(
        self, user_id: str, unread_only: bool = False,
        limit: int = 50, offset: int = 0, ntype: str | None = None,
    ) -> dict[str, Any]:
        items, total = await self.repository.list_notifications(
            user_id, unread_only, limit, offset, ntype,
        )
        return {"notifications": items, "total": total, "page": offset // limit + 1, "page_size": limit}

    async def mark_read(self, notification_id: str, user_id: str) -> dict[str, Any]:
        return await self.repository.mark_read(notification_id, user_id)

    async def mark_all_read(self, user_id: str) -> dict[str, Any]:
        count = await self.repository.mark_all_read(user_id)
        return {"marked_read": count}

    async def delete(self, notification_id: str, user_id: str) -> None:
        await self.repository.delete(notification_id, user_id)

    async def unread_count(self, user_id: str) -> int:
        return await self.repository.unread_count(user_id)
