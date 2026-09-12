"""Persistent Workflow State for Fixly AI.

Stores multi-step workflow state in SQLite. Enables resume/restart
after app closure.
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class WorkflowStep:
    id: str
    tool_name: str
    parameters: dict[str, Any]
    status: str = "pending"  # pending | running | completed | failed | skipped
    result: Any = None
    error: str | None = None
    started_at: float | None = None
    completed_at: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tool_name": self.tool_name,
            "parameters": self.parameters,
            "status": self.status,
            "result": self.result,
            "error": self.error,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }


@dataclass
class Workflow:
    id: str
    user_id: str
    name: str
    description: str
    steps: list[WorkflowStep] = field(default_factory=list)
    status: str = "pending"  # pending | running | completed | failed | paused
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "description": self.description,
            "steps": [s.to_dict() for s in self.steps],
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "error": self.error,
            "metadata": self.metadata,
        }


class WorkflowStore:
    """SQLite-backed persistent workflow storage."""

    def __init__(self, db_path: str | None = None) -> None:
        import sqlite3
        self._db_path = db_path or ":memory:"
        self._conn = sqlite3.connect(self._db_path)
        self._conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self) -> None:
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS ai_workflows (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                steps TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                error TEXT,
                metadata TEXT DEFAULT '{}'
            );
            CREATE INDEX IF NOT EXISTS idx_workflow_user ON ai_workflows(user_id);
            CREATE INDEX IF NOT EXISTS idx_workflow_status ON ai_workflows(status);
        """)
        self._conn.commit()

    def create(self, workflow: Workflow) -> Workflow:
        self._conn.execute(
            """INSERT INTO ai_workflows (id, user_id, name, description, steps, status, created_at, updated_at, error, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (workflow.id, workflow.user_id, workflow.name, workflow.description,
             json.dumps([s.to_dict() for s in workflow.steps]),
             workflow.status, workflow.created_at, workflow.updated_at,
             workflow.error, json.dumps(workflow.metadata)),
        )
        self._conn.commit()
        return workflow

    def get(self, workflow_id: str, user_id: str) -> Workflow | None:
        row = self._conn.execute(
            "SELECT * FROM ai_workflows WHERE id = ? AND user_id = ?",
            (workflow_id, user_id),
        ).fetchone()
        if row is None:
            return None
        return self._row_to_workflow(row)

    def list_by_user(self, user_id: str, status: str | None = None) -> list[Workflow]:
        if status:
            rows = self._conn.execute(
                "SELECT * FROM ai_workflows WHERE user_id = ? AND status = ? ORDER BY updated_at DESC",
                (user_id, status),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM ai_workflows WHERE user_id = ? ORDER BY updated_at DESC",
                (user_id,),
            ).fetchall()
        return [self._row_to_workflow(r) for r in rows]

    def update(self, workflow: Workflow) -> Workflow:
        workflow.updated_at = time.time()
        self._conn.execute(
            """UPDATE ai_workflows SET steps = ?, status = ?, updated_at = ?, error = ?, metadata = ?
               WHERE id = ? AND user_id = ?""",
            (json.dumps([s.to_dict() for s in workflow.steps]),
             workflow.status, workflow.updated_at,
             workflow.error, json.dumps(workflow.metadata),
             workflow.id, workflow.user_id),
        )
        self._conn.commit()
        return workflow

    def delete(self, workflow_id: str, user_id: str) -> bool:
        cursor = self._conn.execute(
            "DELETE FROM ai_workflows WHERE id = ? AND user_id = ?",
            (workflow_id, user_id),
        )
        self._conn.commit()
        return cursor.rowcount > 0

    def list_all(self, user_id: str) -> list[Workflow]:
        return self.list_by_user(user_id)

    def _row_to_workflow(self, row: Any) -> Workflow:
        steps_data = json.loads(row["steps"])
        steps = [WorkflowStep(**s) for s in steps_data]
        return Workflow(
            id=row["id"],
            user_id=row["user_id"],
            name=row["name"],
            description=row["description"],
            steps=steps,
            status=row["status"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            error=row["error"],
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
        )

    def close(self) -> None:
        self._conn.close()
