"""Local SQLite memory store for Fixly AI persistent memory.

Schema:
- ai_memories: user-scoped memories with categories, confidence, provenance
- ai_memory_embeddings: vector embeddings for semantic memory retrieval
- ai_conversation_summaries: conversation summaries for bounded context
"""

from __future__ import annotations

import os
import sqlite3
import threading
import time
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DB_PATH = os.path.join(DB_DIR, "fixly_memory.db")

_thread_local = threading.local()


def _get_conn() -> sqlite3.Connection:
    if not hasattr(_thread_local, "conn") or _thread_local.conn is None:
        os.makedirs(DB_DIR, exist_ok=True)
        conn = sqlite3.connect(DB_PATH, timeout=10)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
        conn.row_factory = sqlite3.Row
        _thread_local.conn = conn
    return _thread_local.conn


def _ensure_tables() -> None:
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS ai_memories (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            category TEXT NOT NULL,
            content TEXT NOT NULL,
            confidence REAL NOT NULL DEFAULT 0.5,
            source TEXT NOT NULL DEFAULT 'inferred',
            source_document_id TEXT,
            source_conversation_id TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            last_reinforced_at TEXT,
            is_archived INTEGER NOT NULL DEFAULT 0,
            metadata TEXT DEFAULT '{}'
        );

        CREATE INDEX IF NOT EXISTS idx_memories_user ON ai_memories(user_id);
        CREATE INDEX IF NOT EXISTS idx_memories_user_category ON ai_memories(user_id, category);
        CREATE INDEX IF NOT EXISTS idx_memories_user_archived ON ai_memories(user_id, is_archived);

        CREATE TABLE IF NOT EXISTS ai_memory_embeddings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            memory_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            embedding BLOB NOT NULL,
            FOREIGN KEY (memory_id) REFERENCES ai_memories(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_mem_emb_user ON ai_memory_embeddings(user_id);
        CREATE INDEX IF NOT EXISTS idx_mem_emb_memory ON ai_memory_embeddings(memory_id);

        CREATE TABLE IF NOT EXISTS ai_conversation_summaries (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            conversation_id TEXT NOT NULL,
            summary TEXT NOT NULL,
            message_range_start INTEGER NOT NULL,
            message_range_end INTEGER NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_summaries_user ON ai_conversation_summaries(user_id);
        CREATE INDEX IF NOT EXISTS idx_summaries_conv ON ai_conversation_summaries(conversation_id);
    """)
    conn.commit()


class MemoryStore:
    """SQLite-backed persistent memory store."""

    def __init__(self, db_path: str | None = None) -> None:
        self._db_path = db_path
        if db_path:
            self._custom_conn = sqlite3.connect(db_path, timeout=10)
            self._custom_conn.execute("PRAGMA journal_mode=WAL")
            self._custom_conn.execute("PRAGMA busy_timeout=5000")
            self._custom_conn.row_factory = sqlite3.Row
            self._ensure_tables_conn(self._custom_conn)
        else:
            _ensure_tables()
            self._custom_conn = None

    @staticmethod
    def _ensure_tables_conn(conn: sqlite3.Connection) -> None:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS ai_memories (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                category TEXT NOT NULL,
                content TEXT NOT NULL,
                confidence REAL NOT NULL DEFAULT 0.5,
                source TEXT NOT NULL DEFAULT 'inferred',
                source_document_id TEXT,
                source_conversation_id TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                last_reinforced_at TEXT,
                is_archived INTEGER NOT NULL DEFAULT 0,
                metadata TEXT DEFAULT '{}'
            );
            CREATE INDEX IF NOT EXISTS idx_memories_user ON ai_memories(user_id);
            CREATE INDEX IF NOT EXISTS idx_memories_user_category ON ai_memories(user_id, category);
            CREATE INDEX IF NOT EXISTS idx_memories_user_archived ON ai_memories(user_id, is_archived);

            CREATE TABLE IF NOT EXISTS ai_memory_embeddings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                memory_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                embedding BLOB NOT NULL,
                FOREIGN KEY (memory_id) REFERENCES ai_memories(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_mem_emb_user ON ai_memory_embeddings(user_id);
            CREATE INDEX IF NOT EXISTS idx_mem_emb_memory ON ai_memory_embeddings(memory_id);

            CREATE TABLE IF NOT EXISTS ai_conversation_summaries (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                conversation_id TEXT NOT NULL,
                summary TEXT NOT NULL,
                message_range_start INTEGER NOT NULL,
                message_range_end INTEGER NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_summaries_user ON ai_conversation_summaries(user_id);
            CREATE INDEX IF NOT EXISTS idx_summaries_conv ON ai_conversation_summaries(conversation_id);
        """)
        conn.commit()

    def _conn(self) -> sqlite3.Connection:
        if self._custom_conn:
            return self._custom_conn
        return _get_conn()

    def close(self) -> None:
        if self._custom_conn:
            self._custom_conn.close()
            self._custom_conn = None

    # ── Memory CRUD ──

    def insert_memory(self, memory: dict[str, Any]) -> None:
        conn = self._conn()
        conn.execute(
            """INSERT OR REPLACE INTO ai_memories
               (id, user_id, category, content, confidence, source,
                source_document_id, source_conversation_id,
                created_at, updated_at, last_reinforced_at, is_archived, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                memory["id"],
                memory["user_id"],
                memory["category"],
                memory["content"],
                memory["confidence"],
                memory.get("source", "inferred"),
                memory.get("source_document_id"),
                memory.get("source_conversation_id"),
                memory["created_at"],
                memory["updated_at"],
                memory.get("last_reinforced_at"),
                1 if memory.get("is_archived") else 0,
                memory.get("metadata", "{}"),
            ),
        )
        conn.commit()

    def get_memory(self, memory_id: str, user_id: str) -> dict[str, Any] | None:
        conn = self._conn()
        row = conn.execute(
            "SELECT * FROM ai_memories WHERE id = ? AND user_id = ?",
            (memory_id, user_id),
        ).fetchone()
        return self._row_to_dict(row) if row else None

    def list_memories(
        self,
        user_id: str,
        category: str | None = None,
        include_archived: bool = False,
        min_confidence: float = 0.0,
    ) -> list[dict[str, Any]]:
        conn = self._conn()
        query = "SELECT * FROM ai_memories WHERE user_id = ? AND confidence >= ?"
        params: list[Any] = [user_id, min_confidence]
        if category:
            query += " AND category = ?"
            params.append(category)
        if not include_archived:
            query += " AND is_archived = 0"
        query += " ORDER BY updated_at DESC"
        rows = conn.execute(query, params).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def update_memory(self, memory_id: str, user_id: str, updates: dict[str, Any]) -> bool:
        conn = self._conn()
        existing = self.get_memory(memory_id, user_id)
        if not existing:
            return False
        fields = []
        values = []
        for key in ("content", "confidence", "is_archived", "metadata", "last_reinforced_at"):
            if key in updates:
                fields.append(f"{key} = ?")
                values.append(updates[key])
        if "is_archived" in updates:
            fields.append("is_archived = ?")
            values.append(1 if updates["is_archived"] else 0)
        fields.append("updated_at = ?")
        values.append(time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
        values.extend([memory_id, user_id])
        conn.execute(
            f"UPDATE ai_memories SET {', '.join(fields)} WHERE id = ? AND user_id = ?",
            values,
        )
        conn.commit()
        return True

    def delete_memory(self, memory_id: str, user_id: str) -> bool:
        conn = self._conn()
        conn.execute("DELETE FROM ai_memory_embeddings WHERE memory_id = ?", (memory_id,))
        cursor = conn.execute(
            "DELETE FROM ai_memories WHERE id = ? AND user_id = ?", (memory_id, user_id)
        )
        conn.commit()
        return cursor.rowcount > 0

    def delete_by_user(self, user_id: str) -> int:
        conn = self._conn()
        conn.execute("DELETE FROM ai_memory_embeddings WHERE user_id = ?", (user_id,))
        cursor = conn.execute("DELETE FROM ai_memories WHERE user_id = ?", (user_id,))
        conn.execute(
            "DELETE FROM ai_conversation_summaries WHERE user_id = ?", (user_id,)
        )
        conn.commit()
        return cursor.rowcount

    def delete_by_document(self, user_id: str, document_id: str) -> int:
        conn = self._conn()
        # Delete document-derived memories
        cursor = conn.execute(
            "DELETE FROM ai_memories WHERE user_id = ? AND source_document_id = ? AND source = 'document'",
            (user_id, document_id),
        )
        deleted = cursor.rowcount
        # Delete their embeddings
        conn.execute(
            """DELETE FROM ai_memory_embeddings WHERE memory_id IN
               (SELECT id FROM ai_memories WHERE user_id = ? AND source_document_id = ? AND source = 'document')""",
            (user_id, document_id),
        )
        conn.commit()
        return deleted

    def get_all_user_ids(self) -> list[str]:
        conn = self._conn()
        rows = conn.execute(
            "SELECT DISTINCT user_id FROM ai_memories"
        ).fetchall()
        return [row["user_id"] for row in rows]

    def count_by_user(self, user_id: str) -> int:
        conn = self._conn()
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM ai_memories WHERE user_id = ? AND is_archived = 0",
            (user_id,),
        ).fetchone()
        return row["cnt"] if row else 0

    # ── Embedding storage ──

    def store_embedding(self, memory_id: str, user_id: str, embedding: list[float]) -> None:
        import struct

        conn = self._conn()
        blob = struct.pack(f"{len(embedding)}f", *embedding)
        conn.execute(
            "INSERT INTO ai_memory_embeddings (memory_id, user_id, embedding) VALUES (?, ?, ?)",
            (memory_id, user_id, blob),
        )
        conn.commit()

    def get_embedding(self, memory_id: str) -> list[float] | None:
        import struct

        conn = self._conn()
        row = conn.execute(
            "SELECT embedding FROM ai_memory_embeddings WHERE memory_id = ?",
            (memory_id,),
        ).fetchone()
        if not row:
            return None
        blob = row["embedding"]
        dim = len(blob) // 4
        return list(struct.unpack(f"{dim}f", blob))

    def get_all_embeddings(self, user_id: str) -> list[dict[str, Any]]:
        import struct

        conn = self._conn()
        rows = conn.execute(
            """SELECT me.memory_id, me.embedding, m.content, m.category, m.confidence
               FROM ai_memory_embeddings me
               JOIN ai_memories m ON me.memory_id = m.id
               WHERE me.user_id = ? AND m.is_archived = 0""",
            (user_id,),
        ).fetchall()
        results = []
        for row in rows:
            blob = row["embedding"]
            dim = len(blob) // 4
            results.append({
                "memory_id": row["memory_id"],
                "embedding": list(struct.unpack(f"{dim}f", blob)),
                "content": row["content"],
                "category": row["category"],
                "confidence": row["confidence"],
            })
        return results

    def delete_embedding(self, memory_id: str) -> None:
        conn = self._conn()
        conn.execute("DELETE FROM ai_memory_embeddings WHERE memory_id = ?", (memory_id,))
        conn.commit()

    # ── Summaries ──

    def insert_summary(self, summary: dict[str, Any]) -> None:
        conn = self._conn()
        conn.execute(
            """INSERT OR REPLACE INTO ai_conversation_summaries
               (id, user_id, conversation_id, summary, message_range_start, message_range_end, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                summary["id"],
                summary["user_id"],
                summary["conversation_id"],
                summary["summary"],
                summary["message_range_start"],
                summary["message_range_end"],
                summary["created_at"],
            ),
        )
        conn.commit()

    def get_summaries(self, user_id: str, conversation_id: str) -> list[dict[str, Any]]:
        conn = self._conn()
        rows = conn.execute(
            "SELECT * FROM ai_conversation_summaries WHERE user_id = ? "
            "AND conversation_id = ? ORDER BY message_range_start",
            (user_id, conversation_id),
        ).fetchall()
        return [dict(r) for r in rows]

    # ── Helpers ──

    def _row_to_dict(self, row: sqlite3.Row) -> dict[str, Any]:
        d = dict(row)
        d["is_archived"] = bool(d.get("is_archived", 0))
        return d
