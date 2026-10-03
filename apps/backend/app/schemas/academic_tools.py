"""Strict tool-layer contracts for P0.2 academic context tools.

Service layer returns plain dicts (repository convention); these models
validate tool INPUTS strictly and re-validate service OUTPUTS so no
arbitrary or malformed payload ever crosses the tool boundary.
"""

from typing import Any, Literal

from pydantic import BaseModel, Field


class StudentContextInput(BaseModel):
    model_config = {"extra": "forbid"}


class CourseContextInput(BaseModel):
    model_config = {"extra": "forbid"}

    subject_ref: str = Field(min_length=1, max_length=100)


class DeadlinesInput(BaseModel):
    model_config = {"extra": "forbid"}

    days: int = Field(default=14, ge=1, le=60)
    limit: int = Field(default=20, ge=1, le=50)


class KnowledgeGapsInput(BaseModel):
    model_config = {"extra": "forbid"}

    subject_ref: str | None = Field(default=None, max_length=100)


class SubjectRef(BaseModel):
    id: str
    name: str


class CourseResolution(BaseModel):
    status: Literal["found", "ambiguous", "missing"]
    subject: SubjectRef | None = None
    candidates: list[SubjectRef] = []
    query: str | None = None


class CourseAssignment(BaseModel):
    title: str = ""
    status: str = ""
    priority: str = "medium"
    due_date: str | None = None


class CourseDocument(BaseModel):
    id: str = ""
    name: str = "Untitled"
    pages: int = 0
    status: str = ""


class StudentContextResponse(BaseModel):
    subjects: list[SubjectRef] = []
    assignment_counts: dict[str, int] = {}
    upcoming: list[dict[str, Any]] = []
    documents: list[dict[str, Any]] = []
    deadlines: list[dict[str, Any]] = []
    truncated: bool = False


class CourseContextResponse(BaseModel):
    subject: SubjectRef | None = None
    resolution: CourseResolution
    assignments: list[CourseAssignment] = []
    documents: list[CourseDocument] = []
    upcoming_dates: list[str] = []
    topic_signals: list[str] = []
    truncated: bool = False


class DeadlineItem(BaseModel):
    title: str = ""
    subject: str = ""
    due_date: str = ""
    overdue: bool = False
    priority: str = "medium"
    estimated_minutes: int | None = None


class DeadlinesResponse(BaseModel):
    deadlines: list[DeadlineItem] = []
    truncated: bool = False


class KnowledgeGapsResponse(BaseModel):
    available: Literal[False] = False
    reason: str = (
        "Knowledge-gap tracking is not implemented yet. "
        "Study sessions, quiz results, and concept mastery are not "
        "persisted, so there is no authoritative signal to report."
    )
    subject_ref: str | None = None
