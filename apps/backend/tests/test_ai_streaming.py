from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.exceptions import AIProviderUnavailableError
from app.main import _is_allowed_origin
from app.services.ai_service import AIService


async def _tokens(*items: str) -> AsyncGenerator[str, None]:
    for item in items:
        yield item


class TestAIStreaming:
    def test_tauri_webview_origin_is_allowed_for_streaming_fetch(self) -> None:
        assert _is_allowed_origin("http://tauri.localhost")

    def _service(self, provider: MagicMock) -> tuple[AIService, AsyncMock]:
        service = AIService()
        repository = AsyncMock()
        repository.get_conversation = AsyncMock(return_value={"id": "conversation-1", "title": "Question"})
        repository.get_messages = AsyncMock(return_value=[])
        repository.create_message = AsyncMock(return_value={"id": "message-1"})
        repository.get_message_count = AsyncMock(return_value=2)
        service.repository = repository
        service._get_settings = AsyncMock(return_value={})  # type: ignore[method-assign]
        service._resolve_provider = AsyncMock(return_value=provider)  # type: ignore[method-assign]
        service._format_messages = AsyncMock(return_value=[{"role": "user", "content": "Question"}])  # type: ignore[method-assign]
        return service, repository

    @pytest.mark.asyncio
    async def test_stream_persists_one_scrubbed_assistant_message(self) -> None:
        provider = MagicMock(name="gemini")
        provider.generate_stream = lambda *_args: _tokens("I am Gem", "ini, ready to help.")
        service, repository = self._service(provider)

        result = [token async for token in service.chat_stream("user-1", "Question", "conversation-1")]

        assert "".join(result) == "I am Fixly AI, ready to help."
        assert repository.create_message.await_count == 2
        assistant_call = repository.create_message.await_args_list[-1]
        assert assistant_call.args[2] == "assistant"
        assert assistant_call.args[3] == "I am Fixly AI, ready to help."
        assert assistant_call.args[4] == "Fixly AI"

    @pytest.mark.asyncio
    async def test_stream_failure_is_a_safe_provider_error(self) -> None:
        provider = MagicMock(name="ollama")

        async def fail(*_args: object) -> AsyncGenerator[str, None]:
            raise RuntimeError("provider secret and internals")
            yield ""  # pragma: no cover

        provider.generate_stream = fail
        service, repository = self._service(provider)

        with pytest.raises(AIProviderUnavailableError, match="currently unavailable"):
            _ = [token async for token in service.chat_stream("user-1", "Question", "conversation-1")]

        assert repository.create_message.await_count == 1
