from fastapi import FastAPI

from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
)


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
