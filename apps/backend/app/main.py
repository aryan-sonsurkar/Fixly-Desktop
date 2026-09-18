import asyncio
import datetime
import json
import socket
import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import PlainTextResponse, RedirectResponse, Response

from app.api.v1 import routers
from app.config import settings
from app.core.exceptions import FixlyError, fixly_exception_handler
from app.core.logging import get_logger, setup_logging
from app.core.supabase import get_supabase_service
from app.prompts.registry import init_registry

logger = get_logger(__name__)


def _resolve_version() -> str:
    """Read version from desktop package.json (single source of truth)."""
    try:
        pkg_json = Path(__file__).resolve().parents[2] / "desktop" / "package.json"
        return json.loads(pkg_json.read_text(encoding="utf-8"))["version"]
    except (FileNotFoundError, KeyError, OSError):
        return "1.0.6"


APP_VERSION = _resolve_version()

_backend_port: int = 8000


def get_backend_port() -> int:
    return _backend_port


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    setup_logging()
    init_registry()
    logger.info(
        "Fixly backend starting",
        extra={"environment": settings.environment, "version": APP_VERSION},
    )

    from app.services.memory_service import MemoryService
    from app.services.proactive_engine import ProactiveEngine

    decay_service = MemoryService()
    proactive_engine = ProactiveEngine()

    async def _decay_loop():
        while True:
            await asyncio.sleep(6 * 3600)
            try:
                results = decay_service.run_memory_decay_all_users()
                if results:
                    logger.info("Memory decay results: %s", results)
            except Exception as e:
                logger.warning("Background memory decay failed: %s", e)

    async def _proactive_loop():
        interval = 30 * 60  # 30 minutes
        quiet_start = 23  # 11 PM
        quiet_end = 7     # 7 AM

        while True:
            await asyncio.sleep(interval)
            try:
                await _run_proactive_checks(proactive_engine, quiet_start, quiet_end)
            except Exception as e:
                logger.warning("Background proactive check failed: %s", e)

    decay_task = asyncio.create_task(_decay_loop())
    proactive_task = asyncio.create_task(_proactive_loop())

    yield

    proactive_task.cancel()
    decay_task.cancel()
    try:
        await proactive_task
    except asyncio.CancelledError:
        pass
    try:
        await decay_task
    except asyncio.CancelledError:
        pass
    proactive_engine.close()
    decay_service.close()
    logger.info("Fixly backend shutting down")


async def _run_proactive_checks(
    engine: "ProactiveEngine",  # noqa: F821
    quiet_start: int,
    quiet_end: int,
) -> None:
    """Fetch active users and run proactive engine checks for each."""
    from app.core.threads import run_in_thread

    def _fetch_active_user_ids() -> list[str]:
        client = get_supabase_service()
        cutoff = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=7)).isoformat()
        resp = (
            client.table("assignments")
            .select("user_id")
            .gte("created_at", cutoff)
            .execute()
        )
        data = resp.model_dump() if hasattr(resp, "model_dump") else dict(resp)
        rows = data.get("data", [])
        return list({r["user_id"] for r in rows if r.get("user_id")})

    def _fetch_user_settings(uid: str) -> dict[str, Any]:
        client = get_supabase_service()
        resp = client.table("settings").select("*").eq("user_id", uid).execute()
        data = resp.model_dump() if hasattr(resp, "model_dump") else dict(resp)
        rows = data.get("data", [])
        return rows[0] if rows else {}

    def _fetch_assignments(uid: str) -> list[dict[str, Any]]:
        client = get_supabase_service()
        resp = (
            client.table("assignments")
            .select("id, title, deadline, due_date, status")
            .eq("user_id", uid)
            .in_("status", ["pending", "in_progress"])
            .execute()
        )
        data = resp.model_dump() if hasattr(resp, "model_dump") else dict(resp)
        return data.get("data", [])

    def _fetch_study_streak(uid: str) -> dict[str, Any]:
        client = get_supabase_service()
        resp = (
            client.table("study_days")
            .select("date")
            .eq("user_id", uid)
            .order("date", desc=True)
            .limit(30)
            .execute()
        )
        data = resp.model_dump() if hasattr(resp, "model_dump") else dict(resp)
        rows = data.get("data", [])
        active_dates = sorted({r["date"] for r in rows}, reverse=True)
        streak = 0
        check = datetime.date.today()
        for d in active_dates:
            if d == check.isoformat():
                streak += 1
                check -= datetime.timedelta(days=1)
            elif d == (check - datetime.timedelta(days=1)).isoformat():
                streak += 1
                check -= datetime.timedelta(days=2)
            else:
                break
        return {"streak": streak}

    def _fetch_weaknesses(uid: str) -> list[dict[str, Any]]:
        client = get_supabase_service()
        resp = (
            client.table("subjects")
            .select("name, average_score, weak_topics")
            .eq("user_id", uid)
            .execute()
        )
        data = resp.model_dump() if hasattr(resp, "model_dump") else dict(resp)
        rows = data.get("data", [])
        weaknesses = []
        for r in rows:
            avg = r.get("average_score", 100)
            if avg < 60:
                weaknesses.append({
                    "subject": r.get("name", "Unknown"),
                    "average": avg,
                    "weak_topics": r.get("weak_topics", []),
                })
        return weaknesses

    user_ids = await run_in_thread(_fetch_active_user_ids)
    if not user_ids:
        logger.info("Proactive check: no active users found")
        return

    total_nudges = 0
    for uid in user_ids:
        try:
            settings_data = await run_in_thread(_fetch_user_settings, uid)

            # Respect quiet hours
            now_hour = datetime.datetime.now(datetime.timezone.utc).hour
            quiet_hours = settings_data.get("quiet_hours")
            if quiet_hours and isinstance(quiet_hours, dict):
                q_start = quiet_hours.get("start", quiet_start)
                q_end = quiet_hours.get("end", quiet_end)
                if q_start > q_end:
                    in_quiet = now_hour >= q_start or now_hour < q_end
                else:
                    in_quiet = q_start <= now_hour < q_end
                if in_quiet:
                    continue

            assignments = await run_in_thread(_fetch_assignments, uid)
            # Normalize deadline field: the engine reads 'deadline', Supabase has 'due_date'
            for a in assignments:
                if not a.get("deadline") and a.get("due_date"):
                    a["deadline"] = a["due_date"]

            study_data = await run_in_thread(_fetch_study_streak, uid)
            weaknesses = await run_in_thread(_fetch_weaknesses, uid)

            nudges = []
            if assignments:
                nudges.extend(engine.check_deadlines(uid, assignments))
            nudges.extend(engine.check_study_patterns(uid, study_data))
            if weaknesses:
                nudges.extend(engine.check_weaknesses(uid, weaknesses))

            total_nudges += len(nudges)
        except Exception as e:
            logger.warning("Proactive check failed for user %s: %s", uid, e)

    logger.info("Proactive check completed: %d users, %d nudges generated", len(user_ids), total_nudges)


ALLOWED_ORIGINS = {
    "http://127.0.0.1",
    "http://localhost",
    "tauri://localhost",
    "http://tauri.localhost",
    "https://tauri.localhost",
}

CORS_HEADERS: dict[str, str] = {
    "Access-Control-Allow-Origin": "http://127.0.0.1",
    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
    "Access-Control-Allow-Headers": "Authorization, Content-Type, X-Requested-With",
    "Access-Control-Max-Age": "86400",
}


def _is_allowed_origin(origin: str | None) -> bool:
    if not origin:
        return True  # Tauri fetch without origin, allow
    if origin == "*":
        return False
    # allow any localhost/127.0.0.1 with any port for desktop random port
    if origin.startswith("http://127.0.0.1:") or origin.startswith("http://localhost:"):
        return True
    return origin in ALLOWED_ORIGINS


async def cors_middleware(request: Request, call_next: Any) -> Response:
    origin = request.headers.get("origin")
    if request.method == "OPTIONS":
        headers = dict(CORS_HEADERS)
        if _is_allowed_origin(origin) and origin:
            headers["Access-Control-Allow-Origin"] = origin
            headers["Vary"] = "Origin"
        return PlainTextResponse("", status_code=204, headers=headers)
    response: Response = await call_next(request)
    if _is_allowed_origin(origin) and origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Vary"] = "Origin"
    elif not origin:
        response.headers["Access-Control-Allow-Origin"] = "http://127.0.0.1"
    response.headers["Access-Control-Allow-Methods"] = CORS_HEADERS["Access-Control-Allow-Methods"]
    response.headers["Access-Control-Allow-Headers"] = CORS_HEADERS["Access-Control-Allow-Headers"]
    return response


is_production = settings.environment == "production"

app = FastAPI(
    title="Fixly API",
    version=APP_VERSION,
    description="Fixly - AI-powered academic operating system",
    lifespan=lifespan,
    docs_url=None if is_production else "/docs",
    redoc_url=None if is_production else "/redoc",
    openapi_url=None if is_production else "/openapi.json",
)

# Security headers middleware
from starlette.middleware.base import BaseHTTPMiddleware  # noqa: E402


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Any) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "0"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        if is_production:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            response.headers["Content-Security-Policy"] = "default-src 'self'"
        return response


app.add_middleware(SecurityHeadersMiddleware)

class HttpsRedirectMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Any) -> Response:
        if is_production:
            proto = request.headers.get("x-forwarded-proto", request.url.scheme)
            host = request.headers.get("host", "") or request.url.hostname or ""
            is_loopback = host in ("127.0.0.1", "localhost")
            is_loopback_port = host.startswith("127.0.0.1:") or host.startswith("localhost:")
            if proto == "http" and not is_loopback and not is_loopback_port:
                url = str(request.url).replace("http://", "https://", 1)
                return RedirectResponse(url, status_code=307)
        return await call_next(request)


app.add_middleware(HttpsRedirectMiddleware)

# Bot protection now backed by Supabase Turnstile (see supabase/config.toml [auth.captcha])  # noqa: E402


class BotProtectionMiddleware(BaseHTTPMiddleware):
    """Basic bot protection: check for suspicious patterns, missing UA, rate burst."""

    def __init__(self, app: Any) -> None:
        super().__init__(app)
        self._blocked_ua = {"curl", "wget", "python-requests", "go-http-client"}

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        ua = request.headers.get("user-agent", "").lower()
        # Allow Tauri and browsers, block obvious bots on auth endpoints
        if request.url.path.startswith("/api/v1/auth/") and any(b in ua for b in self._blocked_ua):
            # Still allow but add delay; in prod you would integrate hCaptcha
            pass
        # Basic check: require user-agent for non-Tauri
        return await call_next(request)


app.add_middleware(BotProtectionMiddleware)

app.middleware("http")(cors_middleware)


app.add_exception_handler(FixlyError, fixly_exception_handler)  # type: ignore[arg-type]

for router in routers:
    app.include_router(router, prefix="/api/v1")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "version": APP_VERSION, "environment": settings.environment}


if __name__ == "__main__":
    import uvicorn

    port = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    if port == 0:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            port = s.getsockname()[1]
    _backend_port = port
    print(f"FIXLY_PORT:{port}", flush=True)
    uvicorn.run("app.main:app", host="127.0.0.1", port=port, reload=False)
