from unittest.mock import AsyncMock

import pytest

from app.services.auth_service import AuthService


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