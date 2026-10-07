"""Pydantic schemas for the experimental Focus Companion (P0.3-sidecar).

Additive only: nothing here is referenced by the Planner, AI Workspace,
or any existing route. All identifiers are caller-supplied; the service
never invents assignment IDs.
"""
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.schemas.common import OptionalUUID


class NextActionRequest(BaseModel):
    available_minutes: int | None = Field(default=None, ge=1, le=480)
    exclude_keys: list[str] = Field(default_factory=list, max_length=20)


class CompanionAction(BaseModel):
    kind: Literal["assignment", "topic", "start"] = "assignment"
    key: str
    title: str
    subject: str = ""
    due_date: str | None = None
    overdue: bool = False
    priority: str = "medium"
    suggested_minutes: int = 15
    reason: str = ""
    document_id: str | None = None
    document_name: str | None = None


class NextActionResponse(BaseModel):
    action: CompanionAction | None = None
    alternates: list[CompanionAction] = Field(default_factory=list)
    empty_reason: str | None = None


class ContinueSessionRequest(BaseModel):
    current_key: str | None = None
    available_minutes: int | None = Field(default=None, ge=1, le=480)


class CompanionChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    conversation_id: OptionalUUID = None
    stream: bool = False


class CompanionChatResponse(BaseModel):
    message: dict[str, Any]
    conversation: dict[str, Any]
