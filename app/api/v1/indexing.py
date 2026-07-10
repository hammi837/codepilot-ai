from fastapi import APIRouter, HTTPException, Depends
from typing import List

from app.schemas.indexing import FileMetadataResponse
from app.services.repository_service import RepositoryService
from app.db.session import get_db
from sqlalchemy.orm import Session
from app.repositories.repository_repository import RepositoryRepository

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
