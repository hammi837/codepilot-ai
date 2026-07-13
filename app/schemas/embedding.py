from pydantic import BaseModel


class EmbeddingRequest(BaseModel):
    text: str


class EmbeddingResponse(BaseModel):
    embedding: list[float]


class EmbeddingMetadata(BaseModel):
    repository: str
    file: str
    chunk_id: str
    dimensions: int
    hash: str
    chunk_index: int
    total_chunks: int
