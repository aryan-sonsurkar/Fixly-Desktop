"""P0.2 academic tool contracts (Loop 5/6).

- strict input schemas accept/reject
- unknown tool rejected
- read-only tools execute through the authorized executor path
- handlers scope queries to the authenticated caller identity
- knowledge-gaps stub is honest
- write tools still require confirmation (boundary preserved)
"""

import pytest
from pydantic import ValidationError as PydanticValidationError

from app.schemas.academic_tools import (
    CourseContextInput,
    DeadlinesInput,
    KnowledgeGapsInput,
    StudentContextInput,
)
from app.services.tool_executor import ToolExecutor
from app.services.tool_handlers import ToolHandlerContext
from app.services.tool_registration import register_all_handlers


@pytest.fixture
def executor():
    exec_ = ToolExecutor()
    register_all_handlers(exec_)
    return exec_


@pytest.fixture
def ctx():
    return ToolHandlerContext(access_token="test-token")


def test_input_schemas_accept_valid():
    assert CourseContextInput(subject_ref="DBMS").subject_ref == "DBMS"
    assert DeadlinesInput().days == 14
    assert DeadlinesInput(days=7, limit=5).limit == 5
    StudentContextInput()
    KnowledgeGapsInput(subject_ref="Physics")


def test_input_schemas_reject_malformed():
    with pytest.raises(PydanticValidationError):
        CourseContextInput(subject_ref="")
    with pytest.raises(PydanticValidationError):
        CourseContextInput()
    with pytest.raises(PydanticValidationError):
        DeadlinesInput(days=0)
    with pytest.raises(PydanticValidationError):
        DeadlinesInput(limit=500)
    with pytest.raises(PydanticValidationError):
        CourseContextInput(subject_ref="x", unknown_key=1)


@pytest.mark.asyncio
async def test_unknown_tool_rejected(executor):
    res = await executor.execute_async("fly_to_the_moon", "u1", {})
    assert res.success is False
    # Unknown tools are denied at the authorization layer.
    assert "tool_not_found" in (res.error or "")


@pytest.mark.asyncio
async def test_read_tools_execute_authorized_path(executor, ctx, monkeypatch):
    from app.services import academic_context as ac_mod
    from app.services import tool_handlers as th  # noqa: F401 (keeps import surface stable)

    seen = {}

    async def fake_student_context(self, user_id, **kw):
        seen["user"] = user_id
        assert self.access_token == "caller-token"
        return {
            "subjects": [{"id": "s1", "name": "DBMS"}],
            "assignment_counts": {"pending_or_active": 0},
            "upcoming": [],
            "documents": [],
            "deadlines": [],
            "truncated": False,
        }

    async def fake_course_context(self, user_id, subject_ref, **kw):
        seen["course_user"] = user_id
        return {
            "subject": {"id": "s1", "name": "DBMS"},
            "resolution": {"status": "found"},
            "assignments": [],
            "documents": [],
            "upcoming_dates": [],
            "topic_signals": [],
            "truncated": False,
        }

    async def fake_deadlines(self, user_id, **kw):
        seen["deadline_args"] = (user_id, kw.get("days"), kw.get("limit"))
        return {"deadlines": [], "truncated": False}

    monkeypatch.setattr(ac_mod.AcademicContextService, "get_student_context", fake_student_context)
    monkeypatch.setattr(ac_mod.AcademicContextService, "get_course_context", fake_course_context)
    monkeypatch.setattr(ac_mod.AcademicContextService, "get_upcoming_deadlines", fake_deadlines)

    r1 = await executor.execute_async("get_student_context", "student-A", {}, access_token="caller-token")
    assert r1.success is True
    assert seen["user"] == "student-A"
    assert r1.result["subjects"] == [{"id": "s1", "name": "DBMS"}]

    r2 = await executor.execute_async("get_course_context", "student-A", {"subject_ref": "DBMS"}, access_token="caller-token")
    assert r2.success is True
    assert seen["course_user"] == "student-A"
    assert r2.result["subject"]["name"] == "DBMS"

    r3 = await executor.execute_async("get_upcoming_deadlines", "student-A", {"days": 7}, access_token="caller-token")
    assert r3.success is True
    assert seen["deadline_args"] == ("student-A", 7, 20)


@pytest.mark.asyncio
async def test_course_tool_rejects_bad_input_without_service_call(executor, ctx, monkeypatch):
    from app.services import academic_context as ac_mod

    called = []
    real = ac_mod.AcademicContextService.get_course_context

    async def spy(self, *a, **k):
        called.append(True)
        return await real(self, *a, **k)

    monkeypatch.setattr(ac_mod.AcademicContextService, "get_course_context", spy)
    res = await executor.execute_async("get_course_context", "u1", {})
    assert res.success is False
    assert called == []


@pytest.mark.asyncio
async def test_knowledge_gaps_stub_is_honest(executor, ctx):
    res = await executor.execute_async("get_knowledge_gaps", "u1", {"subject_ref": "DBMS"})
    assert res.success is True
    assert res.result["available"] is False
    assert "not implemented" in res.result["reason"]
    assert res.result["subject_ref"] == "DBMS"


@pytest.mark.asyncio
async def test_write_tool_still_requires_confirmation(executor, ctx, monkeypatch):
    from app.services import tool_handlers as th

    async def boom(*a, **k):
        raise AssertionError("handler must not run without confirmation")

    monkeypatch.setattr(th, "handle_create_assignment", boom)
    # rebind executor to pick up patched handler
    executor._handlers["create_assignment"] = th.handle_create_assignment
    res = await executor.execute_async(
        "create_assignment", "u1", {"title": "Sneaky task"})
    assert res.success is False
    assert res.error == "confirmation_required"


@pytest.mark.asyncio
async def test_executor_supports_sync_and_async_handlers(executor):
    from app.services.tool_registry import (
        AuthLevel,
        ToolCategory,
        ToolDefinition,
        ToolRegistry,
    )

    def sync_handler(user_id, params, ctx=None):
        assert ctx is not None and ctx.access_token == "tok-9"
        return {"ok": True, "user": user_id}

    async def async_handler(user_id, params, ctx=None):
        assert ctx is not None and ctx.access_token == "tok-9"
        return {"ok": True, "user": user_id}

    reg = ToolRegistry.get_instance()
    reg.register(ToolDefinition(
        name="t_sync_probe", description="probe", category=ToolCategory.READING,
        auth_level=AuthLevel.AUTO))
    reg.register(ToolDefinition(
        name="t_async_probe", description="probe", category=ToolCategory.READING,
        auth_level=AuthLevel.AUTO))
    executor._handlers["t_sync_probe"] = sync_handler
    executor._handlers["t_async_probe"] = async_handler
    try:
        r1 = await executor.execute_async("t_sync_probe", "u9", {}, access_token="tok-9")
        r2 = await executor.execute_async("t_async_probe", "u9", {}, access_token="tok-9")
        assert r1.success is True and r1.result == {"ok": True, "user": "u9"}
        assert r2.success is True and r2.result == {"ok": True, "user": "u9"}
    finally:
        del reg._tools["t_sync_probe"]
        del reg._tools["t_async_probe"]
        del executor._handlers["t_sync_probe"]
        del executor._handlers["t_async_probe"]
