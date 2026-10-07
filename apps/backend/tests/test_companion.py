"""Focus Companion ranking/session tests (deterministic, no model calls)."""
import pytest

from app.services import companion_service as companion_mod
from app.services.companion_service import CompanionService, rank_candidates


def _svc(monkeypatch):
    svc = CompanionService(access_token="tok")

    async def fake_subjects(user_id):
        return [
            {"id": "s-dbms", "user_id": user_id, "name": "Database Management Systems"},
            {"id": "s-math", "user_id": user_id, "name": "Mathematics"},
        ]

    async def fake_assignments(*args, **kwargs):
        rows = [
            {"id": "a1", "user_id": "u9", "title": "DBMS Revision",
             "status": "pending", "priority": "high", "due_date": "2026-10-02T21:00:00Z",
             "subject_id": "s-dbms", "estimated_study_time": 45},
            {"id": "a2", "user_id": "u9", "title": "Mathematics Practice",
             "status": "pending", "priority": "medium", "due_date": "2026-10-09T21:00:00Z",
             "subject_id": "s-math", "estimated_study_time": 20},
            {"id": "a3", "user_id": "u9", "title": "Old done thing",
             "status": "completed", "priority": "low", "due_date": "2026-01-05T21:00:00Z",
             "subject_id": "s-math"},
        ]
        filters = kwargs.get("filters", {}) or {}
        status = filters.get("status")
        if status:
            wanted = set(status if isinstance(status, list) else [status])
            rows = [r for r in rows if r.get("status") in wanted]
        return rows, len(rows)

    async def fake_docs(*args, **kwargs):
        return [], 0

    async def fake_chunks(document_id, user_id):
        return []

    monkeypatch.setattr(svc.academic.subject_repo, "list_subjects", fake_subjects)
    monkeypatch.setattr(svc.academic.assignment_repo, "list_assignments", fake_assignments)
    monkeypatch.setattr(svc.academic.document_repo, "list_documents", fake_docs)
    monkeypatch.setattr(svc.academic.document_repo, "get_chunks", fake_chunks)
    return svc


def _cands():
    # Dates float relative to today so overdue flags stay test-controlled
    # (the ranker treats past-due items as overdue regardless of flags).
    from datetime import date, timedelta
    soon = (date.today() + timedelta(days=2)).isoformat()
    later = (date.today() + timedelta(days=9)).isoformat()
    return [
        {"key": f"assignment:DBMS Revision:{soon}", "title": "DBMS Revision",
         "subject": "DBMS", "due_date": soon, "overdue": False,
         "priority": "high", "estimated_minutes": 45},
        {"key": f"assignment:Maths Practice:{later}", "title": "Maths Practice",
         "subject": "Math", "due_date": later, "overdue": False,
         "priority": "medium", "estimated_minutes": 20},
    ]


def _keys(ranked):
    return [c["key"] for c in ranked]


def test_ranking_is_deterministic_and_deadline_first():
    assert _keys(rank_candidates(_cands())) == _keys(rank_candidates(_cands()))
    assert _keys(rank_candidates(_cands()))[0].startswith("assignment:DBMS Revision:")


def test_overdue_beats_everything():
    cands = _cands()
    cands[1]["overdue"] = True
    assert _keys(rank_candidates(cands))[0].startswith("assignment:Maths Practice:")


def test_limited_time_prefers_fitting_item():
    ranked = rank_candidates(_cands(), available_minutes=20)
    assert _keys(ranked)[0].startswith("assignment:Maths Practice:")
    assert ranked[0]["fits_window"] is True


def test_nothing_fits_falls_back_to_shortest_capped():
    ranked = rank_candidates(_cands(), available_minutes=5)
    assert _keys(ranked)[0].startswith("assignment:Maths Practice:")
    action = companion_mod.to_action(ranked[0], 5)
    assert action["suggested_minutes"] == 5


def test_excluded_keys_are_skipped():
    ranked = rank_candidates(_cands(), exclude_keys=[_cands()[0]["key"]])
    assert _keys(ranked) == [_cands()[1]["key"]]


@pytest.mark.asyncio
async def test_next_action_returns_one_action_from_context(monkeypatch):
    svc = _svc(monkeypatch)
    out = await svc.get_next_action("u9")
    assert out["action"] is not None
    assert out["action"]["title"] == "DBMS Revision"
    assert out["action"]["subject"] == "Database Management Systems"
    assert len(out["alternates"]) <= 3
    assert out["empty_reason"] is None


@pytest.mark.asyncio
async def test_next_action_adapts_to_five_minutes(monkeypatch):
    svc = _svc(monkeypatch)
    out = await svc.get_next_action("u9", available_minutes=5)
    assert out["action"] is not None
    assert out["action"]["suggested_minutes"] == 5


@pytest.mark.asyncio
async def test_reject_offers_next_best(monkeypatch):
    svc = _svc(monkeypatch)
    first = await svc.get_next_action("u9")
    key = first["action"]["key"]
    second = await svc.get_next_action("u9", exclude_keys=[key])
    assert second["action"] is not None
    assert second["action"]["key"] != key
    assert second["action"]["title"] == "Mathematics Practice"


@pytest.mark.asyncio
async def test_empty_state_is_honest(monkeypatch):
    svc = _svc(monkeypatch)

    async def no_assignments(*args, **kwargs):
        return [], 0

    monkeypatch.setattr(svc.academic.assignment_repo, "list_assignments", no_assignments)
    out = await svc.get_next_action("u9")
    assert out["action"] is None
    assert out["alternates"] == []
    assert isinstance(out["empty_reason"], str) and out["empty_reason"]


@pytest.mark.asyncio
async def test_continue_session_resumes_live_item(monkeypatch):
    svc = _svc(monkeypatch)
    first = await svc.get_next_action("u9")
    resumed = await svc.continue_session("u9", current_key=first["action"]["key"])
    assert resumed["resumed"] is True
    assert resumed["action"]["key"] == first["action"]["key"]


@pytest.mark.asyncio
async def test_continue_session_moves_on_when_done(monkeypatch):
    svc = _svc(monkeypatch)
    resumed = await svc.continue_session("u9", current_key="assignment:Gone:2026-01-01")
    assert resumed["resumed"] is False
    assert resumed["action"] is not None
