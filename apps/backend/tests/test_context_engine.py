"""Tests for Phase 3: Intent Classifier + Context Engine + Source Authority."""

from __future__ import annotations

import pytest

from app.services.intent_classifier import Intent, IntentClassifier
from app.services.source_authority import SourceAuthority, SourceType


# ── Intent Classifier Tests ──────────────────────────────────────────


class TestIntentClassifier:
    """Tests for deterministic intent classification."""

    def setup_method(self):
        self.classifier = IntentClassifier()

    def test_simple_chat(self):
        result = self.classifier.classify("Hello, how are you?")
        assert result["intent"] == Intent.SIMPLE_CHAT

    def test_document_query(self):
        result = self.classifier.classify("What does my note say about normalisation?")
        assert result["intent"] == Intent.DOCUMENT_QUERY
        assert result["confidence"] >= 0.8

    def test_document_query_uploaded(self):
        result = self.classifier.classify("According to my uploaded PDF, what is hashing?")
        assert result["intent"] == Intent.DOCUMENT_QUERY

    def test_assignment_solve(self):
        result = self.classifier.classify("Help me solve my DBMS assignment question 3")
        assert result["intent"] == Intent.ASSIGNMENT_SOLVE

    def test_assignment_code(self):
        result = self.classifier.classify("Write code for BST insertion in C")
        assert result["intent"] == Intent.ASSIGNMENT_SOLVE

    def test_tutoring(self):
        result = self.classifier.classify("Explain what normalisation means")
        assert result["intent"] == Intent.TUTORING

    def test_tutoring_concept(self):
        result = self.classifier.classify("What is a binary search tree?")
        assert result["intent"] == Intent.TUTORING

    def test_planning(self):
        result = self.classifier.classify("Create a study plan for my DBMS exam")
        assert result["intent"] == Intent.PLANNING

    def test_workspace_query(self):
        result = self.classifier.classify("What assignments are due this week?")
        assert result["intent"] == Intent.WORKSPACE_QUERY

    def test_workspace_deadlines(self):
        result = self.classifier.classify("Show me my upcoming deadlines")
        assert result["intent"] == Intent.WORKSPACE_QUERY

    def test_web_research(self):
        result = self.classifier.classify("What is the latest version of Next.js?")
        assert result["intent"] == Intent.WEB_RESEARCH

    def test_opportunity(self):
        result = self.classifier.classify("Find internships related to data science")
        assert result["intent"] == Intent.OPPORTUNITY

    def test_opportunity_save(self):
        result = self.classifier.classify("Save this internship listing")
        assert result["intent"] == Intent.OPPORTUNITY

    def test_autonomous_workflow(self):
        result = self.classifier.classify(
            "Read my assignment, find relevant notes, then create a study plan"
        )
        assert result["intent"] == Intent.AUTONOMOUS_WORKFLOW

    def test_fallback_with_documents(self):
        result = self.classifier.classify("Tell me something", has_documents=True)
        assert result["intent"] == Intent.TUTORING

    def test_fallback_without_documents(self):
        result = self.classifier.classify("Tell me something random")
        assert result["intent"] == Intent.SIMPLE_CHAT

    def test_deterministic(self):
        text = "Explain normalisation in databases"
        r1 = self.classifier.classify(text)
        r2 = self.classifier.classify(text)
        assert r1["intent"] == r2["intent"]

    def test_all_intents_covered(self):
        test_cases = [
            ("Hello", Intent.SIMPLE_CHAT),
            ("What does my note say?", Intent.DOCUMENT_QUERY),
            ("Solve this problem", Intent.ASSIGNMENT_SOLVE),
            ("Explain recursion", Intent.TUTORING),
            ("Create a study plan", Intent.PLANNING),
            ("What assignments do I have?", Intent.WORKSPACE_QUERY),
            ("Latest AI news", Intent.WEB_RESEARCH),
            ("Find internships", Intent.OPPORTUNITY),
            ("Read my assignment then find notes then create plan", Intent.AUTONOMOUS_WORKFLOW),
        ]
        for text, expected in test_cases:
            result = self.classifier.classify(text)
            assert result["intent"] == expected, f"'{text}' → {result['intent']}, expected {expected}"


# ── Source Authority Tests ───────────────────────────────────────────


class TestSourceAuthority:
    """Tests for source authority resolution."""

    def test_document_question_primary(self):
        sources = SourceAuthority.resolve("document_question")
        assert sources[0] == SourceType.DOCUMENTS

    def test_workspace_question_primary(self):
        sources = SourceAuthority.resolve("workspace_question")
        assert sources[0] == SourceType.WORKSPACE

    def test_current_information_primary(self):
        sources = SourceAuthority.resolve("current_information")
        assert sources[0] == SourceType.WEB

    def test_concept_explanation_primary(self):
        sources = SourceAuthority.resolve("concept_explanation")
        assert SourceType.DOCUMENTS in sources

    def test_opportunity_search_primary(self):
        sources = SourceAuthority.resolve("opportunity_search")
        assert sources[0] == SourceType.MEMORY

    def test_study_guidance_primary(self):
        sources = SourceAuthority.resolve("study_guidance")
        assert sources[0] == SourceType.WORKSPACE

    def test_general_fallback(self):
        sources = SourceAuthority.resolve("nonexistent_type")
        assert sources[0] == SourceType.MODEL

    def test_classify_question_type_document(self):
        qt = SourceAuthority.classify_question_type("document_query", "What does my note say?")
        assert qt == "document_question"

    def test_classify_question_type_workspace(self):
        qt = SourceAuthority.classify_question_type("workspace_query", "What assignments do I have?")
        assert qt == "workspace_question"

    def test_classify_question_type_web(self):
        qt = SourceAuthority.classify_question_type("web_research", "Latest Next.js version")
        assert qt == "current_information"

    def test_select_best_source(self):
        sources = [
            {"source_type": "model", "content": "general answer"},
            {"source_type": "documents", "content": "from your notes"},
        ]
        best = SourceAuthority.select_best_source(sources, "document_question")
        assert best["source_type"] == "documents"

    def test_select_best_workspace(self):
        sources = [
            {"source_type": "model", "content": "general"},
            {"source_type": "workspace", "content": "your assignments"},
        ]
        best = SourceAuthority.select_best_source(sources, "workspace_question")
        assert best["source_type"] == "workspace"


# ── Context Engine Tests ─────────────────────────────────────────────


class TestContextEngine:
    """Tests for context engine assembly."""

    def test_import_context_engine(self):
        from app.services.context_engine import ContextEngine, TOTAL_BUDGET, BUDGET_ALLOCATION
        assert TOTAL_BUDGET == 4000
        assert sum(BUDGET_ALLOCATION.values()) == TOTAL_BUDGET

    def test_intent_classified_in_context(self):
        from app.services.context_engine import ContextEngine
        engine = ContextEngine()
        import asyncio
        result = asyncio.run(engine.assemble_context(
            user_id="u1",
            message="What does my note say about normalisation?",
        ))
        assert result["intent"] == Intent.DOCUMENT_QUERY
        assert "question_type" in result
        assert "source_authority" in result

    def test_workspace_context_included(self):
        from app.services.context_engine import ContextEngine
        engine = ContextEngine()
        workspace = {
            "profile": {"full_name": "Test Student"},
            "subjects": [{"name": "DBMS"}, {"name": "OS"}],
            "assignments": [{"title": "HW1", "deadline": "2026-09-15"}],
        }
        import asyncio
        result = asyncio.run(engine.assemble_context(
            user_id="u1",
            message="What assignments do I have?",
            workspace_data=workspace,
        ))
        assert any(s["type"] == "workspace" for s in result["sources"])

    def test_memory_context_included(self):
        from app.services.context_engine import ContextEngine
        engine = ContextEngine()
        # Add a memory first
        engine.memory_service.add_memory("u1", "I prefer dark mode", "preference")
        import asyncio
        result = asyncio.run(engine.assemble_context(
            user_id="u1",
            message="What should I study today?",
        ))
        assert any(s["type"] == "memory" for s in result["sources"])
        engine.memory_service.clear_all_memories("u1")

    def test_budget_not_exceeded(self):
        from app.services.context_engine import ContextEngine, TOTAL_BUDGET
        engine = ContextEngine()
        import asyncio
        result = asyncio.run(engine.assemble_context(
            user_id="u1",
            message="Hello",
        ))
        assert result["budget_used"] <= TOTAL_BUDGET

    def test_citations_empty_without_docs(self):
        from app.services.context_engine import ContextEngine
        engine = ContextEngine()
        import asyncio
        result = asyncio.run(engine.assemble_context(
            user_id="u1",
            message="Hello",
        ))
        assert result["citations"] == []
