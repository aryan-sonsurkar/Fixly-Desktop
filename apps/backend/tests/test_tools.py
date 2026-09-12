"""Tests for Phase 4: Tool Layer + Authorization + Audit."""

from __future__ import annotations

import pytest

from app.services.tool_authorizer import (
    SafetyClassification,
    ToolAuthorizer,
)
from app.services.tool_executor import ToolExecutor, ToolResult
from app.services.tool_registry import AuthLevel, ToolCategory, ToolDefinition, ToolRegistry


# ── Tool Registry Tests ──────────────────────────────────────────────


class TestToolRegistry:
    """Tests for the tool registry."""

    def setup_method(self):
        ToolRegistry.reset()
        self.registry = ToolRegistry.get_instance()

    def test_singleton(self):
        r1 = ToolRegistry.get_instance()
        r2 = ToolRegistry.get_instance()
        assert r1 is r2

    def test_defaults_registered(self):
        tools = self.registry.list_tools()
        assert len(tools) >= 20

    def test_get_tool(self):
        tool = self.registry.get("read_pdf")
        assert tool is not None
        assert tool.name == "read_pdf"
        assert tool.category == ToolCategory.READING
        assert tool.auth_level == AuthLevel.AUTO

    def test_list_by_category(self):
        reading = self.registry.list_tools(ToolCategory.READING)
        assert len(reading) >= 3
        assert all(t.category == ToolCategory.READING for t in reading)

    def test_destructive_tools(self):
        destructive = self.registry.list_tools(ToolCategory.DESTRUCTIVE)
        assert len(destructive) >= 2
        assert all(t.auth_level == AuthLevel.CONFIRMATION for t in destructive)

    def test_confirmation_required_tools(self):
        confirmation_tools = [t for t in self.registry.list_tools() if t.auth_level == AuthLevel.CONFIRMATION]
        assert len(confirmation_tools) >= 10

    def test_to_dict(self):
        tool = self.registry.get("web_search")
        d = tool.to_dict()
        assert d["name"] == "web_search"
        assert d["category"] == "web"
        assert d["auth_level"] == "confirmation_required"

    def test_custom_registration(self):
        self.registry.register(ToolDefinition(
            name="custom_tool",
            description="A custom tool",
            category=ToolCategory.SYSTEM,
            auth_level=AuthLevel.AUTO,
        ))
        tool = self.registry.get("custom_tool")
        assert tool is not None

    def test_list_all(self):
        all_tools = self.registry.list_all()
        assert len(all_tools) >= 20
        assert all(isinstance(t, dict) for t in all_tools)


# ── Tool Authorizer Tests ────────────────────────────────────────────


class TestToolAuthorizer:
    """Tests for authorization and audit."""

    def setup_method(self):
        ToolRegistry.reset()
        self.authorizer = ToolAuthorizer()

    def test_auto_approve_safe_tool(self):
        result = self.authorizer.check_authorization(
            "read_pdf", "user1", {"document_id": "doc1"}
        )
        assert result.allowed is True
        assert result.requires_confirmation is False
        assert result.classification == SafetyClassification.SAFE

    def test_confirmation_required_for_writing(self):
        result = self.authorizer.check_authorization(
            "create_assignment", "user1", {"title": "HW1"}
        )
        assert result.allowed is True
        assert result.requires_confirmation is True

    def test_denied_missing_params(self):
        result = self.authorizer.check_authorization(
            "read_pdf", "user1", {}
        )
        assert result.allowed is False
        assert "document_id" in result.reason

    def test_denied_unknown_tool(self):
        result = self.authorizer.check_authorization(
            "nonexistent_tool", "user1", {}
        )
        assert result.allowed is False

    def test_disabled_tool(self):
        self.authorizer.disable_tool("read_pdf")
        result = self.authorizer.check_authorization(
            "read_pdf", "user1", {"document_id": "doc1"}
        )
        assert result.allowed is False
        assert result.reason == "tool_disabled"

    def test_enable_tool(self):
        self.authorizer.disable_tool("read_pdf")
        self.authorizer.enable_tool("read_pdf")
        result = self.authorizer.check_authorization(
            "read_pdf", "user1", {"document_id": "doc1"}
        )
        assert result.allowed is True

    def test_disable_category(self):
        self.authorizer.disable_category(ToolCategory.WEB)
        result = self.authorizer.check_authorization(
            "web_search", "user1", {"query": "test"}
        )
        assert result.allowed is False

    def test_enable_category(self):
        self.authorizer.disable_category(ToolCategory.WEB)
        self.authorizer.enable_category(ToolCategory.WEB)
        result = self.authorizer.check_authorization(
            "web_search", "user1", {"query": "test"}
        )
        assert result.allowed is True

    def test_session_limit(self):
        tool = self.authorizer.registry.get("read_pdf")
        tool.max_per_session = 2
        for _ in range(2):
            self.authorizer.record_execution(
                "user1", "read_pdf", {}, SafetyClassification.SAFE, "executed"
            )
        result = self.authorizer.check_authorization(
            "read_pdf", "user1", {"document_id": "doc1"}
        )
        assert result.allowed is False
        assert "session_limit" in result.reason
        tool.max_per_session = None

    def test_audit_log(self):
        self.authorizer.record_execution(
            "user1", "read_pdf", {"document_id": "doc1"},
            SafetyClassification.SAFE, "executed"
        )
        log = self.authorizer.get_audit_log("user1")
        assert len(log) == 1
        assert log[0]["tool_name"] == "read_pdf"
        assert log[0]["status"] == "executed"

    def test_audit_user_isolation(self):
        self.authorizer.record_execution(
            "user1", "read_pdf", {}, SafetyClassification.SAFE, "executed"
        )
        self.authorizer.record_execution(
            "user2", "read_pdf", {}, SafetyClassification.SAFE, "executed"
        )
        log1 = self.authorizer.get_audit_log("user1")
        log2 = self.authorizer.get_audit_log("user2")
        assert len(log1) == 1
        assert len(log2) == 1

    def test_safety_classification_destructive(self):
        result = self.authorizer.check_authorization(
            "delete_assignment", "user1", {"assignment_id": "a1"}
        )
        assert result.classification == SafetyClassification.DESTRUCTIVE

    def test_confirmation_message(self):
        result = self.authorizer.check_authorization(
            "create_assignment", "user1", {"title": "Test"}
        )
        assert "About to:" in result.confirmation_message

    def test_get_tool_suggestions(self):
        suggestions = self.authorizer.get_tool_suggestions("document_query")
        assert "read_pdf" in suggestions
        assert "search_documents" in suggestions

    def test_empty_suggestions_for_unknown(self):
        suggestions = self.authorizer.get_tool_suggestions("unknown_intent")
        assert suggestions == []

    def test_reset_session_counts(self):
        self.authorizer.record_execution(
            "user1", "read_pdf", {}, SafetyClassification.SAFE, "executed"
        )
        self.authorizer.reset_session_counts("user1")
        assert "user1" not in self.authorizer._session_counts


# ── Tool Executor Tests ──────────────────────────────────────────────


class TestToolExecutor:
    """Tests for tool execution with audit."""

    def setup_method(self):
        ToolRegistry.reset()
        self.executor = ToolExecutor()

    def test_execute_with_handler(self):
        def handler(user_id, params):
            return {"content": "test content"}

        self.executor.register_handler("read_pdf", handler)
        result = self.executor.execute(
            "read_pdf", "user1", {"document_id": "doc1"}
        )
        assert result.success is True
        assert result.result == {"content": "test content"}
        assert result.execution_time_ms >= 0

    def test_execute_without_handler(self):
        result = self.executor.execute(
            "read_pdf", "user1", {"document_id": "doc1"}
        )
        assert result.success is False
        assert "no_handler" in result.error

    def test_execute_denied(self):
        self.executor.authorizer.disable_tool("read_pdf")
        result = self.executor.execute(
            "read_pdf", "user1", {"document_id": "doc1"}
        )
        assert result.success is False
        assert "denied" in result.error

    def test_execute_confirmation_required(self):
        def handler(user_id, params):
            return {"created": True}

        self.executor.register_handler("create_assignment", handler)
        result = self.executor.execute(
            "create_assignment", "user1", {"title": "Test"}
        )
        assert result.success is False
        assert result.error == "confirmation_required"

    def test_execute_handler_error(self):
        def handler(user_id, params):
            raise ValueError("something went wrong")

        self.executor.register_handler("read_pdf", handler)
        result = self.executor.execute(
            "read_pdf", "user1", {"document_id": "doc1"}
        )
        assert result.success is False
        assert "something went wrong" in result.error

    def test_audit_trail_recorded(self):
        def handler(user_id, params):
            return "ok"

        self.executor.register_handler("read_pdf", handler)
        self.executor.execute("read_pdf", "user1", {"document_id": "doc1"})
        log = self.executor.authorizer.get_audit_log("user1")
        assert len(log) == 1
        assert log[0]["status"] == "executed"

    def test_get_available_tools(self):
        tools = self.executor.get_available_tools()
        assert len(tools) >= 20

    def test_get_tools_by_intent(self):
        tools = self.executor.get_available_tools("document_query")
        assert any(t["name"] == "read_pdf" for t in tools)

    def test_rollback_not_available(self):
        result = self.executor.rollback("nonexistent", "user1")
        assert result.success is False

    def test_to_dict_result(self):
        result = ToolResult(
            success=True,
            tool_name="test",
            result="ok",
            execution_time_ms=10.5,
        )
        d = result.to_dict()
        assert d["success"] is True
        assert d["execution_time_ms"] == 10.5
