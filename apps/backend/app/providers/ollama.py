from collections.abc import AsyncGenerator
from typing import Any

import httpx

from app.config import settings
from app.core.exceptions import AIProviderUnavailableError
from app.core.logging import get_logger
from app.providers.base import AIProvider

logger = get_logger(__name__)


class OllamaProvider(AIProvider):
    name = "ollama"

    # Demo-optimized: smallest reliable model for 8GB Windows laptop
    # If team laptop has 16GB+, they can use llama3.2:3b via provider_model setting
    DEFAULT_MODEL = "gemma2:2b"
    FALLBACK_MODEL = "llama3.2:1b"

    def __init__(self) -> None:
        self.base_url = settings.ollama_host.rstrip("/")
        self.model = self.DEFAULT_MODEL
        self.timeout = 90

    def set_model(self, model: str) -> None:
        self.model = model

    async def generate(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        try:
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
        except httpx.HTTPStatusError as e:
            logger.warning("Ollama generate HTTP error: %s", e)
            raise AIProviderUnavailableError(f"Ollama error: {e.response.status_code}") from e
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            raise AIProviderUnavailableError("Ollama not available") from e
        except Exception as e:
            logger.warning("Ollama generate failed: %s", e)
            raise AIProviderUnavailableError(str(e)) from e

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

    # short TTL cache to reduce cold-start on repeated checks (demo: rapid AI calls)
    _cache: dict[str, Any] = {}
    _cache_ts: float = 0.0

    async def check_availability(self) -> bool:
        detail = await self.check_availability_detail()
        return bool(detail.get("available"))

    async def check_availability_detail(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "name": self.name,
            "available": False,
            "installed": False,
            "running": False,
            "models": [],
            "error": None,
            "model_count": 0,
            "required_model": self.model,
        }
        try:
            async with httpx.AsyncClient(timeout=1.5) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                if response.status_code == 200:
                    result["installed"] = True
                    result["running"] = True
                    data = response.json()
                    models = data.get("models", [])
                    result["models"] = [m.get("name", "") for m in models]
                    result["model_count"] = len(models)
                    has_required = any(self.model in m or self.FALLBACK_MODEL in m for m in result["models"])
                    result["available"] = len(models) > 0 and has_required
                    if len(models) > 0 and not has_required:
                        result["error"] = f"Fixly AI model is not installed. Required: {self.model}. Run: ollama pull {self.model}"
                    elif len(models) == 0:
                        result["error"] = f"Ollama installed but no models. Run: ollama pull {self.model}"
                else:
                    result["running"] = True
                    result["error"] = f"Ollama responded with status {response.status_code}"
        except httpx.ConnectError:
            result["error"] = "Ollama is required for local Fixly AI. Not installed or daemon not running. Install: https://ollama.com → then: ollama pull gemma2:2b"
        except httpx.TimeoutException:
            result["running"] = True
            result["error"] = "Ollama daemon is running but not responding (timeout) – try: ollama serve"
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
