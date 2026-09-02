import json
from collections.abc import AsyncGenerator
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse

from app.core.exceptions import AIProviderUnavailableError
from app.core.rate_limiter import ai_limiter
from app.dependencies.auth import CurrentUser, get_current_user
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
    ProviderDetailResponse,
    RegenerateRequest,
)
from app.schemas.planner import PlanResponse, RevisionPlanRequest
from app.services.ai_service import AIService
from app.services.planner_service import PlannerService

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    ai_limiter.check(request)
    service = AIService(access_token=current_user.access_token)
    return await service.chat(
        current_user.id,
        body.message,
        str(body.conversation_id) if body.conversation_id else None,
        body.stream,
    )


@router.post("/chat/stream")
async def chat_stream(
    body: ChatRequest,
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
) -> StreamingResponse:
    ai_limiter.check(request)
    service = AIService(access_token=current_user.access_token)

    async def gen() -> AsyncGenerator[str, None]:
        convo_id = str(body.conversation_id) if body.conversation_id else None
        try:
            if not convo_id:
                conversation = await service.repository.create_conversation(current_user.id, body.message[:80])
                convo_id = str(conversation["id"])
            async for token in service.chat_stream(current_user.id, body.message, convo_id):
                yield f"data: {json.dumps({'token': token})}\n\n"
            conversation = await service.get_conversation(convo_id, current_user.id)
            message = next((item for item in reversed(conversation["messages"]) if item["role"] == "assistant"), None)
            if message is None:
                raise AIProviderUnavailableError("Fixly AI did not return a response. Please retry.")
            yield f"data: {json.dumps({'done': True, 'message': message, 'conversation': conversation})}\n\n"
        except AIProviderUnavailableError as exc:
            yield f"data: {json.dumps({'error': exc.detail})}\n\n"
        except Exception:
            yield f"data: {json.dumps({'error': 'Fixly AI is currently unavailable. Please retry.'})}\n\n"

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/regenerate", response_model=ChatResponse)
async def regenerate(
    body: RegenerateRequest,
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    ai_limiter.check(request)
    service = AIService(access_token=current_user.access_token)
    return await service.regenerate(
        current_user.id,
        str(body.conversation_id),
        str(body.message_id),
    )


@router.get("/conversations", response_model=list[ConversationSummary])
async def list_conversations(
    current_user: CurrentUser = Depends(get_current_user),
) -> list[dict[str, Any]]:
    service = AIService(access_token=current_user.access_token)
    return await service.list_conversations(current_user.id)


@router.get("/conversations/search", response_model=list[ConversationSummary])
async def search_conversations(
    query: str = Query(min_length=1, max_length=200),
    current_user: CurrentUser = Depends(get_current_user),
) -> list[dict[str, Any]]:
    service = AIService(access_token=current_user.access_token)
    return await service.search_conversations(current_user.id, query)


@router.post("/conversations", response_model=ConversationSummary)
async def create_conversation(
    body: ConversationCreate,
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    service = AIService(access_token=current_user.access_token)
    return await service.repository.create_conversation(
        current_user.id, body.title or "New conversation"
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    service = AIService(access_token=current_user.access_token)
    return await service.get_conversation(str(conversation_id), current_user.id)


@router.put("/conversations/{conversation_id}", response_model=ConversationSummary)
async def update_conversation(
    conversation_id: UUID,
    body: ConversationUpdate,
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    service = AIService(access_token=current_user.access_token)
    updates = body.model_dump(exclude_none=True)
    return await service.update_conversation_properties(
        str(conversation_id), current_user.id, updates
    )


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, str]:
    service = AIService(access_token=current_user.access_token)
    await service.delete_conversation(str(conversation_id), current_user.id)
    return {"message": "Conversation deleted"}


@router.put("/messages/{message_id}/feedback", response_model=MessageResponse)
async def set_message_feedback(
    message_id: UUID,
    body: MessageFeedbackUpdate,
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    service = AIService(access_token=current_user.access_token)
    return await service.set_message_feedback(str(message_id), current_user.id, body.feedback)


@router.put("/messages/{message_id}", response_model=MessageResponse)
async def edit_message(
    message_id: UUID,
    body: MessageEditRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    service = AIService(access_token=current_user.access_token)
    return await service.edit_message(str(message_id), current_user.id, body.content)


@router.delete("/messages/{message_id}")
async def delete_message(
    message_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, str]:
    service = AIService(access_token=current_user.access_token)
    await service.delete_message(str(message_id), current_user.id)
    return {"message": "Message deleted"}


@router.get("/settings", response_model=AISettingsResponse)
async def get_ai_settings(
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    service = AIService(access_token=current_user.access_token)
    return await service.get_settings(current_user.id)


@router.put("/settings", response_model=AISettingsResponse)
async def update_ai_settings(
    body: AISettingsUpdate,
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    service = AIService(access_token=current_user.access_token)
    return await service.update_settings(
        current_user.id, body.model_dump(exclude_none=True)
    )


@router.get("/providers")
async def check_providers(current_user: CurrentUser = Depends(get_current_user)) -> dict[str, bool]:
    service = AIService(access_token=current_user.access_token)
    return await service.check_availability()


@router.get("/providers/detail", response_model=ProviderDetailResponse)
async def check_providers_detail(current_user: CurrentUser = Depends(get_current_user)) -> dict[str, dict[str, Any]]:
    service = AIService(access_token=current_user.access_token)
    providers_data = await service.check_providers_detail(current_user.id)
    return {"providers": providers_data}


@router.get("/providers/ollama/models")
async def list_ollama_models(
    refresh: bool = Query(False),
    current_user: CurrentUser = Depends(get_current_user),
) -> list[dict[str, Any]]:
    # Deprecated: only Fixly AI (bundled) is supported
    return []


@router.post("/plan/daily", response_model=PlanResponse)
async def daily_plan(
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    service = PlannerService(access_token=current_user.access_token)
    return await service.generate_daily_plan(current_user.id)


@router.post("/plan/weekly", response_model=PlanResponse)
async def weekly_plan(
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    service = PlannerService(access_token=current_user.access_token)
    return await service.generate_weekly_plan(current_user.id)


@router.post("/plan/revision", response_model=PlanResponse)
async def revision_plan(
    body: RevisionPlanRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    service = PlannerService(access_token=current_user.access_token)
    return await service.generate_revision_plan(current_user.id, body.subject_ids)


@router.get("/plans")
async def list_plans(
    current_user: CurrentUser = Depends(get_current_user),
) -> list[dict[str, Any]]:
    service = AIService(access_token=current_user.access_token)
    convs = await service.list_conversations(current_user.id)
    plans = []
    for conv in convs:
        title = conv.get("title", "")
        if title in ("Daily Plan", "Weekly Plan", "Revision Plan"):
            try:
                detail = await service.get_conversation(conv["id"], current_user.id)
                msgs = detail.get("messages", [])
                assistant_msg = next((m for m in reversed(msgs) if m.get("role") == "assistant"), None)
                if assistant_msg:
                    plan_type = "daily" if title == "Daily Plan" else "weekly" if title == "Weekly Plan" else "revision"
                    plans.append({
                        "plan_type": plan_type,
                        "content": assistant_msg.get("content", ""),
                        "conversation_id": conv["id"],
                        "generated_at": str(conv.get("updated_at", "")),
                    })
            except Exception:
                continue
    return plans
