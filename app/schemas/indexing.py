from pydantic import BaseModel

class FileMetadataResponse(BaseModel):
    path: str
    extension: str
    language: str
    size: int

class RepositoryStatsResponse(BaseModel):
    total_files: int
    total_size: int
