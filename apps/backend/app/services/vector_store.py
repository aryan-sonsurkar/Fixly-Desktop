"""Local vector storage backed by SQLite.

Stores document chunk embeddings in a local SQLite database.
Provides cosine similarity search without external vector extensions.
All operations are scoped to a single user_id for security.
"""

from __future__ import annotations

import math
import os
import sqlite3
import threading
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)

DB_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data",
)
DB_NAME = "fixly_vectors.db"


def _default_db_path() -> str:
    """Return the path to the local vector database."""
    os.makedirs(DB_DIR, exist_ok=True)
    return os.path.join(DB_DIR, DB_NAME)


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors (pure Python)."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class VectorStore:
    """SQLite-backed vector store for document chunk embeddings.

    Args:
        db_path: Optional custom database path (for testing).
                 If None, uses the default data directory.
    """

    def __init__(self, db_path: str | None = None) -> None:
        self._db_path = db_path or _default_db_path()
        self._local = threading.local()
        self._ensure_schema()

    def _get_connection(self) -> sqlite3.Connection:
        """Get a thread-local SQLite connection."""
        conn = sqlite3.connect(self._db_path, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        return conn

    def _thread_conn(self) -> sqlite3.Connection:
        """Get or create a thread-local connection."""
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = self._get_connection()
        return self._local.conn

    def _ensure_schema(self) -> None:
        """Create the embeddings table if it doesn't exist."""
        conn = self._thread_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS document_embeddings (
                id TEXT PRIMARY KEY,
                chunk_id TEXT NOT NULL,
                document_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                chunk_content TEXT NOT NULL,
                embedding BLOB NOT NULL,
                chunk_index INTEGER,
                page_number INTEGER,
                heading TEXT,
                chunk_type TEXT DEFAULT 'text',
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_emb_user ON document_embeddings(user_id)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_emb_document ON document_embeddings(document_id)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_emb_chunk ON document_embeddings(chunk_id)
        """)
        conn.commit()

    def upsert_embedding(
        self,
        user_id: str,
        chunk_id: str,
        document_id: str,
        embedding: list[float],
        chunk_content: str,
        chunk_index: int | None = None,
        page_number: int | None = None,
        heading: str | None = None,
        chunk_type: str = "text",
    ) -> None:
        """Insert or update a single embedding record."""
        from app.services.embedding_service import EmbeddingService

        conn = self._thread_conn()
        blob = EmbeddingService.embedding_to_blob(embedding)
        conn.execute(
            """
            INSERT OR REPLACE INTO document_embeddings
                (id, chunk_id, document_id, user_id, chunk_content, embedding,
                 chunk_index, page_number, heading, chunk_type, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """,
            (chunk_id, chunk_id, document_id, user_id, chunk_content, blob,
             chunk_index, page_number, heading, chunk_type),
        )
        conn.commit()

    def upsert_batch(
        self,
        user_id: str,
        document_id: str,
        records: list[dict[str, Any]],
    ) -> int:
        """Insert or update a batch of embeddings.

        Each record must contain:
            chunk_id, embedding (list[float]), chunk_content,
            and optionally chunk_index, page_number, heading, chunk_type.

        Returns the number of records upserted.
        """
        from app.services.embedding_service import EmbeddingService

        if not records:
            return 0

        conn = self._thread_conn()
        blobs = [EmbeddingService.embedding_to_blob(r["embedding"]) for r in records]
        rows = [
            (
                r["chunk_id"], r["chunk_id"], document_id, user_id,
                r["chunk_content"], blobs[i],
                r.get("chunk_index"), r.get("page_number"),
                r.get("heading"), r.get("chunk_type", "text"),
            )
            for i, r in enumerate(records)
        ]
        conn.executemany(
            """
            INSERT OR REPLACE INTO document_embeddings
                (id, chunk_id, document_id, user_id, chunk_content, embedding,
                 chunk_index, page_number, heading, chunk_type, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """,
            rows,
        )
        conn.commit()
        return len(rows)

    def search(
        self,
        user_id: str,
        query_embedding: list[float],
        top_k: int = 10,
        document_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Find the most similar chunks to the query embedding.

        Results are scoped to the given user_id.
        Returns a list of dicts with chunk data and similarity score.
        """
        from app.services.embedding_service import EmbeddingService

        conn = self._thread_conn()

        if document_id:
            cursor = conn.execute(
                "SELECT chunk_id, document_id, chunk_content, embedding, "
                "chunk_index, page_number, heading, chunk_type "
                "FROM document_embeddings WHERE user_id = ? AND document_id = ?",
                (user_id, document_id),
            )
        else:
            cursor = conn.execute(
                "SELECT chunk_id, document_id, chunk_content, embedding, "
                "chunk_index, page_number, heading, chunk_type "
                "FROM document_embeddings WHERE user_id = ?",
                (user_id,),
            )

        results: list[dict[str, Any]] = []
        for row in cursor:
            emb = EmbeddingService.blob_to_embedding(row[3])
            score = cosine_similarity(query_embedding, emb)
            results.append({
                "chunk_id": row[0],
                "document_id": row[1],
                "content": row[2],
                "score": score,
                "chunk_index": row[4],
                "page_number": row[5],
                "heading": row[6],
                "chunk_type": row[7],
            })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def delete_by_document(self, user_id: str, document_id: str) -> int:
        """Delete all embeddings for a document. Returns count deleted."""
        conn = self._thread_conn()
        cursor = conn.execute(
            "DELETE FROM document_embeddings WHERE user_id = ? AND document_id = ?",
            (user_id, document_id),
        )
        conn.commit()
        return cursor.rowcount

    def delete_by_user(self, user_id: str) -> int:
        """Delete all embeddings for a user. Returns count deleted."""
        conn = self._thread_conn()
        cursor = conn.execute(
            "DELETE FROM document_embeddings WHERE user_id = ?",
            (user_id,),
        )
        conn.commit()
        return cursor.rowcount

    def count(self, user_id: str, document_id: str | None = None) -> int:
        """Count embeddings for a user, optionally filtered by document."""
        conn = self._thread_conn()
        if document_id:
            row = conn.execute(
                "SELECT COUNT(*) FROM document_embeddings WHERE user_id = ? AND document_id = ?",
                (user_id, document_id),
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT COUNT(*) FROM document_embeddings WHERE user_id = ?",
                (user_id,),
            ).fetchone()
        return row[0] if row else 0

    def list_documents(self, user_id: str) -> list[dict[str, Any]]:
        """List all documents with embeddings for a user."""
        conn = self._thread_conn()
        cursor = conn.execute(
            "SELECT document_id, COUNT(*) as chunk_count, MIN(created_at) as indexed_at "
            "FROM document_embeddings WHERE user_id = ? GROUP BY document_id",
            (user_id,),
        )
        return [
            {"document_id": row[0], "chunk_count": row[1], "indexed_at": row[2]}
            for row in cursor
        ]

    def is_indexed(self, user_id: str, document_id: str) -> bool:
        """Check if a document has been indexed."""
        return self.count(user_id, document_id) > 0

    def close(self) -> None:
        """Close the thread-local connection."""
        if hasattr(self._local, "conn") and self._local.conn is not None:
            self._local.conn.close()
            self._local.conn = None
