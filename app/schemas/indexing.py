from pydantic import BaseModel
from typing import Optional

class FileMetadataResponse(BaseModel):
    path: str
    extension: str
    language: str
    size: int

class RepositoryStatsResponse(BaseModel):
    total_files: int
    total_size: int

class FileContentResponse(BaseModel):
    path: str
    content: str
    language: str
    size: int
    lines: int
