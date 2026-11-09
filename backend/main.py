from __future__ import annotations

import logging
import logging.config
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config import settings
from backend.database import init_db

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[type-arg]
    """Startup / shutdown lifecycle handler."""
    logger.info("Starting Customer Support Agent API (env=%s)", settings.environment)
    await init_db()
    logger.info("Database initialised successfully.")
    # Ensure Pinecone index exists (no-op if already created)
    from backend.services.pinecone_service import pinecone_service
    pinecone_service.ensure_index()
    logger.info("Pinecone index ready: %s", settings.pinecone_index_name)
    yield
    logger.info("Shutting down Customer Support Agent API.")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Customer Support Agent API",
    description="AI-powered customer support backend with LangGraph agent.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

from backend.api.admin import router as admin_router  # noqa: E402
from backend.api.chat import router as chat_router  # noqa: E402
from backend.api.health import router as health_router  # noqa: E402

app.include_router(health_router)
app.include_router(chat_router)
app.include_router(admin_router)


# ---------------------------------------------------------------------------
# Global exception handler
# ---------------------------------------------------------------------------


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception on %s %s: %s", request.method, request.url, exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please try again later."},
    )
