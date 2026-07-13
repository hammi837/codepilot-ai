import time
import logging
from fastapi import Depends, FastAPI, Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.v1.auth import router as auth_router
from app.api.v1.ai import router as ai_router
from app.api.v1.embedding import router as embedding_router
from app.api.v1.github import router as github_router
from app.api.v1.users import router as users_router
from app.api.v1.repository import router as repository_router
from app.api.v1.indexing import router as indexing_router
from app.api.v1.chunking import router as chunking_router
from app.api.v1.vector import router as vector_router
from app.api.v1.search import router as search_router
from app.api.v1.chat import router as chat_router
from app.api.v1.dashboard import router as dashboard_router
from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.core.exceptions import register_exception_handlers
from app.db.session import get_db

# ── Bootstrap logging first ────────────────────────────────────────────────
setup_logging()
logger = get_logger("main")

# ── Application factory ────────────────────────────────────────────────────
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "CodePilot AI — An AI-powered code intelligence platform. "
        "Clone any GitHub repo, index it semantically, and ask questions "
        "powered by RAG (Retrieval-Augmented Generation)."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ── Global exception handlers ──────────────────────────────────────────────
register_exception_handlers(app)

# ── Request / response logging middleware ──────────────────────────────────
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start) * 1000, 1)
    logger.info(
        f"{request.method} {request.url.path} → {response.status_code} ({duration_ms}ms)"
    )
    return response

# ── Routers ────────────────────────────────────────────────────────────────
app.include_router(auth_router,       prefix="/api/v1")
app.include_router(users_router,      prefix="/api/v1")
app.include_router(github_router,     prefix="/api/v1")
app.include_router(ai_router,         prefix="/api/v1")
app.include_router(embedding_router,  prefix="/api/v1")
app.include_router(repository_router, prefix="/api/v1")
app.include_router(indexing_router,   prefix="/api/v1")
app.include_router(chunking_router,   prefix="/api/v1")
app.include_router(vector_router,     prefix="/api/v1")
app.include_router(search_router,     prefix="/api/v1")
app.include_router(chat_router,       prefix="/api/v1")
app.include_router(dashboard_router,  prefix="/api/v1")


# ── Built-in endpoints ─────────────────────────────────────────────────────
@app.get("/", tags=["system"], summary="Welcome")
def root() -> dict[str, str]:
    """Root endpoint — confirms the API is running."""
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "version": settings.VERSION,
    }


@app.get("/health", tags=["system"], summary="Health check")
def health() -> dict[str, object]:
    """Returns application health status."""
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "debug": settings.DEBUG,
    }


@app.get("/db-test", tags=["system"], summary="Database connectivity test")
def db_test(db: Session = Depends(get_db)) -> dict[str, object]:
    """Verifies the database connection is alive."""
    try:
        db.execute(text("SELECT 1"))
        return {"database": "connected"}
    except Exception as exc:
        logger.error(f"Database connectivity check failed: {exc}")
        return {"database": "failed", "error": str(exc)}
