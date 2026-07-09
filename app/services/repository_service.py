from app.repositories.repository_repository import RepositoryRepository
from app.schemas.repository import RepositoryCreateRequest, RepositoryResponse


class RepositoryService:
    def __init__(self, repository_repository: RepositoryRepository) -> None:
        self.repository_repository = repository_repository

    def list_repositories(self, user_id: int) -> list[RepositoryResponse]:
        repos = self.repository_repository.list_for_user(user_id)
        return [
            RepositoryResponse(
                id=repo.id,
                github_repo_id=repo.github_repo_id,
                repo_name=repo.repo_name,
                branch=repo.branch,
                language=repo.language,
                private=repo.private,
                clone_url=repo.clone_url,
            )
            for repo in repos
        ]

    def connect_repository(self, user_id: int, payload: RepositoryCreateRequest) -> RepositoryResponse:
        repo = self.repository_repository.create(
            user_id=user_id,
            github_repo_id=payload.github_repo_id,
            repo_name=payload.repo_name,
            branch=payload.branch,
            language=payload.language,
            private=payload.private,
            clone_url=payload.clone_url,
        )
        return RepositoryResponse(
            id=repo.id,
            github_repo_id=repo.github_repo_id,
            repo_name=repo.repo_name,
            branch=repo.branch,
            language=repo.language,
            private=repo.private,
            clone_url=repo.clone_url,
        )
