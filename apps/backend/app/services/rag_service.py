"""Retrieval-Augmented Generation service.

Default strategy: semantic-only vector search.
Optional strategy: hybrid semantic + keyword with Reciprocal Rank Fusion (RRF).
Provides cross-document search across all of a user's processed documents.

Gate 2 evaluation showed semantic-only outperforms RRF on Recall@3 (0.94 vs 0.81)
and MRR (0.898 vs 0.803). RRF is preserved as an optional strategy for
experimentation or future use.
"""

from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import VectorStore

logger = get_logger(__name__)

RRF_K = 60  # RRF constant (standard value)
DEFAULT_TOP_K = 10
MAX_TOKENS = 3000


class RAGService:
    """Document retrieval service with semantic and optional keyword fusion.

    Default strategy: "semantic" — pure cosine similarity search.
    Optional strategy: "hybrid" — RRF fusion of semantic + keyword rankings.
    """

    def __init__(self) -> None:
        self.vector_store = VectorStore()
        self.embedding_service = EmbeddingService()

    def _keyword_rank(
        self, chunks: list[dict[str, Any]], query: str
    ) -> list[dict[str, Any]]:
        """Rank chunks by keyword overlap (TF-style scoring)."""
        query_lower = query.lower()
        query_words = set(query_lower.split())

        scored: list[dict[str, Any]] = []
        for chunk in chunks:
            score = 0
            content_lower = chunk.get("content", "").lower()
            content_words = set(content_lower.split())

            # Keyword overlap
            overlap = len(query_words & content_words)
            score += overlap * 2

            # Heading match
            heading = chunk.get("heading", "") or ""
            if heading and any(w in heading.lower() for w in query_words):
                score += 10

            # Exact phrase match
            if query_lower in content_lower:
                score += 20

            scored.append({**chunk, "_keyword_score": score})

        scored.sort(key=lambda c: c["_keyword_score"], reverse=True)
        return scored

    def _rrf_fusion(
        self,
        semantic_results: list[dict[str, Any]],
        keyword_results: list[dict[str, Any]],
        k: int = RRF_K,
    ) -> list[dict[str, Any]]:
        """Merge two ranked lists using Reciprocal Rank Fusion."""
        rrf_scores: dict[str, float] = {}
        chunk_map: dict[str, dict[str, Any]] = {}

        # Semantic results contribute by rank position
        for rank, chunk in enumerate(semantic_results):
            cid = chunk["chunk_id"]
            rrf_scores[cid] = rrf_scores.get(cid, 0) + 1.0 / (k + rank + 1)
            if cid not in chunk_map:
                chunk_map[cid] = chunk

        # Keyword results contribute by rank position
        for rank, chunk in enumerate(keyword_results):
            cid = chunk["chunk_id"]
            rrf_scores[cid] = rrf_scores.get(cid, 0) + 1.0 / (k + rank + 1)
            if cid not in chunk_map:
                chunk_map[cid] = chunk

        # Sort by combined RRF score
        sorted_ids = sorted(rrf_scores.keys(), key=lambda cid: rrf_scores[cid], reverse=True)
        results = []
        for cid in sorted_ids:
            entry = {**chunk_map[cid], "_rrf_score": rrf_scores[cid]}
            # Remove internal scoring keys
            entry.pop("_keyword_score", None)
            entry.pop("_score", None)
            results.append(entry)

        return results

    def _select_top_k(
        self, chunks: list[dict[str, Any]], top_k: int, max_tokens: int = MAX_TOKENS
    ) -> list[dict[str, Any]]:
        """Select top-k chunks within token budget."""
        selected: list[dict[str, Any]] = []
        total_tokens = 0

        for chunk in chunks[:top_k]:
            tokens = chunk.get("token_count", 0) or len(chunk.get("content", "").split())
            if total_tokens + tokens > max_tokens and selected:
                break
            chunk["_tokens"] = tokens
            selected.append(chunk)
            total_tokens += tokens

        return selected

    async def hybrid_search(
        self,
        user_id: str,
        query: str,
        top_k: int = DEFAULT_TOP_K,
        document_id: str | None = None,
        max_tokens: int = MAX_TOKENS,
        strategy: str = "semantic",
    ) -> list[dict[str, Any]]:
        """Search across user's documents using the specified strategy.

        Args:
            user_id: Authenticated user ID (scoped for security).
            query: The search query.
            top_k: Maximum number of results to return.
            document_id: Optional filter to a specific document.
            max_tokens: Maximum total tokens in selected chunks.
            strategy: "semantic" (default), "keyword", or "hybrid" (RRF).

        Returns:
            Ranked list of chunks with scores, source attribution, and content.
        """
        if strategy == "keyword":
            results = self._keyword_search(user_id, query, top_k, document_id)
            selected = self._select_top_k(results, top_k, max_tokens)
            return selected

        # Semantic search (default path)
        semantic_results: list[dict[str, Any]] = []
        if self.embedding_service.is_available():
            try:
                query_embedding = self.embedding_service.embed_text(query)
                semantic_results = self.vector_store.search(
                    user_id, query_embedding, top_k=top_k * 2, document_id=document_id
                )
                for r in semantic_results:
                    r["_semantic_score"] = r.get("score", 0)
            except Exception as e:
                logger.warning("Semantic search failed, falling back to keyword: %s", e)

        if strategy == "hybrid":
            # Optional RRF fusion path
            keyword_results = self._keyword_search(user_id, query, top_k * 2, document_id)
            if semantic_results and keyword_results:
                fused = self._rrf_fusion(semantic_results, keyword_results)
            elif semantic_results:
                fused = semantic_results
            elif keyword_results:
                fused = keyword_results
            else:
                fused = []
            selected = self._select_top_k(fused, top_k, max_tokens)
            return selected

        # Default: semantic-only
        selected = self._select_top_k(semantic_results, top_k, max_tokens)
        return selected

    def _keyword_search(
        self,
        user_id: str,
        query: str,
        top_k: int,
        document_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Keyword-based search across user's document chunks.

        Loads chunks from the vector store (which stores chunk content)
        and applies TF-style scoring.
        """
        conn = self.vector_store._thread_conn() if hasattr(self.vector_store, '_thread_conn') else None
        if conn is None:
            from app.services.vector_store import _thread_conn
            conn = _thread_conn()

        if document_id:
            cursor = conn.execute(
                "SELECT chunk_id, document_id, chunk_content, chunk_index, "
                "page_number, heading, chunk_type "
                "FROM document_embeddings WHERE user_id = ? AND document_id = ?",
                (user_id, document_id),
            )
        else:
            cursor = conn.execute(
                "SELECT chunk_id, document_id, chunk_content, chunk_index, "
                "page_number, heading, chunk_type "
                "FROM document_embeddings WHERE user_id = ?",
                (user_id,),
            )

        chunks = []
        for row in cursor:
            chunks.append({
                "chunk_id": row[0],
                "document_id": row[1],
                "content": row[2],
                "chunk_index": row[3],
                "page_number": row[4],
                "heading": row[5],
                "chunk_type": row[6],
            })

        if not chunks:
            return []

        ranked = self._keyword_rank(chunks, query)
        return ranked[:top_k]

    async def search_with_context(
        self,
        user_id: str,
        query: str,
        top_k: int = DEFAULT_TOP_K,
        document_id: str | None = None,
        strategy: str = "semantic",
    ) -> dict[str, Any]:
        """Search and return results formatted for LLM context injection.

        Args:
            strategy: "semantic" (default), "keyword", or "hybrid" (RRF).

        Returns:
            {
                "chunks": [...],
                "sources": [...],
                "context_prompt": str,
                "total_chunks": int,
            }
        """
        chunks = await self.hybrid_search(
            user_id, query, top_k, document_id, strategy=strategy
        )

        sources = []
        for chunk in chunks:
            sources.append({
                "document_id": chunk.get("document_id"),
                "chunk_id": chunk.get("chunk_id"),
                "heading": chunk.get("heading"),
                "page_number": chunk.get("page_number"),
                "score": round(chunk.get("score", chunk.get("_rrf_score", 0)), 4),
            })

        # Build context prompt
        if not chunks:
            context_prompt = "[No relevant document content found for this query.]"
        else:
            parts = [f"Found {len(chunks)} relevant section(s) from your documents:\n"]
            for i, chunk in enumerate(chunks, 1):
                heading = chunk.get("heading")
                ctype = chunk.get("chunk_type", "text")
                content = chunk.get("content", "")
                header = f"Section {i}"
                if heading:
                    header += f": {heading}"
                if ctype != "text":
                    header += f" [{ctype}]"
                parts.append(f"--- {header} ---\n{content}\n")
            context_prompt = "\n".join(parts)

        return {
            "chunks": chunks,
            "sources": sources,
            "context_prompt": context_prompt,
            "total_chunks": len(chunks),
        }

    async def reindex_document(
        self,
        user_id: str,
        document_id: str,
        chunks: list[dict[str, Any]],
    ) -> int:
        """Reindex a document: delete old embeddings, generate new ones.

        Args:
            user_id: Authenticated user ID.
            document_id: Document to reindex.
            chunks: List of chunk dicts from PDFService.chunk_text().

        Returns:
            Number of chunks indexed.
        """
        # Delete old embeddings
        self.vector_store.delete_by_document(user_id, document_id)

        if not chunks:
            return 0

        # Generate embeddings for all chunks
        texts = [c.get("content", "") for c in chunks]
        embeddings = self.embedding_service.embed_batch(texts)

        # Build records
        records = []
        for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            records.append({
                "chunk_id": f"{document_id}_chunk_{i}",
                "embedding": emb,
                "chunk_content": chunk.get("content", ""),
                "chunk_index": chunk.get("chunk_index", i),
                "page_number": chunk.get("page_number"),
                "heading": chunk.get("heading"),
                "chunk_type": chunk.get("chunk_type", "text"),
            })

        count = self.vector_store.upsert_batch(user_id, document_id, records)
        logger.info("Indexed %d chunks for document %s (user %s)", count, document_id, user_id)
        return count
