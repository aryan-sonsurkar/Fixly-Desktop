"""Comprehensive tests for Phase 2: Memory System + Summarization."""

from __future__ import annotations

import os
import tempfile
import time

import pytest

from app.services.memory_service import (
    DECAY_FLOOR,
    DECAY_INTERVAL_DAYS,
    DECAY_RATE,
    INITIAL_CONFIDENCE,
    VALID_CATEGORIES,
    MemoryService,
)
from app.services.memory_store import MemoryStore
from app.services.summarization_service import SummarizationService


def _tmp_service():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    svc = MemoryService(db_path=path)
    return svc, path


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


# ── MemoryStore Tests ────────────────────────────────────────────────


class TestMemoryStore:
    """Tests for the SQLite memory store."""

    def test_insert_and_get(self):
        svc, path = _tmp_service()
        try:
            mem = svc.add_memory("u1", "I prefer dark mode", "preference", source="explicit")
            assert mem["id"].startswith("mem_")
            assert mem["category"] == "preference"
            assert mem["confidence"] == 0.8
            got = svc.get_memory("u1", mem["id"])
            assert got is not None
            assert got["content"] == "I prefer dark mode"
        finally:
            svc.close()
            os.unlink(path)

    def test_list_by_category(self):
        svc, path = _tmp_service()
        try:
            svc.add_memory("u1", "I like Python", "preference")
            svc.add_memory("u1", "I always study at night", "habit")
            svc.add_memory("u1", "I struggle with pointers", "weakness")
            prefs = svc.list_memories("u1", category="preference")
            assert len(prefs) == 1
            assert prefs[0]["category"] == "preference"
        finally:
            svc.close()
            os.unlink(path)

    def test_update_memory(self):
        svc, path = _tmp_service()
        try:
            mem = svc.add_memory("u1", "I like cats", "preference")
            svc.update_memory("u1", mem["id"], {"content": "I like dogs"})
            got = svc.get_memory("u1", mem["id"])
            assert got["content"] == "I like dogs"
        finally:
            svc.close()
            os.unlink(path)

    def test_delete_memory(self):
        svc, path = _tmp_service()
        try:
            mem = svc.add_memory("u1", "test fact", "fact")
            assert svc.delete_memory("u1", mem["id"])
            assert svc.get_memory("u1", mem["id"]) is None
        finally:
            svc.close()
            os.unlink(path)

    def test_archive_and_unarchive(self):
        svc, path = _tmp_service()
        try:
            mem = svc.add_memory("u1", "test", "fact")
            assert svc.archive_memory("u1", mem["id"])
            archived = svc.list_memories("u1", include_archived=False)
            assert len(archived) == 0
            all_mems = svc.list_memories("u1", include_archived=True)
            assert len(all_mems) == 1
            assert svc.unarchive_memory("u1", mem["id"])
            active = svc.list_memories("u1", include_archived=False)
            assert len(active) == 1
        finally:
            svc.close()
            os.unlink(path)

    def test_clear_all_memories(self):
        svc, path = _tmp_service()
        try:
            svc.add_memory("u1", "I study computer science at university", "fact")
            svc.add_memory("u1", "I prefer using dark mode IDE", "preference")
            svc.add_memory("u2", "other user fact about something completely different", "fact")
            deleted = svc.clear_all_memories("u1")
            assert deleted == 2
            assert svc.count_by_user("u1") == 0
            assert svc.count_by_user("u2") == 1
        finally:
            svc.close()
            os.unlink(path)

    def test_delete_by_document(self):
        svc, path = _tmp_service()
        try:
            svc.add_memory("u1", "from doc", "document", source="document", source_document_id="doc1")
            svc.add_memory("u1", "independent", "fact")
            deleted = svc.delete_document_memories("u1", "doc1")
            assert deleted == 1
            remaining = svc.list_memories("u1")
            assert len(remaining) == 1
            assert remaining[0]["content"] == "independent"
        finally:
            svc.close()
            os.unlink(path)


# ── MemoryService Tests ──────────────────────────────────────────────


class TestMemoryService:
    """Tests for memory extraction, confidence, reinforcement, contradiction."""

    def test_add_memory_default_confidence(self):
        svc, path = _tmp_service()
        try:
            mem = svc.add_memory("u1", "I prefer vim", "preference", source="explicit")
            assert mem["confidence"] == 0.8
        finally:
            svc.close()
            os.unlink(path)

    def test_add_memory_inferred_confidence(self):
        svc, path = _tmp_service()
        try:
            mem = svc.add_memory("u1", "I study CS", "fact", source="inferred")
            assert mem["confidence"] == 0.4
        finally:
            svc.close()
            os.unlink(path)

    def test_add_memory_behavioral_confidence(self):
        svc, path = _tmp_service()
        try:
            mem = svc.add_memory("u1", "I always study at night", "habit", source="behavioral")
            assert mem["confidence"] == 0.3
        finally:
            svc.close()
            os.unlink(path)

    def test_invalid_category_raises(self):
        svc, path = _tmp_service()
        try:
            with pytest.raises(ValueError, match="Invalid category"):
                svc.add_memory("u1", "test", "invalid_cat")
        finally:
            svc.close()
            os.unlink(path)

    def test_reinforcement_increases_confidence(self):
        svc, path = _tmp_service()
        try:
            mem = svc.add_memory("u1", "I prefer Python", "preference")
            initial_conf = mem["confidence"]
            # Add same memory again → should reinforce
            mem2 = svc.add_memory("u1", "I prefer Python", "preference")
            assert mem2["confidence"] > initial_conf
            assert mem2["confidence"] == min(1.0, initial_conf + 0.1)
        finally:
            svc.close()
            os.unlink(path)

    def test_reinforcement_cap_at_1(self):
        svc, path = _tmp_service()
        try:
            mem = svc.add_memory("u1", "test", "fact", confidence=0.95)
            svc.add_memory("u1", "test", "fact")
            got = svc.get_memory("u1", mem["id"])
            assert got["confidence"] <= 1.0
        finally:
            svc.close()
            os.unlink(path)

    def test_contradiction_reduces_confidence(self):
        svc, path = _tmp_service()
        try:
            svc.add_memory("u1", "I like Python", "preference")
            # Contradicting statement
            svc.add_memory("u1", "I don't like Python", "preference")
            prefs = svc.list_memories("u1", category="preference")
            # One should have reduced confidence
            confidences = [p["confidence"] for p in prefs]
            assert any(c < 0.8 for c in confidences)
        finally:
            svc.close()
            os.unlink(path)

    def test_extraction_prefers(self):
        svc, path = _tmp_service()
        try:
            memories = svc.extract_memories("u1", "I prefer using VS Code for coding")
            assert len(memories) > 0
            assert any(m["category"] == "preference" for m in memories)
        finally:
            svc.close()
            os.unlink(path)

    def test_extraction_habits(self):
        svc, path = _tmp_service()
        try:
            memories = svc.extract_memories("u1", "I always study at night")
            assert len(memories) > 0
            assert any(m["category"] == "habit" for m in memories)
        finally:
            svc.close()
            os.unlink(path)

    def test_extraction_weaknesses(self):
        svc, path = _tmp_service()
        try:
            memories = svc.extract_memories("u1", "I struggle with pointers in C")
            assert len(memories) > 0
            assert any(m["category"] == "weakness" for m in memories)
        finally:
            svc.close()
            os.unlink(path)

    def test_extraction_strengths(self):
        svc, path = _tmp_service()
        try:
            memories = svc.extract_memories("u1", "I am good at data structures")
            assert len(memories) > 0
            assert any(m["category"] == "strength" for m in memories)
        finally:
            svc.close()
            os.unlink(path)

    def test_extraction_goals(self):
        svc, path = _tmp_service()
        try:
            memories = svc.extract_memories("u1", "I want to learn machine learning")
            assert len(memories) > 0
            assert any(m["category"] == "goal" for m in memories)
        finally:
            svc.close()
            os.unlink(path)

    def test_extraction_facts(self):
        svc, path = _tmp_service()
        try:
            memories = svc.extract_memories("u1", "I study computer science")
            assert len(memories) > 0
            assert any(m["category"] == "fact" for m in memories)
        finally:
            svc.close()
            os.unlink(path)


# ── Decay Tests ──────────────────────────────────────────────────────


class TestDecay:
    """Tests for time-based decay on preferences and habits."""

    def test_decay_only_affects_preference_and_habit(self):
        svc, path = _tmp_service()
        try:
            svc.add_memory("u1", "I like cats", "preference")
            svc.add_memory("u1", "I study CS", "fact")
            svc.add_memory("u1", "I always study at night", "habit")
            archived = svc.apply_decay("u1")
            # With fresh memories, no decay should happen
            assert archived == 0
            all_mems = svc.list_memories("u1")
            assert len(all_mems) == 3
        finally:
            svc.close()
            os.unlink(path)

    def test_decay_floor(self):
        svc, path = _tmp_service()
        try:
            mem = svc.add_memory("u1", "old preference", "preference", confidence=0.25)
            # Manually set old timestamp
            old_time = "2020-01-01T00:00:00Z"
            svc.store.update_memory(mem["id"], "u1", {
                "last_reinforced_at": old_time,
                "updated_at": old_time,
            })
            archived = svc.apply_decay("u1")
            got = svc.get_memory("u1", mem["id"])
            # Should not go below floor
            assert got["confidence"] >= DECAY_FLOOR
        finally:
            svc.close()
            os.unlink(path)


# ── Deduplication Tests ──────────────────────────────────────────────


class TestDeduplication:
    """Tests for memory deduplication via embedding similarity."""

    def test_dedup_same_content(self):
        svc, path = _tmp_service()
        try:
            mem1 = svc.add_memory("u1", "I prefer dark mode", "preference")
            mem2 = svc.add_memory("u1", "I prefer dark mode", "preference")
            # Should reinforce, not create new
            all_mems = svc.list_memories("u1", category="preference")
            assert len(all_mems) == 1
            assert mem2["id"] == mem1["id"]
        finally:
            svc.close()
            os.unlink(path)

    def test_different_content_creates_new(self):
        svc, path = _tmp_service()
        try:
            svc.add_memory("u1", "I prefer dark mode", "preference")
            svc.add_memory("u1", "I prefer light mode", "preference")
            all_mems = svc.list_memories("u1", category="preference")
            assert len(all_mems) == 2
        finally:
            svc.close()
            os.unlink(path)


# ── Summarization Tests ──────────────────────────────────────────────


class TestSummarization:
    """Tests for conversation summarization."""

    def test_no_summarize_when_below_threshold(self):
        svc, path = _tmp_service()
        try:
            summarizer = SummarizationService(svc.store)
            messages = [{"role": "user", "content": f"msg {i}"} for i in range(5)]
            import asyncio
            result = asyncio.run(summarizer.maybe_summarize("u1", "conv1", messages))
            assert result["summarized"] is False
            assert result["messages_retained"] == 5
        finally:
            svc.close()
            os.unlink(path)

    def test_summarize_when_above_threshold(self):
        svc, path = _tmp_service()
        try:
            summarizer = SummarizationService(svc.store)
            messages = [{"role": "user", "content": f"message about topic {i}"} for i in range(25)]
            import asyncio
            result = asyncio.run(summarizer.maybe_summarize("u1", "conv1", messages))
            assert result["summarized"] is True
            assert result["messages_summarized"] > 0
            assert result["messages_retained"] > 0
        finally:
            svc.close()
            os.unlink(path)

    def test_summary_persisted(self):
        svc, path = _tmp_service()
        try:
            summarizer = SummarizationService(svc.store)
            messages = [{"role": "user", "content": f"msg {i}"} for i in range(25)]
            import asyncio
            asyncio.run(summarizer.maybe_summarize("u1", "conv1", messages))
            summaries = svc.store.get_summaries("u1", "conv1")
            assert len(summaries) == 1
            assert summaries[0]["conversation_id"] == "conv1"
        finally:
            svc.close()
            os.unlink(path)

    def test_summary_context(self):
        svc, path = _tmp_service()
        try:
            summarizer = SummarizationService(svc.store)
            messages = [{"role": "user", "content": f"msg {i}"} for i in range(25)]
            import asyncio
            asyncio.run(summarizer.maybe_summarize("u1", "conv1", messages))
            ctx = summarizer.build_summary_context("u1", "conv1")
            assert len(ctx) > 0
        finally:
            svc.close()
            os.unlink(path)


# ── User Isolation Tests ─────────────────────────────────────────────


class TestUserIsolation:
    """Verify strict user scoping for all memory operations."""

    def test_users_cannot_see_each_other_memories(self):
        svc, path = _tmp_service()
        try:
            svc.add_memory("u1", "user1 fact", "fact")
            svc.add_memory("u2", "user2 fact", "fact")
            u1_mems = svc.list_memories("u1")
            u2_mems = svc.list_memories("u2")
            assert len(u1_mems) == 1
            assert u1_mems[0]["content"] == "user1 fact"
            assert len(u2_mems) == 1
            assert u2_mems[0]["content"] == "user2 fact"
        finally:
            svc.close()
            os.unlink(path)

    def test_cannot_get_other_users_memory(self):
        svc, path = _tmp_service()
        try:
            mem = svc.add_memory("u1", "private", "fact")
            assert svc.get_memory("u2", mem["id"]) is None
        finally:
            svc.close()
            os.unlink(path)

    def test_cannot_delete_other_users_memory(self):
        svc, path = _tmp_service()
        try:
            mem = svc.add_memory("u1", "private", "fact")
            assert not svc.delete_memory("u2", mem["id"])
            assert svc.get_memory("u1", mem["id"]) is not None
        finally:
            svc.close()
            os.unlink(path)


# ── Provenance Tests ─────────────────────────────────────────────────


class TestProvenance:
    """Tests for source tracking and document memory lifecycle."""

    def test_document_source_recorded(self):
        svc, path = _tmp_service()
        try:
            mem = svc.add_memory(
                "u1", "DBMS covers normalization", "document",
                source="document", source_document_id="doc_123",
            )
            assert mem["source"] == "document"
            assert mem["source_document_id"] == "doc_123"
        finally:
            svc.close()
            os.unlink(path)

    def test_conversation_source_recorded(self):
        svc, path = _tmp_service()
        try:
            mem = svc.add_memory(
                "u1", "I like Python", "preference",
                source="conversation", source_conversation_id="conv_456",
            )
            assert mem["source"] == "conversation"
            assert mem["source_conversation_id"] == "conv_456"
        finally:
            svc.close()
            os.unlink(path)

    def test_document_deletion_cascades(self):
        svc, path = _tmp_service()
        try:
            svc.add_memory("u1", "from doc", "document", source="document", source_document_id="doc1")
            svc.add_memory("u1", "independent", "fact")
            deleted = svc.delete_document_memories("u1", "doc1")
            assert deleted == 1
            remaining = svc.list_memories("u1")
            assert len(remaining) == 1
            assert remaining[0]["content"] == "independent"
        finally:
            svc.close()
            os.unlink(path)


# ── Retrieval Tests ──────────────────────────────────────────────────


class TestRetrieval:
    """Tests for semantic memory retrieval."""

    def test_retrieve_returns_relevant_memories(self):
        svc, path = _tmp_service()
        try:
            svc.add_memory("u1", "I struggle with pointers in C", "weakness")
            svc.add_memory("u1", "I am good at Python", "strength")
            svc.add_memory("u1", "I prefer VS Code", "preference")
            results = svc.retrieve_relevant("u1", "C programming difficulties")
            assert len(results) > 0
            # Weakness about pointers should be most relevant
            assert results[0]["category"] == "weakness"
        finally:
            svc.close()
            os.unlink(path)

    def test_retrieve_respects_min_confidence(self):
        svc, path = _tmp_service()
        try:
            svc.add_memory("u1", "test", "fact", confidence=0.1)
            results = svc.retrieve_relevant("u1", "test", min_confidence=0.5)
            assert len(results) == 0
        finally:
            svc.close()
            os.unlink(path)

    def test_retrieve_respects_top_k(self):
        svc, path = _tmp_service()
        try:
            for i in range(10):
                svc.add_memory("u1", f"fact number {i}", "fact")
            results = svc.retrieve_relevant("u1", "facts", top_k=3)
            assert len(results) <= 3
        finally:
            svc.close()
            os.unlink(path)


# ── Reset Tests ──────────────────────────────────────────────────────


class TestReset:
    """Tests for AI memory reset."""

    def test_clear_all_removes_only_ai_data(self):
        svc, path = _tmp_service()
        try:
            svc.add_memory("u1", "I study computer science at university", "fact")
            svc.add_memory("u1", "I prefer using dark mode IDE", "preference")
            deleted = svc.clear_all_memories("u1")
            assert deleted == 2
            assert svc.count_by_user("u1") == 0
        finally:
            svc.close()
            os.unlink(path)

    def test_reset_is_user_scoped(self):
        svc, path = _tmp_service()
        try:
            svc.add_memory("u1", "my fact", "fact")
            svc.add_memory("u2", "other fact", "fact")
            svc.clear_all_memories("u1")
            assert svc.count_by_user("u1") == 0
            assert svc.count_by_user("u2") == 1
        finally:
            svc.close()
            os.unlink(path)


# ── Context Injection Tests ──────────────────────────────────────────


class TestContextInjection:
    """Tests for memory context building."""

    def test_build_memory_context_empty(self):
        svc, path = _tmp_service()
        try:
            ctx = svc.build_memory_context("u1", "anything")
            assert ctx == ""
        finally:
            svc.close()
            os.unlink(path)

    def test_build_memory_context_with_memories(self):
        svc, path = _tmp_service()
        try:
            svc.add_memory("u1", "I prefer dark mode", "preference")
            svc.add_memory("u1", "I struggle with pointers", "weakness")
            ctx = svc.build_memory_context("u1", "coding preferences")
            assert "[Student Memory]" in ctx
            assert "dark mode" in ctx or "pointers" in ctx
        finally:
            svc.close()
            os.unlink(path)

    def test_build_memory_context_respects_token_budget(self):
        svc, path = _tmp_service()
        try:
            for i in range(20):
                svc.add_memory("u1", f"memory item {i} with some content", "fact")
            ctx = svc.build_memory_context("u1", "memories", max_tokens=50)
            assert len(ctx.split()) <= 100  # rough check
        finally:
            svc.close()
            os.unlink(path)


# ── Category Validation Tests ────────────────────────────────────────


class TestCategoryValidation:
    """Tests for valid memory categories."""

    def test_all_categories_accepted(self):
        svc, path = _tmp_service()
        try:
            for cat in VALID_CATEGORIES:
                mem = svc.add_memory("u1", f"test {cat}", cat)
                assert mem["category"] == cat
        finally:
            svc.close()
            os.unlink(path)

    def test_invalid_category_rejected(self):
        svc, path = _tmp_service()
        try:
            with pytest.raises(ValueError):
                svc.add_memory("u1", "test", "nonexistent")
        finally:
            svc.close()
            os.unlink(path)
