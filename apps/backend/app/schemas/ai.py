from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    conversation_id: str | None = None
    message: str = Field(min_length=1, max_length=10000)
    stream: bool = False


class ChatResponse(BaseModel):
    message: dict[str, Any]
    conversation: dict[str, Any]


class ConversationCreate(BaseModel):
    title: str | None = None


class ConversationUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    is_pinned: bool | None = None
    is_archived: bool | None = None


class ConversationSummary(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int | None = None
    is_pinned: bool = False
    is_archived: bool = False


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    provider: str | None = None
    tokens: int | None = None
    feedback: str | None = None
    created_at: str


class ConversationDetail(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int | None = None
    is_pinned: bool = False
    is_archived: bool = False
    messages: list[MessageResponse]


class AISettingsUpdate(BaseModel):
    preferred_provider: str | None = Field(default=None, pattern=r"^(ollama|gemini|auto)$")
    provider_model: str | None = Field(default=None, max_length=100)
    temperature: float | None = Field(default=None, ge=0, le=2)
    max_tokens: int | None = Field(default=None, ge=1, le=8192)
    streaming_enabled: bool | None = None
    system_prompt: str | None = Field(default=None, max_length=2000)
    academic_context: bool | None = None
    conversation_memory: int | None = Field(default=None, ge=1, le=500)
    fallback_provider: str | None = Field(default=None, pattern=r"^(ollama|gemini|auto)$")
    ai_enabled: bool | None = None


class AISettingsResponse(BaseModel):
    preferred_provider: str = "auto"
    provider_model: str | None = None
    temperature: float = 0.7
    max_tokens: int = 2048
    streaming_enabled: bool = True
    system_prompt: str | None = None
    academic_context: bool = True
    conversation_memory: int = 50
    fallback_provider: str = "auto"
    ai_enabled: bool = True
    ollama_available: bool = False
    gemini_available: bool = False


class RegenerateRequest(BaseModel):
    conversation_id: str
    message_id: str


class MessageFeedbackUpdate(BaseModel):
    feedback: str | None = Field(default=None, pattern=r"^(like|dislike)?$")


class MessageEditRequest(BaseModel):
    content: str = Field(min_length=1, max_length=10000)


class ProviderDetail(BaseModel):
    name: str
    available: bool
    installed: bool = False
    running: bool = False
    model_count: int = 0
    models: list[str] = []
    error: str | None = None


class ProviderDetailResponse(BaseModel):
    providers: dict[str, ProviderDetail]
