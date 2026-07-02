from typing import Any

from pydantic import BaseModel, Field


class NotificationCreate(BaseModel):
    type: str = Field(..., pattern=r"^(assignment_reminder|deadline_alert|exam_reminder|pomodoro_finished|daily_briefing|email_sync|ocr_completed|document_processed|ai_recommendation)$")  # noqa: E501
    title: str = Field(min_length=1, max_length=200)
    message: str = Field(min_length=1, max_length=2000)
    metadata: dict[str, Any] = Field(default_factory=dict)


class NotificationResponse(BaseModel):
    id: str
    user_id: str
    type: str
    title: str
    message: str
    metadata: dict[str, Any]
    is_read: bool = False
    read_at: str | None = None
    created_at: str


class NotificationListResponse(BaseModel):
    notifications: list[NotificationResponse]
    total: int
    page: int = 1
    page_size: int = 50


class NotificationMarkReadResponse(BaseModel):
    marked_read: int
