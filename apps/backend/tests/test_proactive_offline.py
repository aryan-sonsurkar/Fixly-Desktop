"""Tests for Phase 9 + 10: Proactive Engine + Offline Manager."""

from __future__ import annotations

import pytest

from app.services.offline_manager import (
    ConflictResolver,
    OfflineManager,
    PendingOperation,
    SyncStatus,
)
from app.services.proactive_engine import Nudge, ProactiveEngine


# ── Proactive Engine Tests ───────────────────────────────────────────


class TestProactiveEngine:
    def setup_method(self):
        self.engine = ProactiveEngine(db_path=":memory:")

    def test_deadline_reminder_urgent(self):
        import datetime
        tomorrow = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1)).isoformat()
        nudges = self.engine.check_deadlines("u1", [{"id": "a1", "title": "HW1", "deadline": tomorrow}])
        assert len(nudges) == 1
        assert nudges[0].priority == "high"
        assert nudges[0].type == "deadline_reminder"

    def test_deadline_reminder_soon(self):
        import datetime
        in_3_days = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=3)).isoformat()
        nudges = self.engine.check_deadlines("u1", [{"id": "a1", "title": "HW1", "deadline": in_3_days}])
        assert len(nudges) == 1
        assert nudges[0].priority == "medium"

    def test_no_deadline_reminder(self):
        import datetime
        far_future = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=30)).isoformat()
        nudges = self.engine.check_deadlines("u1", [{"id": "a1", "title": "HW1", "deadline": far_future}])
        assert len(nudges) == 0

    def test_study_suggestion_no_streak(self):
        nudges = self.engine.check_study_patterns("u1", {"streak": 0})
        assert len(nudges) == 1
        assert nudges[0].type == "study_suggestion"

    def test_study_suggestion_long_streak(self):
        nudges = self.engine.check_study_patterns("u1", {"streak": 10})
        assert len(nudges) == 1
        assert "streak" in nudges[0].title.lower()

    def test_weakness_alert(self):
        nudges = self.engine.check_weaknesses("u1", [
            {"subject": "DBMS", "average": 35, "weak_topics": ["normalisation"]}
        ])
        assert len(nudges) == 1
        assert nudges[0].priority == "high"

    def test_get_nudges_sorted(self):
        import datetime
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        self.engine.check_deadlines("u1", [{"id": "a1", "title": "HW", "deadline": now_iso}])
        self.engine.check_study_patterns("u1", {"streak": 0})
        nudges = self.engine.get_nudges("u1")
        assert len(nudges) >= 1

    def test_dismiss_nudge(self):
        nudges = self.engine.check_study_patterns("u1", {"streak": 0})
        assert self.engine.dismiss("u1", nudges[0].id) is True
        active = self.engine.get_nudges("u1")
        assert len(active) == 0

    def test_user_isolation(self):
        self.engine.check_study_patterns("u1", {"streak": 0})
        self.engine.check_study_patterns("u2", {"streak": 0})
        assert len(self.engine.get_nudges("u1")) == 1
        assert len(self.engine.get_nudges("u2")) == 1

    def test_nudge_to_dict(self):
        nudge = Nudge(id="n1", user_id="u1", type="test", title="T", message="M")
        d = nudge.to_dict()
        assert d["title"] == "T"
        assert d["dismissed"] is False


# ── Offline Manager Tests ────────────────────────────────────────────


class TestOfflineManager:
    def setup_method(self):
        self.manager = OfflineManager(db_path=":memory:")

    def test_initially_online(self):
        assert self.manager.is_online is True

    def test_set_offline(self):
        self.manager.set_online(False)
        assert self.manager.is_online is False

    def test_queue_operation(self):
        op = self.manager.queue_operation("u1", "create", "assignment", "a1", {"title": "HW"})
        assert op.id.startswith("sync_")
        assert op.status == SyncStatus.PENDING

    def test_get_pending(self):
        self.manager.queue_operation("u1", "create", "assignment", "a1")
        self.manager.queue_operation("u1", "update", "assignment", "a2")
        self.manager.queue_operation("u2", "create", "goal", "g1")
        pending = self.manager.get_pending("u1")
        assert len(pending) == 2

    def test_mark_synced(self):
        op = self.manager.queue_operation("u1", "create", "assignment", "a1")
        assert self.manager.mark_synced(op.id) is True
        pending = self.manager.get_pending("u1")
        assert len(pending) == 0

    def test_mark_failed(self):
        op = self.manager.queue_operation("u1", "create", "assignment", "a1")
        assert self.manager.mark_failed(op.id, "network error") is True
        pending = self.manager.get_pending("u1")
        assert pending[0].status == SyncStatus.FAILED

    def test_clear_synced(self):
        op = self.manager.queue_operation("u1", "create", "assignment", "a1")
        self.manager.mark_synced(op.id)
        cleared = self.manager.clear_synced("u1")
        assert cleared == 1

    def test_pending_count(self):
        self.manager.queue_operation("u1", "create", "assignment", "a1")
        self.manager.queue_operation("u1", "create", "assignment", "a2")
        assert self.manager.get_pending_count("u1") == 2

    def test_total_pending(self):
        self.manager.queue_operation("u1", "create", "assignment", "a1")
        self.manager.queue_operation("u2", "create", "goal", "g1")
        assert self.manager.get_total_pending_count() == 2

    def test_operation_to_dict(self):
        op = self.manager.queue_operation("u1", "create", "assignment", "a1", {"title": "HW"})
        d = op.to_dict()
        assert d["operation"] == "create"
        assert d["entity_type"] == "assignment"


class TestConflictResolver:
    def test_last_write_wins_local(self):
        local = {"updated_at": 200}
        remote = {"updated_at": 100}
        result = ConflictResolver.resolve(local, remote)
        assert result is local

    def test_last_write_wins_remote(self):
        local = {"updated_at": 100}
        remote = {"updated_at": 200}
        result = ConflictResolver.resolve(local, remote)
        assert result is remote

    def test_local_wins(self):
        local = {"data": "local"}
        remote = {"data": "remote"}
        result = ConflictResolver.resolve(local, remote, strategy="local_wins")
        assert result is local

    def test_remote_wins(self):
        local = {"data": "local"}
        remote = {"data": "remote"}
        result = ConflictResolver.resolve(local, remote, strategy="remote_wins")
        assert result is remote

    def test_detect_conflict(self):
        assert ConflictResolver.detect_conflict(2, 3) is True
        assert ConflictResolver.detect_conflict(1, 1) is False
        assert ConflictResolver.detect_conflict(0, 1) is False
