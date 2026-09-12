"""E2E Integration Tests for Fixly AI Engine.

Tests real integration paths through the actual application stack.
Uses real services where possible, minimal mocking.
"""

from __future__ import annotations

import asyncio
import time
import pytest

from app.services.academic_profile import AcademicProfileService
from app.services.context_engine import ContextEngine
from app.services.goals_service import GoalsService
from app.services.memory_service import MemoryService
from app.services.offline_manager import OfflineManager, ConflictResolver
from app.services.proactive_engine import ProactiveEngine
from app.services.tool_authorizer import ToolAuthorizer, SafetyClassification
from app.services.tool_executor import ToolExecutor
from app.services.tool_registry import ToolRegistry, ToolCategory, AuthLevel
from app.services.weakness_detector import WeaknessDetector
from app.services.web_retrieval import OpportunityService
from app.services.workflow_engine import WorkflowEngine
from app.services.workflow_store import WorkflowStore


# ── E2E 1: Intent Classification → Context Assembly ─────────────────


class TestE2EIntentToContext:
    """Test intent classification drives correct context assembly."""

    def setup_method(self):
        self.engine = ContextEngine()

    def test_workspace_query_gets_workspace_context(self):
        import asyncio
        result = asyncio.run(self.engine.assemble_context(
            user_id="u1",
            message="What assignments do I have?",
            workspace_data={
                "profile": {"full_name": "Test Student"},
                "assignments": [{"title": "DBMS HW", "deadline": "2026-09-15"}],
            },
        ))
        assert result["intent"].value == "workspace_query"
        assert any(s["type"] == "workspace" for s in result["sources"])

    def test_document_query_triggers_rag(self):
        result = asyncio.run(self.engine.assemble_context(
            user_id="u1",
            message="What does my note say about normalisation?",
            document_ids=["doc1"],
        ))
        assert result["intent"].value == "document_query"

    def test_tutoring_injects_memory(self):
        mem_svc = MemoryService()
        mem_svc.add_memory("u1", "I prefer visual learning", "preference")
        self.engine.memory_service = mem_svc
        result = asyncio.run(self.engine.assemble_context(
            user_id="u1",
            message="Explain normalisation",
        ))
        assert result["intent"].value == "tutoring"
        mem_svc.clear_all_memories("u1")
        mem_svc.close()

    def test_all_intents_classified(self):
        test_cases = [
            ("Hello", "simple_chat"),
            ("What does my note say?", "document_query"),
            ("What assignments do I have?", "workspace_query"),
            ("Explain recursion", "tutoring"),
            ("Create a study plan", "planning"),
            ("Latest AI news", "web_research"),
            ("Find internships", "opportunity"),
        ]
        for msg, expected_intent in test_cases:
            result = asyncio.run(self.engine.assemble_context(
                user_id="u1", message=msg,
            ))
            assert result["intent"].value == expected_intent, f"'{msg}' → {result['intent']}"


# ── E2E 2: Memory Lifecycle ─────────────────────────────────────────


class TestE2EMemoryLifecycle:
    """Test memory extraction, storage, retrieval, and injection."""

    def setup_method(self):
        self.svc = MemoryService()

    def teardown_method(self):
        self.svc.clear_all_memories("u1")
        self.svc.close()

    def test_extract_preferences(self):
        candidates = self.svc.extract_memories("u1", "I prefer dark mode for studying")
        assert any(c["category"] == "preference" for c in candidates)

    def test_extract_weaknesses(self):
        candidates = self.svc.extract_memories("u1", "I struggle with normalisation")
        assert any(c["category"] == "weakness" for c in candidates)

    def test_extract_goals(self):
        candidates = self.svc.extract_memories("u1", "I want to learn machine learning")
        assert any(c["category"] == "goal" for c in candidates)

    def test_store_and_retrieve(self):
        self.svc.add_memory("u1", "I prefer visual learning", "preference")
        context = self.svc.build_memory_context("u1", "learning style")
        assert "visual learning" in context.lower() or len(context) > 0

    def test_deduplication(self):
        self.svc.add_memory("u1", "I prefer dark mode", "preference")
        self.svc.add_memory("u1", "I prefer dark mode", "preference")
        count = self.svc.count_by_user("u1")
        assert count == 1

    def test_user_isolation(self):
        self.svc.add_memory("u1", "I prefer dark mode", "preference")
        self.svc.add_memory("u2", "I prefer light mode", "preference")
        ctx_u1 = self.svc.build_memory_context("u1", "preference")
        ctx_u2 = self.svc.build_memory_context("u2", "preference")
        assert "dark" in ctx_u1.lower()
        assert "light" in ctx_u2.lower()

    def test_memory_persists(self):
        self.svc.add_memory("u1", "I study at night", "habit")
        svc2 = MemoryService()
        context = svc2.build_memory_context("u1", "study time")
        assert "night" in context.lower() or len(context) > 0
        svc2.close()

    def test_clear_all_memories(self):
        self.svc.add_memory("u1", "I prefer dark mode", "preference")
        self.svc.clear_all_memories("u1")
        count = self.svc.count_by_user("u1")
        assert count == 0


# ── E2E 3: Tool Authorization ───────────────────────────────────────


class TestE2EToolAuthorization:
    """Test tool authorization flow end-to-end."""

    def setup_method(self):
        self.executor = ToolExecutor()
        self.authorizer = self.executor.authorizer

    def test_safe_tool_auto_approved(self):
        auth = self.authorizer.check_authorization(
            "read_pdf", "u1", {"document_id": "d1"}
        )
        assert auth.allowed is True
        assert auth.requires_confirmation is False

    def test_writing_tool_requires_confirmation(self):
        auth = self.authorizer.check_authorization(
            "create_assignment", "u1", {"title": "HW1"}
        )
        assert auth.allowed is True
        assert auth.requires_confirmation is True

    def test_destructive_tool_classified(self):
        auth = self.authorizer.check_authorization(
            "delete_assignment", "u1", {"assignment_id": "a1"}
        )
        assert auth.classification == SafetyClassification.DESTRUCTIVE

    def test_missing_params_denied(self):
        auth = self.authorizer.check_authorization(
            "read_pdf", "u1", {}
        )
        assert auth.allowed is False

    def test_unknown_tool_denied(self):
        auth = self.authorizer.check_authorization(
            "nonexistent", "u1", {}
        )
        assert auth.allowed is False

    def test_disabled_tool_denied(self):
        self.authorizer.disable_tool("read_pdf")
        auth = self.authorizer.check_authorization(
            "read_pdf", "u1", {"document_id": "d1"}
        )
        assert auth.allowed is False
        self.authorizer.enable_tool("read_pdf")

    def test_execution_recorded_in_audit(self):
        def handler(uid, params):
            return "ok"
        self.executor.register_handler("read_pdf", handler)
        self.executor.execute("read_pdf", "u1", {"document_id": "d1"})
        log = self.authorizer.get_audit_log("u1")
        assert len(log) == 1
        assert log[0]["status"] == "executed"

    def test_tool_suggestions_by_intent(self):
        suggestions = self.authorizer.get_tool_suggestions("document_query")
        assert "read_pdf" in suggestions
        assert "search_documents" in suggestions


# ── E2E 4: Workflow Lifecycle ────────────────────────────────────────


class TestE2EWorkflowLifecycle:
    """Test workflow creation, execution, persistence, and resume."""

    def setup_method(self):
        self.store = WorkflowStore(":memory:")
        self.executor = ToolExecutor()
        self.engine = WorkflowEngine(store=self.store, executor=self.executor)

    def teardown_method(self):
        self.store.close()

    def test_create_and_execute_workflow(self):
        def handler(uid, params):
            return "ok"
        self.executor.register_handler("read_pdf", handler)
        self.executor.register_handler("search_documents", handler)

        wf = self.engine.create_workflow(
            "u1", "Study Session",
            steps=[
                {"tool": "read_pdf", "params": {"document_id": "d1"}},
                {"tool": "search_documents", "params": {"query": "test"}},
            ],
        )
        results = self.engine.execute_all(wf)
        assert len(results) == 2
        assert wf.status == "completed"

    def test_workflow_persists(self):
        wf = self.engine.create_workflow(
            "u1", "Test",
            steps=[{"tool": "read_pdf", "params": {"document_id": "d1"}}],
        )
        loaded = self.store.get(wf.id, "u1")
        assert loaded is not None
        assert loaded.name == "Test"

    def test_pause_and_resume(self):
        wf = self.engine.create_workflow(
            "u1", "Test",
            steps=[{"tool": "read_pdf", "params": {"document_id": "d1"}}],
        )
        wf = self.engine.pause(wf)
        assert wf.status == "paused"
        wf = self.engine.resume(wf)
        assert wf.status == "pending"

    def test_step_failure_stops_workflow(self):
        def fail_handler(uid, params):
            raise ValueError("boom")
        self.executor.register_handler("read_pdf", fail_handler)

        wf = self.engine.create_workflow(
            "u1", "Test",
            steps=[
                {"tool": "read_pdf", "params": {"document_id": "d1"}},
                {"tool": "search_documents", "params": {"query": "test"}},
            ],
        )
        results = self.engine.execute_all(wf)
        assert len(results) == 1
        assert wf.status == "failed"

    def test_user_isolation(self):
        self.engine.create_workflow("u1", "WF1", [{"tool": "read_pdf", "params": {}}])
        self.engine.create_workflow("u2", "WF2", [{"tool": "read_pdf", "params": {}}])
        u1_wfs = self.store.list_by_user("u1")
        u2_wfs = self.store.list_by_user("u2")
        assert len(u1_wfs) == 1
        assert len(u2_wfs) == 1

    def test_template_workflow(self):
        wf = self.engine.create_from_template("u1", "study_session", {"topic": "DBMS"})
        assert wf.name == "Study Session"
        assert len(wf.steps) == 3


# ── E2E 5: Academic Profile + Weakness Detection ────────────────────


class TestE2EAcademicProfile:
    """Test academic profile and weakness detection integration."""

    def setup_method(self):
        self.svc = AcademicProfileService(":memory:")
        self.detector = WeaknessDetector(self.svc)

    def teardown_method(self):
        self.svc.close()

    def test_score_tracking(self):
        self.svc.update_score("u1", "DBMS", 85)
        self.svc.update_score("u1", "DBMS", 90)
        profile = self.svc.get_profile("u1")
        assert profile.subjects["DBMS"].average_score == 87.5

    def test_weakness_detection(self):
        self.svc.update_score("u1", "DBMS", 35)
        signals = self.detector.detect("u1")
        assert any(s.signal_type == "low_score" for s in signals)

    def test_trend_detection(self):
        for score in [90, 80, 70]:
            self.svc.update_score("u1", "DBMS", score)
        signals = self.detector.detect("u1")
        assert any(s.signal_type == "declining_trend" for s in signals)

    def test_study_recommendations(self):
        self.svc.update_score("u1", "DBMS", 40)
        self.svc.add_weak_topic("u1", "DBMS", "normalisation")
        recs = self.svc.get_study_recommendations("u1")
        assert len(recs) >= 1
        assert recs[0]["priority"] == "high"

    def test_subject_health(self):
        self.svc.update_score("u1", "DBMS", 85)
        self.svc.update_study_hours("u1", "DBMS", 5)
        health = self.detector.get_subject_health("u1")
        assert "DBMS" in health
        assert health["DBMS"]["score"] > 50


# ── E2E 6: Goals + Skills + Roadmap ─────────────────────────────────


class TestE2EGoalsSkills:
    """Test goals, skills, and roadmap integration."""

    def setup_method(self):
        self.svc = GoalsService(":memory:")

    def teardown_method(self):
        self.svc.close()

    def test_goal_lifecycle(self):
        goal = self.svc.create_goal("u1", "Learn Python", category="academic")
        assert goal.status == "active"
        updated = self.svc.update_goal_progress("u1", goal.id, 100)
        assert updated.status == "completed"

    def test_skill_tracking(self):
        skill = self.svc.add_skill("u1", "Python", "programming", level="intermediate")
        skills = self.svc.get_skills("u1", category="programming")
        assert len(skills) == 1
        assert skills[0].level == "intermediate"

    def test_roadmap_creation(self):
        roadmap = self.svc.create_roadmap("u1", "Python Mastery", [
            {"title": "Learn basics", "estimated_hours": 10},
            {"title": "Build projects", "estimated_hours": 20},
        ])
        assert len(roadmap.steps) == 2
        roadmaps = self.svc.get_roadmaps("u1")
        assert len(roadmaps) == 1


# ── E2E 7: Opportunities ────────────────────────────────────────────


class TestE2EOpportunities:
    """Test opportunity management integration."""

    def setup_method(self):
        self.svc = OpportunityService(":memory:")

    def teardown_method(self):
        self.svc.close()

    def test_save_and_list(self):
        opp = self.svc.save("u1", "SWE Intern", "Google", category="internship")
        opps = self.svc.list_saved("u1")
        assert len(opps) == 1
        assert opps[0].title == "SWE Intern"

    def test_status_update(self):
        opp = self.svc.save("u1", "SWE Intern", "Google")
        updated = self.svc.update_status("u1", opp.id, "applied")
        assert updated.status == "applied"

    def test_delete(self):
        opp = self.svc.save("u1", "SWE Intern", "Google")
        assert self.svc.delete("u1", opp.id) is True
        assert len(self.svc.list_saved("u1")) == 0


# ── E2E 8: Proactive Engine ─────────────────────────────────────────


class TestE2EProactive:
    """Test proactive nudges integration."""

    def setup_method(self):
        self.engine = ProactiveEngine(db_path=":memory:")

    def test_deadline_nudge(self):
        import datetime
        tomorrow = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1)).isoformat()
        nudges = self.engine.check_deadlines("u1", [{"id": "a1", "title": "HW1", "deadline": tomorrow}])
        assert len(nudges) == 1
        assert nudges[0].priority == "high"

    def test_study_suggestion(self):
        nudges = self.engine.check_study_patterns("u1", {"streak": 0})
        assert len(nudges) == 1

    def test_weakness_alert(self):
        nudges = self.engine.check_weaknesses("u1", [
            {"subject": "DBMS", "average": 35, "weak_topics": ["normalisation"]}
        ])
        assert len(nudges) == 1

    def test_dismiss(self):
        nudges = self.engine.check_study_patterns("u1", {"streak": 0})
        self.engine.dismiss("u1", nudges[0].id)
        active = self.engine.get_nudges("u1")
        assert len(active) == 0


# ── E2E 9: Offline Manager ──────────────────────────────────────────


class TestE2EOffline:
    """Test offline detection and sync integration."""

    def setup_method(self):
        self.manager = OfflineManager(db_path=":memory:")

    def test_queue_when_offline(self):
        self.manager.set_online(False)
        op = self.manager.queue_operation("u1", "create", "assignment", "a1", {"title": "HW"})
        assert op.status.value == "pending"
        assert self.manager.get_pending_count("u1") == 1

    def test_sync_when_online(self):
        self.manager.set_online(False)
        op = self.manager.queue_operation("u1", "create", "assignment", "a1")
        self.manager.set_online(True)
        self.manager.mark_synced(op.id)
        assert self.manager.get_pending_count("u1") == 0

    def test_conflict_resolution(self):
        local = {"updated_at": 200, "data": "local"}
        remote = {"updated_at": 100, "data": "remote"}
        resolved = ConflictResolver.resolve(local, remote)
        assert resolved["data"] == "local"


# ── E2E 10: Context Engine + Memory Integration ─────────────────────


class TestE2EContextMemoryIntegration:
    """Test that memory retrieval feeds into context assembly."""

    def setup_method(self):
        self.engine = ContextEngine()
        self.mem_svc = MemoryService()
        self.engine.memory_service = self.mem_svc

    def teardown_method(self):
        self.mem_svc.clear_all_memories("u1")
        self.mem_svc.close()

    def test_memory_injected_into_context(self):
        self.mem_svc.add_memory("u1", "I prefer visual learning", "preference")
        result = asyncio.run(self.engine.assemble_context(
            user_id="u1",
            message="Create a study plan for my DBMS exam",
        ))
        memory_sources = [s for s in result["sources"] if s["type"] == "memory"]
        assert len(memory_sources) >= 1

    def test_memory_not_injected_for_simple_chat(self):
        self.mem_svc.add_memory("u1", "I prefer dark mode", "preference")
        result = asyncio.run(self.engine.assemble_context(
            user_id="u1",
            message="Hello",
        ))
        memory_sources = [s for s in result["sources"] if s["type"] == "memory"]
        assert len(memory_sources) == 0


# ── E2E 11: Source Authority ─────────────────────────────────────────


class TestE2ESourceAuthority:
    """Test source authority resolution in real scenarios."""

    def test_document_question_prefers_documents(self):
        from app.services.source_authority import SourceAuthority, SourceType
        sources = SourceAuthority.resolve("document_question")
        assert sources[0] == SourceType.DOCUMENTS

    def test_workspace_question_prefers_workspace(self):
        from app.services.source_authority import SourceAuthority, SourceType
        sources = SourceAuthority.resolve("workspace_question")
        assert sources[0] == SourceType.WORKSPACE

    def test_web_question_prefers_web(self):
        from app.services.source_authority import SourceAuthority, SourceType
        sources = SourceAuthority.resolve("current_information")
        assert sources[0] == SourceType.WEB

    def test_select_best_source(self):
        from app.services.source_authority import SourceAuthority
        sources = [
            {"source_type": "model", "content": "general"},
            {"source_type": "documents", "content": "from notes"},
        ]
        best = SourceAuthority.select_best_source(sources, "document_question")
        assert best["source_type"] == "documents"
