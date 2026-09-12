"""Deterministic Intent Classifier for Fixly AI.

Classifies user requests into internal intents using rule-based routing.
No LLM dependency — deterministic, fast, auditable.

Intents:
- simple_chat: general conversation
- document_query: ask about uploaded documents
- workspace_query: ask about assignments, planner, schedule
- assignment_solve: solve/answer assignment questions
- tutoring: explain concepts, teach
- planning: create study plans, schedules
- web_research: needs current external information
- opportunity: career/internship related
- autonomous_workflow: multi-step task requiring tool orchestration
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Any


class Intent(str, Enum):
    SIMPLE_CHAT = "simple_chat"
    DOCUMENT_QUERY = "document_query"
    WORKSPACE_QUERY = "workspace_query"
    ASSIGNMENT_SOLVE = "assignment_solve"
    TUTORING = "tutoring"
    PLANNING = "planning"
    WEB_RESEARCH = "web_research"
    OPPORTUNITY = "opportunity"
    AUTONOMOUS_WORKFLOW = "autonomous_workflow"


class IntentClassifier:
    """Rule-based intent classifier.

    Deterministic: same input always produces same intent.
    Auditable: returns match details for debugging.
    Extensible: patterns can be added without changing logic.
    """

    def __init__(self) -> None:
        self._rules = self._build_rules()

    def classify(self, text: str, has_documents: bool = False) -> dict[str, Any]:
        """Classify user text into an intent.

        Args:
            text: User message text.
            has_documents: Whether the user has uploaded documents.

        Returns:
            {
                "intent": Intent,
                "confidence": float,
                "reason": str,
            }
        """
        text_lower = text.lower().strip()

        for rule in self._rules:
            match = rule["pattern"].search(text_lower)
            if match:
                return {
                    "intent": rule["intent"],
                    "confidence": rule["confidence"],
                    "reason": rule["reason"],
                    "matched": match.group(),
                }

        # Fallback: document-aware default
        if has_documents:
            return {
                "intent": Intent.TUTORING,
                "confidence": 0.4,
                "reason": "fallback_with_documents",
            }

        return {
            "intent": Intent.SIMPLE_CHAT,
            "confidence": 0.5,
            "reason": "fallback_general",
        }

    def _build_rules(self) -> list[dict[str, Any]]:
        return [
            # ── Autonomous workflow (multi-step) ──
            {
                "pattern": re.compile(
                    r"(?:read|find|search|create|schedule|then|after that|and then|also|add|make).*(?:then|after|and then|also).*(?:create|schedule|add|make|find|search)",
                ),
                "intent": Intent.AUTONOMOUS_WORKFLOW,
                "confidence": 0.8,
                "reason": "multi_step_indicators",
            },
            # ── Document query ──
            {
                "pattern": re.compile(
                    r"(?:what does (?:my|the) (?:note|document|pdf|file|upload) say|"
                    r"according to (?:my|the) (?:note|document|pdf|file|upload)|"
                    r"in (?:my|the) (?:note|document|pdf|file|upload)|"
                    r"from (?:my|the) (?:note|document|pdf|file|upload)|"
                    r"what did (?:my|the) (?:note|document|pdf) (?:say|mention|cover)|"
                    r"based on (?:my|the) (?:note|document|pdf)|"
                    r"extract from (?:my|the) (?:note|document|pdf))",
                ),
                "intent": Intent.DOCUMENT_QUERY,
                "confidence": 0.9,
                "reason": "document_reference",
            },
            # ── Assignment solve ──
            {
                "pattern": re.compile(
                    r"(?:solve|answer|help me (?:with|solve)|write (?:code|answer|solution)|"
                    r"(?:my|the) assignment (?:question|problem|exercise)|"
                    r"(?:implement|code|write).*(?:algorithm|program|function|code)|"
                    r"assignment.*(?:solution|answer|help))",
                ),
                "intent": Intent.ASSIGNMENT_SOLVE,
                "confidence": 0.85,
                "reason": "assignment_solve_request",
            },
            # ── Planning ──
            {
                "pattern": re.compile(
                    r"(?:create (?:a )?(?:study )?plan|"
                    r"(?:study|revision|exam) plan|"
                    r"(?:plan|schedule| timetable|routine) (?:my|for)|"
                    r"(?:how should|what should) (?:I|we) (?:study|prepare|review)|"
                    r"(?:weekly|daily|monthly) (?:plan|schedule))",
                ),
                "intent": Intent.PLANNING,
                "confidence": 0.85,
                "reason": "planning_request",
            },
            # ── Workspace query ──
            {
                "pattern": re.compile(
                    r"(?:(?:what|which) (?:are|is|do|does) (?:i |my |the )?(?:have |know )?(?:about )?(?:assignment|deadline|task|subject|schedule)s?|"
                    r"(?:what|which) (?:assignment|deadline|task|subject|schedule)s? (?:are|is|do|does) (?:i |my |the )?(?:have|know|due)|"
                    r"(?:show|list|check|tell me about) (?:my|the) (?:assignment|deadline|task|subject|planner|schedule|pomodoro)|"
                    r"(?:upcoming|pending|overdue|due) (?:assignment|deadline|task)|"
                    r"how (?:many|much).*(?:assignment|task|subject|point))",
                ),
                "intent": Intent.WORKSPACE_QUERY,
                "confidence": 0.85,
                "reason": "workspace_reference",
            },
            # ── Opportunity / career ──
            {
                "pattern": re.compile(
                    r"(?:internship|job|career|opportunity|opportunity|position|role|"
                    r"find (?:me )?(?:internship|job|opportunity)|"
                    r"save (?:this|that) (?:internship|job|opportunity)|"
                    r"(?:prepare|get ready) for (?:interview|internship|job|opportunity)|"
                    r"(?:roadmap|learning path|career path))",
                ),
                "intent": Intent.OPPORTUNITY,
                "confidence": 0.8,
                "reason": "career_opportunity",
            },
            # ── Web research ──
            {
                "pattern": re.compile(
                    r"(?:latest|current|recent|newest|today|now|this year|202[0-9]|"
                    r"what(?:'s| is) (?:the )?(?:latest|current|newest)|"
                    r"search (?:the )?(?:web|online|internet)|"
                    r"look up|find online|research|"
                    r"(?:compare|versus|vs).*(?:202[0-9]|latest|current))",
                ),
                "intent": Intent.WEB_RESEARCH,
                "confidence": 0.75,
                "reason": "web_research_need",
            },
            # ── Tutoring (explain, teach) ──
            {
                "pattern": re.compile(
                    r"(?:explain|teach|what is|what are|how does|how do|"
                    r"can you explain|help me understand|"
                    r"what (?:is|are) (?:a |an |the )?"
                    r"(?:normalisation|normalization|binary|recursion|pointer|"
                    r"thread|process|deadlock|virtual memory|hash|tree|graph|"
                    r"queue|stack|heap|sort|search|network|protocol|osi|tcp|udp|"
                    r"ip|dns|http|html|css|javascript|python|java|sql|database|"
                    r"algorithm|complexity|big.o))",
                ),
                "intent": Intent.TUTORING,
                "confidence": 0.8,
                "reason": "tutoring_explain",
            },
        ]
