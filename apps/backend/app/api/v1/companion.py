"""Experimental Focus Companion routes (sidecar, additive only).

- POST /companion/next-action: deterministic, LLM-free single next action.
- POST /companion/chat(+/stream): normal AI Workspace pipeline
  (auth, persistence, course routing, streaming) with the companion
  system prompt. No duplicated routing, context, or planner logic.
"""
import json
from collections.abc import AsyncGenerator
from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.core.exceptions import AIProviderUnavailableError
from app.core.rate_limiter import ai_limiter
from app.dependencies.auth import CurrentUser, get_current_user
from app.prompts.registry import PromptType
from app.schemas.ai import ChatResponse
from app.schemas.companion import (
    CompanionChatRequest,
    ContinueSessionRequest,
    NextActionRequest,
    NextActionResponse,
)
from app.services.ai_service import AIService
from app.services.companion_service import CompanionService

router = APIRouter(prefix="/companion", tags=["companion"])


class ContinueSessionResponse(BaseModel):
    action: dict[str, Any] | None = None
    alternates: list[dict[str, Any]] = Field(default_factory=list)
    empty_reason: str | None = None
    resumed: bool = False


@router.post("/next-action", response_model=NextActionResponse)
async def next_action(
    body: NextActionRequest,
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    ai_limiter.check(request)
    service = CompanionService(access_token=current_user.access_token)
    return await service.get_next_action(
        current_user.id,
        available_minutes=body.available_minutes,
        exclude_keys=body.exclude_keys,
    )


@router.post("/continue", response_model=ContinueSessionResponse)
async def continue_session(
    body: ContinueSessionRequest,
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    ai_limiter.check(request)
    service = CompanionService(access_token=current_user.access_token)
    return await service.continue_session(
        current_user.id,
        current_key=body.current_key,
        available_minutes=body.available_minutes,
    )


@router.post("/chat", response_model=ChatResponse)
async def companion_chat(
    body: CompanionChatRequest,
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
        system_prompt_type=PromptType.COMPANION,
    )


@router.post("/chat/stream")
async def companion_chat_stream(
    body: CompanionChatRequest,
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
            async for token in service.chat_stream(
                current_user.id, body.message, convo_id,
                system_prompt_type=PromptType.COMPANION,
            ):
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
