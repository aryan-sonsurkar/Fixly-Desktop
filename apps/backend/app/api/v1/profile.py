from typing import Any

from fastapi import APIRouter, Depends

from app.dependencies.auth import get_current_user
from app.schemas.profile import (
    OnboardingRequest,
    ProfileResponse,
    ProfileUpdate,
    SettingsResponse,
    SettingsUpdate,
)
from app.services.profile_service import ProfileService
from app.services.subject_service import SubjectService

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("/me", response_model=ProfileResponse)
async def get_my_profile(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    service = ProfileService()
    profile = await service.get_profile(current_user["id"])
    return profile


@router.put("/me", response_model=ProfileResponse)
async def update_my_profile(
    body: ProfileUpdate,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    service = ProfileService()
    result = await service.update_profile(
        current_user["id"], body.model_dump(exclude_none=True)
    )
    return result


@router.get("/settings", response_model=SettingsResponse)
async def get_my_settings(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    service = ProfileService()
    settings = await service.get_settings(current_user["id"])
    return settings


@router.put("/settings", response_model=SettingsResponse)
async def update_my_settings(
    body: SettingsUpdate,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    service = ProfileService()
    result = await service.update_settings(
        current_user["id"], body.model_dump(exclude_none=True)
    )
    return result


@router.post("/onboarding")
async def complete_onboarding(
    body: OnboardingRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    profile_service = ProfileService()
    subject_service = SubjectService()

    result = await profile_service.complete_onboarding(
        current_user["id"],
        body.profile.model_dump(exclude_none=True) if body.profile else {},
        body.settings.model_dump(exclude_none=True) if body.settings else {},
    )

    if body.subjects:
        await subject_service.bulk_create(current_user["id"], body.subjects)

    return result


@router.get("/onboarding/status")
async def check_onboarding_status(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, bool]:
    service = ProfileService()
    return await service.check_onboarding(current_user["id"])
