"""Opportunities API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies.auth import CurrentUser, get_current_user
from app.services.web_retrieval import OpportunityService

router = APIRouter(prefix="/opportunities", tags=["opportunities"])

def _get_service() -> OpportunityService:
    return OpportunityService()


@router.post("")
async def save_opportunity(
    body: dict,
    current_user: CurrentUser = Depends(get_current_user),
):
    svc = _get_service()
    try:
        opp = svc.save(
            current_user.id,
            title=body.get("title", ""),
            company=body.get("company", ""),
            category=body.get("category", "internship"),
            url=body.get("url"),
            description=body.get("description", ""),
            deadline=body.get("deadline"),
        )
        return opp.to_dict()
    finally:
        svc.close()


@router.get("")
async def list_opportunities(
    status: str | None = None,
    current_user: CurrentUser = Depends(get_current_user),
):
    svc = _get_service()
    try:
        opps = svc.list_saved(current_user.id, status=status)
        return [o.to_dict() for o in opps]
    finally:
        svc.close()


@router.put("/{opp_id}/status")
async def update_status(
    opp_id: str,
    body: dict,
    current_user: CurrentUser = Depends(get_current_user),
):
    svc = _get_service()
    try:
        opp = svc.update_status(current_user.id, opp_id, body.get("status", "saved"))
        if not opp:
            raise HTTPException(status_code=404, detail="Opportunity not found")
        return opp.to_dict()
    finally:
        svc.close()


@router.delete("/{opp_id}")
async def delete_opportunity(
    opp_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    svc = _get_service()
    try:
        deleted = svc.delete(current_user.id, opp_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Opportunity not found")
        return {"deleted": True}
    finally:
        svc.close()
