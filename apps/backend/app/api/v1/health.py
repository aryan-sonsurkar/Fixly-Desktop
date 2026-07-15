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
        client.table("_health").select("1").limit(1).execute()
        return "connected", None
    except Exception as e:
        logger.warning("Supabase health check failed", extra={"error": str(e)})
        return "disconnected", str(e)


async def check_ollama() -> dict[str, Any]:
    try:
        import httpx

        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{settings.ollama_host}/api/tags")
            if resp.status_code == 200:
                data = resp.json()
                models = [m["name"] for m in data.get("models", [])]
                return {
                    "installed": True,
                    "running": True,
                    "model_count": len(models),
                    "models": models,
                    "error": None,
                }
            return {
                "installed": True,
                "running": False,
                "model_count": 0,
                "models": [],
                "error": "Ollama is not running",
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
    ollama = await check_ollama()

    db_status = "connected"
    db_error = None
    if supabase_status != "connected":
        db_status = "disconnected"
        db_error = supabase_error

    ai_status = "available" if (ollama["running"] or settings.gemini_api_key) else "unconfigured"
    ai_provider = "ollama" if ollama["running"] else "gemini" if settings.gemini_api_key else None

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
        "ai_model": None,
        "ai_error": None,
        "ollama_installed": ollama["installed"],
        "ollama_running": ollama["running"],
        "ollama_model_count": ollama["model_count"],
        "ollama_models": ollama["models"],
        "sync": "healthy",
        "last_sync": None,
        "sync_error": None,
    }
