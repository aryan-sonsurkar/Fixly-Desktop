from collections.abc import AsyncGenerator
from typing import Any

import httpx

from app.config import settings
from app.core.exceptions import AIProviderUnavailableError
from app.core.logging import get_logger
from app.providers.base import AIProvider

logger = get_logger(__name__)

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"
GEMINI_MODEL = "gemini-2.0-flash"

_PLACEHOLDER_KEYS = {
    "",
    "your_gemini_api_key",
    "your_api_key",
    "your-api-key",
    "api_key",
    "changeme",
    "change-me",
    "replaceme",
    "<your-api-key>",
    "<your_gemini_api_key>",
}


def _has_usable_key(key: str) -> bool:
    k = (key or "").strip()
    if not k:
        return False
    if k.lower() in _PLACEHOLDER_KEYS:
        return False
    lowered = k.lower()
    if lowered.startswith("your_") or lowered.startswith("your-"):
        return False
    if k.startswith("<") or "env(" in lowered:
        return False
    return True


class GeminiProvider(AIProvider):
    name = "gemini"

    def __init__(self) -> None:
        self.api_key = settings.gemini_api_key
        self.timeout = 60

    def _format_messages(
        self, messages: list[dict[str, str]]
    ) -> tuple[list[dict[str, Any]], str | None]:
        contents: list[dict[str, Any]] = []
        system_instruction: str | None = None
        for msg in messages:
            if msg["role"] == "system":
                system_instruction = msg["content"]
            elif msg["role"] == "user":
                contents.append({"role": "user", "parts": [{"text": msg["content"]}]})
            elif msg["role"] == "assistant":
                contents.append({"role": "model", "parts": [{"text": msg["content"]}]})
        return contents, system_instruction

    async def generate(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        if not _has_usable_key(self.api_key):
            raise AIProviderUnavailableError("Gemini API key is not configured")
        contents, system_instruction = self._format_messages(messages)
        payload: dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        url = f"{GEMINI_API_BASE}/models/{GEMINI_MODEL}:generateContent"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload, params={"key": self.api_key})
                response.raise_for_status()
                data = response.json()
        except Exception as e:
            logger.warning("Gemini generate failed: %s", e)
            raise AIProviderUnavailableError(f"Gemini request failed: {e}") from e
        candidates = data.get("candidates", [])
        if not candidates:
            return ""
        parts = candidates[0].get("content", {}).get("parts", [])
        return "".join(str(p.get("text", "")) for p in parts)

    async def generate_stream(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncGenerator[str, None]:
        if not _has_usable_key(self.api_key):
            raise AIProviderUnavailableError("Gemini API key is not configured")
        contents, system_instruction = self._format_messages(messages)
        payload: dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        url = f"{GEMINI_API_BASE}/models/{GEMINI_MODEL}:streamGenerateContent"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream(
                    "POST", url, json=payload, params={"key": self.api_key}
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line.strip() or line.startswith("["):
                            continue
                        line = line.strip().lstrip(",")
                        if not line:
                            continue
                        try:
                            import json
                            data = json.loads(line)
                            candidates = data.get("candidates", [])
                            if candidates:
                                parts = candidates[0].get("content", {}).get("parts", [])
                                text = "".join(str(p.get("text", "")) for p in parts)
                                if text:
                                    yield text
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            logger.warning("Gemini stream failed: %s", e)
            raise AIProviderUnavailableError(f"Gemini request failed: {e}") from e

    async def check_availability(self) -> bool:
        if not _has_usable_key(self.api_key):
            return False
        try:
            url = f"{GEMINI_API_BASE}/models/{GEMINI_MODEL}"
            async with httpx.AsyncClient(timeout=3) as client:
                response = await client.get(url, params={"key": self.api_key})
                return response.status_code == 200
        except Exception as e:
            logger.warning("Gemini not available: %s", e)
            return False
