from typing import Any

from pydantic import BaseModel


class PlanResponse(BaseModel):
    plan_type: str
    content: str
    conversation_id: str
    generated_at: str
    context_summary: dict[str, Any] | None = None


class RevisionPlanRequest(BaseModel):
    subject_ids: list[str] | None = None
