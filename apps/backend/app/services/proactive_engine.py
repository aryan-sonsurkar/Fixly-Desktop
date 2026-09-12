"""Proactive Engine for Fixly AI.

Provides contextual nudges, reminders, and proactive suggestions
based on student's goals, deadlines, and study patterns.
"""

from __future__ import annotations

import os
import sqlite3
import threading
import time
from dataclasses import dataclass, field
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)

_DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
_NUDGE_DB_PATH = os.path.join(_DB_DIR, "fixly_nudges.db")
_thread_local = threading.local()


def _get_conn(db_path: str | None = None) -> sqlite3.Connection:
    effective_path = db_path or _NUDGE_DB_PATH
    conn_attr = f"conn_{hash(effective_path)}"
    if not hasattr(_thread_local, conn_attr) or getattr(_thread_local, conn_attr) is None:
        if effective_path != ":memory:":
            os.makedirs(os.path.dirname(effective_path), exist_ok=True)
        conn = sqlite3.connect(effective_path, timeout=10)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
        conn.row_factory = sqlite3.Row
        setattr(_thread_local, conn_attr, conn)
    return getattr(_thread_local, conn_attr)


def _ensure_tables(db_path: str | None = None) -> None:
    conn = _get_conn(db_path)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS proactive_nudges (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            type TEXT NOT NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            priority TEXT NOT NULL DEFAULT 'medium',
            action_suggestion TEXT,
            created_at REAL NOT NULL,
            dismissed INTEGER NOT NULL DEFAULT 0
        );
        CREATE INDEX IF NOT EXISTS idx_nudges_user ON proactive_nudges(user_id);
        CREATE INDEX IF NOT EXISTS idx_nudges_user_dismissed ON proactive_nudges(user_id, dismissed);
    """)
    conn.commit()


@dataclass
class Nudge:
    id: str
    user_id: str
    type: str  # deadline_reminder | study_suggestion | weakness_alert | goal_progress
    title: str
    message: str
    priority: str = "medium"  # low | medium | high
    action_suggestion: str | None = None
    created_at: float = field(default_factory=time.time)
    dismissed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "user_id": self.user_id,
            "type": self.type, "title": self.title,
            "message": self.message, "priority": self.priority,
            "action_suggestion": self.action_suggestion,
            "created_at": self.created_at, "dismissed": self.dismissed,
        }


class ProactiveEngine:
    """Generates proactive nudges based on student context."""

    def __init__(self, db_path: str | None = None) -> None:
        self._db_path = db_path
        self._nudges: dict[str, list[Nudge]] = {}
        _ensure_tables(db_path)
        if db_path == ":memory:":
            conn = _get_conn(db_path)
            conn.execute("DELETE FROM proactive_nudges")
            conn.commit()
        self._load_from_db()

    def _load_from_db(self) -> None:
        conn = _get_conn(self._db_path)
        rows = conn.execute(
            "SELECT * FROM proactive_nudges ORDER BY created_at DESC LIMIT 500"
        ).fetchall()
        for row in rows:
            nudge = Nudge(
                id=row["id"],
                user_id=row["user_id"],
                type=row["type"],
                title=row["title"],
                message=row["message"],
                priority=row["priority"],
                action_suggestion=row["action_suggestion"],
                created_at=row["created_at"],
                dismissed=bool(row["dismissed"]),
            )
            self._nudges.setdefault(nudge.user_id, []).append(nudge)
        if rows:
            logger.info("Loaded %d nudges from disk", len(rows))

    def _persist_nudge(self, nudge: Nudge) -> None:
        conn = _get_conn(self._db_path)
        conn.execute(
            """INSERT OR REPLACE INTO proactive_nudges
               (id, user_id, type, title, message, priority, action_suggestion, created_at, dismissed)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (nudge.id, nudge.user_id, nudge.type, nudge.title, nudge.message,
             nudge.priority, nudge.action_suggestion, nudge.created_at, 1 if nudge.dismissed else 0),
        )
        conn.commit()

    def _update_dismissed(self, nudge_id: str, dismissed: bool) -> None:
        conn = _get_conn(self._db_path)
        conn.execute(
            "UPDATE proactive_nudges SET dismissed = ? WHERE id = ?",
            (1 if dismissed else 0, nudge_id),
        )
        conn.commit()

    def close(self) -> None:
        conn_attr = f"conn_{hash(self._db_path or _NUDGE_DB_PATH)}"
        if hasattr(_thread_local, conn_attr) and getattr(_thread_local, conn_attr) is not None:
            getattr(_thread_local, conn_attr).close()
            setattr(_thread_local, conn_attr, None)

    def check_deadlines(self, user_id: str, assignments: list[dict[str, Any]]) -> list[Nudge]:
        """Check for approaching deadlines and generate nudges."""
        nudges = []
        now = time.time()
        for a in assignments:
            deadline_str = a.get("deadline", "")
            if not deadline_str:
                continue
            try:
                import datetime
                deadline = datetime.datetime.fromisoformat(deadline_str.replace("Z", "+00:00"))
                days_left = (deadline - datetime.datetime.now(datetime.timezone.utc)).days
                if days_left <= 3 and days_left >= 0:
                    nudge = Nudge(
                        id=f"nudge_{int(now)}_{a.get('id', '')}",
                        user_id=user_id,
                        type="deadline_reminder",
                        title=f"Assignment due in {days_left} day{'s' if days_left != 1 else ''}",
                        message=f"'{a.get('title', 'Untitled')}' is due {deadline_str}",
                        priority="high" if days_left <= 1 else "medium",
                        action_suggestion="Review and complete the assignment",
                    )
                    nudges.append(nudge)
            except (ValueError, TypeError):
                continue
        self._nudges.setdefault(user_id, []).extend(nudges)
        for n in nudges:
            self._persist_nudge(n)
        return nudges

    def check_study_patterns(self, user_id: str, study_data: dict[str, Any]) -> list[Nudge]:
        """Generate study suggestions based on patterns."""
        nudges = []
        now = time.time()
        streak = study_data.get("streak", 0)
        if streak == 0:
            nudges.append(Nudge(
                id=f"nudge_study_{int(now)}",
                user_id=user_id,
                type="study_suggestion",
                title="Start your study streak",
                message="You haven't studied today. A short session counts!",
                priority="medium",
                action_suggestion="Start a 25-minute Pomodoro session",
            ))
        elif streak >= 7:
            nudges.append(Nudge(
                id=f"nudge_streak_{int(now)}",
                user_id=user_id,
                type="study_suggestion",
                title=f"{streak}-day streak!",
                message=f"Amazing {streak}-day streak! Keep it going.",
                priority="low",
            ))
        self._nudges.setdefault(user_id, []).extend(nudges)
        for n in nudges:
            self._persist_nudge(n)
        return nudges

    def check_weaknesses(self, user_id: str, weaknesses: list[dict[str, Any]]) -> list[Nudge]:
        """Generate alerts for weak areas."""
        nudges = []
        now = time.time()
        for w in weaknesses[:3]:
            nudges.append(Nudge(
                id=f"nudge_weak_{int(now)}_{w.get('subject', '')}",
                user_id=user_id,
                type="weakness_alert",
                title=f"Weak area: {w.get('subject', 'Unknown')}",
                message=f"Your average in {w.get('subject', '')} is {w.get('average', 0):.0f}%",
                priority="high" if w.get("average", 100) < 40 else "medium",
                action_suggestion=f"Review {', '.join(w.get('weak_topics', [])[:3])}",
            ))
        self._nudges.setdefault(user_id, []).extend(nudges)
        for n in nudges:
            self._persist_nudge(n)
        return nudges

    def get_nudges(self, user_id: str, include_dismissed: bool = False) -> list[Nudge]:
        nudges = self._nudges.get(user_id, [])
        if not include_dismissed:
            nudges = [n for n in nudges if not n.dismissed]
        return sorted(nudges, key=lambda n: {"high": 0, "medium": 1, "low": 2}.get(n.priority, 3))

    def dismiss(self, user_id: str, nudge_id: str) -> bool:
        for nudge in self._nudges.get(user_id, []):
            if nudge.id == nudge_id:
                nudge.dismissed = True
                self._update_dismissed(nudge_id, True)
                return True
        return False
