from unittest.mock import AsyncMock

import pytest

from app.services.auth_service import AuthService
from app.services.planner_service import PlannerService


@pytest.mark.asyncio
async def test_google_callback_returns_flattened_session_tokens() -> None:
    service = AuthService()
    service.repository.exchange_code_for_session = AsyncMock(
        return_value={
            "session": {"access_token": "access", "refresh_token": "refresh"},
            "user": {"id": "user-1"},
        }
    )

    result = await service.handle_google_callback("code", "fixly://auth/callback")

    assert result == {
        "access_token": "access",
        "refresh_token": "refresh",
        "user": {"id": "user-1"},
    }


def test_planner_accepts_the_json_contract_requested_by_its_prompt() -> None:
    service = PlannerService()
    content = (
        '{"schedule_items":[{"title":"Math","description":"Review algebra",'
        '"start_time":"2026-08-25T09:00:00Z","end_time":"2026-08-25T10:00:00Z",'
        '"priority":"high","type":"study"}]}'
    )

    items = service._validate_schedule_items(content)

    assert items[0]["title"] == "Math"