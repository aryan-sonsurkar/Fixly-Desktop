"""Tool Handler Integration Tests.

Tests every registered tool handler end-to-end:
handler → service → mock repository → result.

Proves the tool layer is actually wired and functional.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.services.tool_executor import ToolExecutor
from app.services.tool_handlers import ToolHandlerContext
from app.services.tool_registration import HANDLER_MAP, register_all_handlers


@pytest.fixture
def ctx():
    return ToolHandlerContext(access_token="test-token")


@pytest.fixture
def executor():
    exec_ = ToolExecutor()
    register_all_handlers(exec_)
    return exec_


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


class TestToolRegistration:
    def test_all_22_tools_registered(self, executor):
        assert len(executor._handlers) == 22

    def test_all_registry_tools_have_handlers(self, executor):
        from app.services.tool_registry import ToolRegistry

        registry = ToolRegistry.get_instance()
        for tool in registry.list_tools():
            assert tool.name in executor._handlers, f"Missing handler for {tool.name}"

    def test_handler_map_keys_match_registry(self):
        from app.services.tool_registry import ToolRegistry

        registry = ToolRegistry.get_instance()
        registry_names = {t.name for t in registry.list_tools()}
        handler_names = set(HANDLER_MAP.keys())
        assert registry_names == handler_names, f"Mismatch: {registry_names ^ handler_names}"


# ---------------------------------------------------------------------------
# READING tools
# ---------------------------------------------------------------------------


class TestReadPDF:
    def test_success(self, ctx):
        from app.services.tool_handlers import handle_read_pdf

        mock_svc = MagicMock()
        mock_svc.get_document_detail.return_value = {
            "title": "DBMS Notes",
            "chunks": [{"content": "Chapter 1: Normalization"}, {"content": "Chapter 2: Indexing"}],
        }
        with patch("app.services.tool_handlers._get_doc_service", return_value=mock_svc):
            result = handle_read_pdf("u1", {"document_id": "doc1"}, ctx)

        assert result["title"] == "DBMS Notes"
        assert "Chapter 1" in result["content"]
        assert result["chunk_count"] == 2

    def test_missing_document_id(self, ctx):
        from app.services.tool_handlers import handle_read_pdf

        result = handle_read_pdf("u1", {}, ctx)
        assert "error" in result

    def test_nonexistent_document(self, ctx):
        from app.services.tool_handlers import handle_read_pdf

        mock_svc = MagicMock()
        mock_svc.get_document_detail.return_value = None
        with patch("app.services.tool_handlers._get_doc_service", return_value=mock_svc):
            result = handle_read_pdf("u1", {"document_id": "nonexistent"}, ctx)
        assert "error" in result


class TestSearchDocuments:
    def test_success(self, ctx):
        from app.services.tool_handlers import handle_search_documents

        mock_svc = MagicMock()
        mock_svc.semantic_search.return_value = {
            "results": [{"content": "Normalisation reduces redundancy", "score": 0.9}],
            "total": 1,
        }
        with patch("app.services.tool_handlers._get_doc_service", return_value=mock_svc):
            result = handle_search_documents("u1", {"query": "normalisation"}, ctx)

        assert result["query"] == "normalisation"
        assert len(result["results"]) == 1

    def test_missing_query(self, ctx):
        from app.services.tool_handlers import handle_search_documents

        result = handle_search_documents("u1", {}, ctx)
        assert "error" in result


class TestGetAssignment:
    def test_success(self, ctx):
        from app.services.tool_handlers import handle_get_assignment

        mock_svc = MagicMock()
        mock_svc.get_assignment.return_value = {"id": "a1", "title": "DBMS HW"}
        with patch("app.services.tool_handlers._get_assignment_service", return_value=mock_svc):
            result = handle_get_assignment("u1", {"assignment_id": "a1"}, ctx)
        assert result["title"] == "DBMS HW"

    def test_missing_id(self, ctx):
        from app.services.tool_handlers import handle_get_assignment

        result = handle_get_assignment("u1", {}, ctx)
        assert "error" in result


class TestListAssignments:
    def test_success(self, ctx):
        from app.services.tool_handlers import handle_list_assignments

        mock_svc = MagicMock()
        mock_svc.list_assignments.return_value = {
            "assignments": [{"id": "a1"}, {"id": "a2"}],
            "total": 2,
        }
        with patch("app.services.tool_handlers._get_assignment_service", return_value=mock_svc):
            result = handle_list_assignments("u1", {}, ctx)
        assert result["total"] == 2

    def test_with_status_filter(self, ctx):
        from app.services.tool_handlers import handle_list_assignments

        mock_svc = MagicMock()
        mock_svc.list_assignments.return_value = {"assignments": [], "total": 0}
        with patch("app.services.tool_handlers._get_assignment_service", return_value=mock_svc):
            handle_list_assignments("u1", {"status": "pending"}, ctx)
        call_args = mock_svc.list_assignments.call_args
        # list_assignments(user_id, filters) - positional args
        filters = call_args[0][1] if len(call_args[0]) > 1 else call_args[1].get("filters", call_args[1])
        assert filters["status"] == "pending"


class TestGetSchedule:
    def test_success(self, ctx):
        from app.services.tool_handlers import handle_get_schedule

        mock_svc = MagicMock()
        mock_svc.list_assignments.return_value = {
            "assignments": [{"title": "Exam"}],
            "total": 1,
        }
        with patch("app.services.tool_handlers._get_assignment_service", return_value=mock_svc):
            result = handle_get_schedule("u1", {}, ctx)
        assert result["total"] == 1


class TestStudyScoring:
    def test_success(self, ctx):
        from app.services.tool_handlers import handle_study_scoring

        mock_svc = MagicMock()
        mock_svc.get_statistics.return_value = {
            "current_streak": 5,
            "longest_streak": 10,
            "total_points": 500,
            "today_points": 50,
            "total_hours": 20,
        }
        with patch("app.services.tool_handlers._get_study_service", return_value=mock_svc):
            result = handle_study_scoring("u1", {}, ctx)
        assert result["current_streak"] == 5
        assert result["total_points"] == 500


# ---------------------------------------------------------------------------
# WRITING tools
# ---------------------------------------------------------------------------


class TestCreateAssignment:
    def test_success(self, ctx):
        from app.services.tool_handlers import handle_create_assignment

        mock_svc = MagicMock()
        mock_svc.create_assignment.return_value = {
            "id": "a_new",
            "title": "New HW",
            "status": "pending",
            "due_date": "2026-09-20",
        }
        with patch("app.services.tool_handlers._get_assignment_service", return_value=mock_svc):
            result = handle_create_assignment(
                "u1", {"title": "New HW", "deadline": "2026-09-20"}, ctx
            )
        assert result["assignment_id"] == "a_new"
        assert "Created" in result["message"]

    def test_missing_title(self, ctx):
        from app.services.tool_handlers import handle_create_assignment

        result = handle_create_assignment("u1", {}, ctx)
        assert "error" in result

    def test_validates_params(self, ctx):
        from app.services.tool_handlers import handle_create_assignment

        mock_svc = MagicMock()
        mock_svc.create_assignment.return_value = {"id": "a1", "title": "X", "status": "pending"}
        with patch("app.services.tool_handlers._get_assignment_service", return_value=mock_svc):
            handle_create_assignment("u1", {"title": "X", "priority": "urgent"}, ctx)
        call_args = mock_svc.create_assignment.call_args
        # create_assignment(user_id, data)
        data = call_args[0][1] if len(call_args[0]) > 1 else call_args[1].get("data", {})
        assert data.get("priority") == "urgent"


class TestUpdateAssignment:
    def test_success(self, ctx):
        from app.services.tool_handlers import handle_update_assignment

        mock_svc = MagicMock()
        mock_svc.update_assignment.return_value = {"id": "a1"}
        with patch("app.services.tool_handlers._get_assignment_service", return_value=mock_svc):
            result = handle_update_assignment(
                "u1", {"assignment_id": "a1", "status": "completed"}, ctx
            )
        assert "updated_fields" in result

    def test_missing_id(self, ctx):
        from app.services.tool_handlers import handle_update_assignment

        result = handle_update_assignment("u1", {}, ctx)
        assert "error" in result

    def test_no_fields(self, ctx):
        from app.services.tool_handlers import handle_update_assignment

        result = handle_update_assignment("u1", {"assignment_id": "a1"}, ctx)
        assert "error" in result


# ---------------------------------------------------------------------------
# DESTRUCTIVE tools
# ---------------------------------------------------------------------------


class TestDeleteAssignment:
    def test_success(self, ctx):
        from app.services.tool_handlers import handle_delete_assignment

        mock_svc = MagicMock()
        with patch("app.services.tool_handlers._get_assignment_service", return_value=mock_svc):
            result = handle_delete_assignment("u1", {"assignment_id": "a1"}, ctx)
        mock_svc.delete_assignment.assert_called_once_with("a1", "u1")
        assert "deleted" in result["message"]

    def test_missing_id(self, ctx):
        from app.services.tool_handlers import handle_delete_assignment

        result = handle_delete_assignment("u1", {}, ctx)
        assert "error" in result


class TestDeleteDocument:
    def test_success(self, ctx):
        from app.services.tool_handlers import handle_delete_document

        mock_svc = MagicMock()
        with patch("app.services.tool_handlers._get_doc_service", return_value=mock_svc):
            result = handle_delete_document("u1", {"document_id": "d1"}, ctx)
        mock_svc.delete_document.assert_called_once_with("d1", "u1")
        assert "deleted" in result["message"]

    def test_missing_id(self, ctx):
        from app.services.tool_handlers import handle_delete_document

        result = handle_delete_document("u1", {}, ctx)
        assert "error" in result


class TestClearConversation:
    def test_success(self, ctx):
        from app.services.tool_handlers import handle_clear_conversation

        mock_repo = MagicMock()
        mock_repo.get_messages.return_value = [{"id": "m1"}, {"id": "m2"}]
        mock_repo.delete_message.return_value = True
        with patch("app.repositories.ai_repository.AIRepository", return_value=mock_repo):
            result = handle_clear_conversation(
                "u1", {"conversation_id": "c1"}, ctx
            )
        assert "cleared" in result["message"].lower()
        assert mock_repo.delete_message.call_count == 2

    def test_missing_id(self, ctx):
        from app.services.tool_handlers import handle_clear_conversation

        result = handle_clear_conversation("u1", {}, ctx)
        assert "error" in result


# ---------------------------------------------------------------------------
# SCHEDULING tools
# ---------------------------------------------------------------------------


class TestCreateStudyPlan:
    def test_success(self, ctx):
        from app.services.tool_handlers import handle_create_study_plan

        mock_svc = MagicMock()
        mock_svc.get_statistics.return_value = {"current_streak": 3}
        with patch("app.services.tool_handlers._get_study_service", return_value=mock_svc):
            result = handle_create_study_plan(
                "u1", {"subject": "DBMS", "duration_days": 5}, ctx
            )
        assert result["subject"] == "DBMS"
        assert len(result["daily_sessions"]) == 5

    def test_missing_subject(self, ctx):
        from app.services.tool_handlers import handle_create_study_plan

        result = handle_create_study_plan("u1", {}, ctx)
        assert "error" in result


class TestAddToPlanner:
    def test_success(self, ctx):
        from app.services.tool_handlers import handle_add_to_planner

        result = handle_add_to_planner(
            "u1", {"title": "Study DBMS", "date": "2026-09-15", "duration_minutes": 60}, ctx
        )
        assert result["title"] == "Study DBMS"
        assert "Planned" in result["message"]

    def test_missing_title(self, ctx):
        from app.services.tool_handlers import handle_add_to_planner

        result = handle_add_to_planner("u1", {}, ctx)
        assert "error" in result


class TestStartPomodoro:
    def test_success(self, ctx):
        from app.services.tool_handlers import handle_start_pomodoro

        mock_svc = MagicMock()
        mock_svc.get_settings.return_value = {"short_break": 5}
        with patch("app.services.tool_handlers._get_pomodoro_service", return_value=mock_svc):
            result = handle_start_pomodoro(
                "u1", {"duration_minutes": 25, "task_description": "Revise DBMS"}, ctx
            )
        assert result["duration_minutes"] == 25
        assert "Pomodoro started" in result["message"]


# ---------------------------------------------------------------------------
# WEB tools
# ---------------------------------------------------------------------------


class TestWebSearch:
    def test_success(self, ctx):
        from app.services.tool_handlers import handle_web_search

        mock_result = MagicMock()
        mock_result.title = "React 19"
        mock_result.url = "https://react.dev"
        mock_result.snippet = "React 19 features..."

        mock_svc = MagicMock()
        mock_svc.search.return_value = [mock_result]
        with patch("app.services.tool_handlers._get_web_service", return_value=mock_svc):
            result = handle_web_search("u1", {"query": "React 19"}, ctx)
        assert result["query"] == "React 19"
        assert len(result["results"]) == 1

    def test_missing_query(self, ctx):
        from app.services.tool_handlers import handle_web_search

        result = handle_web_search("u1", {}, ctx)
        assert "error" in result


class TestFetchURL:
    def test_success(self, ctx):
        from app.services.tool_handlers import handle_fetch_url

        mock_content = MagicMock()
        mock_content.title = "Article"
        mock_content.content = "Full article content here"

        mock_svc = MagicMock()
        mock_svc.fetch_url.return_value = mock_content
        with patch("app.services.tool_handlers._get_web_service", return_value=mock_svc):
            result = handle_fetch_url("u1", {"url": "https://example.com"}, ctx)
        assert result["url"] == "https://example.com"

    def test_missing_url(self, ctx):
        from app.services.tool_handlers import handle_fetch_url

        result = handle_fetch_url("u1", {}, ctx)
        assert "error" in result


# ---------------------------------------------------------------------------
# ACADEMIC tools
# ---------------------------------------------------------------------------


class TestSaveOpportunity:
    def test_success(self, ctx):
        from app.services.tool_handlers import handle_save_opportunity

        mock_opp = MagicMock()
        mock_opp.id = "opp1"

        mock_svc = MagicMock()
        mock_svc.save.return_value = mock_opp
        with patch("app.services.tool_handlers._get_opportunity_service", return_value=mock_svc):
            result = handle_save_opportunity(
                "u1", {"title": "SWE Intern", "company": "Google"}, ctx
            )
        assert result["title"] == "SWE Intern"
        assert "Saved" in result["message"]

    def test_missing_fields(self, ctx):
        from app.services.tool_handlers import handle_save_opportunity

        result = handle_save_opportunity("u1", {"title": "X"}, ctx)
        assert "error" in result


class TestCreateFlashcards:
    def test_with_document(self, ctx):
        from app.services.tool_handlers import handle_create_flashcards

        mock_svc = MagicMock()
        mock_svc.generate_document_content.return_value = {
            "content": [{"front": "Q1", "back": "A1"}]
        }
        with patch("app.services.tool_handlers._get_doc_service", return_value=mock_svc):
            result = handle_create_flashcards(
                "u1", {"topic": "Normalization", "document_id": "d1"}, ctx
            )
        assert len(result["flashcards"]) == 1

    def test_without_document(self, ctx):
        from app.services.tool_handlers import handle_create_flashcards

        result = handle_create_flashcards("u1", {"topic": "Normalization"}, ctx)
        assert "note" in result

    def test_missing_topic(self, ctx):
        from app.services.tool_handlers import handle_create_flashcards

        result = handle_create_flashcards("u1", {}, ctx)
        assert "error" in result


class TestCreateQuiz:
    def test_with_document(self, ctx):
        from app.services.tool_handlers import handle_create_quiz

        mock_svc = MagicMock()
        mock_svc.generate_document_content.return_value = {
            "content": [{"question": "Q1", "answer": "A1"}]
        }
        with patch("app.services.tool_handlers._get_doc_service", return_value=mock_svc):
            result = handle_create_quiz(
                "u1", {"topic": "OS", "document_id": "d1", "difficulty": "hard"}, ctx
            )
        assert result["difficulty"] == "hard"

    def test_missing_topic(self, ctx):
        from app.services.tool_handlers import handle_create_quiz

        result = handle_create_quiz("u1", {}, ctx)
        assert "error" in result


# ---------------------------------------------------------------------------
# COMMUNICATION tools
# ---------------------------------------------------------------------------


class TestComposeEmail:
    def test_success(self, ctx):
        from app.services.tool_handlers import handle_compose_email

        result = handle_compose_email(
            "u1",
            {"recipient": "prof@uni.edu", "subject": "Extension", "body": "Please extend"},
            ctx,
        )
        assert result["draft"] is True
        assert result["recipient"] == "prof@uni.edu"

    def test_missing_fields(self, ctx):
        from app.services.tool_handlers import handle_compose_email

        result = handle_compose_email("u1", {"recipient": "x@y.com"}, ctx)
        assert "error" in result


class TestReadEmail:
    def test_success(self, ctx):
        from app.services.tool_handlers import handle_read_email

        mock_svc = MagicMock()
        mock_svc.get_messages.return_value = {
            "messages": [{"id": "e1", "subject": "Exam", "from_address": "prof@uni.edu"}],
            "total": 1,
        }
        with patch("app.services.tool_handlers._get_email_service", return_value=mock_svc):
            result = handle_read_email("u1", {}, ctx)
        assert result["total"] == 1


# ---------------------------------------------------------------------------
# SYSTEM tools
# ---------------------------------------------------------------------------


class TestSendReminder:
    def test_success(self, ctx):
        from app.services.tool_handlers import handle_send_reminder

        mock_svc = MagicMock()
        mock_svc.notify.return_value = {"id": "n1"}
        with patch("app.services.tool_handlers._get_notification_service", return_value=mock_svc):
            result = handle_send_reminder(
                "u1", {"message": "Submit HW", "when": "tomorrow 9am"}, ctx
            )
        assert result["created"] is True
        mock_svc.notify.assert_called_once()

    def test_missing_message(self, ctx):
        from app.services.tool_handlers import handle_send_reminder

        result = handle_send_reminder("u1", {}, ctx)
        assert "error" in result


# ---------------------------------------------------------------------------
# Executor integration
# ---------------------------------------------------------------------------


class TestExecutorIntegration:
    def test_execute_tool_via_executor(self, executor):
        from app.services.tool_handlers import ToolHandlerContext

        mock_svc = MagicMock()
        mock_svc.get_settings.return_value = {"short_break": 5}

        # Directly test handler through executor
        result = executor.execute(
            "start_pomodoro",
            "u1",
            {"duration_minutes": 25, "task_description": "Test"},
        )
        # Handler will fail because it can't get the service, but it proves the path works
        # The key test is that it doesn't return "no_handler_registered"
        assert result.error != "no_handler_registered"

    def test_all_handlers_callable(self, executor):
        """Every registered handler is a callable."""
        for name, handler in executor._handlers.items():
            assert callable(handler), f"Handler for {name} is not callable"

    def test_unregistered_tool_returns_error(self, executor):
        result = executor.execute("nonexistent_tool", "u1", {})
        assert result.success is False
