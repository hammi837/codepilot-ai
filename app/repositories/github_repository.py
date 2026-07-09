from sqlalchemy.orm import Session

from app.models.github_account import GitHubAccount


class GitHubRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_user_id(self, user_id: int) -> GitHubAccount | None:
        return self.db.query(GitHubAccount).filter(GitHubAccount.user_id == user_id).first()

    def save_account(self, *, user_id: int, github_id: int, username: str, access_token: str, avatar_url: str | None, profile_url: str | None) -> GitHubAccount:
        existing = self.get_by_user_id(user_id)
        if existing:
            existing.github_id = github_id
            existing.username = username
            existing.access_token = access_token
            existing.avatar_url = avatar_url
            existing.profile_url = profile_url
            self.db.commit()
            self.db.refresh(existing)
            return existing

        account = GitHubAccount(
            user_id=user_id,
            github_id=github_id,
            username=username,
            access_token=access_token,
            avatar_url=avatar_url,
            profile_url=profile_url,
        )
        self.db.add(account)
        self.db.commit()
        self.db.refresh(account)
        return account
