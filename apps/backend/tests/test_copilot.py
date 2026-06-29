from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.prompts.registry import PromptType, get_registry


class TestNewPromptTypes:
    def test_new_types_registered(self) -> None:
        registry = get_registry()
        new_types = [
            PromptType.DAILY_MISSION,
            PromptType.PRODUCTIVITY_COACH,
            PromptType.RESCHEDULER,
            PromptType.RISK_DETECTOR,
            PromptType.WEEKLY_REVIEW,
            PromptType.INSIGHTS,
            PromptType.SMART_COMMANDS,
        ]
        for pt in new_types:
            template = registry.get(pt)
            assert template is not None
            assert template.name
            assert template.version
            assert len(template.template) > 10
            assert "{" in template.template


class TestPromptRegistry:
    def test_registry_contains_new_entries(self) -> None:
        registry = get_registry()
        types = registry.types
        type_values = {t.value for t in types}
        assert "daily_mission" in type_values
        assert "productivity_coach" in type_values
        assert "rescheduler" in type_values
        assert "risk_detector" in type_values
        assert "weekly_review" in type_values
        assert "insights" in type_values
        assert "smart_commands" in type_values

    def test_template_metadata_for_new_templates(self) -> None:
        registry = get_registry()
        new_types = [
            PromptType.DAILY_MISSION,
            PromptType.PRODUCTIVITY_COACH,
            PromptType.RESCHEDULER,
            PromptType.RISK_DETECTOR,
            PromptType.WEEKLY_REVIEW,
            PromptType.INSIGHTS,
            PromptType.SMART_COMMANDS,
        ]
        for pt in new_types:
            tpl = registry.get(pt)
            assert tpl.version
            assert tpl.description
            assert tpl.author == "Fixly Team"
            assert tpl.last_updated
            assert len(tpl.template) > 50


class TestWorkspaceContextExpansion:
    @pytest.mark.asyncio
    async def test_gather_with_copilot_budget(self) -> None:
        with patch("app.services.workspace_context.WorkspaceContext._get_profile", return_value={"name": "Alice", "streak": 5, "xp": 100}):
            with patch("app.services.workspace_context.WorkspaceContext._get_subjects", return_value=[]):
                with patch("app.services.workspace_context.WorkspaceContext._get_assignments", return_value={"total": 3, "deadlines": [], "overdue_count": 0, "_tokens": 50}):
                    with patch("app.services.workspace_context.WorkspaceContext._get_pomodoro_summary", return_value={"weekly_cycles": 10, "today_focus_minutes": 30, "_tokens": 20}):
                        with patch("app.services.workspace_context.WorkspaceContext._get_study_summary", return_value={"total_hours": 15, "study_days": 5, "avg_daily": 60, "weekly_trend": [], "_tokens": 30}):
                            with patch("app.services.workspace_context.WorkspaceContext._get_email_summary", return_value={"unread": 3, "pending_review": 1, "_tokens": 20}):
                                with patch("app.services.workspace_context.WorkspaceContext._get_timezone", return_value="Asia/Kolkata"):
                                    with patch("app.services.workspace_context.WorkspaceContext._get_notifications", return_value={"unread_count": 2, "recent": [], "_tokens": 20}):
                                        with patch("app.services.workspace_context.WorkspaceContext._get_recent_documents", return_value={"recent": [], "count": 0, "_tokens": 10}):
                                            from app.services.workspace_context import WorkspaceContext

                                            ctx = WorkspaceContext()
                                            result = await ctx.gather("user-123", budget="copilot")

                                            assert result["profile"]["name"] == "Alice"
                                            assert result["timezone"] == "Asia/Kolkata"
                                            assert result["notifications"]["unread_count"] == 2
                                            assert result["_budget_total"] == 5000

    @pytest.mark.asyncio
    async def test_gather_with_planner_and_chats(self) -> None:
        with patch("app.services.workspace_context.WorkspaceContext._get_profile", return_value={"name": "Bob", "streak": 3, "xp": 50}):
            with patch("app.services.workspace_context.WorkspaceContext._get_subjects", return_value=[]):
                with patch("app.services.workspace_context.WorkspaceContext._get_assignments", return_value={"total": 0, "deadlines": [], "overdue_count": 0, "_tokens": 30}):
                    with patch("app.services.workspace_context.WorkspaceContext._get_pomodoro_summary", return_value={"weekly_cycles": 5, "today_focus_minutes": 20, "_tokens": 20}):
                        with patch("app.services.workspace_context.WorkspaceContext._get_study_summary", return_value={"total_hours": 10, "study_days": 4, "avg_daily": 45, "weekly_trend": [], "_tokens": 30}):
                            with patch("app.services.workspace_context.WorkspaceContext._get_email_summary", return_value={"unread": 0, "pending_review": 0, "_tokens": 20}):
                                with patch("app.services.workspace_context.WorkspaceContext._get_timezone", return_value="UTC"):
                                    with patch("app.services.workspace_context.WorkspaceContext._get_notifications", return_value={"unread_count": 0, "recent": [], "_tokens": 20}):
                                        with patch("app.services.workspace_context.WorkspaceContext._get_recent_documents", return_value={"recent": [], "count": 0, "_tokens": 10}):
                                            with patch("app.services.workspace_context.WorkspaceContext._get_planner_context", return_value={"today_sessions": "09:00-10:00 | 60m | study | Math", "today_points": 10, "_tokens": 30}):
                                                with patch("app.services.workspace_context.WorkspaceContext._get_ai_chats", return_value=[{"title": "Test Chat", "message_count": 5, "updated_at": "2026-06-29"}]):
                                                    from app.services.workspace_context import WorkspaceContext

                                                    ctx = WorkspaceContext()
                                                    result = await ctx.gather("user-123", budget="copilot", include_planner=True, include_ai_chats=True)

                                                    assert result["planner"]["today_sessions"] == "09:00-10:00 | 60m | study | Math"
                                                    assert len(result["ai_chats"]) == 1
                                                    assert result["ai_chats"][0]["title"] == "Test Chat"

    @pytest.mark.asyncio
    async def test_heatmap_and_diary(self) -> None:
        with patch("app.services.workspace_context.WorkspaceContext._get_profile", return_value={"name": "Charlie", "streak": 1, "xp": 10}):
            with patch("app.services.workspace_context.WorkspaceContext._get_subjects", return_value=[]):
                with patch("app.services.workspace_context.WorkspaceContext._get_assignments", return_value={"total": 0, "deadlines": [], "overdue_count": 0, "_tokens": 30}):
                    with patch("app.services.workspace_context.WorkspaceContext._get_pomodoro_summary", return_value={"weekly_cycles": 0, "today_focus_minutes": 0, "_tokens": 20}):
                        with patch("app.services.workspace_context.WorkspaceContext._get_study_summary", return_value={"total_hours": 0, "study_days": 0, "avg_daily": 0, "weekly_trend": [], "_tokens": 30}):
                            with patch("app.services.workspace_context.WorkspaceContext._get_email_summary", return_value={"unread": 0, "pending_review": 0, "_tokens": 20}):
                                with patch("app.services.workspace_context.WorkspaceContext._get_timezone", return_value="UTC"):
                                    with patch("app.services.workspace_context.WorkspaceContext._get_notifications", return_value={"unread_count": 0, "recent": [], "_tokens": 20}):
                                        with patch("app.services.workspace_context.WorkspaceContext._get_recent_documents", return_value={"recent": [], "count": 0, "_tokens": 10}):
                                            with patch("app.services.workspace_context.WorkspaceContext._get_heatmap", return_value={"entries": [{"date": "2026-06-29", "points": 10, "minutes": 60}], "count": 1, "_tokens": 20}):
                                                with patch("app.services.workspace_context.WorkspaceContext._get_diary", return_value={"today_note": "Studied calculus", "date": "2026-06-29", "_tokens": 20}):
                                                    from app.services.workspace_context import WorkspaceContext

                                                    ctx = WorkspaceContext()
                                                    result = await ctx.gather("user-123", budget="copilot", include_heatmap=True, include_diary=True)

                                                    assert len(result["heatmap"]["entries"]) == 1
                                                    assert result["diary"]["today_note"] == "Studied calculus"


class TestRiskDetectorService:
    @pytest.mark.asyncio
    async def test_assess_returns_with_health_score(self) -> None:
        with patch("app.services.risk_detector_service.WorkspaceContext.gather", return_value={
            "profile": {"name": "Alice", "streak": 5, "xp": 100},
            "study": {"study_days": 5, "total_hours": 15, "avg_daily": 60, "weekly_trend_str": ""},
            "pomodoro": {"weekly_cycles": 10, "today_focus_minutes": 30},
            "email": {"unread": 3, "pending_review": 1},
            "assignments": {"total": 3, "deadlines": [], "overdue_count": 0, "overdue_titles": [], "urgent_deadlines": []},
            "notifications": {"unread_count": 2, "recent": []},
            "documents": {"count": 0},
            "timezone": "UTC",
        }):
            mock_ai_repo = AsyncMock()
            mock_ai_repo.create_conversation = AsyncMock(return_value={"id": "conv-1"})

            mock_ai_service = AsyncMock()
            mock_ai_service.chat = AsyncMock(return_value={
                "message": {"content": '{"academic_health_score": 85, "risk_level": "Low", "alerts": []}'},
            })

            mock_prompt_manager = AsyncMock()
            mock_prompt_manager.build = AsyncMock(return_value="Built prompt text")

            with patch("app.services.risk_detector_service.AIRepository", return_value=mock_ai_repo):
                with patch("app.services.risk_detector_service.AIService", return_value=mock_ai_service):
                    mock_pm_instance = MagicMock()
                    mock_pm_instance.build = AsyncMock(return_value="Built prompt text")
                    with patch("app.services.risk_detector_service.PromptManager", return_value=mock_pm_instance):
                        from app.services.risk_detector_service import RiskDetectorService

                        service = RiskDetectorService()
                        result = await service.assess("user-123")

                        assert result["academic_health_score"] == 85
                        assert result["risk_level"] == "Low"
                        assert "content" in result
                        assert "generated_at" in result

    @pytest.mark.asyncio
    async def test_health_score_fallback(self) -> None:
        from app.services.risk_detector_service import RiskDetectorService

        service = RiskDetectorService()
        score = service._extract_health_score("Random text", {"overdue_count": 0}, {"study_days": 7}, {"unread": 2})
        assert 0 <= score <= 100

    @pytest.mark.asyncio
    async def test_fallback_on_no_overdue(self) -> None:
        from app.services.risk_detector_service import RiskDetectorService

        service = RiskDetectorService()
        score = service._extract_health_score("No JSON", {"overdue_count": 0}, {"study_days": 7}, {"unread": 1})
        base_score = 50 + 15 + 15 + 5
        assert score == min(100, base_score)

    @pytest.mark.asyncio
    async def test_risk_level_calculation(self) -> None:
        from app.services.risk_detector_service import RiskDetectorService

        service = RiskDetectorService()
        assert service._calculate_risk_level(85) == "Low"
        assert service._calculate_risk_level(55) == "Medium"
        assert service._calculate_risk_level(30) == "High"


class TestCommandService:
    @pytest.mark.asyncio
    async def test_interpret_returns_command(self) -> None:
        from app.services.command_service import CommandService

        service = CommandService()
        cmd_type, confidence = service._parse_response('{"command_type": "plan_weekend", "confidence": 0.9}')
        assert cmd_type == "plan_weekend"
        assert confidence == 0.9

    @pytest.mark.asyncio
    async def test_parse_response_fallback(self) -> None:
        from app.services.command_service import CommandService

        service = CommandService()
        cmd_type, confidence = service._parse_response("Random text without JSON")
        assert cmd_type == "custom"
        assert confidence == 0.0

    @pytest.mark.asyncio
    async def test_confidence_clamped(self) -> None:
        from app.services.command_service import CommandService

        service = CommandService()
        _, high = service._parse_response('{"command_type": "test", "confidence": 2.5}')
        assert high == 1.0
        _, low = service._parse_response('{"command_type": "test", "confidence": -1.0}')
        assert low == 0.0


class TestCopilotService:
    @pytest.mark.asyncio
    async def test_assess_risk_delegation(self) -> None:
        mock_risk = AsyncMock()
        mock_risk.assess = AsyncMock(return_value={"academic_health_score": 90, "risk_level": "Low", "content": "All good", "generated_at": "now"})

        with patch("app.services.copilot_service.RiskDetectorService", return_value=mock_risk):
            from app.services.copilot_service import CopilotService

            service = CopilotService()
            result = await service.assess_risk("user-123")
            assert result["academic_health_score"] == 90
            assert result["risk_level"] == "Low"

    @pytest.mark.asyncio
    async def test_interpret_command_delegation(self) -> None:
        mock_cmd = AsyncMock()
        mock_cmd.interpret = AsyncMock(return_value={"content": '{"command_type": "plan_weekend"}', "command_type": "plan_weekend", "confidence": 0.8, "generated_at": "now"})

        with patch("app.services.copilot_service.CommandService", return_value=mock_cmd):
            from app.services.copilot_service import CopilotService

            service = CopilotService()
            result = await service.interpret_command("user-123", "Plan my weekend")
            assert result["command_type"] == "plan_weekend"
