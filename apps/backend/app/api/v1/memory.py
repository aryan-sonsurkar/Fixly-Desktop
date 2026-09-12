"""AI Memory API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from app.dependencies.auth import CurrentUser, get_current_user
from app.schemas.memory import (
    ConversationSummarizeRequest,
    ConversationSummarizeResponse,
    MemoryCreate,
    MemoryListResponse,
    MemoryResetRequest,
    MemoryResetResponse,
    MemoryResponse,
    MemorySearchRequest,
    MemorySearchResponse,
    MemoryStatsResponse,
    MemoryUpdate,
    SummaryResponse,
)
from app.services.memory_service import MemoryService
from app.services.summarization_service import SummarizationService

router = APIRouter(prefix="/memory", tags=["memory"])


def _get_service() -> MemoryService:
    return MemoryService()


@router.get("", response_model=MemoryListResponse)
async def list_memories(
    category: str | None = None,
    include_archived: bool = False,
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    service = _get_service()
    try:
        memories = service.list_memories(
            current_user.id, category=category, include_archived=include_archived
        )
        categories: dict[str, int] = {}
        for m in memories:
            cat = m["category"]
            categories[cat] = categories.get(cat, 0) + 1
        return {
            "memories": memories,
            "total": len(memories),
            "categories": categories,
        }
    finally:
        service.close()


@router.get("/stats", response_model=MemoryStatsResponse)
async def memory_stats(
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    service = _get_service()
    try:
        all_memories = service.list_memories(current_user.id, include_archived=True)
        by_cat: dict[str, int] = {}
        by_src: dict[str, int] = {}
        archived = 0
        total_conf = 0.0
        for m in all_memories:
            cat = m["category"]
            by_cat[cat] = by_cat.get(cat, 0) + 1
            src = m["source"]
            by_src[src] = by_src.get(src, 0) + 1
            if m["is_archived"]:
                archived += 1
            total_conf += m["confidence"]
        avg_conf = total_conf / len(all_memories) if all_memories else 0.0
        return {
            "total_memories": len(all_memories),
            "by_category": by_cat,
            "by_source": by_src,
            "archived_count": archived,
            "avg_confidence": round(avg_conf, 3),
        }
    finally:
        service.close()


@router.get("/{memory_id}", response_model=MemoryResponse)
async def get_memory(
    memory_id: str,
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    service = _get_service()
    try:
        memory = service.get_memory(current_user.id, memory_id)
        if not memory:
            from app.core.exceptions import NotFoundError
            raise NotFoundError("Memory not found")
        return memory
    finally:
        service.close()


@router.post("", response_model=MemoryResponse, status_code=201)
async def create_memory(
    body: MemoryCreate,
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    service = _get_service()
    try:
        memory = service.add_memory(
            user_id=current_user.id,
            content=body.content,
            category=body.category,
            source=body.source,
            confidence=body.confidence,
            source_document_id=body.source_document_id,
            source_conversation_id=body.source_conversation_id,
        )
        return memory
    finally:
        service.close()


@router.put("/{memory_id}", response_model=MemoryResponse)
async def update_memory(
    memory_id: str,
    body: MemoryUpdate,
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    service = _get_service()
    try:
        updates = body.model_dump(exclude_none=True)
        success = service.update_memory(current_user.id, memory_id, updates)
        if not success:
            from app.core.exceptions import NotFoundError
            raise NotFoundError("Memory not found")
        return service.get_memory(current_user.id, memory_id)
    finally:
        service.close()


@router.delete("/{memory_id}")
async def delete_memory(
    memory_id: str,
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, str]:
    service = _get_service()
    try:
        success = service.delete_memory(current_user.id, memory_id)
        if not success:
            from app.core.exceptions import NotFoundError
            raise NotFoundError("Memory not found")
        return {"message": "Memory deleted"}
    finally:
        service.close()


@router.post("/{memory_id}/archive")
async def archive_memory(
    memory_id: str,
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, str]:
    service = _get_service()
    try:
        success = service.archive_memory(current_user.id, memory_id)
        if not success:
            from app.core.exceptions import NotFoundError
            raise NotFoundError("Memory not found")
        return {"message": "Memory archived"}
    finally:
        service.close()


@router.post("/{memory_id}/unarchive")
async def unarchive_memory(
    memory_id: str,
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, str]:
    service = _get_service()
    try:
        success = service.unarchive_memory(current_user.id, memory_id)
        if not success:
            from app.core.exceptions import NotFoundError
            raise NotFoundError("Memory not found")
        return {"message": "Memory unarchived"}
    finally:
        service.close()


@router.post("/search", response_model=MemorySearchResponse)
async def search_memories(
    body: MemorySearchRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    service = _get_service()
    try:
        memories = service.retrieve_relevant(
            current_user.id,
            body.query,
            top_k=body.top_k,
            min_confidence=body.min_confidence,
            category=body.category,
        )
        return {"memories": memories, "total": len(memories)}
    finally:
        service.close()


@router.post("/reset", response_model=MemoryResetResponse)
async def reset_memories(
    body: MemoryResetRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    if body.confirmation != "RESET":
        from app.core.exceptions import ValidationError
        raise ValidationError("Type RESET to confirm memory deletion")
    service = _get_service()
    try:
        deleted = service.clear_all_memories(current_user.id)
        return {"deleted": deleted, "message": f"Deleted {deleted} memories"}
    finally:
        service.close()


@router.post("/summarize", response_model=ConversationSummarizeResponse)
async def summarize_conversation(
    body: ConversationSummarizeRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    summarizer = SummarizationService()
    try:
        result = await summarizer.maybe_summarize(
            current_user.id, body.conversation_id, body.messages
        )
        return result
    finally:
        summarizer.store.close()


@router.get("/summaries/{conversation_id}", response_model=list[SummaryResponse])
async def get_summaries(
    conversation_id: str,
    current_user: CurrentUser = Depends(get_current_user),
) -> list[dict[str, Any]]:
    summarizer = SummarizationService()
    try:
        return summarizer.get_summaries(current_user.id, conversation_id)
    finally:
        summarizer.store.close()
