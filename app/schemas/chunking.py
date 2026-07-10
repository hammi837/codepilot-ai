from pydantic import BaseModel


class ChunkMetadata(BaseModel):
    repository: str
    file: str
    language: str
    type: str  # "function", "class", "method", "global", "markdown_section", etc.
    name: str | None = None  # "login", "UserService", etc.
    parent: str | None = None  # parent class name if this is a method
    start_line: int
    end_line: int
    chunk_index: int  # 1-indexed
    total_chunks: int
    hash: str  # SHA-256 of content for change detection


class ChunkResponse(BaseModel):
    content: str
    metadata: ChunkMetadata
