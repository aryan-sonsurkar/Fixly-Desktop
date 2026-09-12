"""Source Authority Resolution for Fixly AI.

Determines which information sources are authoritative based on
question type. No single universal hierarchy — authority depends
on what the student is asking.
"""

from __future__ import annotations

from enum import Enum
from typing import Any


class SourceType(str, Enum):
    DOCUMENTS = "documents"
    WORKSPACE = "workspace"
    WEB = "web"
    MODEL = "model"
    MEMORY = "memory"


class SourceAuthority:
    """Resolves source priority based on question type.

    Each question type has a ranked list of authoritative sources.
    The first source in the list is primary.
    """

    # Question type → ordered source priority (first = primary)
    AUTHORITY_MAP: dict[str, list[SourceType]] = {
        # "What does my note say?" → documents primary
        "document_question": [
            SourceType.DOCUMENTS,
            SourceType.MODEL,
            SourceType.WORKSPACE,
        ],
        # "What assignments do I have?" → workspace primary
        "workspace_question": [
            SourceType.WORKSPACE,
            SourceType.MEMORY,
            SourceType.MODEL,
        ],
        # "What's the latest Next.js version?" → web primary
        "current_information": [
            SourceType.WEB,
            SourceType.MODEL,
        ],
        # "Explain this concept" → documents + model
        "concept_explanation": [
            SourceType.DOCUMENTS,
            SourceType.MODEL,
            SourceType.MEMORY,
        ],
        # "Find internships" → goals + web
        "opportunity_search": [
            SourceType.MEMORY,
            SourceType.WEB,
            SourceType.WORKSPACE,
        ],
        # "How should I study today?" → workspace + memory
        "study_guidance": [
            SourceType.WORKSPACE,
            SourceType.MEMORY,
            SourceType.MODEL,
        ],
        # General conversation
        "general": [
            SourceType.MODEL,
            SourceType.MEMORY,
        ],
    }

    @classmethod
    def resolve(cls, question_type: str) -> list[SourceType]:
        """Get ordered source priority for a question type."""
        return cls.AUTHORITY_MAP.get(question_type, cls.AUTHORITY_MAP["general"])

    @classmethod
    def get_primary(cls, question_type: str) -> SourceType:
        """Get the primary (most authoritative) source."""
        sources = cls.resolve(question_type)
        return sources[0] if sources else SourceType.MODEL

    @classmethod
    def classify_question_type(cls, intent: str, text: str) -> str:
        """Map an intent + text to a question type for source resolution."""
        text_lower = text.lower()

        if intent == "document_query":
            return "document_question"
        if intent == "workspace_query":
            return "workspace_question"
        if intent == "web_research":
            return "current_information"
        if intent == "opportunity":
            return "opportunity_search"
        if intent == "planning":
            return "study_guidance"
        if intent == "tutoring":
            if any(w in text_lower for w in ("my note", "my document", "my pdf", "uploaded")):
                return "document_question"
            return "concept_explanation"
        if intent == "assignment_solve":
            if any(w in text_lower for w in ("my note", "my document", "from my")):
                return "document_question"
            return "concept_explanation"

        return "general"

    @classmethod
    def detect_source_conflict(
        cls,
        source_a: dict[str, Any],
        source_b: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Detect when two sources provide conflicting information.

        Returns conflict details or None if no conflict detected.
        """
        content_a = source_a.get("content", "").lower()
        content_b = source_b.get("content", "").lower()

        # Simple conflict detection: check for negation patterns
        negation_pairs = [
            ("is", "is not"), ("can", "cannot"), ("will", "will not"),
            ("does", "does not"), ("has", "has not"), ("true", "false"),
        ]
        for pos, neg in negation_pairs:
            if (pos in content_a and neg in content_b) or (neg in content_a and pos in content_b):
                return {
                    "conflict": True,
                    "source_a": source_a.get("source_type", "unknown"),
                    "source_b": source_b.get("source_type", "unknown"),
                    "type": "negation",
                }

        return None

    @classmethod
    def select_best_source(
        cls,
        sources: list[dict[str, Any]],
        question_type: str,
    ) -> dict[str, Any]:
        """Select the best source from available sources based on authority.

        Considers:
        1. Source authority rank
        2. Freshness (newer is better)
        3. Specificity (more specific is better)
        """
        if not sources:
            return {}

        priority = cls.resolve(question_type)
        priority_map = {s.value: i for i, s in enumerate(priority)}

        def source_rank(source: dict[str, Any]) -> tuple[int, float, float]:
            st = source.get("source_type", "model")
            rank = priority_map.get(st, 99)
            freshness = source.get("freshness", 0.5)
            specificity = source.get("specificity", 0.5)
            return (rank, -freshness, -specificity)

        return min(sources, key=source_rank)
