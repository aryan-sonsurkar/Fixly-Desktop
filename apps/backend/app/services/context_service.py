from typing import Any

from app.core.logging import get_logger
from app.repositories.document_repository import DocumentRepository

logger = get_logger(__name__)


class ContextService:
    """Document Context Manager: chunk retrieval, ranking, token optimization."""

    MAX_TOKENS = 3000
    CHUNKS_PER_QUERY = 5

    def __init__(self) -> None:
        self.repository = DocumentRepository()

    async def get_relevant_chunks(
        self, document_id: str, user_id: str, query: str, max_tokens: int | None = None
    ) -> list[dict[str, Any]]:
        chunks = await self.repository.get_chunks(document_id, user_id)
        if not chunks:
            return []

        scored = self._rank_chunks(chunks, query)
        selected = self._select_chunks(scored, max_tokens or self.MAX_TOKENS)

        return selected

    def _rank_chunks(self, chunks: list[dict[str, Any]], query: str) -> list[dict[str, Any]]:
        query_lower = query.lower()
        query_words = set(query_lower.split())

        scored: list[dict[str, Any]] = []
        for chunk in chunks:
            score = 0
            content_lower = chunk.get("content", "").lower()

            # keyword overlap
            content_words = set(content_lower.split())
            overlap = len(query_words & content_words)
            score += overlap * 2

            # heading match
            heading = chunk.get("heading", "")
            if heading and any(w in heading.lower() for w in query_words):
                score += 10

            # exact phrase
            if query_lower in content_lower:
                score += 20

            scored.append({**chunk, "_score": score})

        scored.sort(key=lambda c: c["_score"], reverse=True)
        return scored

    def _select_chunks(
        self, chunks: list[dict[str, Any]], max_tokens: int
    ) -> list[dict[str, Any]]:
        selected: list[dict[str, Any]] = []
        total = 0

        for chunk in chunks[: self.CHUNKS_PER_QUERY]:
            tokens = chunk.get("token_count", 0) or len(chunk.get("content", "").split())
            if total + tokens > max_tokens:
                continue
            chunk["_tokens"] = tokens
            selected.append(chunk)
            total += tokens

        return selected

    async def build_context_prompt(
        self, document_id: str, user_id: str, query: str
    ) -> str:
        chunks = await self.get_relevant_chunks(document_id, user_id, query)

        if not chunks:
            doc = await self.repository.get_document(document_id, user_id)
            name = doc.get("original_name", "document") if doc else "document"
            return f"[Analyzing document: {name}. No relevant chunks found for your query.]"

        parts = [f"Document contains {len(chunks)} relevant section(s):\n"]
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

        return "\n".join(parts)
