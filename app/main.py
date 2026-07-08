from fastapi import FastAPI

from app.core.config import settings

app = FastAPI(
    title=settings.project_name,
    version=settings.version,
)


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Welcome to CodePilot AI"}


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "healthy"}
