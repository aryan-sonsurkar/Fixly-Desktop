
from app.core.logging import get_logger
from app.core.supabase import get_supabase

logger = get_logger(__name__)

DEFAULT_WEIGHTS: dict[str, int] = {
    "pomodoro": 10,
    "assignment": 25,
    "ai_study": 8,
    "reading": 5,
    "manual": 6,
    "email": 3,
    "ocr": 4,
    "pdf_analysis": 7,
    "quiz": 12,
    "flashcard": 4,
    "revision": 15,
}

_weights_cache: dict[str, int] | None = None


def _load_weights() -> dict[str, int]:
    global _weights_cache
    if _weights_cache is not None:
        return _weights_cache
    try:
        client = get_supabase()
        response = client.table("study_points_config").select("activity_type, points").eq("is_active", True).execute()
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        rows = data.get("data", [])
        if rows:
            _weights_cache = {r["activity_type"]: r["points"] for r in rows}
            return _weights_cache
    except Exception as e:
        logger.warning("Failed to load weights from DB, using defaults: %s", e)
    _weights_cache = dict(DEFAULT_WEIGHTS)
    return _weights_cache


def reload_weights() -> None:
    global _weights_cache
    _weights_cache = None
    _load_weights()


def get_points(activity_type: str) -> int:
    weights = _load_weights()
    return weights.get(activity_type, 0)


def calculate_daily_goal_bonus(total_points: int, daily_goal: int = 50) -> int:
    if total_points >= daily_goal:
        return 15
    return 0
