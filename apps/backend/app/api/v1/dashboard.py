from typing import Any

from fastapi import APIRouter, Depends

from app.dependencies.auth import get_current_user
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("")
async def get_dashboard(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    service = DashboardService()
    return await service.get_dashboard(current_user["id"])


@router.get("/briefing")
async def get_daily_briefing(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    service = DashboardService()
    return await service.get_daily_briefing(current_user["id"])
