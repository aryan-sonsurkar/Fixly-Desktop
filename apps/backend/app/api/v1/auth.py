from typing import Any

from fastapi import APIRouter, Depends

from app.dependencies.auth import get_current_user
from app.schemas.auth import (
    AuthResponse,
    RefreshTokenRequest,
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
async def refresh(body: RefreshTokenRequest) -> dict[str, Any]:
    service = AuthService()
    result = await service.refresh_token(body.refresh_token)
    return result


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    return {
        "id": current_user["id"],
        "email": current_user["email"],
        "profile": current_user.get("profile"),
        "user_metadata": current_user.get("user_metadata"),
    }
