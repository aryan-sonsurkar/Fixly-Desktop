"""AI workspace stabilization regression tests.

Covers: resident model reuse, stream error propagation (no masked
failures), prompt budget truncation, diagnostics shape.
"""

import pytest

from app.providers.fixly_local import (
    MAX_TOKENS_CAP,
    PROMPT_CHAR_BUDGET,
    FixlyLocalProvider,
    _truncate_to_budget,
)


@pytest.fixture
def preserve_shared_state():
    llama = FixlyLocalProvider._shared_llama
    err = FixlyLocalProvider._shared_load_error
    yield
    FixlyLocalProvider._shared_llama = llama
    FixlyLocalProvider._shared_load_error = err


def test_truncate_keeps_system_and_tail_under_budget():
    system = {"role": "system", "content": "S" * 1000}
    rest = [{"role": "user", "content": "x" * 2000} for _ in range(10)]
    out = _truncate_to_budget([system] + rest)
    assert out[0]["role"] == "system"
    assert sum(len(m["content"]) for m in out) <= PROMPT_CHAR_BUDGET
    # tail preserved (most recent messages kept)
    assert out[-1] is rest[-1]


def test_truncate_noop_when_under_budget():
    msgs = [{"role": "user", "content": "hello"}]
    assert _truncate_to_budget(msgs) == msgs


def test_max_tokens_cap_sane():
    assert MAX_TOKENS_CAP <= 1024


def test_shared_model_reused_across_instances(preserve_shared_state):
    FixlyLocalProvider._shared_llama = None
    FixlyLocalProvider._shared_load_error = None
    first = FixlyLocalProvider()._load_llama()
    second = FixlyLocalProvider()._load_llama()
    assert first is second
    assert FixlyLocalProvider.is_resident() is (first is not None)


@pytest.mark.asyncio
async def test_stream_propagates_engine_error(preserve_shared_state):
    """A dead engine must raise (honest error), never yield silent empty."""
    FixlyLocalProvider._shared_llama = None
    provider = FixlyLocalProvider()
    provider.model_path = None  # force unavailable
    with pytest.raises(RuntimeError):
        async for _ in provider.generate_stream(
            [{"role": "user", "content": "hello"}]
        ):
            pass


@pytest.mark.asyncio
async def test_generate_propagates_engine_error(preserve_shared_state):
    FixlyLocalProvider._shared_llama = None
    provider = FixlyLocalProvider()
    provider.model_path = None
    with pytest.raises(RuntimeError):
        await provider.generate([{"role": "user", "content": "hello"}])


@pytest.mark.asyncio
async def test_check_availability_detail_student_safe(preserve_shared_state):
    FixlyLocalProvider._shared_llama = None
    provider = FixlyLocalProvider()
    provider.model_path = None
    detail = await provider.check_availability_detail()
    assert detail["available"] is False
    assert detail["reason"] in ("needs_update", "unavailable")
    for banned in ("pip install", "llama-cpp", "llama_cpp", "Traceback", "site-packages"):
        assert banned not in str(detail.get("error") or "")


@pytest.mark.asyncio
async def test_diagnostics_shape():
    from app.services.ai_service import AIService

    service = AIService(access_token=None)
    diag = await service.get_diagnostics("test-user")
    assert diag["status"] == "ok"
    assert "available" in diag["runtime"]
    assert "index_chunks" in diag["rag"]
    assert diag["rag"]["embedding_available"] is True
    assert "available" in diag["memory"]
