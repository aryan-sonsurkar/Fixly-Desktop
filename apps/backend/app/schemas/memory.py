"""Pydantic schemas for AI Memory API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class MemoryCreate(BaseModel):
    content: str = Field(min_length=1, max_length=5000)
    category: str = Field(pattern=r"^(fact|preference|habit|weakness|strength|goal|document)$")
    source: str = Field(default="explicit", pattern=r"^(explicit|inferred|behavioral|document|conversation)$")
    source_document_id: str | None = None
    source_conversation_id: str | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)


class MemoryUpdate(BaseModel):
    content: str | None = Field(default=None, min_length=1, max_length=5000)
    category: str | None = Field(default=None, pattern=r"^(fact|preference|habit|weakness|strength|goal|document)$")
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    is_archived: bool | None = None


class MemoryResponse(BaseModel):
    id: str
    user_id: str
    category: str
    content: str
    confidence: float
    source: str
    source_document_id: str | None = None
    source_conversation_id: str | None = None
    created_at: str
    updated_at: str
    last_reinforced_at: str | None = None
    is_archived: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class MemoryListResponse(BaseModel):
    memories: list[MemoryResponse]
    total: int
    categories: dict[str, int]


class MemorySearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=10, ge=1, le=50)
    category: str | None = None
    min_confidence: float = Field(default=0.3, ge=0.0, le=1.0)


class MemorySearchResponse(BaseModel):
    memories: list[MemoryResponse]
    total: int


class MemoryStatsResponse(BaseModel):
    total_memories: int
    by_category: dict[str, int]
    by_source: dict[str, int]
    archived_count: int
    avg_confidence: float


class MemoryResetRequest(BaseModel):
    confirmation: str = Field(description="Must be 'RESET' to confirm")


class MemoryResetResponse(BaseModel):
    deleted: int
    message: str


class SummaryResponse(BaseModel):
    id: str
    conversation_id: str
    summary: str
    message_range_start: int
    message_range_end: int
    created_at: str


class ConversationSummarizeRequest(BaseModel):
    conversation_id: str
    messages: list[dict[str, str]]


class ConversationSummarizeResponse(BaseModel):
    summarized: bool
    summary: str | None = None
    messages_retained: int
    messages_summarized: int
