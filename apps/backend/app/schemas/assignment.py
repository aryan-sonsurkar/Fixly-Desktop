from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

StatusEnum = Literal["pending", "in_progress", "completed", "cancelled", "overdue"]
PriorityEnum = Literal["low", "medium", "high", "urgent"]


class AssignmentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    description: str | None = None
    subject_id: str | None = None
    priority: PriorityEnum = "medium"
    status: StatusEnum = "pending"
    due_date: datetime | None = None
    estimated_study_time: int | None = Field(default=None, ge=1, le=1440)
    tags: list[str] | None = None
    notes: str | None = None
    is_pinned: bool = False
    is_favorite: bool = False


class AssignmentUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = None
    subject_id: str | None = None
    priority: PriorityEnum | None = None
    status: StatusEnum | None = None
    due_date: datetime | None = None
    estimated_study_time: int | None = Field(default=None, ge=1, le=1440)
    tags: list[str] | None = None
    notes: str | None = None
    is_archived: bool | None = None
    is_pinned: bool | None = None
    is_favorite: bool | None = None


class AssignmentResponse(BaseModel):
    id: str
    user_id: str
    subject_id: str | None = None
    title: str
    description: str | None = None
    status: str
    priority: str
    due_date: str | None = None
    estimated_study_time: int | None = None
    tags: list[str] | None = None
    notes: str | None = None
    completion_date: str | None = None
    is_archived: bool = False
    is_pinned: bool = False
    is_favorite: bool = False
    source: str = "manual"
    ai_draft: str | None = None
    ai_draft_generated: bool = False
    created_at: str
    updated_at: str


class BulkActionRequest(BaseModel):
    ids: list[str] = Field(min_length=1, max_length=100)
    action: str
    value: str | bool | None = None


class AssignmentsQuery(BaseModel):
    search: str | None = Field(default=None, max_length=200)
    status: str | None = None
    priority: str | None = None
    subject_id: str | None = None
    tags: list[str] | None = None
    is_archived: bool | None = False
    is_favorite: bool | None = None
    is_pinned: bool | None = None
    due_date_from: datetime | None = None
    due_date_to: datetime | None = None
    sort_by: str = "created_at"
    sort_order: str = "desc"
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class PaginatedAssignments(BaseModel):
    data: list[dict[str, Any]]
    total: int
    page: int
    page_size: int
    total_pages: int


class AssignmentStats(BaseModel):
    total: int
    completed: int
    pending: int
    in_progress: int
    overdue: int
    completion_percentage: float
    due_today: int
    due_this_week: int
    avg_completion_time_hours: float | None = None
