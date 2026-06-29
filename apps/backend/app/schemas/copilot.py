from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class DailyMissionRequest(BaseModel):
    pass


class DailyMissionResponse(BaseModel):
    content: str
    generated_at: datetime
    context_summary: dict[str, Any] = Field(default_factory=dict)


class ProductivityCoachResponse(BaseModel):
    content: str
    generated_at: datetime


class RescheduleRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)


class RescheduleResponse(BaseModel):
    content: str
    generated_at: datetime


class RiskAssessmentResponse(BaseModel):
    content: str
    generated_at: datetime
    risk_level: str = "Low"
    academic_health_score: int = 50


class WeeklyReviewResponse(BaseModel):
    content: str
    generated_at: datetime


class InsightsResponse(BaseModel):
    content: str
    generated_at: datetime


class SmartCommandRequest(BaseModel):
    command: str = Field(min_length=1, max_length=500)


class SmartCommandResponse(BaseModel):
    content: str
    command_type: str = "custom"
    confidence: float = 0.0
    generated_at: datetime


class CopilotChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    conversation_id: str | None = None


class CopilotChatResponse(BaseModel):
    content: str
    conversation_id: str
    generated_at: datetime
