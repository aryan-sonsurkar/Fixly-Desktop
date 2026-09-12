"""Conversation Summarization Service for Fixly.

Provides bounded conversation context by summarizing older messages
when conversation history exceeds the configured threshold.
"""

from __future__ import annotations

import time
import uuid
from typing import Any

from app.core.logging import get_logger
from app.services.memory_store import MemoryStore

logger = get_logger(__name__)

# Thresholds
HISTORY_THRESHOLD = 20  # messages before summarization triggers
SUMMARY_MAX_TOKENS = 200  # rough estimate for summary length
RETAIN_RECENT = 10  # always keep last N messages


class SummarizationService:
    """Manages conversation summarization for bounded context."""

    def __init__(self, memory_store: MemoryStore | None = None) -> None:
        self.store = memory_store or MemoryStore()

    async def maybe_summarize(
        self,
        user_id: str,
        conversation_id: str,
        messages: list[dict[str, str]],
    ) -> dict[str, Any]:
        """Check if summarization is needed and perform it.

        Returns:
            {
                "summarized": bool,
                "summary": str | None,
                "messages_retained": int,
                "messages_summarized": int,
            }
        """
        if len(messages) <= HISTORY_THRESHOLD:
            return {
                "summarized": False,
                "summary": None,
                "messages_retained": len(messages),
                "messages_summarized": 0,
            }

        # Find existing summary range
        existing = self.store.get_summaries(user_id, conversation_id)
        already_summarized = sum(s["message_range_end"] - s["message_range_start"] for s in existing)

        # Messages to summarize: everything except recent N
        summarize_end = len(messages) - RETAIN_RECENT
        if summarize_end <= already_summarized:
            return {
                "summarized": False,
                "summary": None,
                "messages_retained": len(messages),
                "messages_summarized": already_summarized,
            }

        # Get messages to summarize (from after last summary to current cutoff)
        start_idx = already_summarized
        to_summarize = messages[start_idx:summarize_end]

        if not to_summarize:
            return {
                "summarized": False,
                "summary": None,
                "messages_retained": len(messages),
                "messages_summarized": already_summarized,
            }

        # Build summary text from message content
        summary_parts = []
        for msg in to_summarize:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if content:
                summary_parts.append(f"{role}: {content[:200]}")

        summary_text = "Previous conversation:\n" + "\n".join(summary_parts)

        # Persist summary
        summary_id = f"sum_{uuid.uuid4().hex[:12]}"
        summary_record = {
            "id": summary_id,
            "user_id": user_id,
            "conversation_id": conversation_id,
            "summary": summary_text,
            "message_range_start": start_idx,
            "message_range_end": summarize_end,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        self.store.insert_summary(summary_record)

        logger.info(
            "Summarized %d messages for conversation %s",
            len(to_summarize),
            conversation_id,
        )

        return {
            "summarized": True,
            "summary": summary_text,
            "messages_retained": RETAIN_RECENT + (len(messages) - summarize_end),
            "messages_summarized": summarize_end,
        }

    def get_summaries(
        self, user_id: str, conversation_id: str
    ) -> list[dict[str, Any]]:
        """Get all summaries for a conversation."""
        return self.store.get_summaries(user_id, conversation_id)

    def build_summary_context(
        self, user_id: str, conversation_id: str, max_tokens: int = 300
    ) -> str:
        """Build a summary context string for injection into AI prompts."""
        summaries = self.get_summaries(user_id, conversation_id)
        if not summaries:
            return ""
        # Combine summaries (most recent last)
        parts = []
        for s in summaries:
            parts.append(s["summary"])
        context = "\n\n".join(parts)
        # Rough truncation
        words = context.split()
        if len(words) > max_tokens:
            context = " ".join(words[:max_tokens]) + "..."
        return context
