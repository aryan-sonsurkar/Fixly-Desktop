import socket
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.core.logging import get_logger, setup_logging

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info(
        "Fixly backend starting",
        extra={"environment": settings.environment, "version": "0.1.0"},
    )
    yield
    logger.info("Fixly backend shutting down")


app = FastAPI(
    title="Fixly API",
    version="0.1.0",
    description="Fixly - AI-powered academic operating system",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0", "environment": settings.environment}


if __name__ == "__main__":
    import uvicorn

    port = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    if port == 0:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            port = s.getsockname()[1]
    print(f"FIXLY_PORT:{port}", flush=True)
    uvicorn.run("app.main:app", host="127.0.0.1", port=port, reload=False)
