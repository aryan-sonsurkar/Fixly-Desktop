from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.rate_limiter import auth_limiter

from app.config import settings
from app.dependencies.auth import CurrentUser, get_current_user
from app.schemas.auth import (
    AuthResponse,
    ForgotPasswordRequest,
    GoogleAuthRequest,
    RefreshTokenRequest,
    ResendVerificationRequest,
    ResetPasswordRequest,
    SignInRequest,
    SignUpRequest,
    UserResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/signup", response_model=AuthResponse)
async def sign_up(body: SignUpRequest, request: Request) -> dict[str, Any]:
    auth_limiter.check(request)
    service = AuthService()
    result = await service.sign_up(body.email, body.password, body.full_name)
    return result


@router.post("/signin", response_model=AuthResponse)
async def sign_in(body: SignInRequest, request: Request) -> dict[str, Any]:
    auth_limiter.check(request)
    service = AuthService()
    result = await service.sign_in(body.email, body.password)
    return result


@router.post("/signout")
async def sign_out(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
) -> dict[str, str]:
    service = AuthService()
    await service.sign_out(credentials.credentials if credentials else "")
    return {"message": "Signed out successfully"}


@router.post("/refresh", response_model=AuthResponse)
async def refresh(body: RefreshTokenRequest, request: Request) -> dict[str, Any]:
    auth_limiter.check(request)
    service = AuthService()
    result = await service.refresh_token(body.refresh_token)
    return result


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: CurrentUser = Depends(get_current_user)) -> dict[str, Any]:
    return {
        "id": current_user.id,
        "email": current_user.email,
        "profile": current_user.profile,
        "user_metadata": current_user.user_metadata,
    }


@router.post("/forgot-password")
async def forgot_password(body: ForgotPasswordRequest, request: Request) -> dict[str, str]:
    auth_limiter.check(request)
    service = AuthService()
    await service.forgot_password(body.email)
    return {"message": "Password reset email sent"}


@router.post("/reset-password")
async def reset_password(body: ResetPasswordRequest, request: Request) -> dict[str, str]:
    auth_limiter.check(request)
    service = AuthService()
    await service.validate_token(body.access_token)
    await service.reset_password(body.access_token, body.new_password)
    return {"message": "Password reset successfully"}


@router.post("/resend-verification")
async def resend_verification(body: ResendVerificationRequest, request: Request) -> dict[str, str]:
    auth_limiter.check(request)
    service = AuthService()
    await service.resend_verification(body.email)
    return {"message": "Verification email sent"}


# Production: Email verification callback
# TODO: When deploying to production:
# 1. Set Supabase site_url to production domain (e.g., https://fixly.app)
# 2. Add production domain to additional_redirect_urls in Supabase config
# 3. Configure email template to use production verification URL
# 4. This endpoint will be called by Supabase after user clicks verification link
@router.get("/verify-email", response_model=None)
async def verify_email(
    token: str,
    request: Request,
    type: str = "signup",
) -> RedirectResponse:
    try:
        if settings.environment == "development":
            frontend_url = request.headers.get("origin", "http://localhost:1420")
            return RedirectResponse(url=f"{frontend_url}/verify-email?verified=true&token={token}")

        return RedirectResponse(url=f"fixly://auth/verified?token={token}&type={type}")
    except Exception:
        if settings.environment == "development":
            frontend_url = request.headers.get("origin", "http://localhost:1420")
            return RedirectResponse(url=f"{frontend_url}/login?error=verification_failed")
        return RedirectResponse(url="fixly://auth/login?error=verification_failed")


@router.get("/google/status")
async def google_auth_status() -> dict[str, Any]:
    """Lightweight check so frontend can disable the button when provider not configured."""

    # Probe once – if get_google_auth_url would throw, we report unavailable
    service = AuthService()
    try:
        # Try to generate URL but do not return it; just test provider
        # Use a cheap path: check supabase config via env flag
        import os

        google_secret = os.environ.get("SUPABASE_AUTH_EXTERNAL_GOOGLE_SECRET", "")
        # Also check supabase/config.toml enabled flag could be false in dev
        if not google_secret and settings.environment == "development":
            return {"enabled": False, "reason": "Google OAuth not configured in development. Use email sign-in."}
        url = await service.get_google_auth_url()
        return {"enabled": bool(url), "url": url}
    except Exception as e:
        return {"enabled": False, "reason": str(e)}


@router.get("/google/url")
async def google_auth_url(redirect_to: str | None = None) -> dict[str, str]:
    service = AuthService()
    url = await service.get_google_auth_url(redirect_to)
    return {"url": url}


@router.post("/google/callback")
async def google_callback(body: GoogleAuthRequest) -> dict[str, Any]:
    service = AuthService()
    result = await service.handle_google_callback(body.code, body.redirect_uri)
    return result


# Production: Google OAuth callback
# TODO: When Google OAuth is configured in Supabase:
# 1. Add Google provider in Supabase dashboard with Client ID/Secret
# 2. Set redirect URI to: https://your-domain.com/auth/google/callback (web)
#    AND fixly://auth/callback (desktop deep link)
# 3. This endpoint will receive the callback from Supabase after Google auth
@router.get("/google/callback", response_model=None)
async def google_oauth_callback(
    code: str,
    request: Request,
    redirect_uri: str,
) -> RedirectResponse:
    service = AuthService()

    try:
        result = await service.handle_google_callback(code, redirect_uri)
        access_token = result.get("access_token", "")
        refresh_token = result.get("refresh_token", "")

        if settings.environment == "development":
            frontend_url = request.headers.get("origin", "http://localhost:1420")
            return RedirectResponse(
                url=f"{frontend_url}/auth/callback#access_token={access_token}&refresh_token={refresh_token}"
            )

        return RedirectResponse(
            url=f"fixly://auth/callback?access_token={access_token}&refresh_token={refresh_token}"
        )
    except Exception:
        if settings.environment == "development":
            frontend_url = request.headers.get("origin", "http://localhost:1420")
            return RedirectResponse(url=f"{frontend_url}/login?error=google_auth_failed")
        return RedirectResponse(url="fixly://auth/login?error=google_auth_failed")
