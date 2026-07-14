from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse

from app.config import settings
from app.dependencies.auth import get_current_user
from app.schemas.auth import (
    AuthResponse,
    ForgotPasswordRequest,
    GoogleAuthRequest,
    ResendVerificationRequest,
    ResetPasswordRequest,
    SignInRequest,
    SignUpRequest,
    UserResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/signup", response_model=AuthResponse)
async def sign_up(body: SignUpRequest) -> dict[str, Any]:
    service = AuthService()
    result = await service.sign_up(body.email, body.password, body.full_name)
    return result


@router.post("/signin", response_model=AuthResponse)
async def sign_in(body: SignInRequest) -> dict[str, Any]:
    service = AuthService()
    result = await service.sign_in(body.email, body.password)
    return result


@router.post("/signout")
async def sign_out(current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, str]:
    service = AuthService()
    await service.sign_out(current_user.get("id", ""))
    return {"message": "Signed out successfully"}


@router.post("/refresh", response_model=AuthResponse)
async def refresh(body: dict[str, str]) -> dict[str, Any]:
    service = AuthService()
    result = await service.refresh_token(body["refresh_token"])
    return result


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    return {
        "id": current_user["id"],
        "email": current_user["email"],
        "profile": current_user.get("profile"),
        "user_metadata": current_user.get("user_metadata"),
    }


@router.post("/forgot-password")
async def forgot_password(body: ForgotPasswordRequest) -> dict[str, str]:
    service = AuthService()
    await service.forgot_password(body.email)
    return {"message": "Password reset email sent"}


@router.post("/reset-password")
async def reset_password(body: ResetPasswordRequest) -> dict[str, str]:
    service = AuthService()
    payload = await service.validate_token(body.access_token)
    user_id = payload.get("sub", "")
    await service.reset_password(user_id, body.new_password)
    return {"message": "Password reset successfully"}


@router.post("/resend-verification")
async def resend_verification(body: ResendVerificationRequest) -> dict[str, str]:
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
    type: str = "signup",
    request: Request = None,
) -> RedirectResponse:
    """
    Email verification callback from Supabase.
    In production, Supabase redirects here after user clicks verification link.
    For desktop app, this should redirect to deep link: fixly://auth/verified?token=<token>
    """
    # AuthService instance not needed for this endpoint - Supabase handles verification via redirect
    # We just redirect to the appropriate frontend/deep link URL

    try:
        # Verify the token with Supabase
        # In production, Supabase handles this automatically via the redirect
        # We just need to redirect to the desktop app via deep link

        if settings.environment == "development":
            # In dev, redirect to frontend verify page with token
            frontend_url = request.headers.get("origin", "http://localhost:1420") if request else "http://localhost:1420"
            return RedirectResponse(url=f"{frontend_url}/verify-email?verified=true&token={token}")

        # Production: redirect to deep link
        # TODO: Register fixly:// as custom URL scheme in Tauri config
        # TODO: Ensure Tauri handles deep links properly
        return RedirectResponse(url=f"fixly://auth/verified?token={token}&type={type}")
    except Exception:
        # On error, redirect to login with error
        if settings.environment == "development":
            frontend_url = request.headers.get("origin", "http://localhost:1420") if request else "http://localhost:1420"
            return RedirectResponse(url=f"{frontend_url}/login?error=verification_failed")
        return RedirectResponse(url="fixly://auth/login?error=verification_failed")


@router.get("/google/url")
async def google_auth_url() -> dict[str, str]:
    service = AuthService()
    url = await service.get_google_auth_url()
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
    redirect_uri: str,
    request: Request = None,
) -> RedirectResponse:
    """
    Google OAuth callback from Supabase.
    Supabase redirects here after user authorizes with Google.
    For desktop app, this should redirect to deep link: fixly://auth/callback?code=<code>
    """
    service = AuthService()

    try:
        result = await service.handle_google_callback(code, redirect_uri)
        session = result.get("session") or {}
        _user = result.get("user") or {}

        access_token = session.get("access_token", "")
        refresh_token = session.get("refresh_token", "")

        if settings.environment == "development":
            # In dev, redirect to frontend with tokens in hash fragment
            frontend_url = request.headers.get("origin", "http://localhost:1420") if request else "http://localhost:1420"
            return RedirectResponse(
                url=f"{frontend_url}/auth/callback#access_token={access_token}&refresh_token={refresh_token}"
            )

        # Production: redirect to deep link with tokens
        # TODO: Handle token storage securely in Tauri
        return RedirectResponse(
            url=f"fixly://auth/callback?access_token={access_token}&refresh_token={refresh_token}"
        )
    except Exception:
        if settings.environment == "development":
            frontend_url = request.headers.get("origin", "http://localhost:1420") if request else "http://localhost:1420"
            return RedirectResponse(url=f"{frontend_url}/login?error=google_auth_failed")
        return RedirectResponse(url="fixly://auth/login?error=google_auth_failed")
