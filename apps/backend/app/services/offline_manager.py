"""Offline Detection and Sync Management for Fixly AI.

Provides offline status detection, queue management for pending operations,
and sync conflict resolution.
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)

_DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
_OFFLINE_DB_PATH = os.path.join(_DB_DIR, "fixly_offline.db")
_thread_local = threading.local()


def _get_conn(db_path: str | None = None) -> sqlite3.Connection:
    effective_path = db_path or _OFFLINE_DB_PATH
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
        CREATE TABLE IF NOT EXISTS pending_operations (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            operation TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            data TEXT NOT NULL DEFAULT '{}',
            status TEXT NOT NULL DEFAULT 'pending',
            created_at REAL NOT NULL,
            synced_at REAL,
            error TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_pending_ops_user ON pending_operations(user_id);
        CREATE INDEX IF NOT EXISTS idx_pending_ops_status ON pending_operations(status);

        CREATE TABLE IF NOT EXISTS conflict_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            operation_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            local_data TEXT NOT NULL,
            remote_data TEXT NOT NULL,
            resolution TEXT NOT NULL,
            resolved_at REAL NOT NULL,
            FOREIGN KEY (operation_id) REFERENCES pending_operations(id)
        );
        CREATE INDEX IF NOT EXISTS idx_conflict_log_user ON conflict_log(user_id);
    """)
    conn.commit()


class SyncStatus(str, Enum):
    PENDING = "pending"
    SYNCING = "syncing"
    SYNCED = "synced"
    FAILED = "failed"
    CONFLICT = "conflict"


@dataclass
class PendingOperation:
    id: str
    user_id: str
    operation: str  # create | update | delete
    entity_type: str  # assignment | goal | memory | opportunity
    entity_id: str
    data: dict[str, Any] = field(default_factory=dict)
    status: SyncStatus = SyncStatus.PENDING
    created_at: float = field(default_factory=time.time)
    synced_at: float | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "user_id": self.user_id,
            "operation": self.operation, "entity_type": self.entity_type,
            "entity_id": self.entity_id, "data": self.data,
            "status": self.status.value, "created_at": self.created_at,
            "synced_at": self.synced_at, "error": self.error,
        }


class OfflineManager:
    """Manages offline detection and sync queue."""

    def __init__(self, db_path: str | None = None) -> None:
        self._db_path = db_path
        self._is_online = True
        self._pending_operations: dict[str, list[PendingOperation]] = {}
        self._last_check: float = 0
        _ensure_tables(db_path)
        if db_path == ":memory:":
            conn = _get_conn(db_path)
            conn.execute("DELETE FROM pending_operations")
            conn.execute("DELETE FROM conflict_log")
            conn.commit()
        self._load_from_db()

    def _load_from_db(self) -> None:
        conn = _get_conn(self._db_path)
        rows = conn.execute(
            "SELECT * FROM pending_operations WHERE status IN ('pending', 'failed')"
        ).fetchall()
        for row in rows:
            op = PendingOperation(
                id=row["id"],
                user_id=row["user_id"],
                operation=row["operation"],
                entity_type=row["entity_type"],
                entity_id=row["entity_id"],
                data=json.loads(row["data"]),
                status=SyncStatus(row["status"]),
                created_at=row["created_at"],
                synced_at=row["synced_at"],
                error=row["error"],
            )
            self._pending_operations.setdefault(op.user_id, []).append(op)
        if rows:
            logger.info("Loaded %d pending operations from disk", len(rows))

    def _persist_op(self, op: PendingOperation) -> None:
        conn = _get_conn(self._db_path)
        conn.execute(
            """INSERT OR REPLACE INTO pending_operations
               (id, user_id, operation, entity_type, entity_id, data, status, created_at, synced_at, error)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (op.id, op.user_id, op.operation, op.entity_type, op.entity_id,
             json.dumps(op.data), op.status.value, op.created_at, op.synced_at, op.error),
        )
        conn.commit()

    def _update_op_status(
        self, op_id: str, status: str, error: str | None = None, synced_at: float | None = None
    ) -> None:
        conn = _get_conn(self._db_path)
        conn.execute(
            "UPDATE pending_operations SET status = ?, error = ?, synced_at = ? WHERE id = ?",
            (status, error, synced_at, op_id),
        )
        conn.commit()

    def _delete_synced_from_db(self, user_id: str) -> int:
        conn = _get_conn(self._db_path)
        cursor = conn.execute(
            "DELETE FROM pending_operations WHERE user_id = ? AND status = 'synced'",
            (user_id,),
        )
        conn.commit()
        return cursor.rowcount

    def close(self) -> None:
        conn_attr = f"conn_{hash(self._db_path or _OFFLINE_DB_PATH)}"
        if hasattr(_thread_local, conn_attr) and getattr(_thread_local, conn_attr) is not None:
            getattr(_thread_local, conn_attr).close()
            setattr(_thread_local, conn_attr, None)

    @property
    def is_online(self) -> bool:
        return self._is_online

    def set_online(self, online: bool) -> None:
        if self._is_online != online:
            self._is_online = online
            logger.info("Network status changed: %s", "online" if online else "offline")

    def queue_operation(
        self,
        user_id: str,
        operation: str,
        entity_type: str,
        entity_id: str,
        data: dict[str, Any] | None = None,
    ) -> PendingOperation:
        """Queue an operation for sync when back online."""
        op = PendingOperation(
            id=f"sync_{uuid.uuid4().hex[:12]}",
            user_id=user_id,
            operation=operation,
            entity_type=entity_type,
            entity_id=entity_id,
            data=data or {},
        )
        self._pending_operations.setdefault(user_id, []).append(op)
        self._persist_op(op)
        logger.info("Queued operation: %s %s for user %s", operation, entity_type, user_id)
        return op

    def get_pending(self, user_id: str) -> list[PendingOperation]:
        return [
            op for op in self._pending_operations.get(user_id, [])
            if op.status in (SyncStatus.PENDING, SyncStatus.FAILED)
        ]

    def get_all_pending(self) -> list[PendingOperation]:
        all_ops = []
        for ops in self._pending_operations.values():
            all_ops.extend([op for op in ops if op.status in (SyncStatus.PENDING, SyncStatus.FAILED)])
        return all_ops

    def mark_synced(self, operation_id: str) -> bool:
        for ops in self._pending_operations.values():
            for op in ops:
                if op.id == operation_id:
                    op.status = SyncStatus.SYNCED
                    op.synced_at = time.time()
                    self._update_op_status(operation_id, "synced", synced_at=op.synced_at)
                    return True
        return False

    def mark_failed(self, operation_id: str, error: str) -> bool:
        for ops in self._pending_operations.values():
            for op in ops:
                if op.id == operation_id:
                    op.status = SyncStatus.FAILED
                    op.error = error
                    self._update_op_status(operation_id, "failed", error=error)
                    return True
        return False

    def clear_synced(self, user_id: str) -> int:
        ops = self._pending_operations.get(user_id, [])
        before = len(ops)
        self._pending_operations[user_id] = [op for op in ops if op.status != SyncStatus.SYNCED]
        self._delete_synced_from_db(user_id)
        return before - len(self._pending_operations[user_id])

    def get_pending_count(self, user_id: str) -> int:
        return len(self.get_pending(user_id))

    def get_total_pending_count(self) -> int:
        return len(self.get_all_pending())


class ConflictResolver:
    """Handles sync conflicts with last-write-wins strategy."""

    @staticmethod
    def resolve(
        local: dict[str, Any],
        remote: dict[str, Any],
        strategy: str = "last_write_wins",
    ) -> dict[str, Any]:
        if strategy == "last_write_wins":
            local_time = local.get("updated_at", 0)
            remote_time = remote.get("updated_at", 0)
            return local if local_time >= remote_time else remote
        if strategy == "local_wins":
            return local
        if strategy == "remote_wins":
            return remote
        return local

    @staticmethod
    def detect_conflict(
        local_version: int,
        remote_version: int,
    ) -> bool:
        return local_version != remote_version and local_version > 0 and remote_version > 0
