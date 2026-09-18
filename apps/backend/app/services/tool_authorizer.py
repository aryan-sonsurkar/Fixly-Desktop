"""Tool Authorization and Audit for Fixly AI.

Handles:
- Safety classification (auto-confirm, confirmation_required, disabled)
- Authorization checks before execution
- Audit trail of all tool invocations
- Rollback support for reversible operations
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Any

from app.core.logging import get_logger
from app.services.tool_registry import AuthLevel, ToolCategory, ToolDefinition, ToolRegistry

logger = get_logger(__name__)


class SafetyClassification(str, Enum):
    SAFE = "safe"
    MODERATE = "moderate"
    DESTRUCTIVE = "destructive"
    DISABLED = "disabled"


@dataclass
class AuditEntry:
    id: str
    user_id: str
    tool_name: str
    auth_level: str
    safety_classification: str
    parameters: dict[str, Any]
    status: str  # "authorized", "denied", "executed", "failed", "rolled_back"
    timestamp: float
    error: str | None = None
    rollback_available: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "tool_name": self.tool_name,
            "auth_level": self.auth_level,
            "safety_classification": self.safety_classification,
            "parameters": self.parameters,
            "status": self.status,
            "timestamp": self.timestamp,
            "error": self.error,
            "rollback_available": self.rollback_available,
        }


@dataclass
class AuthorizationResult:
    allowed: bool
    classification: SafetyClassification
    reason: str
    requires_confirmation: bool = False
    confirmation_message: str = ""


class ToolAuthorizer:
    """Handles authorization and audit for tool invocations."""

    def __init__(self) -> None:
        self.registry = ToolRegistry.get_instance()
        self._audit_log: list[AuditEntry] = []
        self._session_counts: dict[str, dict[str, int]] = {}
        self._disabled_tools: set[str] = set()
        self._disabled_categories: set[ToolCategory] = set()

    def check_authorization(
        self,
        tool_name: str,
        user_id: str,
        parameters: dict[str, Any],
    ) -> AuthorizationResult:
        """Check if a tool invocation is authorized.

        Returns AuthorizationResult with allowed status and confirmation details.
        """
        tool = self.registry.get(tool_name)
        if tool is None:
            return AuthorizationResult(
                allowed=False,
                classification=SafetyClassification.DISABLED,
                reason="tool_not_found",
            )

        if tool.name in self._disabled_tools:
            return AuthorizationResult(
                allowed=False,
                classification=SafetyClassification.DISABLED,
                reason="tool_disabled",
            )
        if tool.category in self._disabled_categories:
            return AuthorizationResult(
                allowed=False,
                classification=SafetyClassification.DISABLED,
                reason="category_disabled",
            )

        classification = self._classify_safety(tool)

        if classification == SafetyClassification.DISABLED:
            return AuthorizationResult(
                allowed=False,
                classification=classification,
                reason="safety_disabled",
            )

        required_missing = [p for p in tool.required_params if p not in parameters]
        if required_missing:
            return AuthorizationResult(
                allowed=False,
                classification=classification,
                reason=f"missing_required_params: {', '.join(required_missing)}",
            )

        if tool.max_per_session is not None:
            count = self._session_counts.get(user_id, {}).get(tool_name, 0)
            if count >= tool.max_per_session:
                return AuthorizationResult(
                    allowed=False,
                    classification=classification,
                    reason="session_limit_reached",
                )

        if tool.auth_level == AuthLevel.CONFIRMATION:
            confirmation_msg = self._build_confirmation_message(tool, parameters)
            return AuthorizationResult(
                allowed=True,
                classification=classification,
                reason="confirmation_required",
                requires_confirmation=True,
                confirmation_message=confirmation_msg,
            )

        return AuthorizationResult(
            allowed=True,
            classification=classification,
            reason="auto_approved",
        )

    def record_execution(
        self,
        user_id: str,
        tool_name: str,
        parameters: dict[str, Any],
        classification: SafetyClassification,
        status: str,
        error: str | None = None,
    ) -> AuditEntry:
        """Record a tool execution in the audit log."""
        entry = AuditEntry(
            id=f"audit_{uuid.uuid4().hex[:12]}",
            user_id=user_id,
            tool_name=tool_name,
            auth_level=self.registry.get(tool_name).auth_level.value if self.registry.get(tool_name) else "unknown",
            safety_classification=classification.value,
            parameters=parameters,
            status=status,
            timestamp=time.time(),
            error=error,
            rollback_available=status == "executed" and self._is_reversible(tool_name),
        )
        self._audit_log.append(entry)

        if status == "executed":
            if user_id not in self._session_counts:
                self._session_counts[user_id] = {}
            self._session_counts[user_id][tool_name] = (
                self._session_counts[user_id].get(tool_name, 0) + 1
            )

        logger.info(
            "Tool audit: user=%s tool=%s status=%s class=%s",
            user_id, tool_name, status, classification.value,
        )
        return entry

    def get_audit_log(
        self, user_id: str, limit: int = 50
    ) -> list[dict[str, Any]]:
        """Get audit log entries for a user."""
        entries = [e for e in self._audit_log if e.user_id == user_id]
        entries.sort(key=lambda e: e.timestamp, reverse=True)
        return [e.to_dict() for e in entries[:limit]]

    def disable_tool(self, tool_name: str) -> None:
        self._disabled_tools.add(tool_name)

    def enable_tool(self, tool_name: str) -> None:
        self._disabled_tools.discard(tool_name)

    def disable_category(self, category: ToolCategory) -> None:
        self._disabled_categories.add(category)

    def enable_category(self, category: ToolCategory) -> None:
        self._disabled_categories.discard(category)

    def reset_session_counts(self, user_id: str) -> None:
        self._session_counts.pop(user_id, None)

    def _classify_safety(self, tool: ToolDefinition) -> SafetyClassification:
        if tool.category == ToolCategory.DESTRUCTIVE or not tool.reversible:
            return SafetyClassification.DESTRUCTIVE
        if tool.category in (ToolCategory.WRITING, ToolCategory.COMMUNICATION):
            return SafetyClassification.MODERATE
        return SafetyClassification.SAFE

    def _is_reversible(self, tool_name: str) -> bool:
        tool = self.registry.get(tool_name)
        return tool.reversible if tool else False

    def _build_confirmation_message(
        self, tool: ToolDefinition, parameters: dict[str, Any]
    ) -> str:
        parts = [f"About to: {tool.description}"]
        for k, v in parameters.items():
            parts.append(f"  {k}: {v}")
        if not tool.reversible:
            parts.append("⚠ This action cannot be undone.")
        return "\n".join(parts)

    def get_tool_suggestions(self, intent: str) -> list[str]:
        """Suggest tools based on user intent."""
        suggestions = {
            "document_query": ["read_pdf", "search_documents"],
            "assignment_solve": ["get_assignment", "search_documents"],
            "workspace_query": ["list_assignments", "get_schedule"],
            "tutoring": ["search_documents", "create_flashcards", "create_quiz"],
            "planning": ["create_study_plan", "add_to_planner"],
            "web_research": ["web_search", "fetch_url"],
            "opportunity": ["save_opportunity", "web_search"],
        }
        return suggestions.get(intent, [])
