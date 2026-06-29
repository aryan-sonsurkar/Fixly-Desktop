from typing import Any

from fastapi import APIRouter, Depends, Query

from app.dependencies.auth import get_current_user
from app.schemas.search import SearchResponse
from app.services.search_service import SearchService

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=SearchResponse)
async def search(
    query: str = Query(min_length=1, max_length=200),
    limit: int = Query(5, ge=1, le=20),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    service = SearchService()
    return await service.search_all(current_user["id"], query, limit)
