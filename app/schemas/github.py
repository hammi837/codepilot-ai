from pydantic import BaseModel


class GitHubAccountResponse(BaseModel):
    id: int
    github_id: int
    username: str
    avatar_url: str | None = None
    profile_url: str | None = None


class GitHubRepositoryItem(BaseModel):
    id: int
    name: str
    full_name: str
    private: bool
    language: str | None = None
    default_branch: str
    html_url: str
    description: str | None = None
    clone_url: str | None = None
    stars: int = 0
    updated_at: str | None = None
