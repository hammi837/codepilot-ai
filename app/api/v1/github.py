from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.repositories.github_repository import GitHubRepository
from app.repositories.repository_repository import RepositoryRepository
from app.schemas.github import GitHubAccountResponse, GitHubRepositoryItem
from app.services.github_service import GitHubService

router = APIRouter(prefix="/github", tags=["github"])


@router.get("/login", response_model=None)
def github_login(request: Request, current_user: User = Depends(get_current_user)):
    service = GitHubService(GitHubRepository(None))
    url = service.get_authorization_url(state=str(current_user.id))

    if request.headers.get("accept", "").lower().startswith("application/json"):
        return {"authorization_url": url}

    return RedirectResponse(url=url)


@router.get("/callback")
def github_callback(
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    if not code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing code")
    if not state:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing state")

    user_id = int(state)
    service = GitHubService(GitHubRepository(db))
    try:
        service.exchange_code(code, user_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))
    
    # Redirect back to the frontend repositories page
    return RedirectResponse(url="http://localhost:3000/repositories")


@router.get("/profile", response_model=GitHubAccountResponse)
def github_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GitHubAccountResponse:
    account = GitHubRepository(db).get_by_user_id(current_user.id)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="GitHub account not connected")

    return GitHubAccountResponse(
        id=account.id,
        github_id=account.github_id,
        username=account.username,
        avatar_url=account.avatar_url,
        profile_url=account.profile_url,
    )


@router.get("/repositories", response_model=list[GitHubRepositoryItem])
def github_repositories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[GitHubRepositoryItem]:
    account = GitHubRepository(db).get_by_user_id(current_user.id)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="GitHub account not connected")

    service = GitHubService(
        GitHubRepository(db),
        RepositoryRepository(db),
    )
    return service.get_user_repositories(current_user.id, account.access_token)
