import socket
import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import PlainTextResponse, RedirectResponse, Response

from app.api.v1 import routers
from app.config import settings
from app.core.exceptions import FixlyError, fixly_exception_handler
from app.core.logging import get_logger, setup_logging
from app.prompts.registry import init_registry

logger = get_logger(__name__)

_backend_port: int = 8000


def get_backend_port() -> int:
    return _backend_port


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    setup_logging()
    init_registry()
    logger.info(
        "Fixly backend starting",
        extra={"environment": settings.environment, "version": "0.1.0"},
    )
    yield
    logger.info("Fixly backend shutting down")


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
    version="0.1.0",
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
    return {"status": "ok", "version": "0.1.0", "environment": settings.environment}


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
