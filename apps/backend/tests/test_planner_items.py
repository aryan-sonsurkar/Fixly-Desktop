"""Planner item normalization/validation + structured-list salvage + PRD v2.0 hardening.

Regression coverage for user-facing raw-JSON bugs and PRD v2.0 P0.1 requirements:
- canonical schema validation: explanation + actions + schedule_items;
- malformed JSON handling;
- unknown action types dropped safely while valid siblings survive;
- missing required fields handled safely;
- wrong field types normalized or dropped safely;
- empty action list rejection when no usable structure exists;
- execution and idempotency / duplicate protection;
- never leaking raw JSON into user-facing content/explanation.
"""

import json
from unittest.mock import AsyncMock, patch

import pytest

from app.core.exceptions import ValidationError as FixlyValidationError
from app.services.document_service import DocumentService
from app.services.planner_service import PlannerService


def _svc() -> PlannerService:
    return PlannerService(access_token=None)


def _item(**over):
    base = {
        "title": "DBMS Normalization",
        "description": "Read chapter 3",
        "start_time": "2026-09-28T21:00:00Z",
        "end_time": "2026-09-28T22:00:00Z",
        "priority": "high",
        "type": "study",
    }
    base.update(over)
    return base


def _payload(items):
    return json.dumps({"schedule_items": items})


# ── Legacy schedule validation regression tests ────────────────────────────


def test_valid_items_pass_through():
    out = _svc()._validate_schedule_items(_payload([_item(), _item(title="Break")]))
    assert len(out) == 2
    assert out[0]["priority"] == "high"
    assert out[0]["type"] == "study"


def test_near_miss_enums_normalize():
    out = _svc()._validate_schedule_items(
        _payload([_item(priority=" High ", type="STUDY")])
    )
    assert out[0]["priority"] == "high"
    assert out[0]["type"] == "study"


def test_echoed_option_lists_rejected_not_accepted():
    svc = _svc()
    with pytest.raises(FixlyValidationError):
        svc._validate_schedule_items(
            _payload([
                _item(
                    priority="low|medium|high|urgent",
                    type="study|break|review|assignment|exam|other",
                ),
            ])
        )


def test_partial_items_survive():
    out = _svc()._validate_schedule_items(
        _payload([
            _item(title="Good"),
            _item(title="Bad", priority="whenever"),
        ])
    )
    assert [i["title"] for i in out] == ["Good"]


def test_empty_and_prose_raise():
    svc = _svc()
    with pytest.raises(FixlyValidationError):
        svc._validate_schedule_items(_payload([]))
    with pytest.raises(FixlyValidationError):
        svc._validate_schedule_items("Here is a nice prose study plan.")


def test_looks_like_json_distinguishes_payloads():
    svc = _svc()
    assert svc._looks_like_json('{"schedule_items": []}') is True
    assert svc._looks_like_json('```json\n{"a": 1}\n```') is True
    assert svc._looks_like_json("Study DBMS tonight, then rest.") is False


TRUNCATED = (
    '[{"front": "What is 1NF?", "back": "Atomic values."}, '
    '{"front": "What is 2NF?", "back": "No partial dependency."}, '
    '{"front": "What is 3NF?", "back": "No transitive depend'
)


def test_salvage_recovers_truncated_prefix():
    out = DocumentService._parse_structured_list(TRUNCATED)
    assert [i["front"] for i in out] == ["What is 1NF?", "What is 2NF?"]


def test_salvage_keeps_full_arrays_intact():
    full = (
        '[{"front": "A", "back": "B"}, {"front": "C", "back": "D"}]'
        " trailing prose here"
    )
    out = DocumentService._parse_structured_list(full)
    assert len(out) == 2


def test_salvage_returns_empty_for_garbage():
    assert DocumentService._parse_structured_list("no json here") == []
    assert DocumentService._parse_structured_list("[{broken") == []


def test_salvage_ignores_braces_inside_strings():
    tricky = (
        '[{"front": "A {b} C", "back": "x"}, {"front": "D", "back": "y"}'
        ', {"front": "E", "back": "z'
    )
    out = DocumentService._parse_structured_list(tricky)
    assert [i["front"] for i in out] == ["A {b} C", "D"]


# ── PRD v2.0 P0.1: Structured output hardening tests ───────────────────────


def test_canonical_valid_structured_response():
    """Requirement H.1: Valid structured response with explanation, actions, and schedule."""
    svc = _svc()
    payload = json.dumps({
        "explanation": "Start with Normalization because your DBMS test is tomorrow.",
        "actions": [
            {
                "action": "create_study_session",
                "title": "DBMS Normalization",
                "duration_minutes": 45,
                "priority": "high",
            },
            {
                "action": "create_task",
                "title": "Revise SQL joins",
                "priority": "medium",
                "estimated_minutes": 30,
            },
        ],
        "schedule_items": [
            {
                "title": "DBMS Normalization",
                "description": "Read chapter 3",
                "start_time": "2026-09-28T21:00:00Z",
                "end_time": "2026-09-28T21:45:00Z",
                "priority": "high",
                "type": "study",
            }
        ],
    })

    result = svc.validate_and_parse_plan_output(payload)
    assert result["explanation"] == "Start with Normalization because your DBMS test is tomorrow."
    assert len(result["actions"]) == 2
    assert result["actions"][0]["action"] == "create_study_session"
    assert result["actions"][0]["title"] == "DBMS Normalization"
    assert result["actions"][0]["duration_minutes"] == 45
    assert result["actions"][1]["action"] == "create_task"
    assert result["actions"][1]["title"] == "Revise SQL joins"
    assert len(result["schedule_items"]) == 1
    # Verify no raw JSON in user-facing content
    assert not result["content"].startswith("{")
    assert "Start with Normalization" in result["content"]


def test_malformed_json_handling():
    """Requirement H.2: Malformed JSON raises FixlyValidationError safely."""
    svc = _svc()
    with pytest.raises(FixlyValidationError):
        svc.validate_and_parse_plan_output('```json\n{"actions": [ broken json ...')


def test_valid_json_with_missing_required_fields():
    """Requirement H.3: Actions with missing required fields are dropped, valid siblings survive."""
    svc = _svc()
    payload = json.dumps({
        "explanation": "Here is your plan.",
        "actions": [
            # Missing title: invalid
            {"action": "create_task", "priority": "high"},
            # Valid action
            {"action": "create_task", "title": "Finish Report", "priority": "high"},
            # Missing start_time/end_time: invalid for schedule_task
            {"action": "schedule_task", "title": "Incomplete task"},
        ],
    })
    result = svc.validate_and_parse_plan_output(payload)
    assert len(result["actions"]) == 1
    assert result["actions"][0]["title"] == "Finish Report"


def test_unknown_action_type_dropped():
    """Requirement H.4: Unknown action types are dropped safely without crashing."""
    svc = _svc()
    payload = json.dumps({
        "actions": [
            {"action": "unknown_ai_command", "title": "Do something strange"},
            {"action": "create_study_session", "title": "Focus Session", "duration_minutes": 25},
        ]
    })
    result = svc.validate_and_parse_plan_output(payload)
    assert len(result["actions"]) == 1
    assert result["actions"][0]["action"] == "create_study_session"
    assert result["actions"][0]["title"] == "Focus Session"


def test_wrong_field_types_normalized_or_dropped():
    """Requirement H.5: Wrong field types are safely handled (coerced or dropped)."""
    svc = _svc()
    payload = json.dumps({
        "actions": [
            {
                "action": "create_study_session",
                "title": "Study Math",
                # duration_minutes string number gets normalized
                "duration_minutes": "30",
                # Priority whitespace and case get normalized
                "priority": " High ",
            },
            {
                "action": "create_task",
                "title": "Bad Priority Task",
                # Invalid priority string gets dropped
                "priority": "invalid_priority_word",
            },
        ]
    })
    result = svc.validate_and_parse_plan_output(payload)
    assert len(result["actions"]) == 1
    assert result["actions"][0]["duration_minutes"] == 30
    assert result["actions"][0]["priority"] == "high"


def test_empty_action_list_and_empty_schedule_raises():
    """Requirement H.6: Empty payload raises ValidationError."""
    svc = _svc()
    payload = json.dumps({"actions": [], "schedule_items": []})
    with pytest.raises(FixlyValidationError):
        svc.validate_and_parse_plan_output(payload)


def test_stored_plan_never_returns_raw_json():
    """Requirement D & G: parse_and_validate_stored_plan guarantees NO raw JSON in UI."""
    svc = _svc()
    raw_json = '{"schedule_items": [{"title": "DBMS", "start_time": "2026-09-28T21:00:00Z", "end_time": "2026-09-28T22:00:00Z", "priority": "high", "type": "study"}]}'
    result = svc.parse_and_validate_stored_plan(raw_json)
    assert not result["content"].startswith("{")
    assert not result["explanation"].startswith("{")
    assert len(result["actions"]) > 0
    assert result["actions"][0]["title"] == "DBMS"


@pytest.mark.asyncio
async def test_action_execution_and_duplicate_protection():
    """Requirement H.7 & H.8: Backend action execution and repeated execution attempt (idempotency)."""
    svc = _svc()
    user_id = "test-user-123"
    action = {
        "action": "create_task",
        "action_id": "act_test_duplicate_123",
        "title": "DBMS Practice",
        "priority": "high",
    }

    with patch("app.services.assignment_service.AssignmentService.create_assignment", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = {"id": "assign-1", "title": "DBMS Practice"}

        # First execution: should call create_assignment
        res1 = await svc.execute_action(user_id, action, idempotency_key="idemp_key_1")
        assert res1["success"] is True
        assert res1["action_id"] == "act_test_duplicate_123"
        assert mock_create.call_count == 1

        # Second execution with same idempotency key / action_id: should return cached result without calling service
        res2 = await svc.execute_action(user_id, action, idempotency_key="idemp_key_1")
        assert res2["success"] is True
        assert res2["action_id"] == "act_test_duplicate_123"
        # Service was NOT called a second time
        assert mock_create.call_count == 1


@pytest.mark.asyncio
async def test_reschedule_without_match_rejects_instead_of_creating():
    """Rescheduling a nonexistent task must fail loudly, never invent one."""
    svc = _svc()
    action = {
        "action": "reschedule_task",
        "action_id": "act_resched_nomatch",
        "title": "Task That Does Not Exist",
        "new_start_time": "2026-10-05T21:00:00Z",
    }
    with patch("app.services.assignment_service.AssignmentService.list_assignments",
               new_callable=AsyncMock) as mock_list, \
         patch("app.services.assignment_service.AssignmentService.create_assignment",
               new_callable=AsyncMock) as mock_create:
        mock_list.return_value = {"data": []}
        with pytest.raises(FixlyValidationError, match="No matching task"):
            await svc.execute_action("u1", action, idempotency_key="probe-no-match")
        mock_create.assert_not_called()


@pytest.mark.asyncio
async def test_reschedule_title_match_updates_without_creating():
    """Reschedule without task_id resolves via title search, no creation."""
    svc = _svc()
    action = {
        "action": "reschedule_task",
        "action_id": "act_resched_match",
        "title": "Resume Document",
        "new_start_time": "2026-10-06T21:00:00Z",
    }
    with patch("app.services.assignment_service.AssignmentService.list_assignments",
               new_callable=AsyncMock) as mock_list, \
         patch("app.services.assignment_service.AssignmentService.update_assignment",
               new_callable=AsyncMock) as mock_update, \
         patch("app.services.assignment_service.AssignmentService.create_assignment",
               new_callable=AsyncMock) as mock_create:
        mock_list.return_value = {"data": [{"id": "task-1", "title": "Resume Document"}]}
        mock_update.return_value = {"id": "task-1", "title": "Resume Document"}
        res = await svc.execute_action("u1", action, idempotency_key="probe-match")
        assert res["success"] is True
        assert mock_update.call_count == 1
        mock_create.assert_not_called()


@pytest.mark.asyncio
async def test_prioritize_without_match_rejects_instead_of_creating():
    """Reprioritizing a nonexistent task must fail loudly, never invent one."""
    svc = _svc()
    action = {
        "action": "prioritize_task",
        "action_id": "act_prio_nomatch",
        "title": "Task That Does Not Exist",
        "priority": "high",
    }
    with patch("app.services.assignment_service.AssignmentService.list_assignments",
               new_callable=AsyncMock) as mock_list, \
         patch("app.services.assignment_service.AssignmentService.create_assignment",
               new_callable=AsyncMock) as mock_create:
        mock_list.return_value = {"data": []}
        with pytest.raises(FixlyValidationError, match="No matching task"):
            await svc.execute_action("u1", action, idempotency_key="probe-prio-no-match")
        mock_create.assert_not_called()
