from typing import List, Optional
from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    question: str
    history: Optional[List[ChatMessage]] = []
    top_k: int = 5


class SourceReference(BaseModel):
    file: str
    name: Optional[str] = None
    type: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceReference]
    query: str
