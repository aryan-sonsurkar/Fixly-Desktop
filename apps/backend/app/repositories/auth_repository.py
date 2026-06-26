from typing import Any

from app.core.logging import get_logger
from app.core.supabase import get_supabase

logger = get_logger(__name__)


class AuthRepository:
    async def sign_up(
        self, email: str, password: str, full_name: str | None = None
    ) -> dict[str, Any]:
        client = get_supabase()
        credentials: dict[str, Any] = {"email": email, "password": password}
        if full_name:
            credentials["options"] = {"data": {"full_name": full_name}}
        response = client.auth.sign_up(credentials)  # type: ignore[arg-type]
        return response.model_dump() if hasattr(response, "model_dump") else dict(response)

    async def sign_in(self, email: str, password: str) -> dict[str, Any]:
        client = get_supabase()
        response = client.auth.sign_in_with_password({"email": email, "password": password})
        return response.model_dump() if hasattr(response, "model_dump") else dict(response)

    async def sign_out(self, access_token: str) -> None:
        client = get_supabase()
        client.auth.admin.sign_out(access_token)

    async def refresh_token(self, refresh_token: str) -> dict[str, Any]:
        client = get_supabase()
        response = client.auth.refresh_session(refresh_token)
        return response.model_dump() if hasattr(response, "model_dump") else dict(response)

    async def get_user(self, access_token: str) -> dict[str, Any] | None:
        client = get_supabase()
        try:
            response = client.auth.get_user(access_token)
            if not response:
                return None
            data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
            return data.get("user") or data
        except Exception as e:
            logger.error("Failed to get user", extra={"error": str(e)})
            return None

    async def get_profile(self, user_id: str) -> dict[str, Any] | None:
        client = get_supabase()
        response = client.table("profiles").select("*").eq("id", user_id).single().execute()
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        return data.get("data") or data

    async def reset_password_for_email(self, email: str) -> None:
        client = get_supabase()
        client.auth.reset_password_email(email)

    async def update_user(self, access_token: str, password: str) -> dict[str, Any]:
        client = get_supabase()
        response = client.auth.admin.update_user_by_id(access_token, {"password": password})
        return response.model_dump() if hasattr(response, "model_dump") else dict(response)

    async def resend_verification(self, email: str) -> None:
        client = get_supabase()
        client.auth.resend({"email": email, "type": "signup"})

    def get_google_auth_url(self, redirect_uri: str) -> str:
        client = get_supabase()
        result = client.auth.sign_in_with_oauth(
            {"provider": "google", "options": {"redirect_to": redirect_uri}}
        )
        return result.url

    async def exchange_code_for_session(self, code: str, redirect_uri: str) -> dict[str, Any]:
        client = get_supabase()
        response = client.auth.exchange_code_for_session(
            {"auth_code": code, "redirect_to": redirect_uri}  # type: ignore[typeddict-item]
        )
        return response.model_dump() if hasattr(response, "model_dump") else dict(response)
