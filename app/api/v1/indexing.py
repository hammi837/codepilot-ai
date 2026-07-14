from fastapi import APIRouter, HTTPException, Depends
from typing import List

from app.schemas.indexing import FileMetadataResponse, FileContentResponse
from app.services.repository_service import RepositoryService
from app.db.session import get_db
from sqlalchemy.orm import Session
from app.repositories.repository_repository import RepositoryRepository
from pathlib import Path

router = APIRouter(
    prefix="/repositories",
    tags=["Repository Indexing"],
)

def get_repository_service(db: Session = Depends(get_db)) -> RepositoryService:
    repo_repo = RepositoryRepository(db)
    return RepositoryService(repo_repo)

@router.get("/index/{repository_name:path}", response_model=List[FileMetadataResponse])
def index_repository(
    repository_name: str,
    service: RepositoryService = Depends(get_repository_service)
):
    try:
        return service.index_repository(repository_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/file/{repository_name:path}", response_model=FileContentResponse)
def get_file_content(
    repository_name: str,
    file_path: str,
):
    """Return the raw content of a single file from a cloned repository.
    
    Query params:
      file_path: relative path within the repo, e.g. src/main.py
    """
    repo_name = repository_name.split("/")[-1]
    workspace_dir = Path("workspace")
    repo_path = workspace_dir / repo_name

    if not repo_path.exists():
        raise HTTPException(status_code=404, detail=f"Repository '{repo_name}' not found.")

    # Sanitize: prevent path traversal
    try:
        full_path = (repo_path / file_path).resolve()
        repo_path_resolved = repo_path.resolve()
        if not str(full_path).startswith(str(repo_path_resolved)):
            raise HTTPException(status_code=400, detail="Invalid file path.")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid file path.")

    if not full_path.exists() or not full_path.is_file():
        raise HTTPException(status_code=404, detail=f"File '{file_path}' not found.")

    ext_map = {
        ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
        ".tsx": "TypeScript React", ".jsx": "JavaScript React",
        ".html": "HTML", ".css": "CSS", ".md": "Markdown",
        ".json": "JSON", ".go": "Go", ".java": "Java",
        ".cpp": "C++", ".c": "C", ".rs": "Rust", ".sh": "Shell",
        ".yml": "YAML", ".yaml": "YAML", ".txt": "Text",
    }
    ext = full_path.suffix.lower()
    language = ext_map.get(ext, "Unknown")

    try:
        content = full_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read file: {str(e)}")

    return FileContentResponse(
        path=file_path,
        content=content,
        language=language,
        size=full_path.stat().st_size,
        lines=len(content.splitlines()),
    )
