from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.repository import Repository
from app.schemas.dashboard import DashboardOverviewResponse, DashboardStats, RecentRepository, ActivityItem
from app.services.vector_service import VectorService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/overview", response_model=DashboardOverviewResponse)
def get_dashboard_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardOverviewResponse:
    """
    Returns aggregate statistics and recent activity for the user's dashboard.
    """
    vector_service = VectorService()
    collections = vector_service.list_collections()

    # Fetch real repositories from the database for the current user
    db_repos = (
        db.query(Repository)
        .filter(Repository.user_id == current_user.id)
        .order_by(Repository.id.desc())
        .limit(6)
        .all()
    )

    repositories_count = len(db_repos) or len(collections)
    files_indexed = repositories_count * 125
    total_embeddings = repositories_count * 450
    questions_asked = 215  # Mock

    stats = DashboardStats(
        repositories_count=repositories_count,
        files_indexed=files_indexed,
        total_embeddings=total_embeddings,
        questions_asked=questions_asked,
    )

    # Build recent repos from DB — use repo_name as id so the frontend
    # navigates to /repositories/{repo_name} which the workspace can resolve
    recent_repos = [
        RecentRepository(
            id=repo.repo_name,          # use repo_name, NOT db id
            name=repo.repo_name,
            language=repo.language or "Unknown",
            is_private=repo.private,
            last_indexed=None,
        )
        for repo in db_repos
    ]

    recent_activity = [
        ActivityItem(
            id="1",
            type="index",
            title="Repository Indexed",
            description="Finished indexing codepilot-ai",
            timestamp=datetime.utcnow(),
        ),
        ActivityItem(
            id="2",
            type="auth",
            title="GitHub Connected",
            description="Successfully linked GitHub account",
            timestamp=datetime.utcnow(),
        ),
    ]

    return DashboardOverviewResponse(
        stats=stats,
        recent_repositories=recent_repos,
        recent_activity=recent_activity,
    )
