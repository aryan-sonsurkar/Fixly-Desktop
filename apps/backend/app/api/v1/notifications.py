from typing import Any

from fastapi import APIRouter, Depends, Query

from app.dependencies.auth import get_current_user
from app.schemas.notification import (
    NotificationCreate,
    NotificationListResponse,
    NotificationMarkReadResponse,
    NotificationResponse,
)
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    unread_only: bool = Query(False, alias="unread_only"),
    ntype: str | None = Query(None, alias="type", pattern=r"^(assignment_reminder|deadline_alert|exam_reminder|pomodoro_finished|daily_briefing|email_sync|ocr_completed|document_processed|ai_recommendation)?$"),  # noqa: E501
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    service = NotificationService()
    return await service.list_notifications(
        current_user["id"],
        unread_only=unread_only,
        limit=page_size,
        offset=(page - 1) * page_size,
        ntype=ntype,
    )


@router.get("/unread-count")
async def get_unread_count(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, int]:
    service = NotificationService()
    count = await service.unread_count(current_user["id"])
    return {"unread_count": count}


@router.post("", response_model=NotificationResponse, status_code=201)
async def create_notification(
    body: NotificationCreate,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    service = NotificationService()
    return await service.notify(
        current_user["id"], body.type, body.title, body.message, body.metadata,
    )


@router.put("/{notification_id}/read", response_model=NotificationResponse)
async def mark_read(
    notification_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    service = NotificationService()
    return await service.mark_read(notification_id, current_user["id"])


@router.put("/read-all", response_model=NotificationMarkReadResponse)
async def mark_all_read(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    service = NotificationService()
    return await service.mark_all_read(current_user["id"])


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, str]:
    service = NotificationService()
    await service.delete(notification_id, current_user["id"])
    return {"message": "Notification deleted"}
