from collections.abc import AsyncGenerator
from typing import Any

import httpx

from app.config import settings
from app.core.logging import get_logger
from app.providers.base import AIProvider

logger = get_logger(__name__)

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"
GEMINI_MODEL = "gemini-2.0-flash"


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
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload, params={"key": self.api_key})
            response.raise_for_status()
            data = response.json()
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

    async def check_availability(self) -> bool:
        if not self.api_key:
            return False
        try:
            url = f"{GEMINI_API_BASE}/models/{GEMINI_MODEL}"
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(url, params={"key": self.api_key})
                return response.status_code == 200
        except Exception as e:
            logger.warning("Gemini not available: %s", e)
            return False
