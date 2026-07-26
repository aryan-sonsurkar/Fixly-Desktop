import socket
import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from typing import Any

from fastapi import FastAPI
from starlette.datastructures import Headers
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response

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


CORS_HEADERS: dict[str, str] = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "*",
    "Access-Control-Allow-Headers": "*",
    "Access-Control-Max-Age": "86400",
}


async def cors_middleware(request: Request, call_next: Any) -> Response:
    if request.method == "OPTIONS":
        return PlainTextResponse("", status_code=204, headers=dict(CORS_HEADERS))
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response


app = FastAPI(
    title="Fixly API",
    version="0.1.0",
    description="Fixly - AI-powered academic operating system",
    lifespan=lifespan,
)

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
