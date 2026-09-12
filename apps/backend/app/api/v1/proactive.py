"""Proactive Nudges API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.dependencies.auth import CurrentUser, get_current_user
from app.services.proactive_engine import ProactiveEngine

router = APIRouter(prefix="/proactive", tags=["proactive"])

_engine = ProactiveEngine()


@router.get("/nudges")
async def get_nudges(
    current_user: CurrentUser = Depends(get_current_user),
):
    nudges = _engine.get_nudges(current_user.id)
    return [n.to_dict() for n in nudges]


@router.post("/nudges/{nudge_id}/dismiss")
async def dismiss_nudge(
    nudge_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    dismissed = _engine.dismiss(current_user.id, nudge_id)
    return {"dismissed": dismissed}


@router.post("/check-deadlines")
async def check_deadlines(
    body: dict,
    current_user: CurrentUser = Depends(get_current_user),
):
    assignments = body.get("assignments", [])
    nudges = _engine.check_deadlines(current_user.id, assignments)
    return [n.to_dict() for n in nudges]
