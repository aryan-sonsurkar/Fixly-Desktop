"""Academic context service (P0.2 Loop 3/4).

Covers: student overview, course resolution (id/exact/acronym/contains/
ambiguity/missing), course context contents + bounds, upcoming deadlines,
empty states, and relevance (no unrelated data).
"""

import pytest

from app.services.academic_context import AcademicContextService

DBMS_ID = "11111111-2222-3333-4444-555555555555"

SUBJECTS = [
    {"id": DBMS_ID, "user_id": "u1", "name": "Database Management Systems"},
    {"id": "s-dsu", "user_id": "u1", "name": "Data Structures"},
    {"id": "s-dbms-lab", "user_id": "u1", "name": "DBMS Lab"},
    {"id": "s-phy", "user_id": "u1", "name": "Physics"},
]

ASSIGNMENTS = [
    {"id": "a1", "user_id": "u1", "title": "DBMS normalization worksheet",
     "status": "pending", "priority": "high", "due_date": "2026-10-05T21:00:00Z",
     "subject_id": DBMS_ID},
    {"id": "a2", "user_id": "u1", "title": "DSU trees problem set",
     "status": "pending", "priority": "medium", "due_date": "2026-10-20T21:00:00Z",
     "subject_id": "s-dsu"},
    {"id": "a3", "user_id": "u1", "title": "Old physics lab",
     "status": "completed", "priority": "low", "due_date": "2026-01-05T21:00:00Z",
     "subject_id": "s-phy"},
]

DOCS = [
    {"id": "d1", "user_id": "u1", "original_name": "dbms-notes.pdf",
     "page_count": 3, "status": "indexed", "subject_id": DBMS_ID},
    {"id": "d2", "user_id": "u1", "original_name": "random.pdf",
     "page_count": 1, "status": "indexed", "subject_id": None},
]

CHUNKS = [
    {"content": "x", "heading": "First Normal Form", "page_number": 1},
    {"content": "y", "heading": None, "page_number": 1},
    {"content": "z", "heading": "Second Normal Form", "page_number": 2},
]


def _svc(monkeypatch, subjects=None, assignments=None, docs=None, chunks=None):
    svc = AcademicContextService(access_token="tok")

    async def fake_subjects(user_id):
        assert user_id == "u1"
        return list(subjects if subjects is not None else SUBJECTS)

    async def fake_assignments(*args, **kwargs):
        rows = list(assignments if assignments is not None else ASSIGNMENTS)
        filters = {}
        # support both service-style (user_id, params) and repo-style calls
        if len(args) >= 2 and isinstance(args[1], dict):
            filters = args[1]
        else:
            filters = kwargs.get("filters", {}) or {}
        status = filters.get("status")
        if status:
            wanted = set(status if isinstance(status, list) else [status])
            rows = [r for r in rows if r.get("status") in wanted]
        sid = filters.get("subject_id")
        if sid:
            rows = [r for r in rows if r.get("subject_id") == sid]
        return rows, len(rows)

    async def fake_docs(*args, **kwargs):
        rows = list(docs if docs is not None else DOCS)
        sid = kwargs.get("subject_id")
        if sid:
            rows = [r for r in rows if r.get("subject_id") == sid]
        page_size = kwargs.get("page_size", 20)
        return rows[:page_size], len(rows)

    async def fake_chunks(document_id, user_id):
        assert user_id == "u1"
        return list(chunks if chunks is not None else CHUNKS)

    monkeypatch.setattr(svc.subject_repo, "list_subjects", fake_subjects)
    monkeypatch.setattr(svc.assignment_repo, "list_assignments", fake_assignments)
    monkeypatch.setattr(svc.document_repo, "list_documents", fake_docs)
    monkeypatch.setattr(svc.document_repo, "get_chunks", fake_chunks)
    return svc


@pytest.mark.asyncio
async def test_student_context_bounded_overview(monkeypatch):
    svc = _svc(monkeypatch)
    out = await svc.get_student_context("u1")
    assert [s["name"] for s in out["subjects"]] == [
        "Database Management Systems", "Data Structures", "DBMS Lab", "Physics"]
    assert out["assignment_counts"]["pending_or_active"] == 2
    assert out["truncated"] is False
    # only pending/active surface, completed excluded
    assert all("Old physics" not in a["title"] for a in out["upcoming"])
    assert {a["priority"] for a in out["upcoming"]} == {"high", "medium"}


@pytest.mark.asyncio
async def test_student_context_empty_state(monkeypatch):
    svc = _svc(monkeypatch, subjects=[], assignments=[], docs=[])
    out = await svc.get_student_context("u1")
    assert out == {
        "subjects": [],
        "assignment_counts": {"pending_or_active": 0},
        "upcoming": [],
        "documents": [],
        "deadlines": [],
        "truncated": False,
    }


@pytest.mark.asyncio
async def test_resolve_by_id_and_exact_name(monkeypatch):
    svc = _svc(monkeypatch)
    assert (await svc.resolve_course("u1", DBMS_ID))["subject"]["name"] == \
        "Database Management Systems"
    assert (await svc.resolve_course("u1", "database management systems"))["subject"]["id"] == DBMS_ID


@pytest.mark.asyncio
async def test_resolve_acronym_and_contains(monkeypatch):
    svc = _svc(monkeypatch)
    # "DBMS" subsequences into both "Database Management Systems" and
    # "DBMS Lab" -> explicit ambiguity, never a guess
    r = await svc.resolve_course("u1", "DBMS")
    assert r["status"] == "ambiguous"
    assert {c["id"] for c in r["candidates"]} == {DBMS_ID, "s-dbms-lab"}
    # "dms" initials-style query also hits both DBMS subjects -> ambiguous
    r = await svc.resolve_course("u1", "dms")
    assert r["status"] == "ambiguous"
    # "data" matches two subjects -> ambiguity
    r = await svc.resolve_course("u1", "data")
    assert r["status"] == "ambiguous"
    assert {c["id"] for c in r["candidates"]} == {DBMS_ID, "s-dsu"}
    # unambiguous substring
    r2 = await svc.resolve_course("u1", "physics")
    assert r2["status"] == "found" and r2["subject"]["id"] == "s-phy"


@pytest.mark.asyncio
async def test_resolve_missing_and_empty(monkeypatch):
    svc = _svc(monkeypatch)
    assert (await svc.resolve_course("u1", "Astrophysics"))["status"] == "missing"
    assert (await svc.resolve_course("u1", "  "))["status"] == "missing"
    assert (await svc.resolve_course("u1", "00000000-0000-0000-0000-000000000000"))["status"] == "missing"


@pytest.mark.asyncio
async def test_course_context_relevant_only(monkeypatch):
    svc = _svc(monkeypatch)
    out = await svc.get_course_context("u1", "Database Management Systems")
    assert out["subject"]["id"] == DBMS_ID
    assert [a["title"] for a in out["assignments"]] == ["DBMS normalization worksheet"]
    assert [d["name"] for d in out["documents"]] == ["dbms-notes.pdf"]
    assert out["upcoming_dates"] == ["2026-10-05"]
    assert "First Normal Form" in out["topic_signals"]
    assert "Second Normal Form" in out["topic_signals"]
    # no physics/DSU leakage
    blob = str(out)
    assert "Physics" not in blob and "DSU trees" not in blob and "random.pdf" not in blob


@pytest.mark.asyncio
async def test_course_context_missing_course(monkeypatch):
    svc = _svc(monkeypatch)
    out = await svc.get_course_context("u1", "Astrophysics")
    assert out["subject"] is None
    assert out["resolution"]["status"] == "missing"
    assert out["assignments"] == [] and out["documents"] == []


@pytest.mark.asyncio
async def test_course_context_no_material(monkeypatch):
    svc = _svc(monkeypatch, assignments=[], docs=[])
    out = await svc.get_course_context("u1", "Physics")
    assert out["subject"]["id"] == "s-phy"
    assert out["assignments"] == [] and out["documents"] == []
    assert out["upcoming_dates"] == [] and out["topic_signals"] == []


@pytest.mark.asyncio
async def test_upcoming_deadlines_sorted_bounded(monkeypatch):
    svc = _svc(monkeypatch)
    out = await svc.get_upcoming_deadlines("u1", days=30, limit=20)
    dates = [d["due_date"] for d in out["deadlines"]]
    assert dates == sorted(dates)
    assert all(d["subject"] in ("Database Management Systems", "Data Structures")
               for d in out["deadlines"])
    # completed excluded
    assert all("Old physics" not in d["title"] for d in out["deadlines"])


@pytest.mark.asyncio
async def test_upcoming_deadlines_horizon_and_limit(monkeypatch):
    svc = _svc(monkeypatch)
    out = await svc.get_upcoming_deadlines("u1", days=1, limit=20)
    assert out["deadlines"] == []
    out2 = await svc.get_upcoming_deadlines("u1", days=30, limit=1)
    assert len(out2["deadlines"]) == 1 and out2["truncated"] is True


@pytest.mark.asyncio
async def test_detect_course_mention_abbreviation_collides_to_ambiguity(monkeypatch):
    # "DBMS" abbreviates BOTH "Database Management Systems" and "DBMS Lab":
    # the detector must surface ambiguity, never guess between them.
    svc = _svc(monkeypatch)
    r = await svc.detect_course_mention("u1", "I have a DBMS test tomorrow. What should I study?")
    assert r["status"] == "ambiguous"
    ids = {c["id"] for c in r["candidates"]}
    assert {DBMS_ID, "s-dbms-lab"} <= ids


@pytest.mark.asyncio
async def test_detect_course_mention_headline_workflow_single_course(monkeypatch):
    # Phase-9 shape: one DBMS course on the account. The same message
    # must resolve found so the chat layer can inject its context.
    svc = _svc(monkeypatch, subjects=[SUBJECTS[0]])
    r = await svc.detect_course_mention("u1", "I have a DBMS test tomorrow. What should I study?")
    assert r["status"] == "found" and r["subject"]["id"] == DBMS_ID


@pytest.mark.asyncio
async def test_detect_course_mention_generic_message_injects_nothing(monkeypatch):
    svc = _svc(monkeypatch)
    r = await svc.detect_course_mention("u1", "How do I reverse a string in C?")
    assert r["status"] == "missing"


@pytest.mark.asyncio
async def test_detect_course_mention_ambiguous(monkeypatch):
    # "data" subsequence-matches Database Management Systems and Data
    # Structures alike: explicit ambiguity, never a guess.
    svc = _svc(monkeypatch)
    r = await svc.detect_course_mention("u1", "help with data please")
    assert r["status"] == "ambiguous"
    ids = {c["id"] for c in r["candidates"]}
    assert {DBMS_ID, "s-dsu"} <= ids


@pytest.mark.asyncio
async def test_format_course_block_bounded_and_grounded(monkeypatch):
    svc = _svc(monkeypatch)
    ctx = await svc.get_course_context("u1", "Database Management Systems")
    block = AcademicContextService.format_course_context_block(ctx)
    assert "Database Management Systems" in block
    assert "DBMS normalization worksheet" in block
    assert "dbms-notes.pdf" in block
    assert "First Normal Form" in block
    assert "Physics" not in block
    assert len(block) <= 1200


@pytest.mark.asyncio
async def test_format_messages_injects_course_block(monkeypatch):
    from app.services import ai_service as ai_mod

    svc = ai_mod.AIService(access_token="tok")

    async def fake_build(prompt_type, user_id, **kwargs):
        return "Be helpful."

    async def fake_assemble(**kwargs):
        return {"sources": []}

    async def fake_detect(self, user_id, message, subjects=None):
        assert user_id == "student-A"
        return {"status": "found", "subject": {"id": DBMS_ID, "name": "Database Management Systems"}}

    async def fake_course(self, user_id, subject_ref, **kwargs):
        return {
            "subject": {"id": DBMS_ID, "name": "Database Management Systems"},
            "resolution": {"status": "found"},
            "assignments": [],
            "documents": [{"id": "d1", "name": "dbms-notes.pdf", "pages": 3, "status": "indexed"}],
            "upcoming_dates": ["2026-10-05"],
            "topic_signals": [],
            "truncated": False,
        }

    async def fake_gather(self, user_id, budget="briefing"):
        return {"profile": None, "subjects": [],
                "assignments": {"items": [], "deadlines": []}}

    monkeypatch.setattr(svc.prompt_manager, "build", fake_build)
    monkeypatch.setattr(svc.context_engine, "assemble_context", fake_assemble)
    monkeypatch.setattr(
        "app.services.workspace_context.WorkspaceContext.gather", fake_gather)
    monkeypatch.setattr(
        "app.services.academic_context.AcademicContextService.detect_course_mention", fake_detect)
    monkeypatch.setattr(
        "app.services.academic_context.AcademicContextService.get_course_context", fake_course)

    messages = await svc._format_messages(
        history=[], user_id="student-A", current_message="I have a DBMS test tomorrow?")
    system_text = messages[0]["content"]
    assert "[COURSE]" in system_text
    assert "Database Management Systems" in system_text
    assert "dbms-notes.pdf" in system_text


@pytest.mark.asyncio
async def test_format_messages_generic_message_injects_nothing(monkeypatch):
    from app.services import ai_service as ai_mod

    svc = ai_mod.AIService(access_token="tok")

    async def fake_build(prompt_type, user_id, **kwargs):
        return "Be helpful."

    async def fake_assemble(**kwargs):
        return {"sources": []}

    async def fake_detect(self, user_id, message, subjects=None):
        return {"status": "missing"}

    async def boom_course(self, *a, **k):
        raise AssertionError("course context must not load for generic chat")

    async def fake_gather(self, user_id, budget="briefing"):
        return {"profile": None, "subjects": [],
                "assignments": {"items": [], "deadlines": []}}

    monkeypatch.setattr(svc.prompt_manager, "build", fake_build)
    monkeypatch.setattr(svc.context_engine, "assemble_context", fake_assemble)
    monkeypatch.setattr(
        "app.services.workspace_context.WorkspaceContext.gather", fake_gather)
    monkeypatch.setattr(
        "app.services.academic_context.AcademicContextService.detect_course_mention", fake_detect)
    monkeypatch.setattr(
        "app.services.academic_context.AcademicContextService.get_course_context", boom_course)

    messages = await svc._format_messages(
        history=[], user_id="student-A", current_message="How do I reverse a string in C?")
    assert "[COURSE]" not in messages[0]["content"]


@pytest.mark.asyncio
async def test_detect_course_mention_full_name(monkeypatch):
    svc = _svc(monkeypatch)
    r = await svc.detect_course_mention("u1", "Help me revise Database Management Systems.")
    assert r["status"] == "found" and r["subject"]["id"] == DBMS_ID


@pytest.mark.asyncio
async def test_detect_course_mention_pending_dbms(monkeypatch):
    svc = _svc(monkeypatch, subjects=[SUBJECTS[0]])
    r = await svc.detect_course_mention("u1", "What is pending for DBMS?")
    assert r["status"] == "found" and r["subject"]["id"] == DBMS_ID


@pytest.mark.asyncio
async def test_detect_course_mention_unknown_course_injects_nothing(monkeypatch):
    # No Chemistry subject exists: missing, never a fabricated context.
    svc = _svc(monkeypatch)
    r = await svc.detect_course_mention("u1", "My chemistry exam is coming.")
    assert r["status"] == "missing"


@pytest.mark.asyncio
async def test_detect_uses_provided_subjects_without_repo_call(monkeypatch):
    # Perf lock: when the caller already holds the user-scoped subject
    # list (WorkspaceContext.gather), detection must not re-query.
    svc = _svc(monkeypatch)

    async def boom_subjects(user_id):
        raise AssertionError("must reuse provided subjects")

    monkeypatch.setattr(svc.subject_repo, "list_subjects", boom_subjects)
    r = await svc.detect_course_mention(
        "u1", "Help me revise Database Management Systems.", subjects=SUBJECTS)
    assert r["status"] == "found" and r["subject"]["id"] == DBMS_ID


@pytest.mark.asyncio
async def test_resolve_course_accepts_provided_subjects(monkeypatch):
    svc = _svc(monkeypatch)

    async def boom_subjects(user_id):
        raise AssertionError("must reuse provided subjects")

    monkeypatch.setattr(svc.subject_repo, "list_subjects", boom_subjects)
    r = await svc.resolve_course("u1", "DBMS", subjects=[SUBJECTS[0]])
    assert r["status"] == "found" and r["subject"]["id"] == DBMS_ID


@pytest.mark.asyncio
async def test_course_context_missing_docs_and_assignments_safe(monkeypatch):
    svc = _svc(monkeypatch, assignments=[], docs=[], chunks=[])
    ctx = await svc.get_course_context("u1", "Physics")
    assert ctx["subject"]["id"] == "s-phy"
    assert ctx["assignments"] == [] and ctx["documents"] == []
    assert ctx["upcoming_dates"] == [] and ctx["topic_signals"] == []
    block = AcademicContextService.format_course_context_block(ctx)
    assert "Course: Physics" in block
    assert "Assignments:" not in block and "Documents:" not in block
    assert "Upcoming:" not in block and "Topics:" not in block
    assert "No linked assignments" in block
    assert block.startswith("[COURSE]") and block.endswith("[/COURSE]")


def test_format_course_block_caps_oversized_input():
    ctx = {
        "subject": {"id": "s-x", "name": "X" * 200},
        "assignments": [
            {"title": f"worksheet number {i} with a very long title " * 5,
             "due_date": "2026-10-05", "priority": "high"}
            for i in range(30)
        ],
        "documents": [
            {"name": f"notes-{i}.pdf " * 20, "pages": 99} for i in range(10)
        ],
        "upcoming_dates": ["2026-10-05"] * 10,
        "topic_signals": [f"topic {i}" for i in range(60)],
    }
    block = AcademicContextService.format_course_context_block(ctx)
    assert len(block) <= 1200


@pytest.mark.asyncio
async def test_format_messages_combines_workspace_and_course_sources(monkeypatch):
    # Workspace behavior preserved: non-workspace engine sources still
    # flow, workspace dumps stay skipped, course block appended once.
    from app.services import ai_service as ai_mod

    svc = ai_mod.AIService(access_token="tok")

    async def fake_build(prompt_type, user_id, **kwargs):
        return "Be helpful."

    async def fake_assemble(**kwargs):
        return {"sources": [
            {"type": "workspace", "content": "whole profile dump"},
            {"type": "document", "content": "normalization excerpt"},
        ]}

    async def fake_gather(self, user_id, budget="briefing"):
        return {"profile": None, "subjects": [],
                "assignments": {"items": [], "deadlines": []}}

    async def fake_detect(self, user_id, message, subjects=None):
        return {"status": "found", "subject": {"id": DBMS_ID, "name": "Database Management Systems"}}

    async def fake_course(self, user_id, subject_ref, **kwargs):
        return {
            "subject": {"id": DBMS_ID, "name": "Database Management Systems"},
            "resolution": {"status": "found"},
            "assignments": [{"title": "DBMS Revision", "due_date": "2026-10-02",
                             "priority": "high", "status": "pending"}],
            "documents": [],
            "upcoming_dates": ["2026-10-02"],
            "topic_signals": [],
            "truncated": False,
        }

    monkeypatch.setattr(svc.prompt_manager, "build", fake_build)
    monkeypatch.setattr(svc.context_engine, "assemble_context", fake_assemble)
    monkeypatch.setattr(
        "app.services.workspace_context.WorkspaceContext.gather", fake_gather)
    monkeypatch.setattr(
        "app.services.academic_context.AcademicContextService.detect_course_mention", fake_detect)
    monkeypatch.setattr(
        "app.services.academic_context.AcademicContextService.get_course_context", fake_course)

    messages = await svc._format_messages(
        history=[], user_id="student-A", current_message="What is pending for DBMS?")
    system_text = messages[0]["content"]
    assert "[DOCUMENT]\nnormalization excerpt" in system_text
    assert "whole profile dump" not in system_text
    assert "[COURSE]" in system_text
    assert system_text.count("[COURSE]") == 1
    assert "DBMS Revision" in system_text


# ── Loop 9: strict context contract ──────────────────────────

def _loop9_fixture():
    subjects = [
        {"id": DBMS_ID, "user_id": "student-9", "name": "Database Management Systems"},
        {"id": "22222222-2222-3333-4444-555555555555", "user_id": "student-9", "name": "DBMS Lab"},
        {"id": "33333333-3333-3333-4444-555555555555", "user_id": "student-9", "name": "Mathematics"},
    ]
    assignments = [
        {"id": "a-r9", "user_id": "student-9", "title": "DBMS Revision",
         "status": "pending", "priority": "high", "due_date": "2026-10-02T21:00:00Z",
         "subject_id": DBMS_ID},
        {"id": "a-l9", "user_id": "student-9", "title": "DBMS Lab Record",
         "status": "pending", "priority": "medium", "due_date": "2026-10-09T21:00:00Z",
         "subject_id": "22222222-2222-3333-4444-555555555555"},
        {"id": "a-m9", "user_id": "student-9", "title": "Mathematics Practice",
         "status": "pending", "priority": "medium", "due_date": "2026-10-04T21:00:00Z",
         "subject_id": "33333333-3333-3333-4444-555555555555"},
    ]
    docs = [
        {"id": "d-r9", "user_id": "student-9", "original_name": "dbms-notes.pdf",
         "page_count": 3, "status": "indexed", "subject_id": DBMS_ID},
        {"id": "d-l9", "user_id": "student-9", "original_name": "dbms-lab.pdf",
         "page_count": 2, "status": "indexed", "subject_id": "22222222-2222-3333-4444-555555555555"},
        {"id": "d-m9", "user_id": "student-9", "original_name": "maths-notes.pdf",
         "page_count": 5, "status": "indexed", "subject_id": "33333333-3333-3333-4444-555555555555"},
    ]
    return subjects, assignments, docs


def _fmt_setup(monkeypatch):
    """AIService with real course routing over faked repositories.

    Subject list flows through the production path (WorkspaceContext.gather
    shape); assignments/documents/chunks hit class-level repo fakes.
    """
    from app.services import ai_service as ai_mod

    subjects, assignments, docs = _loop9_fixture()
    svc = ai_mod.AIService(access_token="tok")

    async def fake_build(prompt_type, user_id, **kwargs):
        return "Be helpful."

    async def fake_assemble(**kwargs):
        return {"sources": []}

    async def fake_gather(self, user_id, budget="briefing"):
        assert user_id == "student-9"
        return {"profile": None, "subjects": subjects,
                "assignments": {"items": [], "deadlines": []}}

    async def fake_assignments(user_id, *args, **kwargs):
        rows = list(assignments)
        filters = kwargs.get("filters", {}) or {}
        sid = filters.get("subject_id")
        if sid:
            rows = [r for r in rows if r.get("subject_id") == sid]
        return rows, len(rows)

    async def fake_docs(user_id, *args, **kwargs):
        rows = list(docs)
        sid = kwargs.get("subject_id")
        if sid:
            rows = [r for r in rows if r.get("subject_id") == sid]
        return rows[:kwargs.get("page_size", 20)], len(rows)

    async def fake_chunks(document_id, user_id):
        return []

    monkeypatch.setattr(svc.prompt_manager, "build", fake_build)
    monkeypatch.setattr(svc.context_engine, "assemble_context", fake_assemble)
    monkeypatch.setattr(
        "app.services.workspace_context.WorkspaceContext.gather", fake_gather)
    monkeypatch.setattr(
        "app.repositories.assignment_repository.AssignmentRepository.list_assignments",
        staticmethod(fake_assignments))
    monkeypatch.setattr(
        "app.repositories.document_repository.DocumentRepository.list_documents",
        staticmethod(fake_docs))
    monkeypatch.setattr(
        "app.repositories.document_repository.DocumentRepository.get_chunks",
        staticmethod(fake_chunks))
    return svc


async def _system_text(svc, message):
    messages = await svc._format_messages(
        history=[], user_id="student-9", current_message=message)
    return messages[0]["content"]


@pytest.mark.asyncio
async def test_course_block_sections_ordered_and_clean(monkeypatch):
    svc = _svc(monkeypatch)
    ctx = await svc.get_course_context("u1", "Database Management Systems")
    first = AcademicContextService.format_course_context_block(ctx)
    second = AcademicContextService.format_course_context_block(ctx)
    assert first == second  # deterministic
    assert first.startswith("[COURSE]\nCourse: Database Management Systems\n")
    assert first.endswith("\n[/COURSE]")
    order = ["Course:", "Upcoming:", "Assignments:", "Documents:", "Topics:", "Grounding:"]
    positions = [first.index(h) for h in order]
    assert positions == sorted(positions)
    assert "2026-10-05" in first  # dates from persisted data
    assert "DBMS normalization worksheet" in first
    assert "dbms-notes.pdf" in first
    assert "First Normal Form" in first
    # no leakage vectors: ids, user scope, other subjects
    assert DBMS_ID not in first and "user_id" not in first
    assert "u1" not in first
    assert "Physics" not in first and "Data Structures" not in first
    assert len(first) <= 1200


@pytest.mark.asyncio
async def test_course_block_empty_stays_honest(monkeypatch):
    svc = _svc(monkeypatch, assignments=[], docs=[], chunks=[])
    ctx = await svc.get_course_context("u1", "Physics")
    block = AcademicContextService.format_course_context_block(ctx)
    assert block.startswith("[COURSE]\nCourse: Physics\n")
    assert "Assignments:" not in block and "Documents:" not in block
    assert "Upcoming:" not in block and "Topics:" not in block
    assert "No linked assignments" in block
    assert "Grounding:" in block
    assert block.endswith("\n[/COURSE]")


def test_course_block_dedupes_entries():
    ctx = {
        "subject": {"id": "s-x", "name": "Mathematics"},
        "assignments": [
            {"title": "Mathematics Practice", "due_date": "2026-10-04", "priority": "medium"},
            {"title": "Mathematics Practice", "due_date": "2026-10-04", "priority": "medium"},
            {"title": "Other Work", "due_date": None, "priority": "low"},
        ],
        "documents": [
            {"id": "d1", "name": "maths-notes.pdf", "pages": 5},
            {"id": "d1", "name": "maths-notes.pdf", "pages": 5},
        ],
        "upcoming_dates": ["2026-10-04"],
        "topic_signals": [],
    }
    block = AcademicContextService.format_course_context_block(ctx)
    assert block.count("Mathematics Practice") == 1
    assert block.count("maths-notes.pdf") == 1
    assert block.endswith("\n[/COURSE]")


def test_course_block_truncation_keeps_marker_deterministic():
    ctx = {
        "subject": {"id": "s-x", "name": "Y" * 100},
        "assignments": [
            {"title": f"task number {i} " * 10, "due_date": "2026-10-05", "priority": "high"}
            for i in range(30)
        ],
        "documents": [{"id": f"d{i}", "name": f"notes-{i}.pdf " * 10, "pages": 9} for i in range(10)],
        "upcoming_dates": ["2026-10-05"] * 10,
        "topic_signals": [f"topic {i}" for i in range(60)],
    }
    first = AcademicContextService.format_course_context_block(ctx)
    second = AcademicContextService.format_course_context_block(ctx)
    assert first == second
    assert len(first) <= 1200
    assert first.endswith("\n[/COURSE]")
    assert first.startswith("[COURSE]\nCourse: ")


@pytest.mark.asyncio
async def test_format_messages_ambiguous_asks_for_course_names(monkeypatch):
    from app.services import ai_service as ai_mod

    svc = ai_mod.AIService(access_token="tok")

    async def fake_build(prompt_type, user_id, **kwargs):
        return "Be helpful."

    async def fake_assemble(**kwargs):
        return {"sources": []}

    async def fake_gather(self, user_id, budget="briefing"):
        return {"profile": None, "subjects": [],
                "assignments": {"items": [], "deadlines": []}}

    async def fake_ambiguous(self, user_id, message, subjects=None):
        return {"status": "ambiguous", "candidates": [
            {"id": "s-a", "name": "Database Management Systems"},
            {"id": "s-b", "name": "DBMS Lab"},
        ]}

    async def boom_course(self, *a, **k):
        raise AssertionError("ambiguous must not load any single course context")

    monkeypatch.setattr(svc.prompt_manager, "build", fake_build)
    monkeypatch.setattr(svc.context_engine, "assemble_context", fake_assemble)
    monkeypatch.setattr(
        "app.services.workspace_context.WorkspaceContext.gather", fake_gather)
    monkeypatch.setattr(
        "app.services.academic_context.AcademicContextService.detect_course_mention", fake_ambiguous)
    monkeypatch.setattr(
        "app.services.academic_context.AcademicContextService.get_course_context", boom_course)

    messages = await svc._format_messages(
        history=[], user_id="student-A", current_message="Help me study DBMS.")
    system_text = messages[0]["content"]
    assert "[COURSE]" in system_text
    assert "Database Management Systems" in system_text
    assert "DBMS Lab" in system_text


# ── Loop 9: stale-context isolation + source boundaries ────

@pytest.mark.asyncio
async def test_isolation_course_then_generic_stays_clean(monkeypatch):
    # A. Same service instance, sequential messages: DBMS context must
    # not leak into a later unrelated message.
    svc = _fmt_setup(monkeypatch)
    first = await _system_text(svc, "I need help with Database Management Systems.")
    assert "[COURSE]" in first
    assert "DBMS Revision" in first and "dbms-notes.pdf" in first
    assert "DBMS Lab Record" not in first and "Mathematics Practice" not in first
    second = await _system_text(svc, "How do I learn C pointers?")
    assert "[COURSE]" not in second


@pytest.mark.asyncio
async def test_isolation_course_then_today_stays_generic(monkeypatch):
    # B. Follow-up with no course reference stays generic.
    svc = _fmt_setup(monkeypatch)
    first = await _system_text(svc, "Help me with Database Management Systems.")
    assert "[COURSE]" in first
    second = await _system_text(svc, "What should I do today?")
    assert "[COURSE]" not in second


@pytest.mark.asyncio
async def test_isolation_ambiguous_injects_no_course_data(monkeypatch):
    # C. DBMS + DBMS Lab: clarification only, zero course payload.
    svc = _fmt_setup(monkeypatch)
    text = await _system_text(svc, "What's due for DBMS?")
    assert "[COURSE]" in text
    assert "Database Management Systems" in text and "DBMS Lab" in text
    assert "DBMS Revision" not in text
    assert "DBMS Lab Record" not in text
    assert ".pdf" not in text
    assert "2026-10-02" not in text and "2026-10-09" not in text


@pytest.mark.asyncio
async def test_isolation_mathematics_only(monkeypatch):
    # D. Mathematics resolves alone with zero DBMS exposure.
    svc = _fmt_setup(monkeypatch)
    text = await _system_text(svc, "What's due for Mathematics?")
    assert "[COURSE]" in text
    assert "Mathematics Practice" in text and "maths-notes.pdf" in text
    assert "2026-10-04" in text
    assert "DBMS Revision" not in text and "DBMS Lab Record" not in text
    assert "dbms-notes.pdf" not in text and "dbms-lab.pdf" not in text
    assert "Database Management Systems" not in text


@pytest.mark.asyncio
async def test_isolation_unknown_course_injects_nothing(monkeypatch):
    # E. Chemistry does not exist: no block, no fabrication.
    svc = _fmt_setup(monkeypatch)
    text = await _system_text(svc, "Tell me something about chemistry.")
    assert "[COURSE]" not in text


@pytest.mark.asyncio
async def test_boundary_lab_course_resolves_exactly(monkeypatch):
    # "Help me with DBMS Lab." selects the Lab and only the Lab.
    svc = _fmt_setup(monkeypatch)
    text = await _system_text(svc, "Help me with DBMS Lab.")
    assert "[COURSE]" in text
    assert "DBMS Lab Record" in text and "dbms-lab.pdf" in text
    assert "DBMS Revision" not in text and "dbms-notes.pdf" not in text
    assert "Mathematics Practice" not in text


@pytest.mark.asyncio
async def test_boundary_full_name_normalization_query(monkeypatch):
    # Full canonical name: DBMS course data, no Lab/Math leakage.
    svc = _fmt_setup(monkeypatch)
    text = await _system_text(svc, "Explain normalization from Database Management Systems.")
    assert "[COURSE]" in text
    assert "DBMS Revision" in text and "dbms-notes.pdf" in text
    assert "DBMS Lab Record" not in text and "dbms-lab.pdf" not in text
    assert "Mathematics Practice" not in text and "maths-notes.pdf" not in text
