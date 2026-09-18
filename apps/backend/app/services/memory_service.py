"""Persistent AI Memory Service for Fixly.

Handles memory extraction, deduplication, confidence assignment,
reinforcement, contradiction, decay, archival, and retrieval.

Memory categories: fact, preference, habit, weakness, strength, goal, document.
"""

from __future__ import annotations

import time
import uuid
from typing import Any

from app.core.logging import get_logger
from app.services.embedding_service import EmbeddingService
from app.services.memory_store import MemoryStore

logger = get_logger(__name__)

# ── Category rules ──

VALID_CATEGORIES = {"fact", "preference", "habit", "weakness", "strength", "goal", "document"}

# Categories that decay
DECAY_CATEGORIES = {"preference", "habit"}

# Initial confidence by source type
INITIAL_CONFIDENCE = {
    "explicit": 0.8,
    "inferred": 0.4,
    "behavioral": 0.3,
    "document": 0.6,
    "conversation": 0.5,
}

# Decay parameters
DECAY_RATE = 0.05  # per 14 days
DECAY_FLOOR = 0.2
DECAY_INTERVAL_DAYS = 14

# Deduplication threshold
DEDUP_SIMILARITY_THRESHOLD = 0.85


class MemoryService:
    """Manages persistent AI memory for a user."""

    def __init__(self, db_path: str | None = None) -> None:
        self.store = MemoryStore(db_path)
        self.embedding_service = EmbeddingService()

    def close(self) -> None:
        self.store.close()

    # ── Extraction ──

    def extract_memories(
        self,
        user_id: str,
        text: str,
        source: str = "conversation",
        source_conversation_id: str | None = None,
        source_document_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Extract candidate memories from text.

        Uses rule-based extraction (no LLM dependency for core extraction).
        Returns list of memory dicts with confidence scores.
        """
        candidates = []

        # Rule-based extraction patterns
        patterns = [
            # Preferences
            (r"(?:I prefer|I like|I want|I need|I use)\s+(.+)", "preference", "explicit"),
            (r"(?:I don't like|I hate|I avoid|I never)\s+(.+)", "preference", "explicit"),
            (r"(?:my favorite|my preferred)\s+(.+)", "preference", "inferred"),
            # Habits
            (r"(?:I always|I usually|I typically|I normally)\s+(.+)", "habit", "behavioral"),
            (r"(?:I study|I work|I focus)\s+(?:at|during)\s+(.+)", "habit", "behavioral"),
            # Weaknesses
            (r"(?:I struggle with|I find (?:it )?hard|I don't understand|I am weak in)\s+(.+)", "weakness", "explicit"),
            (r"(?:I (?:keep )?(?:forget|miss|fail))\s+(.+)", "weakness", "behavioral"),
            # Strengths
            (r"(?:I am good at|I excel at|I understand|I know well)\s+(.+)", "strength", "explicit"),
            (r"(?:I have experience with|I have worked with)\s+(.+)", "strength", "inferred"),
            # Goals
            (r"(?:I want to|I plan to|I aim to|my goal is to)\s+(.+)", "goal", "explicit"),
            (r"(?:I need to (?:learn|master|complete|finish))\s+(.+)", "goal", "inferred"),
            # Facts
            (r"(?:I am|I'm) (?:a |an )?(.+?)(?:\.|$)", "fact", "inferred"),
            (r"(?:I study|I am studying|I'm studying)\s+(.+)", "fact", "inferred"),
            (r"(?:I attend|I go to)\s+(.+)", "fact", "inferred"),
            (r"(?:my (?:branch|major|subject) is)\s+(.+)", "fact", "explicit"),
        ]

        import re
        text_lower = text.lower()
        for pattern, category, source_type in patterns:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                content = match.group(0).strip()
                if len(content) < 5:
                    continue
                confidence = INITIAL_CONFIDENCE.get(source_type, 0.4)
                candidates.append({
                    "content": content,
                    "category": category,
                    "source": source_type if source_type in INITIAL_CONFIDENCE else source,
                    "confidence": confidence,
                    "source_conversation_id": source_conversation_id,
                    "source_document_id": source_document_id,
                })

        # Deduplicate candidates
        deduped = self._deduplicate_candidates(candidates)
        return deduped

    def _deduplicate_candidates(self, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Remove duplicate candidates within the same extraction batch."""
        seen = set()
        result = []
        for c in candidates:
            key = (c["category"], c["content"][:50].lower())
            if key not in seen:
                seen.add(key)
                result.append(c)
        return result

    # ── Memory CRUD ──

    def add_memory(
        self,
        user_id: str,
        content: str,
        category: str,
        source: str = "inferred",
        confidence: float | None = None,
        source_document_id: str | None = None,
        source_conversation_id: str | None = None,
    ) -> dict[str, Any]:
        """Add a memory, performing deduplication against existing memories."""
        if category not in VALID_CATEGORIES:
            raise ValueError(f"Invalid category: {category}. Must be one of {VALID_CATEGORIES}")

        if confidence is None:
            confidence = INITIAL_CONFIDENCE.get(source, 0.4)

        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        # Check for existing similar memory
        existing = self._find_similar(user_id, content, category)
        if existing:
            # Reinforce existing memory
            new_confidence = min(1.0, existing["confidence"] + 0.1)
            self.store.update_memory(existing["id"], user_id, {
                "confidence": new_confidence,
                "last_reinforced_at": now,
            })
            logger.info("Reinforced memory %s (confidence: %.2f)", existing["id"], new_confidence)
            return self.store.get_memory(existing["id"], user_id)

        # Check for contradicting memory
        contradiction = self._find_contradiction(user_id, content, category)
        if contradiction:
            new_confidence = max(0.0, contradiction["confidence"] - 0.2)
            if new_confidence < 0.2:
                self.store.update_memory(contradiction["id"], user_id, {"is_archived": True})
                logger.info("Archived contradicting memory %s", contradiction["id"])
            else:
                self.store.update_memory(contradiction["id"], user_id, {"confidence": new_confidence})
                logger.info(
                    "Reduced confidence of contradicting memory %s to %.2f",
                    contradiction["id"],
                    new_confidence,
                )

        # Create new memory
        memory_id = f"mem_{uuid.uuid4().hex[:12]}"
        memory = {
            "id": memory_id,
            "user_id": user_id,
            "category": category,
            "content": content,
            "confidence": confidence,
            "source": source,
            "source_document_id": source_document_id,
            "source_conversation_id": source_conversation_id,
            "created_at": now,
            "updated_at": now,
            "last_reinforced_at": now,
            "is_archived": False,
            "metadata": "{}",
        }
        self.store.insert_memory(memory)

        # Store embedding for semantic retrieval
        if self.embedding_service.is_available():
            try:
                embedding = self.embedding_service.embed_text(content)
                self.store.store_embedding(memory_id, user_id, embedding)
            except Exception as e:
                logger.warning("Failed to embed memory %s: %s", memory_id, e)

        return memory

    def _find_similar(self, user_id: str, content: str, category: str) -> dict[str, Any] | None:
        """Find existing memory with high similarity."""
        if not self.embedding_service.is_available():
            return None
        try:
            query_emb = self.embedding_service.embed_text(content)
            existing = self.store.get_all_embeddings(user_id)
            best_sim = 0.0
            best_match = None
            for item in existing:
                if item["category"] != category:
                    continue
                sim = self._cosine_similarity(query_emb, item["embedding"])
                if sim > best_sim:
                    best_sim = sim
                    best_match = item
            if best_sim > DEDUP_SIMILARITY_THRESHOLD and best_match:
                return self.store.get_memory(best_match["memory_id"], user_id)
        except Exception as e:
            logger.warning("Similarity search failed: %s", e)
        return None

    def _find_contradiction(self, user_id: str, content: str, category: str) -> dict[str, Any] | None:
        """Find memory that contradicts the new content."""
        negation_pairs = [
            ("like", "don't like"), ("prefer", "avoid"),
            ("good at", "struggle with"), ("always", "never"),
            ("understand", "don't understand"), ("want to", "don't want to"),
        ]
        content_lower = content.lower()
        existing = self.store.list_memories(user_id, category=category)
        for mem in existing:
            mem_lower = mem["content"].lower()
            for pos, neg in negation_pairs:
                if (pos in content_lower and neg in mem_lower) or (neg in content_lower and pos in mem_lower):
                    return mem
        return None

    def get_memory(self, user_id: str, memory_id: str) -> dict[str, Any] | None:
        return self.store.get_memory(memory_id, user_id)

    def list_memories(
        self,
        user_id: str,
        category: str | None = None,
        include_archived: bool = False,
        min_confidence: float = 0.0,
    ) -> list[dict[str, Any]]:
        return self.store.list_memories(user_id, category, include_archived, min_confidence)

    def update_memory(self, user_id: str, memory_id: str, updates: dict[str, Any]) -> bool:
        return self.store.update_memory(memory_id, user_id, updates)

    def delete_memory(self, user_id: str, memory_id: str) -> bool:
        self.store.delete_embedding(memory_id)
        return self.store.delete_memory(memory_id, user_id)

    def archive_memory(self, user_id: str, memory_id: str) -> bool:
        return self.store.update_memory(memory_id, user_id, {"is_archived": True})

    def unarchive_memory(self, user_id: str, memory_id: str) -> bool:
        return self.store.update_memory(memory_id, user_id, {"is_archived": False})

    def clear_all_memories(self, user_id: str) -> int:
        return self.store.delete_by_user(user_id)

    def count_by_user(self, user_id: str) -> int:
        return self.store.count_by_user(user_id)

    # ── Retrieval ──

    def retrieve_relevant(
        self,
        user_id: str,
        query: str,
        top_k: int = 10,
        min_confidence: float = 0.3,
        category: str | None = None,
    ) -> list[dict[str, Any]]:
        """Retrieve memories relevant to a query via semantic search."""
        if not self.embedding_service.is_available():
            return self.store.list_memories(user_id, category=category, min_confidence=min_confidence)[:top_k]

        try:
            query_emb = self.embedding_service.embed_text(query)
            all_embs = self.store.get_all_embeddings(user_id)
            scored = []
            for item in all_embs:
                if item["confidence"] < min_confidence:
                    continue
                if category and item["category"] != category:
                    continue
                sim = self._cosine_similarity(query_emb, item["embedding"])
                scored.append((sim, item))
            scored.sort(key=lambda x: x[0], reverse=True)
            results = []
            for sim, item in scored[:top_k]:
                mem = self.store.get_memory(item["memory_id"], user_id)
                if mem:
                    mem["_relevance_score"] = sim
                    results.append(mem)
            return results
        except Exception as e:
            logger.warning("Memory retrieval failed: %s", e)
            return self.store.list_memories(user_id, category=category, min_confidence=min_confidence)[:top_k]

    # ── Decay ──

    def apply_decay(self, user_id: str) -> int:
        """Apply time-based decay to preference and habit memories.

        Returns number of memories archived due to decay.
        """
        archived = 0
        now = time.time()
        memories = self.store.list_memories(user_id, include_archived=False)
        for mem in memories:
            if mem["category"] not in DECAY_CATEGORIES:
                continue
            last_reinforced = mem.get("last_reinforced_at") or mem.get("updated_at")
            if not last_reinforced:
                continue
            try:
                from datetime import datetime
                last_ts = datetime.fromisoformat(last_reinforced.replace("Z", "+00:00")).timestamp()
            except (ValueError, AttributeError):
                continue
            days_since = (now - last_ts) / 86400
            intervals = days_since / DECAY_INTERVAL_DAYS
            decay_amount = intervals * DECAY_RATE
            new_confidence = max(DECAY_FLOOR, mem["confidence"] - decay_amount)
            if new_confidence <= DECAY_FLOOR and mem["confidence"] > DECAY_FLOOR:
                self.store.update_memory(mem["id"], user_id, {"is_archived": True})
                archived += 1
                logger.info("Archived memory %s due to decay (was %.2f)", mem["id"], mem["confidence"])
            elif new_confidence != mem["confidence"]:
                self.store.update_memory(mem["id"], user_id, {"confidence": new_confidence})
        return archived

    def run_memory_decay_all_users(self) -> dict[str, int]:
        """Run decay on all users. Returns dict of user_id -> archived count."""
        user_ids = self.store.get_all_user_ids()
        results: dict[str, int] = {}
        for uid in user_ids:
            try:
                count = self.apply_decay(uid)
                if count > 0:
                    results[uid] = count
            except Exception as e:
                logger.warning("Decay failed for user %s: %s", uid, e)
        logger.info("Memory decay completed for %d users, archived %d total memories",
                     len(user_ids), sum(results.values()))
        return results

    # ── Document deletion cascade ──

    def delete_document_memories(self, user_id: str, document_id: str) -> int:
        """Delete all document-derived memories for a specific document."""
        return self.store.delete_by_document(user_id, document_id)

    # ── Context injection ──

    def build_memory_context(
        self,
        user_id: str,
        query: str,
        top_k: int = 10,
        max_tokens: int = 500,
    ) -> str:
        """Build a memory context string for injection into AI prompts."""
        memories = self.retrieve_relevant(user_id, query, top_k=top_k, min_confidence=0.3)
        if not memories:
            return ""
        parts = ["[Student Memory]\n"]
        for mem in memories:
            cat = mem["category"]
            conf = mem["confidence"]
            content = mem["content"]
            parts.append(f"- [{cat}] (confidence: {conf:.1f}) {content}")
        context = "\n".join(parts)
        # Rough token estimate
        estimated_tokens = len(context.split())
        if estimated_tokens > max_tokens:
            truncated = parts[:top_k]
            context = "\n".join(truncated)
        return context

    # ── Helpers ──

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        if len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)
