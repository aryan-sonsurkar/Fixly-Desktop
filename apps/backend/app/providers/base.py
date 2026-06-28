from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator


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

    def count_tokens(self, text: str) -> int:
        return len(text.split())
