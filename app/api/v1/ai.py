from fastapi import APIRouter, HTTPException, status
from app.schemas.ai import AIRequest, AIResponse
from app.services.ai_service import AIService, AIServiceError

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/test", response_model=AIResponse, status_code=status.HTTP_200_OK)
def test_ai_response(payload: AIRequest) -> AIResponse:
    service = AIService()
    try:
        output = service.generate_response(payload.prompt)
    except AIServiceError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    return AIResponse(response=output)
