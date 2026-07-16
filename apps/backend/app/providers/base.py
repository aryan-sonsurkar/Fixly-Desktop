from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from typing import Any

# ── AI Provider base ─────────────────────────────────

class AIProvider(ABC):
    name: str = "base"

    @abstractmethod
    async def generate(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str: ...

    async def generate_stream(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncGenerator[str, None]:
        yield await self.generate(messages, temperature, max_tokens)

    @abstractmethod
    async def check_availability(self) -> bool: ...

    async def check_availability_detail(self) -> dict[str, Any]:
        available = await self.check_availability()
        return {"available": available, "error": None}

    async def list_models(self) -> list[dict[str, Any]]:
        return []

    def count_tokens(self, text: str) -> int:
        return len(text.split())


# ── Email Provider base ──────────────────────────────

@dataclass
class SyncMessage:
    message_id: str
    thread_id: str | None
    subject: str
    from_name: str | None
    from_email: str
    to_emails: list[str]
    body_text: str | None
    received_at: str
    is_read: bool
    is_starred: bool = False
    has_attachments: bool = False
    labels: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class SyncResult:
    messages: list[SyncMessage]
    next_page_token: str | None = None
    history_id: str | None = None


class EmailProvider(ABC):
    @abstractmethod
    async def validate(self, account: dict[str, Any]) -> bool: ...

    @abstractmethod
    async def fetch_messages(
        self,
        account: dict[str, Any],
        page_token: str | None = None,
        max_results: int = 50,
    ) -> SyncResult: ...

    @abstractmethod
    async def fetch_delta(
        self,
        account: dict[str, Any],
        history_id: str,
    ) -> SyncResult: ...

    @abstractmethod
    async def mark_read(
        self,
        account: dict[str, Any],
        message_id: str,
    ) -> None: ...

    @abstractmethod
    async def get_thread(
        self,
        account: dict[str, Any],
        thread_id: str,
    ) -> list[SyncMessage]: ...
