from sqlalchemy.orm import Session

from app.models.repository import Repository


class RepositoryRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_for_user(self, user_id: int) -> list[Repository]:
        return self.db.query(Repository).filter(Repository.user_id == user_id).all()

    def get_by_github_repo_id(self, user_id: int, github_repo_id: int) -> Repository | None:
        return (
            self.db.query(Repository)
            .filter(
                Repository.user_id == user_id,
                Repository.github_repo_id == github_repo_id,
            )
            .first()
        )

    def save(self, *, user_id: int, github_repo_id: int, repo_name: str, branch: str, language: str | None, private: bool, clone_url: str | None) -> Repository:
        existing = self.get_by_github_repo_id(user_id, github_repo_id)
        if existing:
            existing.repo_name = repo_name
            existing.branch = branch
            existing.language = language
            existing.private = private
            existing.clone_url = clone_url
            self.db.commit()
            self.db.refresh(existing)
            return existing

        repo = Repository(
            user_id=user_id,
            github_repo_id=github_repo_id,
            repo_name=repo_name,
            branch=branch,
            language=language,
            private=private,
            clone_url=clone_url,
        )
        self.db.add(repo)
        self.db.commit()
        self.db.refresh(repo)
        return repo
