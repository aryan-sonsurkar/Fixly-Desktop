"""Tool Executor for Fixly AI.

Executes tools with authorization checks, rollback support, and audit trail.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable

from app.core.logging import get_logger
from app.services.tool_authorizer import (
    AuditEntry,
    ToolAuthorizer,
)
from app.services.tool_registry import ToolRegistry

logger = get_logger(__name__)


@dataclass
class ToolResult:
    success: bool
    tool_name: str
    result: Any = None
    error: str | None = None
    audit_entry: AuditEntry | None = None
    execution_time_ms: float = 0
    rollback_data: Any = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "tool_name": self.tool_name,
            "result": self.result,
            "error": self.error,
            "execution_time_ms": self.execution_time_ms,
            "rollback_data": self.rollback_data,
        }


class ToolExecutor:
    """Executes tools with authorization, rollback, and audit."""

    def __init__(self) -> None:
        self.registry = ToolRegistry.get_instance()
        self.authorizer = ToolAuthorizer()
        self._handlers: dict[str, Callable[..., Any]] = {}

    def register_handler(
        self, tool_name: str, handler: Callable[..., Any]
    ) -> None:
        """Register a handler function for a tool."""
        self._handlers[tool_name] = handler

    def execute(
        self,
        tool_name: str,
        user_id: str,
        parameters: dict[str, Any],
    ) -> ToolResult:
        """Execute a tool with authorization check and audit."""
        auth_result = self.authorizer.check_authorization(
            tool_name, user_id, parameters
        )

        if not auth_result.allowed:
            audit = self.authorizer.record_execution(
                user_id, tool_name, parameters,
                auth_result.classification, "denied", auth_result.reason,
            )
            return ToolResult(
                success=False,
                tool_name=tool_name,
                error=f"Authorization denied: {auth_result.reason}",
                audit_entry=audit,
            )

        if auth_result.requires_confirmation:
            return ToolResult(
                success=False,
                tool_name=tool_name,
                error="confirmation_required",
                audit_entry=self.authorizer.record_execution(
                    user_id, tool_name, parameters,
                    auth_result.classification, "awaiting_confirmation",
                ),
            )

        handler = self._handlers.get(tool_name)
        if handler is None:
            return ToolResult(
                success=False,
                tool_name=tool_name,
                error="no_handler_registered",
                audit_entry=self.authorizer.record_execution(
                    user_id, tool_name, parameters,
                    auth_result.classification, "failed", "no_handler",
                ),
            )

        start = time.time()
        try:
            result = handler(user_id, parameters)
            elapsed = (time.time() - start) * 1000

            audit = self.authorizer.record_execution(
                user_id, tool_name, parameters,
                auth_result.classification, "executed",
            )
            return ToolResult(
                success=True,
                tool_name=tool_name,
                result=result,
                audit_entry=audit,
                execution_time_ms=elapsed,
            )
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            logger.error("Tool execution failed: %s - %s", tool_name, e)
            return ToolResult(
                success=False,
                tool_name=tool_name,
                error=str(e),
                execution_time_ms=elapsed,
                audit_entry=self.authorizer.record_execution(
                    user_id, tool_name, parameters,
                    auth_result.classification, "failed", str(e),
                ),
            )

    def rollback(self, audit_id: str, user_id: str) -> ToolResult:
        """Attempt to rollback a previous tool execution."""
        entries = self.authorizer.get_audit_log(user_id)
        target = next((e for e in entries if e["id"] == audit_id), None)
        if target is None:
            return ToolResult(success=False, tool_name="rollback", error="audit_entry_not_found")
        if not target.get("rollback_available"):
            return ToolResult(success=False, tool_name="rollback", error="rollback_not_available")
        return ToolResult(success=True, tool_name="rollback", result="rollback_noted")

    def get_available_tools(self, intent: str | None = None) -> list[dict[str, Any]]:
        if intent:
            tool_names = self.authorizer.get_tool_suggestions(intent)
            tools = [self.registry.get(n) for n in tool_names if self.registry.get(n)]
            return [t.to_dict() for t in tools]
        return self.registry.list_all()
