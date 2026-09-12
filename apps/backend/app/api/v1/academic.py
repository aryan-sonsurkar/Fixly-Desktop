"""Academic Profile API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.dependencies.auth import CurrentUser, get_current_user
from app.services.academic_profile import AcademicProfileService
from app.services.weakness_detector import WeaknessDetector

router = APIRouter(prefix="/academic", tags=["academic"])

def _get_service() -> AcademicProfileService:
    return AcademicProfileService()


@router.get("/profile")
async def get_profile(
    current_user: CurrentUser = Depends(get_current_user),
):
    svc = _get_service()
    try:
        profile = svc.get_profile(current_user.id)
        return profile.to_dict()
    finally:
        svc.close()


@router.post("/scores")
async def update_score(
    body: dict,
    current_user: CurrentUser = Depends(get_current_user),
):
    svc = _get_service()
    try:
        profile = svc.update_score(
            current_user.id,
            subject=body.get("subject", ""),
            score=body.get("score", 0),
        )
        return profile.to_dict()
    finally:
        svc.close()


@router.get("/weak-subjects")
async def get_weak_subjects(
    threshold: float = 60.0,
    current_user: CurrentUser = Depends(get_current_user),
):
    svc = _get_service()
    try:
        weak = svc.get_weak_subjects(current_user.id, threshold=threshold)
        return {"weak_subjects": weak}
    finally:
        svc.close()


@router.get("/recommendations")
async def get_recommendations(
    current_user: CurrentUser = Depends(get_current_user),
):
    svc = _get_service()
    try:
        recs = svc.get_study_recommendations(current_user.id)
        return recs
    finally:
        svc.close()


@router.get("/weaknesses")
async def detect_weaknesses(
    current_user: CurrentUser = Depends(get_current_user),
):
    svc = _get_service()
    try:
        detector = WeaknessDetector(svc)
        signals = detector.detect(current_user.id)
        return [{"subject": s.subject, "topic": s.topic, "type": s.signal_type,
                 "severity": s.severity, "evidence": s.evidence,
                 "recommendation": s.recommendation} for s in signals]
    finally:
        svc.close()


@router.get("/health")
async def get_subject_health(
    current_user: CurrentUser = Depends(get_current_user),
):
    svc = _get_service()
    try:
        detector = WeaknessDetector(svc)
        health = detector.get_subject_health(current_user.id)
        return health
    finally:
        svc.close()
