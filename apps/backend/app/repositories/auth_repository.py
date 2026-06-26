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
