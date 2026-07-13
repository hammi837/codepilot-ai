"""
Background job workers using FastAPI BackgroundTasks.

Handles heavy operations:
- Clone + index + embed + store pipeline
- Incremental re-indexing (changed files only)
"""
import os
import logging
from pathlib import Path
from typing import Callable

from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService, EmbeddingServiceError
from app.services.vector_service import VectorService

logger = logging.getLogger(__name__)


def _get_file_mtimes(repo_path: Path) -> dict[str, float]:
    """Return a dict of relative_path -> mtime for all indexed files."""
    ignored_dirs = {".git", "venv", "node_modules", "__pycache__", "dist", "build", ".next"}
    mtimes: dict[str, float] = {}
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in ignored_dirs]
        for f in files:
            fp = Path(root) / f
            rel = str(fp.relative_to(repo_path)).replace("\\", "/")
            mtimes[rel] = fp.stat().st_mtime
    return mtimes


def full_index_job(
    repository: str,
    on_complete: Callable[[dict], None] | None = None,
) -> dict:
    """
    Full pipeline: chunk → embed → store in ChromaDB.
    Designed to be called from FastAPI BackgroundTasks or directly.
    """
    repo_name = repository.split("/")[-1]
    logger.info(f"[BG] Starting full index for: {repo_name}")

    chunking_service = ChunkingService()
    embedding_service = EmbeddingService()
    vector_service = VectorService()

    try:
        chunks = chunking_service.chunk_repository(repo_name)
    except ValueError as exc:
        result = {"status": "error", "repository": repo_name, "detail": str(exc)}
        if on_complete:
            on_complete(result)
        return result

    if not chunks:
        result = {"status": "done", "repository": repo_name, "chunks": 0}
        if on_complete:
            on_complete(result)
        return result

    texts = [c.content for c in chunks]
    try:
        embeddings = embedding_service.generate_embeddings(texts)
    except EmbeddingServiceError as exc:
        result = {"status": "error", "repository": repo_name, "detail": str(exc)}
        if on_complete:
            on_complete(result)
        return result

    stored = vector_service.add_chunks(repository=repo_name, chunks=chunks, embeddings=embeddings)
    result = {"status": "done", "repository": repo_name, "chunks": stored}
    logger.info(f"[BG] Full index complete for {repo_name}: {stored} chunks stored")
    if on_complete:
        on_complete(result)
    return result


def incremental_index_job(
    repository: str,
    on_complete: Callable[[dict], None] | None = None,
) -> dict:
    """
    Incremental re-index: git pull, detect changed files, re-embed only those.
    """
    from git import Repo, InvalidGitRepositoryError

    repo_name = repository.split("/")[-1]
    repo_path = Path("workspace") / repo_name
    logger.info(f"[BG] Starting incremental index for: {repo_name}")

    if not repo_path.exists():
        result = {"status": "error", "detail": f"Repository {repo_name} not cloned yet."}
        if on_complete:
            on_complete(result)
        return result

    # Snapshot mtimes before pull
    before = _get_file_mtimes(repo_path)

    # Git pull
    try:
        git_repo = Repo(str(repo_path))
        origin = git_repo.remotes.origin
        origin.pull()
        logger.info(f"[BG] git pull completed for {repo_name}")
    except InvalidGitRepositoryError:
        logger.warning(f"[BG] {repo_name} is not a git repo — skipping pull, re-indexing all")
    except Exception as exc:
        logger.warning(f"[BG] git pull failed for {repo_name}: {exc} — re-indexing all")

    # Snapshot mtimes after pull
    after = _get_file_mtimes(repo_path)

    # Find changed/new files
    changed_files = {
        rel for rel, mtime in after.items()
        if rel not in before or before[rel] != mtime
    }

    if not changed_files:
        result = {"status": "done", "repository": repo_name, "changed_files": 0, "chunks": 0}
        if on_complete:
            on_complete(result)
        return result

    logger.info(f"[BG] {len(changed_files)} changed files detected in {repo_name}")

    # Re-chunk, filter to changed files only
    chunking_service = ChunkingService()
    embedding_service = EmbeddingService()
    vector_service = VectorService()

    all_chunks = chunking_service.chunk_repository(repo_name)
    changed_chunks = [c for c in all_chunks if c.metadata.file in changed_files]

    if not changed_chunks:
        result = {"status": "done", "repository": repo_name, "changed_files": len(changed_files), "chunks": 0}
        if on_complete:
            on_complete(result)
        return result

    texts = [c.content for c in changed_chunks]
    try:
        embeddings = embedding_service.generate_embeddings(texts)
    except EmbeddingServiceError as exc:
        result = {"status": "error", "repository": repo_name, "detail": str(exc)}
        if on_complete:
            on_complete(result)
        return result

    stored = vector_service.add_chunks(repository=repo_name, chunks=changed_chunks, embeddings=embeddings)
    result = {
        "status": "done",
        "repository": repo_name,
        "changed_files": len(changed_files),
        "chunks": stored,
    }
    logger.info(f"[BG] Incremental index complete for {repo_name}: {stored} chunks updated")
    if on_complete:
        on_complete(result)
    return result
