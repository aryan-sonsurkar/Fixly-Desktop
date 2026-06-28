from datetime import datetime, timezone
from typing import Any

from app.core.exceptions import NotFoundError, ValidationError
from app.core.logging import get_logger
from app.repositories.assignment_repository import AssignmentRepository

logger = get_logger(__name__)


class AssignmentService:
    VALID_STATUSES = {"pending", "in_progress", "completed", "cancelled", "overdue"}
    VALID_PRIORITIES = {"low", "medium", "high", "urgent"}

    def __init__(self) -> None:
        self.repository = AssignmentRepository()

    async def _auto_mark_overdue(self, user_id: str) -> None:
        try:
            affected = await self.repository.mark_overdue_assignments(user_id)
            if affected > 0:
                logger.info("Marked %d assignments as overdue for user %s", affected, user_id)
        except Exception as e:
            logger.warning("Failed to auto-mark overdue assignments: %s", e)

    async def list_assignments(
        self, user_id: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        await self._auto_mark_overdue(user_id)
        page = params.pop("page", 1)
        page_size = params.pop("page_size", 20)
        sort_by = params.pop("sort_by", "created_at")
        sort_order = params.pop("sort_order", "desc")

        rows, total = await self.repository.list_assignments(
            user_id, page, page_size, sort_by, sort_order, params
        )
        return {
            "data": rows,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": max(1, (total + page_size - 1) // page_size),
        }

    async def get_assignment(self, assignment_id: str, user_id: str) -> dict[str, Any]:
        await self._auto_mark_overdue(user_id)
        assignment = await self.repository.get_assignment(assignment_id, user_id)
        if not assignment:
            raise NotFoundError("Assignment not found")
        return assignment

    async def create_assignment(self, user_id: str, data: dict[str, Any]) -> dict[str, Any]:
        self._validate(data)
        return await self.repository.create_assignment(user_id, data)

    async def update_assignment(
        self, assignment_id: str, user_id: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        existing = await self.repository.get_assignment(assignment_id, user_id)
        if not existing:
            raise NotFoundError("Assignment not found")
        clean = {k: v for k, v in data.items() if v is not None}
        if clean:
            self._validate(clean, partial=True)
        return await self.repository.update_assignment(assignment_id, user_id, clean)

    async def delete_assignment(self, assignment_id: str, user_id: str) -> None:
        existing = await self.repository.get_assignment(assignment_id, user_id)
        if not existing:
            raise NotFoundError("Assignment not found")
        await self.repository.delete_assignment(assignment_id, user_id)

    async def duplicate_assignment(self, assignment_id: str, user_id: str) -> dict[str, Any]:
        existing = await self.repository.get_assignment(assignment_id, user_id)
        if not existing:
            raise NotFoundError("Assignment not found")
        payload = {
            "title": f"{existing['title']} (Copy)",
            "description": existing.get("description"),
            "subject_id": existing.get("subject_id"),
            "priority": existing.get("priority", "medium"),
            "status": "pending",
            "due_date": existing.get("due_date"),
            "estimated_study_time": existing.get("estimated_study_time"),
            "tags": existing.get("tags"),
            "notes": existing.get("notes"),
            "is_pinned": False,
            "is_favorite": False,
        }
        return await self.repository.create_assignment(user_id, payload)

    async def bulk_action(
        self, ids: list[str], user_id: str, action: str, value: Any = None
    ) -> list[dict[str, Any]]:
        if action == "delete":
            await self.repository.bulk_delete(ids, user_id)
            return []
        elif action == "complete":
            return await self.repository.bulk_update(ids, user_id, {
                "status": "completed",
                "completion_date": datetime.now(timezone.utc).isoformat(),
            })
        elif action == "archive":
            return await self.repository.bulk_update(ids, user_id, {"is_archived": True})
        elif action == "restore":
            return await self.repository.bulk_update(ids, user_id, {"is_archived": False})
        elif action == "pin":
            return await self.repository.bulk_update(ids, user_id, {"is_pinned": True})
        elif action == "unpin":
            return await self.repository.bulk_update(ids, user_id, {"is_pinned": False})
        elif action == "favorite":
            return await self.repository.bulk_update(ids, user_id, {"is_favorite": True})
        elif action == "unfavorite":
            return await self.repository.bulk_update(ids, user_id, {"is_favorite": False})
        elif action == "set_status" and value:
            return await self.repository.bulk_update(ids, user_id, {
                "status": str(value),
                **({"completion_date": datetime.now(timezone.utc).isoformat()} if str(value) == "completed" else {}),
            })
        elif action == "set_priority" and value:
            return await self.repository.bulk_update(ids, user_id, {"priority": str(value)})
        else:
            raise ValidationError(f"Unknown bulk action: {action}")

    async def get_attachments(self, assignment_id: str, user_id: str) -> list[dict[str, Any]]:
        assignment = await self.repository.get_assignment(assignment_id, user_id)
        if not assignment:
            raise NotFoundError("Assignment not found")
        return await self.repository.get_attachments(assignment_id)

    async def get_stats(self, user_id: str) -> dict[str, Any]:
        await self._auto_mark_overdue(user_id)
        return await self.repository.get_stats(user_id)

    def _validate(self, data: dict[str, Any], partial: bool = False) -> None:
        if not partial or "status" in data:
            status = data.get("status")
            if status and status not in self.VALID_STATUSES:
                raise ValidationError(f"Invalid status: {status}")
        if not partial or "priority" in data:
            priority = data.get("priority")
            if priority and priority not in self.VALID_PRIORITIES:
                raise ValidationError(f"Invalid priority: {priority}")
