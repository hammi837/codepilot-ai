from fastapi import APIRouter, HTTPException, Depends
from typing import List

from app.schemas.repository import CloneRepositoryRequest, CloneRepositoryResponse
from app.services.repository_service import RepositoryService
from app.db.session import get_db
from sqlalchemy.orm import Session
from app.repositories.repository_repository import RepositoryRepository

router = APIRouter(prefix="/repositories", tags=["repositories"])

# We need a dependency to get RepositoryService, since its __init__ takes RepositoryRepository.
# Wait, my added methods to RepositoryService don't use RepositoryRepository directly, but the __init__ requires it.
def get_repository_service(db: Session = Depends(get_db)) -> RepositoryService:
    repo_repo = RepositoryRepository(db)
    return RepositoryService(repo_repo)

@router.post("/clone", response_model=CloneRepositoryResponse)
def clone_repository(
    request: CloneRepositoryRequest,
    service: RepositoryService = Depends(get_repository_service)
):
    try:
        path = service.clone_repository(request.repository)
        return CloneRepositoryResponse(status="success", path=path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


