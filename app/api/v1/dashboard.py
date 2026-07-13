"""
Repository Dashboard & Background Indexing API
- GET  /repositories/dashboard/{repository} — analytics
- POST /repositories/index/{repository}     — full index (background)
- POST /repositories/reindex/{repository}   — incremental re-index (background)
"""
from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from app.schemas.conversation import RepositoryStats
from app.services.chunking_service import ChunkingService
from app.services.vector_service import VectorService
from app.workers.indexing_worker import full_index_job, incremental_index_job

router = APIRouter(prefix="/repositories", tags=["repositories"])


@router.get("/dashboard/{repository:path}", response_model=RepositoryStats)
def repository_dashboard(repository: str) -> RepositoryStats:
    """Return analytics for an indexed repository."""
    repo_name = repository.split("/")[-1]

    try:
        chunking_service = ChunkingService()
        chunks = chunking_service.chunk_repository(repo_name)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    # Count unique files
    unique_files = len({c.metadata.file for c in chunks})

    vector_service = VectorService()
    collections = vector_service.list_collections()

    return RepositoryStats(
        repository=repo_name,
        files=unique_files,
        chunks=len(chunks),
        embeddings=len(chunks),   # 1:1 with chunks after indexing
        collections=collections,
        last_indexed=None,        # Can be extended with a DB timestamp later
    )


@router.post("/index/{repository:path}", status_code=status.HTTP_202_ACCEPTED)
def index_repository_background(repository: str, background_tasks: BackgroundTasks) -> dict:
    """
    Trigger a full clone → chunk → embed → store pipeline in the background.
    Returns immediately with a 202 Accepted.
    """
    repo_name = repository.split("/")[-1]
    background_tasks.add_task(full_index_job, repository)
    return {
        "status": "accepted",
        "repository": repo_name,
        "message": f"Full indexing of '{repo_name}' started in the background.",
    }


@router.post("/reindex/{repository:path}", status_code=status.HTTP_202_ACCEPTED)
def reindex_repository_background(repository: str, background_tasks: BackgroundTasks) -> dict:
    """
    Git pull + detect changed files + re-embed only what changed.
    Returns immediately with 202 Accepted.
    """
    repo_name = repository.split("/")[-1]
    background_tasks.add_task(incremental_index_job, repository)
    return {
        "status": "accepted",
        "repository": repo_name,
        "message": f"Incremental re-indexing of '{repo_name}' started in the background.",
    }
