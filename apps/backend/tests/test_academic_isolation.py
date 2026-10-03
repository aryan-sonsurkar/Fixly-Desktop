"""P0.2 Loop 6: user isolation across the academic context layer.

A fake two-user store proves every read path scopes to the authenticated
caller identity: Student A never receives Student B's subjects,
assignments, documents, deadlines, or context. Model/tool callers supply
no user ids of their own — scope always comes from the request identity.
"""

import pytest

from app.services.academic_context import AcademicContextService

STORE = {
    "subjects": [
        {"id": "s-a1", "user_id": "student-A", "name": "DBMS"},
        {"id": "s-b1", "user_id": "student-B", "name": "DBMS"},
        {"id": "s-b2", "user_id": "student-B", "name": "Secret Research"},
    ],
    "assignments": [
        {"id": "a-a1", "user_id": "student-A", "title": "A normalisation",
         "status": "pending", "priority": "high",
         "due_date": "2026-10-05T21:00:00Z", "subject_id": "s-a1"},
        {"id": "a-b1", "user_id": "student-B", "title": "B classified work",
         "status": "pending", "priority": "urgent",
         "due_date": "2026-10-06T21:00:00Z", "subject_id": "s-b1"},
    ],
    "documents": [
        {"id": "d-a1", "user_id": "student-A", "original_name": "a-notes.pdf",
         "page_count": 2, "status": "indexed", "subject_id": "s-a1"},
        {"id": "d-b1", "user_id": "student-B", "original_name": "b-secret.pdf",
         "page_count": 9, "status": "indexed", "subject_id": "s-b1"},
    ],
}


def _svc(monkeypatch):
    svc = AcademicContextService(access_token="tok")

    async def subjects(user_id):
        return [s for s in STORE["subjects"] if s["user_id"] == user_id]

    async def assignments(user_id, page=1, page_size=50, sort_by="x", sort_order="asc", filters=None):
        rows = [a for a in STORE["assignments"] if a["user_id"] == user_id]
        status = (filters or {}).get("status")
        if status:
            wanted = set(status if isinstance(status, list) else [status])
            rows = [r for r in rows if r.get("status") in wanted]
        sid = (filters or {}).get("subject_id")
        if sid:
            rows = [r for r in rows if r.get("subject_id") == sid]
        return rows, len(rows)

    async def documents(user_id, page=1, page_size=20, subject_id=None, **kwargs):
        rows = [d for d in STORE["documents"] if d["user_id"] == user_id]
        if subject_id:
            rows = [r for r in rows if r.get("subject_id") == subject_id]
        return rows[:page_size], len(rows)

    async def chunks(document_id, user_id):
        return []

    monkeypatch.setattr(svc.subject_repo, "list_subjects", subjects)
    monkeypatch.setattr(svc.assignment_repo, "list_assignments", assignments)
    monkeypatch.setattr(svc.document_repo, "list_documents", documents)
    monkeypatch.setattr(svc.document_repo, "get_chunks", chunks)
    return svc


def _blob(value):
    return str(value)


@pytest.mark.asyncio
async def test_student_context_isolated(monkeypatch):
    svc = _svc(monkeypatch)
    out = await svc.get_student_context("student-A")
    blob = _blob(out)
    assert "Secret Research" not in blob
    assert "B classified work" not in blob
    assert "b-secret.pdf" not in blob
    assert "DBMS" in blob and "A normalisation" in blob


@pytest.mark.asyncio
async def test_course_context_isolated_and_cross_subject_id_rejected(monkeypatch):
    svc = _svc(monkeypatch)
    out = await svc.get_course_context("student-A", "DBMS")
    assert out["subject"]["id"] == "s-a1"
    assert _blob(out).find("b-secret") == -1
    # student B's subject id is invisible to student A
    out2 = await svc.get_course_context("student-A", "s-b1")
    assert out2["subject"] is None
    assert out2["resolution"]["status"] == "missing"


@pytest.mark.asyncio
async def test_deadlines_isolated(monkeypatch):
    svc = _svc(monkeypatch)
    out = await svc.get_upcoming_deadlines("student-A", days=60)
    titles = [d["title"] for d in out["deadlines"]]
    assert titles == ["A normalisation"]
    out_b = await svc.get_upcoming_deadlines("student-B", days=60)
    assert [d["title"] for d in out_b["deadlines"]] == ["B classified work"]


@pytest.mark.asyncio
async def test_resolve_never_returns_foreign_subject(monkeypatch):
    svc = _svc(monkeypatch)
    r = await svc.resolve_course("student-A", "Secret Research")
    assert r["status"] == "missing"
