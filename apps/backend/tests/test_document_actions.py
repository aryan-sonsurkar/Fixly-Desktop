"""Document action pipeline: guards, structured parsing, conversation-free gen."""

import pytest

from app.services.document_service import DocumentService


def _service(monkeypatch, doc, chunks):
    svc = DocumentService(access_token="tok")

    async def fake_get_document(document_id, user_id):
        return doc

    async def fake_get_chunks(document_id, user_id):
        return chunks

    async def fake_log_session(*args, **kwargs):
        return None

    async def fake_generate_text(**kwargs):
        fake_generate_text.calls.append(kwargs)
        return fake_generate_text.response

    fake_generate_text.calls = []
    fake_generate_text.response = ""
    monkeypatch.setattr(svc.repository, "get_document", fake_get_document)
    monkeypatch.setattr(svc.repository, "get_chunks", fake_get_chunks)
    monkeypatch.setattr(svc.study_service, "log_session", fake_log_session)
    monkeypatch.setattr(svc.ai_service, "generate_text", fake_generate_text)
    return svc, fake_generate_text


def _doc(status="indexed"):
    return {"id": "d1", "user_id": "u1", "original_name": "DBMS Notes.pdf",
            "file_type": "pdf", "status": status, "subject_id": None}


def _chunks():
    return [
        {"content": "Normalization reduces redundancy.", "page_number": 3,
         "heading": None, "chunk_index": 0},
        {"content": "B-trees speed range queries.", "page_number": 5,
         "heading": None, "chunk_index": 1},
    ]


@pytest.mark.asyncio
async def test_summarize_uses_document_content(monkeypatch):
    svc, gen = _service(monkeypatch, _doc(), _chunks())
    gen.response = "## Summary\n\nNormalization helps."
    out = await svc.generate_document_content("u1", "d1", "summarize")
    assert out["content"] == "## Summary\n\nNormalization helps."
    assert out["sources"][0]["title"] == "DBMS Notes.pdf"
    assert out["sources"][0]["pages"] == [3, 5]
    # Prompt sent to the model contains the document text (no pasting needed)
    assert "Normalization reduces redundancy" in gen.calls[0]["prompt"]
    # No conversation key: conversation-free path
    assert "conversation" not in out


@pytest.mark.asyncio
async def test_pending_document_refuses_clearly(monkeypatch):
    svc, gen = _service(monkeypatch, _doc(status="processing"), _chunks())
    from app.core.exceptions import ValidationError

    with pytest.raises(ValidationError, match="still being processed"):
        await svc.generate_document_content("u1", "d1", "summarize")
    assert gen.calls == []


@pytest.mark.asyncio
async def test_empty_document_refuses_clearly(monkeypatch):
    svc, gen = _service(monkeypatch, _doc(status="empty"), [])
    from app.core.exceptions import ValidationError

    with pytest.raises(ValidationError, match="no extractable text"):
        await svc.generate_document_content("u1", "d1", "quiz")


@pytest.mark.asyncio
async def test_flashcards_structured(monkeypatch):
    svc, gen = _service(monkeypatch, _doc(), _chunks())
    gen.response = (
        '[{"front": "What is normalization?", "back": "Organizing tables."},'
        ' {"front": "What is a B-tree?", "back": "An index."}]'
    )
    out = await svc.generate_document_content("u1", "d1", "flashcards", count=2)
    assert len(out["cards"]) == 2
    assert out["cards"][0]["front"] == "What is normalization?"
    assert out["sources"][0]["pages"] == [3, 5]


@pytest.mark.asyncio
async def test_quiz_structured_with_markdown_fallback(monkeypatch):
    svc, gen = _service(monkeypatch, _doc(), _chunks())
    gen.response = (
        '[{"question": "What is 1NF?", "options": ["A) x", "B) y"],'
        ' "answer": "A) x", "explanation": "Because."}]'
    )
    out = await svc.generate_document_content("u1", "d1", "quiz", count=1)
    assert len(out["questions"]) == 1
    assert out["questions"][0]["answer"] == "A) x"

    gen.response = "Here is your quiz:\n\n1. What is 1NF? It removes groups."
    out2 = await svc.generate_document_content("u1", "d1", "quiz", count=1)
    assert out2["questions"] == []
    assert "1NF" in out2["content"]


def test_parse_structured_list_edge_cases():
    parse = DocumentService._parse_structured_list
    assert parse("no json here") == []
    assert parse('```json\n[{"a": 1}]\n```') == [{"a": 1}]
    assert parse('{"not": "a list"}') == []
    assert parse("[1, 2") == []
