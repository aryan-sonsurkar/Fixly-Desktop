from collections.abc import AsyncGenerator
from typing import Any

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

    def set_model(self, model: str) -> None:
        self.model = model

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

    async def check_availability_detail(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "available": False,
            "installed": False,
            "running": False,
            "models": [],
            "error": None,
            "model_count": 0,
        }
        try:
            async with httpx.AsyncClient(timeout=3) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                if response.status_code == 200:
                    result["installed"] = True
                    result["running"] = True
                    data = response.json()
                    models = data.get("models", [])
                    result["models"] = [m.get("name", "") for m in models]
                    result["model_count"] = len(models)
                    result["available"] = len(models) > 0
                else:
                    result["running"] = True
                    result["error"] = f"Ollama responded with status {response.status_code}"
        except httpx.ConnectError:
            result["error"] = "Ollama is not installed or the daemon is not running. Download from https://ollama.com"
        except httpx.TimeoutException:
            result["running"] = True
            result["error"] = "Ollama daemon is running but not responding (timeout)"
        except Exception as e:
            result["error"] = str(e)
        return result

    async def list_models(self) -> list[dict[str, Any]]:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                data = response.json()
                return [
                    {
                        "name": m.get("name", ""),
                        "size": m.get("size", 0),
                        "modified_at": str(m.get("modified_at", "")),
                    }
                    for m in data.get("models", [])
                ]
        except Exception as e:
            logger.warning("Failed to list Ollama models: %s", e)
            return []
