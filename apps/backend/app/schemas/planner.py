from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, Field


class GeneratedScheduleItem(BaseModel):
    title: str
    description: str = ""
    start_time: str
    end_time: str
    priority: Annotated[str, Field(pattern=r"^(low|medium|high|urgent)$")] = "medium"
    type: Annotated[str, Field(pattern=r"^(study|break|review|assignment|exam|other)$")] = "study"


class CreateTaskAction(BaseModel):
    action: Literal["create_task"] = "create_task"
    action_id: str
    title: str
    description: str = ""
    priority: Annotated[str, Field(pattern=r"^(low|medium|high|urgent)$")] = "medium"
    due_date: str | None = None
    estimated_minutes: int | None = None
    subject_id: str | None = None


class ScheduleTaskAction(BaseModel):
    action: Literal["schedule_task"] = "schedule_task"
    action_id: str
    title: str
    start_time: str
    end_time: str
    priority: Annotated[str, Field(pattern=r"^(low|medium|high|urgent)$")] = "medium"
    type: Annotated[str, Field(pattern=r"^(study|break|review|assignment|exam|other)$")] = "study"
    task_id: str | None = None


class CreateStudySessionAction(BaseModel):
    action: Literal["create_study_session"] = "create_study_session"
    action_id: str
    title: str
    duration_minutes: int = 25
    scheduled_time: str | None = None
    subject_id: str | None = None
    priority: Annotated[str, Field(pattern=r"^(low|medium|high|urgent)$")] = "medium"


class RescheduleTaskAction(BaseModel):
    action: Literal["reschedule_task"] = "reschedule_task"
    action_id: str
    title: str
    new_start_time: str
    new_end_time: str | None = None
    task_id: str | None = None
    reason: str = ""


class PrioritizeTaskAction(BaseModel):
    action: Literal["prioritize_task"] = "prioritize_task"
    action_id: str
    title: str
    priority: Annotated[str, Field(pattern=r"^(low|medium|high|urgent)$")]
    task_id: str | None = None
    reason: str = ""


PlannerAction = Annotated[
    Union[
        CreateTaskAction,
        ScheduleTaskAction,
        CreateStudySessionAction,
        RescheduleTaskAction,
        PrioritizeTaskAction,
    ],
    Field(discriminator="action"),
]


class PlanResponse(BaseModel):
    plan_type: str
    explanation: str = ""
    actions: list[PlannerAction] = []
    schedule_items: list[GeneratedScheduleItem] | None = None
    content: str = ""
    conversation_id: str = ""
    generated_at: str = ""
    context_summary: dict[str, Any] | None = None


class ExecuteActionRequest(BaseModel):
    action_id: str
    action: Annotated[
        str,
        Field(pattern=r"^(create_task|schedule_task|create_study_session|reschedule_task|prioritize_task)$"),
    ]
    parameters: dict[str, Any] = {}
    idempotency_key: str | None = None


class ExecuteActionResponse(BaseModel):
    success: bool
    action_id: str
    action: str
    message: str
    result_data: dict[str, Any] = {}


class BriefingQuote(BaseModel):
    text: str
    attribution: str = "Fixly AI"


class BriefingNextAction(BaseModel):
    label: str
    target: str = "pomodoro"


class DailyBriefingResponse(BaseModel):
    date: str
    greeting: str
    summary: str
    focus_items: list[GeneratedScheduleItem] = []
    quote: BriefingQuote
    motivation: str
    next_action: BriefingNextAction | None = None
    ai_available: bool = True
    generated_at: str


class RevisionPlanRequest(BaseModel):
    subject_ids: list[str] | None = None
