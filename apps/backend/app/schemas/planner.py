from typing import Annotated, Any

from pydantic import BaseModel, Field


class GeneratedScheduleItem(BaseModel):
    title: str
    description: str
    start_time: str
    end_time: str
    priority: Annotated[str, Field(pattern=r"^(low|medium|high|urgent)$")] = "medium"
    type: Annotated[str, Field(pattern=r"^(study|break|review|assignment|exam|other)$")] = "study"


class PlanResponse(BaseModel):
    plan_type: str
    content: str
    conversation_id: str
    generated_at: str
    context_summary: dict[str, Any] | None = None
    schedule_items: list[GeneratedScheduleItem] | None = None


class RevisionPlanRequest(BaseModel):
    subject_ids: list[str] | None = None
