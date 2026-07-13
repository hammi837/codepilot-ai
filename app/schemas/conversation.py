from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from app.schemas.chat import SourceReference


class ConversationCreate(BaseModel):
    repository: str
    title: Optional[str] = None


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    sources: Optional[List[SourceReference]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationOut(BaseModel):
    id: int
    repository: str
    title: Optional[str] = None
    status: str
    created_at: datetime
    messages: List[MessageOut] = []

    class Config:
        from_attributes = True


class ConversationListItem(BaseModel):
    id: int
    repository: str
    title: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class RepositoryStats(BaseModel):
    repository: str
    files: int
    chunks: int
    embeddings: int
    collections: List[str]
    last_indexed: Optional[datetime] = None
