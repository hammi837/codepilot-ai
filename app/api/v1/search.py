from fastapi import APIRouter, HTTPException, status
from app.schemas.search import SearchRequest, SearchResponse
from app.services.search_service import SearchService

router = APIRouter(prefix="/search", tags=["search"])

@router.post("/{repository:path}", response_model=SearchResponse, status_code=status.HTTP_200_OK)
def search_repository(repository: str, request: SearchRequest) -> SearchResponse:
    """Search for code chunks within a specific repository."""
    search_service = SearchService()
    repo_name = repository.split("/")[-1]
    
    try:
        return search_service.search_repository(
            query=request.query, 
            repository=repo_name, 
            top_k=request.top_k
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
        
@router.post("", response_model=SearchResponse, status_code=status.HTTP_200_OK)
def search_all(request: SearchRequest) -> SearchResponse:
    """Search across all indexed repositories."""
    search_service = SearchService()
    
    try:
        return search_service.search_all(
            query=request.query, 
            top_k=request.top_k
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
