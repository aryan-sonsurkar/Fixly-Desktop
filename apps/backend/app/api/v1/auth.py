from typing import Any

from fastapi import APIRouter, Depends

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
    await service.reset_password(body.access_token, body.new_password)
    return {"message": "Password reset successfully"}


@router.post("/resend-verification")
async def resend_verification(body: ResendVerificationRequest) -> dict[str, str]:
    service = AuthService()
    await service.resend_verification(body.email)
    return {"message": "Verification email sent"}


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
