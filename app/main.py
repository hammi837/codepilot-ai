from fastapi import Depends, FastAPI
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
from app.core.config import settings
from app.db.session import get_db

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(github_router, prefix="/api/v1")
app.include_router(ai_router, prefix="/api/v1")
app.include_router(embedding_router, prefix="/api/v1")
app.include_router(repository_router, prefix="/api/v1")
app.include_router(indexing_router, prefix="/api/v1")
app.include_router(chunking_router, prefix="/api/v1")
app.include_router(vector_router, prefix="/api/v1")
app.include_router(search_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")

@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "version": settings.VERSION,
    }


@app.get("/health")
def health() -> dict[str, object]:
    return {
        "status": "healthy",
        "debug": settings.DEBUG,
    }


@app.get("/db-test")
def db_test(db: Session = Depends(get_db)) -> dict[str, object]:
    try:
        db.execute(text("SELECT 1"))
        return {"database": "connected"}
    except Exception as exc:
        return {"database": "failed", "error": str(exc)}
