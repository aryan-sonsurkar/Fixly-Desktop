"""Workflow API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies.auth import CurrentUser, get_current_user
from app.services.workflow_engine import WorkflowEngine

router = APIRouter(prefix="/workflows", tags=["workflows"])

def _get_engine() -> WorkflowEngine:
    return WorkflowEngine()


@router.post("")
async def create_workflow(
    body: dict,
    current_user: CurrentUser = Depends(get_current_user),
):
    engine = _get_engine()
    wf = engine.create_workflow(
        user_id=current_user.id,
        name=body.get("name", "Unnamed Workflow"),
        steps=body.get("steps", []),
        description=body.get("description", ""),
    )
    return wf.to_dict()


@router.post("/template/{template_name}")
async def create_from_template(
    template_name: str,
    body: dict | None = None,
    current_user: CurrentUser = Depends(get_current_user),
):
    engine = _get_engine()
    try:
        wf = engine.create_from_template(
            current_user.id,
            template_name,
            variables=(body or {}).get("variables", {}),
        )
        return wf.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("")
async def list_workflows(
    status: str | None = None,
    current_user: CurrentUser = Depends(get_current_user),
):
    engine = _get_engine()
    wfs = engine.store.list_by_user(current_user.id, status=status)
    return [w.to_dict() for w in wfs]


@router.get("/templates")
async def list_templates():
    engine = _get_engine()
    return engine.list_templates()


@router.get("/{workflow_id}")
async def get_workflow(
    workflow_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    engine = _get_engine()
    wf = engine.store.get(workflow_id, current_user.id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return wf.to_dict()


@router.post("/{workflow_id}/execute")
async def execute_workflow(
    workflow_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    engine = _get_engine()
    wf = engine.store.get(workflow_id, current_user.id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    results = engine.execute_all(wf)
    return {
        "workflow": wf.to_dict(),
        "results": [r.to_dict() for r in results],
    }


@router.post("/{workflow_id}/pause")
async def pause_workflow(
    workflow_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    engine = _get_engine()
    wf = engine.store.get(workflow_id, current_user.id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    wf = engine.pause(wf)
    return wf.to_dict()


@router.post("/{workflow_id}/resume")
async def resume_workflow(
    workflow_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    engine = _get_engine()
    wf = engine.store.get(workflow_id, current_user.id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    wf = engine.resume(wf)
    return wf.to_dict()


@router.post("/{workflow_id}/cancel")
async def cancel_workflow(
    workflow_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    engine = _get_engine()
    wf = engine.store.get(workflow_id, current_user.id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    wf = engine.cancel(wf)
    return wf.to_dict()
