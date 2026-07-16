from typing import Any

from pydantic import BaseModel, Field


class DocumentResponse(BaseModel):
    id: str
    user_id: str
    filename: str
    original_name: str
    file_type: str
    file_size: int
    page_count: int = 0
    status: str = "pending"
    error_message: str | None = None
    processing_time_ms: int | None = None
    storage_path: str | None = None
    subject_id: str | None = None
    is_favorite: bool = False
    last_opened_at: str | None = None
    created_at: str
    updated_at: str


class DocumentRecentResponse(BaseModel):
    id: str
    original_name: str
    file_type: str
    status: str
    created_at: str
    page_count: int = 0
    file_size: int = 0


class DocumentUpdate(BaseModel):
    subject_id: str | None = None
    is_favorite: bool | None = None


class DocumentRename(BaseModel):
    original_name: str = Field(min_length=1, max_length=500)


class DocumentChunkResponse(BaseModel):
    id: str
    document_id: str
    chunk_index: int
    chunk_type: str = "text"
    content: str
    heading: str | None = None
    page_number: int | None = None
    token_count: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentDetailResponse(DocumentResponse):
    chunks: list[DocumentChunkResponse] = []
    conversation_ids: list[str] = []


class OCRResultResponse(BaseModel):
    id: str
    document_id: str
    extracted_text: str
    confidence: float = 0
    processing_time_ms: int = 0
    engine: str = "builtin"
    created_at: str


class DocumentChatRequest(BaseModel):
    document_id: str
    message: str = Field(min_length=1, max_length=10000)
    conversation_id: str | None = None


class DocumentChatResponse(BaseModel):
    message: dict[str, Any]
    conversation: dict[str, Any]
    chunks_used: list[dict[str, Any]] = []


class DocumentSummaryRequest(BaseModel):
    max_length: int = Field(default=500, ge=100, le=4000)


class DocumentNotesRequest(BaseModel):
    style: str = Field(default="detailed", pattern=r"^(detailed|concise|bullet|outline)$")


class DocumentFlashcardsRequest(BaseModel):
    count: int = Field(default=10, ge=1, le=50)


class DocumentQuizRequest(BaseModel):
    count: int = Field(default=5, ge=1, le=20)
    difficulty: str = Field(default="medium", pattern=r"^(easy|medium|hard)$")


class DocumentLibraryFilter(BaseModel):
    subject_id: str | None = None
    status: str | None = None
    file_type: str | None = None
    search: str | None = None
    favorites_only: bool = False
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
