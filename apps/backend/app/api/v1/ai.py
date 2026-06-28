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
from app.services.ai_service import AIService

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
