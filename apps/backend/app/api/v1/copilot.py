from typing import Any

from fastapi import APIRouter, Depends

from app.dependencies.auth import get_current_user
from app.schemas.copilot import (
    CopilotChatRequest,
    CopilotChatResponse,
    DailyMissionResponse,
    InsightsResponse,
    ProductivityCoachResponse,
    RescheduleRequest,
    RescheduleResponse,
    RiskAssessmentResponse,
    SmartCommandRequest,
    SmartCommandResponse,
    WeeklyReviewResponse,
)
from app.services.copilot_service import CopilotService

router = APIRouter(prefix="/copilot", tags=["copilot"])


@router.get("/mission", response_model=DailyMissionResponse)
async def daily_mission(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    service = CopilotService()
    return await service.get_daily_mission(current_user["id"])


@router.get("/coach", response_model=ProductivityCoachResponse)
async def productivity_coach(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    service = CopilotService()
    return await service.get_productivity_coach(current_user["id"])


@router.post("/reschedule", response_model=RescheduleResponse)
async def reschedule(
    body: RescheduleRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    service = CopilotService()
    return await service.reschedule(current_user["id"], body.message)


@router.get("/risk", response_model=RiskAssessmentResponse)
async def risk_assessment(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    service = CopilotService()
    return await service.assess_risk(current_user["id"])


@router.get("/review", response_model=WeeklyReviewResponse)
async def weekly_review(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    service = CopilotService()
    return await service.get_weekly_review(current_user["id"])


@router.get("/insights", response_model=InsightsResponse)
async def insights(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    service = CopilotService()
    return await service.get_insights(current_user["id"])


@router.post("/command", response_model=SmartCommandResponse)
async def smart_command(
    body: SmartCommandRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    service = CopilotService()
    return await service.interpret_command(current_user["id"], body.command)


@router.post("/chat", response_model=CopilotChatResponse)
async def copilot_chat(
    body: CopilotChatRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    service = CopilotService()
    return await service.chat(current_user["id"], body.message, body.conversation_id)
