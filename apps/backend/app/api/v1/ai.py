from typing import Any

from fastapi import APIRouter, Depends, Query

from app.dependencies.auth import get_current_user
from app.schemas.ai import (
    AISettingsResponse,
    AISettingsUpdate,
    ChatRequest,
    ChatResponse,
    ConversationCreate,
    ConversationDetail,
    ConversationSummary,
    ConversationUpdate,
    MessageEditRequest,
    MessageFeedbackUpdate,
    MessageResponse,
    RegenerateRequest,
)
from app.schemas.planner import PlanResponse, RevisionPlanRequest
from app.services.ai_service import AIService
from app.services.planner_service import PlannerService

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    service = AIService()
    return await service.chat(
        current_user["id"],
        body.message,
        body.conversation_id,
        body.stream,
    )


@router.post("/regenerate", response_model=ChatResponse)
async def regenerate(
    body: RegenerateRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    service = AIService()
    return await service.regenerate(
        current_user["id"],
        body.conversation_id,
        body.message_id,
    )


@router.get("/conversations", response_model=list[ConversationSummary])
async def list_conversations(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> list[dict[str, Any]]:
    service = AIService()
    return await service.list_conversations(current_user["id"])


@router.get("/conversations/search", response_model=list[ConversationSummary])
async def search_conversations(
    query: str = Query(min_length=1, max_length=200),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> list[dict[str, Any]]:
    service = AIService()
    return await service.search_conversations(current_user["id"], query)


@router.post("/conversations", response_model=ConversationSummary)
async def create_conversation(
    body: ConversationCreate,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    service = AIService()
    return await service.repository.create_conversation(
        current_user["id"], body.title or "New conversation"
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    service = AIService()
    return await service.get_conversation(conversation_id, current_user["id"])


@router.put("/conversations/{conversation_id}", response_model=ConversationSummary)
async def update_conversation(
    conversation_id: str,
    body: ConversationUpdate,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    service = AIService()
    updates = body.model_dump(exclude_none=True)
    return await service.update_conversation_properties(
        conversation_id, current_user["id"], updates
    )


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, str]:
    service = AIService()
    await service.delete_conversation(conversation_id, current_user["id"])
    return {"message": "Conversation deleted"}


@router.put("/messages/{message_id}/feedback", response_model=MessageResponse)
async def set_message_feedback(
    message_id: str,
    body: MessageFeedbackUpdate,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    service = AIService()
    return await service.set_message_feedback(message_id, current_user["id"], body.feedback)


@router.put("/messages/{message_id}", response_model=MessageResponse)
async def edit_message(
    message_id: str,
    body: MessageEditRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    service = AIService()
    return await service.edit_message(message_id, current_user["id"], body.content)


@router.delete("/messages/{message_id}")
async def delete_message(
    message_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, str]:
    service = AIService()
    await service.delete_message(message_id, current_user["id"])
    return {"message": "Message deleted"}


@router.get("/settings", response_model=AISettingsResponse)
async def get_ai_settings(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    service = AIService()
    return await service.get_settings(current_user["id"])


@router.put("/settings", response_model=AISettingsResponse)
async def update_ai_settings(
    body: AISettingsUpdate,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    service = AIService()
    return await service.update_settings(
        current_user["id"], body.model_dump(exclude_none=True)
    )


@router.get("/providers")
async def check_providers() -> dict[str, bool]:
    service = AIService()
    return await service.check_availability()


@router.post("/plan/daily", response_model=PlanResponse)
async def daily_plan(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    service = PlannerService()
    return await service.generate_daily_plan(current_user["id"])


@router.post("/plan/weekly", response_model=PlanResponse)
async def weekly_plan(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    service = PlannerService()
    return await service.generate_weekly_plan(current_user["id"])


@router.post("/plan/revision", response_model=PlanResponse)
async def revision_plan(
    body: RevisionPlanRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    service = PlannerService()
    return await service.generate_revision_plan(current_user["id"], body.subject_ids)
