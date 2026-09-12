"""Tests for Phase 5: Agent Workflows + Persistent State."""

from __future__ import annotations

import pytest

from app.services.tool_authorizer import SafetyClassification, ToolAuthorizer
from app.services.tool_executor import ToolExecutor
from app.services.tool_registry import ToolRegistry
from app.services.workflow_engine import WorkflowEngine, WORKFLOW_TEMPLATES
from app.services.workflow_store import Workflow, WorkflowStep, WorkflowStore


# ── Workflow Store Tests ─────────────────────────────────────────────


class TestWorkflowStore:
    """Tests for persistent workflow storage."""

    def setup_method(self):
        self.store = WorkflowStore(":memory:")

    def teardown_method(self):
        self.store.close()

    def _make_workflow(self, user_id: str = "u1", name: str = "Test WF") -> Workflow:
        import uuid
        return Workflow(
            id=f"wf_{uuid.uuid4().hex[:12]}",
            user_id=user_id,
            name=name,
            description="test",
            steps=[
                WorkflowStep(id="s1", tool_name="read_pdf", parameters={"document_id": "d1"}),
                WorkflowStep(id="s2", tool_name="search_documents", parameters={"query": "test"}),
            ],
        )

    def test_create_and_get(self):
        wf = self._make_workflow()
        self.store.create(wf)
        got = self.store.get(wf.id, "u1")
        assert got is not None
        assert got.name == "Test WF"
        assert len(got.steps) == 2

    def test_get_nonexistent(self):
        assert self.store.get("nonexistent", "u1") is None

    def test_get_wrong_user(self):
        wf = self._make_workflow(user_id="u1")
        self.store.create(wf)
        assert self.store.get(wf.id, "u2") is None

    def test_list_by_user(self):
        wf1 = self._make_workflow(user_id="u1", name="WF1")
        wf2 = self._make_workflow(user_id="u1", name="WF2")
        wf3 = self._make_workflow(user_id="u2", name="WF3")
        self.store.create(wf1)
        self.store.create(wf2)
        self.store.create(wf3)
        u1_wfs = self.store.list_by_user("u1")
        assert len(u1_wfs) == 2

    def test_list_by_status(self):
        wf = self._make_workflow()
        wf.status = "running"
        self.store.create(wf)
        running = self.store.list_by_user("u1", status="running")
        assert len(running) == 1
        pending = self.store.list_by_user("u1", status="pending")
        assert len(pending) == 0

    def test_update(self):
        wf = self._make_workflow()
        self.store.create(wf)
        wf.steps[0].status = "completed"
        wf.status = "running"
        self.store.update(wf)
        got = self.store.get(wf.id, "u1")
        assert got.steps[0].status == "completed"
        assert got.status == "running"

    def test_delete(self):
        wf = self._make_workflow()
        self.store.create(wf)
        assert self.store.delete(wf.id, "u1") is True
        assert self.store.get(wf.id, "u1") is None

    def test_delete_wrong_user(self):
        wf = self._make_workflow(user_id="u1")
        self.store.create(wf)
        assert self.store.delete(wf.id, "u2") is False
        assert self.store.get(wf.id, "u1") is not None

    def test_steps_roundtrip(self):
        wf = self._make_workflow()
        wf.steps[0].status = "completed"
        wf.steps[0].result = {"content": "test"}
        self.store.create(wf)
        got = self.store.get(wf.id, "u1")
        assert got.steps[0].status == "completed"
        assert got.steps[0].result == {"content": "test"}

    def test_metadata_roundtrip(self):
        wf = self._make_workflow()
        wf.metadata = {"template": "exam_prep", "source": "chat"}
        self.store.create(wf)
        got = self.store.get(wf.id, "u1")
        assert got.metadata["template"] == "exam_prep"


# ── Workflow Engine Tests ────────────────────────────────────────────


class TestWorkflowEngine:
    """Tests for workflow orchestration."""

    def setup_method(self):
        ToolRegistry.reset()
        self.store = WorkflowStore(":memory:")
        self.executor = ToolExecutor()
        self.engine = WorkflowEngine(store=self.store, executor=self.executor)

    def teardown_method(self):
        self.store.close()

    def test_create_workflow(self):
        wf = self.engine.create_workflow(
            user_id="u1",
            name="Test",
            steps=[{"tool": "read_pdf", "params": {"document_id": "d1"}}],
        )
        assert wf.id.startswith("wf_")
        assert len(wf.steps) == 1
        assert wf.status == "pending"

    def test_create_from_template(self):
        wf = self.engine.create_from_template(
            "u1", "study_session", {"topic": "DBMS"}
        )
        assert wf.name == "Study Session"
        assert len(wf.steps) == 3
        assert wf.metadata["template"] == "study_session"

    def test_create_from_invalid_template(self):
        with pytest.raises(ValueError):
            self.engine.create_from_template("u1", "nonexistent")

    def test_execute_next_step(self):
        def handler(uid, params):
            return {"content": "test"}
        self.executor.register_handler("read_pdf", handler)

        wf = self.engine.create_workflow(
            "u1", "Test",
            steps=[
                {"tool": "read_pdf", "params": {"document_id": "d1"}},
                {"tool": "search_documents", "params": {"query": "test"}},
            ],
        )
        result = self.engine.execute_next_step(wf)
        assert result is not None
        assert result.success is True
        assert wf.steps[0].status == "completed"
        assert wf.steps[1].status == "pending"
        assert wf.status == "running"

    def test_execute_all_steps(self):
        def handler(uid, params):
            return "ok"
        self.executor.register_handler("read_pdf", handler)
        self.executor.register_handler("search_documents", handler)

        wf = self.engine.create_workflow(
            "u1", "Test",
            steps=[
                {"tool": "read_pdf", "params": {"document_id": "d1"}},
                {"tool": "search_documents", "params": {"query": "test"}},
            ],
        )
        results = self.engine.execute_all(wf)
        assert len(results) == 2
        assert wf.status == "completed"

    def test_execute_step_failure(self):
        def fail_handler(uid, params):
            raise ValueError("boom")
        self.executor.register_handler("read_pdf", fail_handler)

        wf = self.engine.create_workflow(
            "u1", "Test",
            steps=[{"tool": "read_pdf", "params": {"document_id": "d1"}}],
        )
        result = self.engine.execute_next_step(wf)
        assert result.success is False
        assert wf.steps[0].status == "failed"
        assert wf.status == "failed"

    def test_pause_and_resume(self):
        wf = self.engine.create_workflow(
            "u1", "Test",
            steps=[{"tool": "read_pdf", "params": {"document_id": "d1"}}],
        )
        wf = self.engine.pause(wf)
        assert wf.status == "paused"
        wf = self.engine.resume(wf)
        assert wf.status == "pending"

    def test_cancel(self):
        wf = self.engine.create_workflow(
            "u1", "Test",
            steps=[
                {"tool": "read_pdf", "params": {"document_id": "d1"}},
                {"tool": "search_documents", "params": {"query": "test"}},
            ],
        )
        wf = self.engine.cancel(wf)
        assert wf.status == "failed"
        assert wf.error == "Cancelled by user"
        assert all(s.status == "skipped" for s in wf.steps)

    def test_get_status(self):
        wf = self.engine.create_workflow(
            "u1", "Test",
            steps=[
                {"tool": "read_pdf", "params": {"document_id": "d1"}},
                {"tool": "search_documents", "params": {"query": "test"}},
            ],
        )
        status = self.engine.get_status(wf)
        assert status["progress"] == "0/2"
        assert status["total_steps"] == 2

    def test_list_templates(self):
        templates = self.engine.list_templates()
        assert len(templates) >= 4
        names = [t["name"] for t in templates]
        assert "study_session" in names

    def test_workflow_persists(self):
        wf = self.engine.create_workflow(
            "u1", "Test",
            steps=[{"tool": "read_pdf", "params": {"document_id": "d1"}}],
        )
        got = self.store.get(wf.id, "u1")
        assert got is not None
        assert got.name == "Test"

    def test_user_isolation(self):
        wf1 = self.engine.create_workflow("u1", "WF1", [{"tool": "read_pdf", "params": {}}])
        wf2 = self.engine.create_workflow("u2", "WF2", [{"tool": "read_pdf", "params": {}}])
        u1_wfs = self.store.list_by_user("u1")
        u2_wfs = self.store.list_by_user("u2")
        assert len(u1_wfs) == 1
        assert len(u2_wfs) == 1
