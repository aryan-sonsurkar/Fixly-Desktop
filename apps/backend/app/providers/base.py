from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import Any


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
