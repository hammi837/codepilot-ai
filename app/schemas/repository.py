from pydantic import BaseModel


class RepositoryCreateRequest(BaseModel):
    github_repo_id: int
    repo_name: str
    branch: str
    language: str | None = None
    private: bool = False
    clone_url: str | None = None


class RepositoryResponse(BaseModel):
    id: int
    github_repo_id: int
    repo_name: str
    branch: str
    language: str | None = None
    private: bool
    clone_url: str | None = None

class CloneRepositoryRequest(BaseModel):
    repository: str

class CloneRepositoryResponse(BaseModel):
    status: str
    path: str

class RepositoryFile(BaseModel):
    path: str
    language: str
    size: int
