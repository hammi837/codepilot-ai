from fastapi import APIRouter, HTTPException
from typing import List

from app.schemas.chunking import ChunkResponse
from app.services.chunking_service import ChunkingService

router = APIRouter(
    prefix="/repositories",
    tags=["Code Chunking"],
)


@router.post("/chunk/{repository_name:path}", response_model=List[ChunkResponse])
def chunk_repository(repository_name: str):
    """Semantically chunk all files in a cloned repository."""
    service = ChunkingService()
    try:
        return service.chunk_repository(repository_name)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
