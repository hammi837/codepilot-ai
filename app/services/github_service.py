from typing import Any
import urllib.parse

import httpx

from app.core.config import settings
from app.repositories.github_repository import GitHubRepository
from app.repositories.repository_repository import RepositoryRepository
from app.schemas.github import GitHubAccountResponse, GitHubRepositoryItem


class GitHubService:
    def __init__(
        self,
        github_repository: GitHubRepository,
        repository_repository: RepositoryRepository | None = None,
    ) -> None:
        self.github_repository = github_repository
        self.repository_repository = repository_repository

    def get_authorization_url(self, state: str | None = None) -> str:
        client_id = settings.GITHUB_CLIENT_ID or "dummy-client-id"
        callback_url = settings.GITHUB_CALLBACK_URL or "http://localhost:8000/api/v1/github/callback"

        url = (
            "https://github.com/login/oauth/authorize"
            f"?client_id={urllib.parse.quote_plus(client_id)}"
            f"&redirect_uri={urllib.parse.quote_plus(callback_url)}"
            f"&scope=repo,user"
            f"&prompt=consent"
        )
        if state:
            url += f"&state={urllib.parse.quote_plus(state)}"
        return url

    def exchange_code(self, code: str, user_id: int) -> GitHubAccountResponse:
        if not settings.GITHUB_CLIENT_ID or not settings.GITHUB_CLIENT_SECRET or not settings.GITHUB_CALLBACK_URL:
            raise ValueError("GitHub OAuth is not configured")

        response = httpx.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": settings.GITHUB_CALLBACK_URL,
            },
            timeout=15.0,
        )
        response.raise_for_status()
        payload = response.json()
        access_token = payload.get("access_token")
        if not access_token:
            error_message = payload.get("error_description") or payload.get("error") or "GitHub token exchange failed"
            raise ValueError(
                f"GitHub token exchange failed: {error_message}. Response payload: {payload}"
            )

        profile = self._get_user_profile(access_token)
        account = self.github_repository.save_account(
            user_id=user_id,
            github_id=profile["id"],
            username=profile["login"],
            access_token=access_token,
            avatar_url=profile.get("avatar_url"),
            profile_url=profile.get("html_url"),
        )
        return GitHubAccountResponse(
            id=account.id,
            github_id=account.github_id,
            username=account.username,
            avatar_url=account.avatar_url,
            profile_url=account.profile_url,
        )

    def _get_user_profile(self, access_token: str) -> dict[str, Any]:
        response = httpx.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
            },
            timeout=15.0,
        )
        response.raise_for_status()
        return response.json()

    def get_user_repositories(self, user_id: int, access_token: str) -> list[GitHubRepositoryItem]:
        response = httpx.get(
            "https://api.github.com/user/repos",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
            },
            timeout=15.0,
        )
        response.raise_for_status()
        payload = response.json()
        repos = []

        for repo in payload:
            if self.repository_repository:
                self.repository_repository.save(
                    user_id=user_id,
                    github_repo_id=repo["id"],
                    repo_name=repo["name"],
                    branch=repo.get("default_branch", "main"),
                    language=repo.get("language"),
                    private=repo.get("private", False),
                    clone_url=repo.get("html_url", ""),
                )

            repos.append(
                GitHubRepositoryItem(
                    id=repo["id"],
                    name=repo["name"],
                    full_name=repo["full_name"],
                    private=repo.get("private", False),
                    language=repo.get("language"),
                    default_branch=repo.get("default_branch", "main"),
                    html_url=repo.get("html_url", ""),
                    description=repo.get("description"),
                    clone_url=repo.get("clone_url"),
                    stars=repo.get("stargazers_count", 0),
                    updated_at=repo.get("updated_at"),
                )
            )

        return repos
