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

    def __init__(self) -> None:
        self.base_url = settings.ollama_host.rstrip("/")
        self.model = self.DEFAULT_MODEL
        self.timeout = 90

    _models_cache: dict[str, tuple[float, list[dict[str, Any]]]] = {}
    MODEL_CACHE_TTL = 10.0

    def set_model(self, model: str) -> None:
        self.model = model

    async def select_model(self, requested: str | None = None) -> str:
        models = await self.list_models()
        names = [str(model.get("name", "")) for model in models]
        if requested:
            if requested not in names:
                raise AIProviderUnavailableError("Selected Ollama model is no longer installed")
            self.model = requested
        elif names:
            self.model = self.DEFAULT_MODEL if self.DEFAULT_MODEL in names else names[0]
        return self.model

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

    async def check_availability(self) -> bool:
        models = await self.list_models()
        if not models:
            return False
        if self.model:
            names = [m.get("name", "") for m in models]
            return self.model in names
        return True

    async def _discover_models(self, force_refresh: bool = False) -> tuple[bool, list[dict[str, Any]]]:
        import time

        cached = self._models_cache.get(self.base_url)
        if not force_refresh and cached and time.time() - cached[0] < self.MODEL_CACHE_TTL:
            return True, cached[1]
        try:
            async with httpx.AsyncClient(timeout=1.5) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                if response.status_code != 200:
                    return False, []
                data = response.json()
                models = [
                    {
                        "name": str(model.get("name", "")),
                        "size": model.get("size", 0),
                        "modified_at": str(model.get("modified_at", "")),
                    }
                    for model in data.get("models", [])
                    if model.get("name")
                ]
                self._models_cache[self.base_url] = (time.time(), models)
                return True, models
        except Exception as e:
            logger.warning("Ollama model discovery failed: %s", e)
            return False, []

    async def check_availability_detail(self, force_refresh: bool = False) -> dict[str, Any]:
        result: dict[str, Any] = {
            "name": self.name,
            "available": False,
            "installed": False,
            "running": False,
            "models": [],
            "error": None,
            "model_count": 0,
            "selected_model": self.model,
        }
        reachable, models = await self._discover_models(force_refresh)
        result["models"] = [str(model["name"]) for model in models]
        result["model_count"] = len(models)
        if reachable:
            result["installed"] = True
            result["running"] = True
            result["available"] = len(models) > 0
            if not models:
                result["error"] = "No models installed. Install an Ollama model to use Fixly AI."
            elif self.model not in result["models"]:
                result["error"] = "Selected model is no longer installed."
        else:
            result["error"] = "Ollama is not running or cannot be reached. Start Ollama to use Fixly AI."
        return result

    async def list_models(self, force_refresh: bool = False) -> list[dict[str, Any]]:
        _reachable, models = await self._discover_models(force_refresh)
        return models
