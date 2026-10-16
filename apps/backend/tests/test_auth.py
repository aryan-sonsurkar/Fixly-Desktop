from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.exceptions import AuthenticationError
from app.services.auth_service import AuthService, _is_transient_supabase_failure
from app.services.planner_service import PlannerService


class _DefinitiveRejectionError(Exception):
    """Mimics supabase_auth AuthApiError for invalid_grant (HTTP 400)."""

    def __init__(self) -> None:
        super().__init__("invalid_grant: Invalid Refresh Token")
        self.status = 400
        self.code = "invalid_grant"


class _ConnectFailureError(Exception):
    """Mimics httpx.ConnectError when Supabase is unreachable."""


class _ServerFailureError(Exception):
    """Mimics supabase_auth AuthApiError for HTTP 503."""

    def __init__(self) -> None:
        super().__init__("service unavailable")
        self.status = 503


@pytest.mark.asyncio
async def test_refresh_maps_definitive_rejection_to_session_expired() -> None:
    service = AuthService()
    service.repository.refresh_token = AsyncMock(side_effect=_DefinitiveRejectionError())

    with pytest.raises(AuthenticationError, match="Session expired"):
        await service.refresh_token("dead-token")


@pytest.mark.asyncio
async def test_refresh_reraises_transient_failures_untouched() -> None:
    service = AuthService()
    for failure in (_ConnectFailureError("connection refused"),
                    _ServerFailureError(),
                    Exception("AuthRetryableError: caused by ConnectError")):
        service.repository.refresh_token = AsyncMock(side_effect=failure)
        with pytest.raises(type(failure)):
            await service.refresh_token("good-token")


def test_transient_discriminator_matrix() -> None:
    assert _is_transient_supabase_failure(_ConnectFailureError("connection refused")) is True
    assert _is_transient_supabase_failure(_ServerFailureError()) is True
    assert _is_transient_supabase_failure(_DefinitiveRejectionError()) is False
    assert _is_transient_supabase_failure(AuthenticationError("x")) is False
    assert _is_transient_supabase_failure(ValueError("timeout contacting upstream")) is True


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


@pytest.mark.asyncio
async def test_sign_up_with_password_passes_it_through() -> None:
    service = AuthService()
    service.repository.sign_up = AsyncMock(
        return_value={
            "session": {"access_token": "access", "refresh_token": "refresh"},
            "user": {"id": "user-1", "email": "new@x.com"},
        }
    )

    result = await service.sign_up("new@x.com", "password123", "New User")

    assert result["access_token"] == "access"
    service.repository.sign_up.assert_called_once_with("new@x.com", "password123", "New User")


@pytest.mark.asyncio
async def test_sign_up_without_password_generates_server_secret() -> None:
    service = AuthService()
    service.repository.sign_up = AsyncMock(
        return_value={
            "session": {"access_token": "access", "refresh_token": "refresh"},
            "user": {"id": "user-2", "email": "nopass@x.com"},
        }
    )

    result = await service.sign_up("nopass@x.com", None, "No Password")

    assert result["access_token"] == "access"
    _args, _kwargs = service.repository.sign_up.call_args
    generated = _args[1]
    assert isinstance(generated, str) and len(generated) >= 16


@pytest.mark.asyncio
async def test_sign_in_returns_flattened_session() -> None:
    service = AuthService()
    service.repository.sign_in = AsyncMock(
        return_value={
            "session": {"access_token": "access", "refresh_token": "refresh"},
            "user": {"id": "user-1", "email": "user@x.com"},
        }
    )

    result = await service.sign_in("user@x.com", "password123")

    assert result["access_token"] == "access"
    assert result["user"]["email"] == "user@x.com"
    service.repository.sign_in.assert_called_once_with("user@x.com", "password123")


@pytest.mark.asyncio
async def test_sign_in_wrong_password_maps_to_credentials_error() -> None:
    service = AuthService()
    service.repository.sign_in = AsyncMock(side_effect=Exception("Invalid login credentials"))

    with pytest.raises(AuthenticationError, match="check your credentials"):
        await service.sign_in("user@x.com", "wrong-password")


@pytest.mark.asyncio
async def test_google_auth_url_disabled_provider_maps_to_friendly_error() -> None:
    service = AuthService()
    service.repository.get_google_auth_url = MagicMock(
        side_effect=Exception("provider is disabled for this project")
    )

    with pytest.raises(AuthenticationError, match="not enabled"):
        await service.get_google_auth_url("fixly://auth/callback")


def test_planner_accepts_the_json_contract_requested_by_its_prompt() -> None:
    service = PlannerService()
    content = (
        '{"schedule_items":[{"title":"Math","description":"Review algebra",'
        '"start_time":"2026-08-25T09:00:00Z","end_time":"2026-08-25T10:00:00Z",'
        '"priority":"high","type":"study"}]}'
    )

    items = service._validate_schedule_items(content)

    assert items[0]["title"] == "Math"
