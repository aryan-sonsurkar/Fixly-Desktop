from datetime import date as date_func
from typing import Any

from fastapi import APIRouter, Depends, Query

from app.dependencies.auth import CurrentUser, get_current_user
from app.schemas.pomodoro import (
    PomodoroAnalytics,
    PomodoroSessionCreate,
    PomodoroSessionResponse,
    PomodoroSettings,
)
from app.services.pomodoro_service import PomodoroService

router = APIRouter(prefix="/pomodoro", tags=["pomodoro"])


@router.get("/settings", response_model=PomodoroSettings)
async def get_settings(
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    service = PomodoroService(access_token=current_user.access_token)
    return await service.get_settings(current_user.id)


@router.put("/settings", response_model=PomodoroSettings)
async def update_settings(
    body: PomodoroSettings,
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    service = PomodoroService(access_token=current_user.access_token)
    return await service.update_settings(current_user.id, body.model_dump(exclude_none=True))


@router.post("/sessions", response_model=PomodoroSessionResponse)
async def complete_session(
    body: PomodoroSessionCreate,
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    service = PomodoroService(access_token=current_user.access_token)
    return await service.complete_session(current_user.id, body.model_dump())


@router.get("/sessions")
async def get_sessions(
    date: str | None = Query(default=None),
    current_user: CurrentUser = Depends(get_current_user),
) -> list[dict[str, Any]]:
    service = PomodoroService(access_token=current_user.access_token)
    target = date or str(date_func.today())
    return await service.get_sessions_for_date(current_user.id, target)


@router.get("/analytics", response_model=PomodoroAnalytics)
async def get_analytics(
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    service = PomodoroService(access_token=current_user.access_token)
    return await service.get_analytics(current_user.id)
