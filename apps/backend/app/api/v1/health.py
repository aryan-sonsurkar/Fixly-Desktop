from typing import Any

from fastapi import APIRouter, Request

from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["health"])


async def check_supabase() -> tuple[str, str | None]:
    try:
        from supabase import create_client

        client = create_client(settings.supabase_url, settings.supabase_anon_key)
        client.table("profiles").select("id").limit(1).execute()
        return "connected", None
    except Exception as e:
        logger.warning("Supabase health check failed", extra={"error": str(e)})
        return "disconnected", str(e)


async def check_ai() -> dict[str, Any]:
    """Check Fixly AI (bundled local model) availability."""
    try:
        from app.providers.fixly_local import FixlyLocalProvider

        provider = FixlyLocalProvider()
        detail = await provider.check_availability_detail()
        return {
            "installed": detail.get("installed", False),
            "running": detail.get("running", False),
            "model_count": detail.get("model_count", 0),
            "models": detail.get("models", []),
            "error": detail.get("error"),
        }
    except Exception as e:
        return {
            "installed": False,
            "running": False,
            "model_count": 0,
            "models": [],
            "error": str(e),
        }


@router.get("/health")
async def health(request: Request) -> dict[str, Any]:
    supabase_status, supabase_error = await check_supabase()
    fixly_ai = await check_ai()

    db_status = "connected"
    db_error = None
    if supabase_status != "connected":
        db_status = "disconnected"
        db_error = supabase_error

    ai_status = "available" if fixly_ai["running"] else "unconfigured"
    ai_provider = "fixly-local" if fixly_ai["running"] else None

    return {
        "status": "ok",
        "version": "0.1.0",
        "environment": settings.environment,
        "port": request.url.port or 8000,
        "supabase": supabase_status,
        "supabase_error": supabase_error,
        "database": db_status,
        "database_error": db_error,
        "ai": ai_status,
        "ai_provider": ai_provider,
        "ai_model": "qwen2-0.5b-instruct-q4_k_m.gguf" if fixly_ai["running"] else None,
        "ai_error": fixly_ai.get("error"),
        "ollama_installed": False,
        "ollama_running": False,
        "ollama_model_count": 0,
        "ollama_models": [],
        "sync": "healthy",
        "last_sync": None,
        "sync_error": None,
    }
