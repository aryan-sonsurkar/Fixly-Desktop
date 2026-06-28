from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, Query

from app.dependencies.auth import get_current_user
from app.schemas.study import (
    CalendarResponse,
    DayDetail,
    StudyDayUpdate,
    StudySessionCreate,
    StudyStatistics,
    StudyStreak,
)
from app.services.study_service import StudyService

router = APIRouter(prefix="/study", tags=["study"])


@router.get("/calendar", response_model=CalendarResponse)
async def get_calendar(
    year: int = Query(default_factory=lambda: date.today().year),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    service = StudyService()
    return await service.get_calendar(current_user["id"], year)


@router.get("/day/{day_date}", response_model=DayDetail)
async def get_day(
    day_date: str,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    service = StudyService()
    return await service.get_day_detail(current_user["id"], day_date)


@router.put("/day/{day_date}", response_model=DayDetail)
async def update_day(
    day_date: str,
    body: StudyDayUpdate,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    service = StudyService()
    return await service.update_day(
        current_user["id"], day_date, body.model_dump(exclude_none=True)
    )


@router.post("/session")
async def log_session(
    body: StudySessionCreate,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    service = StudyService()
    return await service.log_session(current_user["id"], body.model_dump())


@router.get("/statistics", response_model=StudyStatistics)
async def get_statistics(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    service = StudyService()
    return await service.get_statistics(current_user["id"])


@router.get("/streak", response_model=StudyStreak)
async def get_streak(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    service = StudyService()
    return await service.get_streak(current_user["id"])
