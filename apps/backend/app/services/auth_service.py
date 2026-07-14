from typing import Any

from app.config import settings
from app.core.exceptions import AuthenticationError
from app.core.jwt import verify_token
from app.core.logging import get_logger
from app.repositories.auth_repository import AuthRepository

logger = get_logger(__name__)


class AuthService:
    def __init__(self) -> None:
        self.repository = AuthRepository()

    async def sign_up(
        self, email: str, password: str, full_name: str | None = None
    ) -> dict[str, Any]:
        try:
            result = await self.repository.sign_up(email, password, full_name)
            session = result.get("session") or {}
            user = result.get("user") or {}

            # In development, if no session (email not confirmed), create a temporary session
            # by signing in immediately. This allows dev without email verification.
            if not session.get("access_token") and settings.environment == "development":
                logger.info("Development mode: email not confirmed, attempting immediate sign in")
                sign_in_result = await self.repository.sign_in(email, password)
                session = sign_in_result.get("session") or {}
                user = sign_in_result.get("user") or {}

            return {
                "access_token": session.get("access_token", ""),
                "refresh_token": session.get("refresh_token", ""),
                "user": user,
            }
        except AuthenticationError:
            raise
        except Exception as e:
            error_msg = str(e).lower()
            if "already exists" in error_msg or "already registered" in error_msg:
                raise AuthenticationError("An account with this email already exists.")
            logger.error("Sign up failed: %s", e)
            raise AuthenticationError(f"Sign up failed: {e}")

    async def sign_in(self, email: str, password: str) -> dict[str, Any]:
        try:
            result = await self.repository.sign_in(email, password)
            session = result.get("session") or {}
            user = result.get("user") or {}
            return {
                "access_token": session.get("access_token", ""),
                "refresh_token": session.get("refresh_token", ""),
                "user": user,
            }
        except AuthenticationError:
            raise
        except Exception as e:
            error_msg = str(e).lower()
            if "email not confirmed" in error_msg:
                if settings.environment == "development":
                    logger.info("Development mode: email not confirmed, attempting sign up flow")
                    try:
                        # Try to sign up (which will auto-confirm in dev)
                        sign_up_result = await self.repository.sign_up(email, password)
                        session = sign_up_result.get("session") or {}
                        user = sign_up_result.get("user") or {}
                        return {
                            "access_token": session.get("access_token", ""),
                            "refresh_token": session.get("refresh_token", ""),
                            "user": user,
                        }
                    except Exception:
                        pass
                raise AuthenticationError("Please verify your email before signing in.")
            logger.error("Sign in failed: %s", e)
            raise AuthenticationError(f"Sign in failed: {e}")

    async def sign_out(self, user_id: str) -> None:
        try:
            await self.repository.sign_out(user_id)
        except Exception as e:
            logger.error("Sign out failed", extra={"error": str(e)})

    async def refresh_token(self, refresh_token: str) -> dict[str, Any]:
        try:
            result = await self.repository.refresh_token(refresh_token)
            session = result.get("session") or {}
            user = result.get("user") or {}
            return {
                "access_token": session.get("access_token", ""),
                "refresh_token": session.get("refresh_token", ""),
                "user": user,
            }
        except AuthenticationError:
            raise
        except Exception as e:
            logger.error("Token refresh failed: %s", e)
            raise AuthenticationError(f"Session expired: {e}")

    async def validate_token(self, token: str) -> dict[str, Any]:
        payload = await verify_token(token)
        if not payload:
            raise AuthenticationError("Invalid or expired token.")
        return payload

    async def get_current_user(self, token: str) -> dict[str, Any]:
        payload = await self.validate_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationError("Invalid token payload.")
        user = await self.repository.get_user(token)
        if not user:
            raise AuthenticationError("User not found.")
        profile = await self.repository.get_profile(user_id)
        return {
            "id": user_id,
            "email": payload.get("email", ""),
            "profile": profile or {},
            "user_metadata": user.get("user_metadata", {}),
        }

    async def forgot_password(self, email: str) -> None:
        try:
            await self.repository.reset_password_for_email(email)
        except Exception as e:
            logger.error("Forgot password failed", extra={"error": str(e), "email": email})
            raise AuthenticationError("Could not send reset email. Please try again.")

    async def reset_password(self, user_id: str, new_password: str) -> None:
        try:
            await self.repository.update_user(user_id, new_password)
        except Exception as e:
            logger.error("Reset password failed", extra={"error": str(e)})
            raise AuthenticationError("Could not reset password. The link may have expired.")

    async def resend_verification(self, email: str) -> None:
        try:
            await self.repository.resend_verification(email)
        except Exception as e:
            logger.error("Resend verification failed", extra={"error": str(e), "email": email})
            raise AuthenticationError("Could not resend verification email.")

    async def get_google_auth_url(self) -> str:
        try:
            return self.repository.get_google_auth_url("fixly://auth/callback")
        except AuthenticationError:
            raise
        except Exception as e:
            logger.error("Failed to get Google auth URL: %s", e)
            raise AuthenticationError(f"Google auth unavailable: {e}")

    async def handle_google_callback(self, code: str, redirect_uri: str) -> dict[str, Any]:
        try:
            result = await self.repository.exchange_code_for_session(code, redirect_uri)
            session = result.get("session") or {}
            user = result.get("user") or {}
            return {
                "access_token": session.get("access_token", ""),
                "refresh_token": session.get("refresh_token", ""),
                "user": user,
            }
        except AuthenticationError:
            raise
        except Exception as e:
            logger.error("Google auth callback failed: %s", e)
            raise AuthenticationError(f"Google authentication failed: {e}")
