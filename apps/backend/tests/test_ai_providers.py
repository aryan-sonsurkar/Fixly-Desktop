from unittest.mock import AsyncMock

import pytest

from app.providers.ollama import OllamaProvider


@pytest.mark.asyncio
async def test_ollama_is_unavailable_when_configured_model_is_missing() -> None:
    provider = OllamaProvider()
    provider.check_availability_detail = AsyncMock(
        return_value={"available": False, "running": True, "models": ["llama3.2:3b"]}
    )

    assert await provider.check_availability() is False


@pytest.mark.asyncio
async def test_ollama_is_available_when_configured_model_is_installed() -> None:
    provider = OllamaProvider()
    provider.check_availability_detail = AsyncMock(
        return_value={"available": True, "running": True, "models": [provider.model]}
    )

    assert await provider.check_availability() is True