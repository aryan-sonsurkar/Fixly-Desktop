from typing import Any

from pydantic import BaseModel, Field


class EmailAccountConnect(BaseModel):
    email: str
    provider: str = Field(default="gmail", pattern=r"^(gmail|outlook|icloud|other)$")
    access_token: str
    refresh_token: str | None = None
    token_expires_at: str | None = None


class EmailAccountResponse(BaseModel):
    id: str
    user_id: str
    email: str
    provider: str = "gmail"
    sync_enabled: bool = True
    sync_status: str = "idle"
    sync_error: str | None = None
    total_emails: int = 0
    last_synced_at: str | None = None
    daily_briefing_enabled: bool = True
    briefing_time: str = "08:00"
    auto_create_assignments: bool = False
    confidence_threshold: float = 0.70
    attachment_download: bool = True
    created_at: str
    updated_at: str


class EmailAccountUpdate(BaseModel):
    sync_enabled: bool | None = None
    daily_briefing_enabled: bool | None = None
    briefing_time: str | None = None
    auto_create_assignments: bool | None = None
    confidence_threshold: float | None = Field(default=None, ge=0, le=1)
    attachment_download: bool | None = None


class EmailMessageResponse(BaseModel):
    id: str
    user_id: str
    account_id: str
    message_id: str
    thread_id: str | None = None
    subject: str = ""
    from_name: str | None = None
    from_email: str = ""
    to_emails: list[str] = []
    body_text: str | None = None
    received_at: str
    is_read: bool = False
    is_starred: bool = False
    has_attachments: bool = False
    labels: list[str] = []
    classification: dict[str, Any] | None = None
    assignment: dict[str, Any] | None = None
    created_at: str


class EmailClassificationResponse(BaseModel):
    id: str
    email_id: str
    category: str
    confidence: float
    is_reviewed: bool = False
    user_feedback: str | None = None
    created_at: str


class EmailAssignmentResponse(BaseModel):
    id: str
    email_id: str
    subject: str | None = None
    title: str | None = None
    due_date: str | None = None
    priority: str = "medium"
    teacher_name: str | None = None
    description: str | None = None
    course: str | None = None
    confidence: float
    status: str = "pending"
    assignment_id: str | None = None
    email: dict[str, Any] | None = None
    created_at: str


class EmailReviewAction(BaseModel):
    status: str = Field(pattern=r"^(approved|edited|rejected)$")
    assignment_id: str | None = None
    edits: dict[str, Any] | None = None


class EmailSyncResponse(BaseModel):
    account_id: str
    synced: int = 0
    classified: int = 0
    assignments_detected: int = 0
    duration_ms: int = 0


class EmailBriefingResponse(BaseModel):
    content: str
    conversation_id: str
    generated_at: str
