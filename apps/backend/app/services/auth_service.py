import secrets
from typing import Any

from app.config import settings
from app.core.exceptions import AuthenticationError
from app.core.jwt import verify_token
from app.core.logging import get_logger
from app.repositories.auth_repository import AuthRepository

logger = get_logger(__name__)

# Client-library markers for Supabase being unreachable or transiently broken
# (supabase_auth AuthRetryableError/AuthUnknownError, httpx connect/timeout
# errors, HTTP 5xx). These must NEVER become 401: the desktop client treats a
# 401 on /auth/refresh as definitive session death and wipes stored tokens.
_TRANSIENT_MARKERS = (
    "connect", "timeout", "timed out", "network", "unreachable",
    "temporarily unavailable", "bad gateway", "service unavailable",
    "gateway timeout", "dns", "refused", "reset by peer",
    "502", "503", "504",
)
_TRANSIENT_TYPES = frozenset({
    "AuthRetryableError", "AuthUnknownError", "ConnectError", "ConnectTimeout",
    "ReadTimeout", "WriteTimeout", "PoolTimeout", "TimeoutException",
    "NetworkError", "NewConnectionError", "MaxRetryError",
})


def _is_transient_supabase_failure(exc: Exception) -> bool:
    """True when Supabase failed transiently (not a real auth rejection)."""
    status = getattr(exc, "status", None)
    if status is None:
        status = getattr(getattr(exc, "response", None), "status_code", None)
    if isinstance(status, int) and status >= 500:
        return True
    if type(exc).__name__ in _TRANSIENT_TYPES:
        return True
    text = f"{type(exc).__name__}: {exc}".lower()
    return any(m in text for m in _TRANSIENT_MARKERS)


class AuthService:
    def __init__(self, access_token: str | None = None) -> None:
        self.repository = AuthRepository(access_token)

    async def sign_up(
        self, email: str, password: str | None, full_name: str | None = None
    ) -> dict[str, Any]:
        try:
            # Account creation without authentication: no password is ever shown.
            # A random secret is generated server-side solely to satisfy Supabase.
            if not password:
                password = secrets.token_urlsafe(24)
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
            raise AuthenticationError("Sign up failed. Please try again.")

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
            raise AuthenticationError("Sign in failed. Please check your credentials.")

    async def sign_out(self, token: str) -> None:
        try:
            await self.repository.sign_out(token)
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
            if _is_transient_supabase_failure(e):
                # Supabase unreachable/transient: re-raise untouched so the
                # endpoint returns 5xx. The desktop client only wipes stored
                # tokens on 4xx; a 5xx keeps the session for a later retry.
                raise
            logger.error("Token refresh failed: %s", e)
            raise AuthenticationError("Session expired. Please sign in again.")

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

    async def reset_password(self, token: str, new_password: str) -> None:
        try:
            await self.repository.update_user(token, new_password)
        except Exception as e:
            logger.error("Reset password failed", extra={"error": str(e)})
            raise AuthenticationError("Could not reset password. The link may have expired.")

    async def resend_verification(self, email: str) -> None:
        try:
            await self.repository.resend_verification(email)
        except Exception as e:
            logger.error("Resend verification failed", extra={"error": str(e), "email": email})
            raise AuthenticationError("Could not resend verification email.")

    async def get_google_auth_url(self, redirect_to: str | None = None) -> str:
        # Default deep-link for desktop; allow caller to override for web flows
        target = redirect_to or "fixly://auth/callback"
        # Allow-list to avoid open-redirect and to surface clear errors for mis-config
        allowed = {
            "fixly://auth/callback",
            "fixly://auth/verified",
            "http://localhost:1420/auth/callback",
            "http://127.0.0.1:1420/auth/callback",
            "http://localhost:3000/auth/callback",
            "http://127.0.0.1:3000/auth/callback",
        }
        if target not in allowed and not target.startswith("http://localhost:") and not target.startswith("http://127.0.0.1:"):
            logger.warning("Blocked non-allowlisted OAuth redirect_to: %s", target)
            target = "fixly://auth/callback"
        try:
            url = self.repository.get_google_auth_url(target)
            # If Supabase returns a URL that still contains an error hint, surface it early
            if not url or "error" in url.lower():
                raise AuthenticationError("Google sign-in is not configured. Please use email to sign in.")
            return url
        except AuthenticationError:
            raise
        except Exception as e:
            msg = str(e).lower()
            # Supabase returns 400/422 when google provider disabled – translate to user-friendly
            disabled = ("disabled" in msg or "not enabled" in msg or "not configured" in msg)
            if "provider" in msg and disabled:
                raise AuthenticationError(
                    "Google sign-in is not enabled. Please use email or contact the administrator."
                )
            if "redirect_uri" in msg or "redirect" in msg:
                logger.error(
                    "Google OAuth redirect_uri mismatch – check Supabase allowed redirects "
                    "and Google Cloud authorized redirect URIs: %s", e
                )
                raise AuthenticationError(
                    "Google sign-in misconfigured (redirect_uri). "
                    "Add fixly://auth/callback to Supabase Auth allowed redirects."
                )
            logger.error("Failed to get Google auth URL: %s", e)
            raise AuthenticationError("Google authentication is currently unavailable. Please try email sign-in.")

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
            raise AuthenticationError("Google authentication failed. Please try again.")
