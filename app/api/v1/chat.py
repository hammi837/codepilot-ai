from fastapi import APIRouter, HTTPException, status

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService
from app.services.ai_service import AIServiceError

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/{repository:path}", response_model=ChatResponse, status_code=status.HTTP_200_OK)
def chat_repository(repository: str, request: ChatRequest) -> ChatResponse:
    """
    Ask a natural language question about a specific repository.
    Returns a grounded AI answer with source citations.
    """
    chat_service = ChatService()
    repo_name = repository.split("/")[-1]

    try:
        return chat_service.chat(
            question=request.question,
            repository=repo_name,
            history=request.history,
            top_k=request.top_k,
        )
    except AIServiceError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.post("", response_model=ChatResponse, status_code=status.HTTP_200_OK)
def chat_all(request: ChatRequest) -> ChatResponse:
    """
    Ask a natural language question across all indexed repositories.
    """
    chat_service = ChatService()

    try:
        return chat_service.chat(
            question=request.question,
            repository=None,
            history=request.history,
            top_k=request.top_k,
        )
    except AIServiceError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
