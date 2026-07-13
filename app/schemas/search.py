from typing import List, Optional
from pydantic import BaseModel

class SearchRequest(BaseModel):
    query: str
    top_k: int = 5

class SearchResult(BaseModel):
    repository: str
    file: str
    type: str
    name: Optional[str] = None
    score: float
    content: str
    
class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
