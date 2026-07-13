"""
Production chat endpoint with:
- Streaming SSE responses
- Persistent conversation management
- Background indexing triggers
"""
import json
from typing import AsyncGenerator, Optional, List

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from fastapi.responses import StreamingResponse

from app.schemas.chat import ChatRequest, ChatResponse, SourceReference
from app.schemas.conversation import ConversationOut, ConversationListItem
from app.services.chat_service import ChatService
from app.services.ai_service import AIServiceError

router = APIRouter(prefix="/chat", tags=["chat"])


# ── Sync Chat (returns full answer at once) ────────────────────────────────

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
    """Ask a natural language question across all indexed repositories."""
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


# ── Streaming Chat (token-by-token SSE) ───────────────────────────────────

@router.post("/stream/{repository:path}")
def stream_chat(repository: str, request: ChatRequest) -> StreamingResponse:
    """
    Streaming RAG chat endpoint using Server-Sent Events.
    Tokens are sent as they are generated — no waiting for the full response.
    """
    chat_service = ChatService()
    repo_name = repository.split("/")[-1]

    def event_generator():
        try:
            for token in chat_service.stream_chat(
                question=request.question,
                repository=repo_name,
                history=request.history or [],
                top_k=request.top_k,
            ):
                yield f"data: {json.dumps({'token': token})}\n\n"

            yield "data: [DONE]\n\n"
        except AIServiceError as exc:
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
