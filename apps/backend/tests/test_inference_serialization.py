"""Loop 12: inference serialization regression tests.

llama.cpp's shared context is not thread-safe: concurrent
create_chat_completion calls corrupt engine state and kill the backend
process (observed: two concurrent chats both reset ~40s in, server dead).
FixlyLocalProvider serializes ALL inference behind one process-wide lock.
These tests prove serialization with a stub engine (no model load).
"""
import asyncio
import threading
import time

import pytest

from app.providers.fixly_local import FixlyLocalProvider


class _StubEngine:
    """Fake llama engine tracking concurrent entry."""

    def __init__(self, stream_chunks=3, delay=0.15):
        self.active = 0
        self.max_active = 0
        self.guard = threading.Lock()
        self.stream_chunks = stream_chunks
        self.delay = delay

    def _enter(self):
        with self.guard:
            self.active += 1
            self.max_active = max(self.max_active, self.active)

    def _leave(self):
        with self.guard:
            self.active -= 1

    def create_chat_completion(self, **kwargs):
        self._enter()
        try:
            time.sleep(self.delay)
            if kwargs.get("stream"):
                return iter([
                    {"choices": [{"delta": {"content": "hi"}}]}
                    for _ in range(self.stream_chunks)
                ])
            return {"choices": [{"message": {"content": "hello"}}]}
        finally:
            self._leave()


def _provider_with_stub(monkeypatch, **stub_kw):
    provider = FixlyLocalProvider.__new__(FixlyLocalProvider)
    provider.model_path = "stub"
    provider.timeout = 90
    stub = _StubEngine(**stub_kw)
    monkeypatch.setattr(provider, "_load_llama", lambda: stub)
    return provider, stub


@pytest.mark.asyncio
async def test_concurrent_generate_calls_are_serialized(monkeypatch):
    provider, stub = _provider_with_stub(monkeypatch)
    messages = [{"role": "user", "content": "hi"}]
    results = await asyncio.gather(
        provider.generate(messages),
        provider.generate(messages),
    )
    assert results == ["hello", "hello"]
    assert stub.max_active == 1


@pytest.mark.asyncio
async def test_concurrent_streams_are_serialized(monkeypatch):
    provider, stub = _provider_with_stub(monkeypatch, stream_chunks=4)
    messages = [{"role": "user", "content": "hi"}]

    async def collect():
        return [tok async for tok in provider.generate_stream(messages)]

    first, second = await asyncio.gather(collect(), collect())
    assert first == ["hi"] * 4 and second == ["hi"] * 4
    assert stub.max_active == 1


@pytest.mark.asyncio
async def test_mixed_generate_and_stream_are_serialized(monkeypatch):
    provider, stub = _provider_with_stub(monkeypatch, stream_chunks=2)
    messages = [{"role": "user", "content": "hi"}]

    async def collect():
        return [tok async for tok in provider.generate_stream(messages)]

    text, tokens = await asyncio.gather(
        provider.generate(messages), collect())
    assert text == "hello" and tokens == ["hi", "hi"]
    assert stub.max_active == 1


def test_lock_is_shared_process_wide():
    assert FixlyLocalProvider._inference_lock is not None
    assert isinstance(FixlyLocalProvider._inference_lock, type(threading.Lock()))
