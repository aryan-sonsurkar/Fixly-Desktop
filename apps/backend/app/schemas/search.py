from typing import Any

from pydantic import BaseModel


class SearchResultItem(BaseModel):
    type: str
    id: str
    title: str
    subtitle: str | None = None
    url: str | None = None


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResultItem]
    total: int = 0
