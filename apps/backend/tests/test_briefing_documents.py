"""Regression tests: document pipeline, briefing narrative, offline embeddings."""

import pytest

from app.services.pdf_service import PDFService
from app.services.planner_service import PlannerService


@pytest.fixture
def pdf_service():
    return PDFService(access_token=None)


@pytest.mark.asyncio
async def test_extract_pages_numbers(pdf_service, tmp_path):
    import asyncio

    # Reuse the hand-built 3-page PDF layout via pypdf writer is complex;
    # instead verify chunk_pages attribution directly.
    pages = [(1, "Alpha beta gamma."), (2, "Delta epsilon zeta.")]
    chunks = await pdf_service.chunk_pages(pages)
    assert len(chunks) == 2
    assert [c["page_number"] for c in chunks] == [1, 2]
    assert chunks[0]["chunk_index"] == 0
    assert chunks[1]["chunk_index"] == 1


@pytest.mark.asyncio
async def test_chunk_text_empty_returns_no_chunks(pdf_service):
    assert await pdf_service.chunk_text("") == []
    assert await pdf_service.chunk_text("[No text layer found in PDF]") == []
    assert await pdf_service.chunk_text("[PDF extraction failed: boom]") == []


@pytest.mark.asyncio
async def test_chunk_text_normal(pdf_service):
    chunks = await pdf_service.chunk_text("Hello world. " * 50, chunk_size=20, overlap=0)
    assert len(chunks) > 1
    assert all(c["page_number"] is None for c in chunks)


def test_parse_narrative_valid():
    svc = PlannerService(access_token=None)
    parsed = svc._parse_narrative(
        '{"summary": "Focus on DBMS.", "quote": "Keep going.", "motivation": "You can do it."}'
    )
    assert parsed is not None
    assert parsed["summary"] == "Focus on DBMS."


def test_parse_narrative_malformed():
    svc = PlannerService(access_token=None)
    assert svc._parse_narrative("not json at all {{{") is None
    assert svc._parse_narrative('{"summary": "", "quote": "", "motivation": ""}') is None
    assert svc._parse_narrative('{"summary": "x"}') is None


def test_parse_narrative_strips_fences():
    svc = PlannerService(access_token=None)
    parsed = svc._parse_narrative(
        '```json\n{"summary": "S.", "quote": "Q.", "motivation": "M."}\n```'
    )
    assert parsed is not None and parsed["quote"] == "Q."


def test_sanitize_quote_drops_attribution():
    svc = PlannerService(access_token=None)
    assert svc._sanitize_quote("Keep going. — Albert Einstein") == "Keep going."
    assert svc._sanitize_quote('"Stay curious." -- Marie Curie') == "Stay curious."
    assert len(svc._sanitize_quote("x" * 500)) <= 200


def test_fallback_quote_deterministic():
    svc = PlannerService(access_token=None)
    assert svc._fallback_quote("2026-09-19") == svc._fallback_quote("2026-09-19")
    assert isinstance(svc._fallback_quote("2026-09-19"), str)


def test_fallback_motivation_grounded():
    svc = PlannerService(access_token=None)
    m = svc._fallback_motivation(
        [{"priority": "high", "title": "DBMS HW"}],
        {"active_assignments": 3, "streak": 5},
    )
    assert "1 high-priority" in m
    m2 = svc._fallback_motivation([], {"active_assignments": 0, "streak": 0})
    assert isinstance(m2, str) and len(m2) > 0


def test_briefing_response_schema():
    from app.schemas.planner import DailyBriefingResponse

    b = DailyBriefingResponse(
        date="2026-09-19",
        greeting="Good morning, Aryan.",
        summary="Focus on DBMS.",
        focus_items=[],
        quote={"text": "Keep going.", "attribution": "Fixly AI"},
        motivation="One session early helps.",
        next_action=None,
        ai_available=False,
        generated_at="2026-09-19T00:00:00+00:00",
    )
    assert b.quote.attribution == "Fixly AI"
    assert b.focus_items == []


def test_bundled_embedding_dir_shape():
    from app.services.embedding_service import _bundled_model_dir

    found = _bundled_model_dir()
    # CI runners lack the snapshot; local checkout has it. Either is valid.
    assert found is None or found.endswith("all-MiniLM-L6-v2")
