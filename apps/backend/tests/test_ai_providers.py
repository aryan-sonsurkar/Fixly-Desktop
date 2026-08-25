from unittest.mock import AsyncMock

import pytest

from app.providers.ollama import OllamaProvider


@pytest.mark.asyncio
async def test_ollama_is_available_when_default_model_is_missing() -> None:
    provider = OllamaProvider()
    provider.list_models = AsyncMock(return_value=[{"name": "llama3.2:3b"}])

    assert await provider.check_availability() is True


@pytest.mark.asyncio
async def test_ollama_is_available_when_configured_model_is_installed() -> None:
    provider = OllamaProvider()
    provider.list_models = AsyncMock(return_value=[{"name": provider.model}])

    assert await provider.check_availability() is True


@pytest.mark.asyncio
async def test_selected_ollama_model_is_used() -> None:
    provider = OllamaProvider()
    provider.list_models = AsyncMock(return_value=[{"name": "qwen2.5:7b"}])

    selected = await provider.select_model("qwen2.5:7b")

    assert selected == "qwen2.5:7b"
    assert provider.model == "qwen2.5:7b"


@pytest.mark.asyncio
async def test_missing_selected_ollama_model_is_rejected() -> None:
    provider = OllamaProvider()
    provider.list_models = AsyncMock(return_value=[{"name": "llama3.2:3b"}])

    with pytest.raises(Exception, match="no longer installed"):
        await provider.select_model("qwen2.5:7b")


@pytest.mark.asyncio
async def test_users_keep_independent_ollama_model_selections() -> None:
    user_a = OllamaProvider()
    user_b = OllamaProvider()
    user_a.list_models = AsyncMock(return_value=[{"name": "qwen2.5:7b"}])
    user_b.list_models = AsyncMock(return_value=[{"name": "gemma2:2b"}])

    await user_a.select_model("qwen2.5:7b")
    await user_b.select_model("gemma2:2b")

    assert user_a.model == "qwen2.5:7b"
    assert user_b.model == "gemma2:2b"