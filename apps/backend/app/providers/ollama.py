from collections.abc import AsyncGenerator

import httpx

from app.config import settings
from app.core.logging import get_logger
from app.providers.base import AIProvider

logger = get_logger(__name__)


class OllamaProvider(AIProvider):
    name = "ollama"

    def __init__(self) -> None:
        self.base_url = settings.ollama_host.rstrip("/")
        self.model = "llama3.2"
        self.timeout = 60

    async def generate(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            payload = {
                "model": self.model,
                "messages": messages,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
                "stream": False,
            }
            response = await client.post(f"{self.base_url}/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()
            return str(data.get("message", {}).get("content", ""))

    async def generate_stream(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncGenerator[str, None]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            payload = {
                "model": self.model,
                "messages": messages,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
                "stream": True,
            }
            async with client.stream("POST", f"{self.base_url}/api/chat", json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    try:
                        import json
                        data = json.loads(line)
                        content = data.get("message", {}).get("content", "")
                        if content:
                            yield content
                    except json.JSONDecodeError:
                        continue

    async def check_availability(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception as e:
            logger.warning("Ollama not available: %s", e)
            return False
