"""Goals, Skills, and Roadmap API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies.auth import CurrentUser, get_current_user
from app.services.goals_service import GoalsService

router = APIRouter(prefix="/goals", tags=["goals"])

def _get_service() -> GoalsService:
    return GoalsService()


@router.post("")
async def create_goal(
    body: dict,
    current_user: CurrentUser = Depends(get_current_user),
):
    svc = _get_service()
    try:
        goal = svc.create_goal(
            current_user.id,
            title=body.get("title", ""),
            description=body.get("description", ""),
            category=body.get("category", "academic"),
            target_date=body.get("target_date"),
        )
        return goal.to_dict()
    finally:
        svc.close()


@router.get("")
async def list_goals(
    status: str | None = None,
    current_user: CurrentUser = Depends(get_current_user),
):
    svc = _get_service()
    try:
        goals = svc.get_goals(current_user.id, status=status)
        return [g.to_dict() for g in goals]
    finally:
        svc.close()


@router.put("/{goal_id}/progress")
async def update_progress(
    goal_id: str,
    body: dict,
    current_user: CurrentUser = Depends(get_current_user),
):
    svc = _get_service()
    try:
        goal = svc.update_goal_progress(current_user.id, goal_id, body.get("progress", 0))
        if not goal:
            raise HTTPException(status_code=404, detail="Goal not found")
        return goal.to_dict()
    finally:
        svc.close()


skills_router = APIRouter(prefix="/skills", tags=["skills"])


@skills_router.post("")
async def create_skill(
    body: dict,
    current_user: CurrentUser = Depends(get_current_user),
):
    svc = _get_service()
    try:
        skill = svc.add_skill(
            current_user.id,
            name=body.get("name", ""),
            category=body.get("category", "academic"),
            level=body.get("level", "beginner"),
        )
        return skill.to_dict()
    finally:
        svc.close()


@skills_router.get("")
async def list_skills(
    category: str | None = None,
    current_user: CurrentUser = Depends(get_current_user),
):
    svc = _get_service()
    try:
        skills = svc.get_skills(current_user.id, category=category)
        return [s.to_dict() for s in skills]
    finally:
        svc.close()


roadmaps_router = APIRouter(prefix="/roadmaps", tags=["roadmaps"])


@roadmaps_router.post("")
async def create_roadmap(
    body: dict,
    current_user: CurrentUser = Depends(get_current_user),
):
    svc = _get_service()
    try:
        roadmap = svc.create_roadmap(
            current_user.id,
            title=body.get("title", ""),
            steps=body.get("steps", []),
            goal_id=body.get("goal_id"),
        )
        return roadmap.to_dict()
    finally:
        svc.close()


@roadmaps_router.get("")
async def list_roadmaps(
    current_user: CurrentUser = Depends(get_current_user),
):
    svc = _get_service()
    try:
        roadmaps = svc.get_roadmaps(current_user.id)
        return [r.to_dict() for r in roadmaps]
    finally:
        svc.close()
