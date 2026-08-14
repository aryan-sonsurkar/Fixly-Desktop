from typing import Any

from supabase import Client

from app.core.logging import get_logger
from app.core.supabase import get_supabase, get_supabase_for_user
from app.repositories.utils import single_or_none

logger = get_logger(__name__)


class AuthRepository:
    def __init__(self, access_token: str | None = None) -> None:
        self.access_token = access_token
        self._client_instance: Client | None = None

    @property
    def _client(self) -> Client:
        if self._client_instance is None:
            self._client_instance = (
                get_supabase_for_user(self.access_token)
                if self.access_token
                else get_supabase()
            )
        return self._client_instance

    async def sign_up(
        self, email: str, password: str, full_name: str | None = None
    ) -> dict[str, Any]:
        credentials: dict[str, Any] = {"email": email, "password": password}
        if full_name:
            credentials["options"] = {"data": {"full_name": full_name}}
        response = self._client.auth.sign_up(credentials)  # type: ignore[arg-type]
        return response.model_dump() if hasattr(response, "model_dump") else dict(response)

    async def sign_in(self, email: str, password: str) -> dict[str, Any]:
        response = self._client.auth.sign_in_with_password({"email": email, "password": password})
        return response.model_dump() if hasattr(response, "model_dump") else dict(response)

    async def sign_out(self, token: str) -> None:
        self._client.auth.set_session(token, "")
        self._client.auth.sign_out()

    async def refresh_token(self, refresh_token: str) -> dict[str, Any]:
        response = self._client.auth.refresh_session(refresh_token)
        return response.model_dump() if hasattr(response, "model_dump") else dict(response)

    async def get_user(self, access_token: str) -> dict[str, Any] | None:
        try:
            response = self._client.auth.get_user(access_token)
            if not response:
                return None
            data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
            return data.get("user") or data
        except Exception as e:
            logger.error("Failed to get user", extra={"error": str(e)})
            return None

    async def get_profile(self, user_id: str) -> dict[str, Any] | None:
        return single_or_none(self._client.table("profiles").select("*").eq("id", user_id))

    async def reset_password_for_email(self, email: str) -> None:
        self._client.auth.reset_password_email(email)

    async def update_user(self, token: str, password: str) -> dict[str, Any]:
        self._client.auth.set_session(token, "")
        response = self._client.auth.update_user({"password": password})
        return response.model_dump() if hasattr(response, "model_dump") else dict(response)

    async def resend_verification(self, email: str) -> None:
        self._client.auth.resend({"email": email, "type": "signup"})

    def get_google_auth_url(self, redirect_uri: str) -> str:
        result = self._client.auth.sign_in_with_oauth(
            {"provider": "google", "options": {"redirect_to": redirect_uri}}
        )
        return result.url

    async def exchange_code_for_session(self, code: str, redirect_uri: str) -> dict[str, Any]:
        response = self._client.auth.exchange_code_for_session(
            {"auth_code": code, "redirect_to": redirect_uri}  # type: ignore[typeddict-item]
        )
        return response.model_dump() if hasattr(response, "model_dump") else dict(response)
