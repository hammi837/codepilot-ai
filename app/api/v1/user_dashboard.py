from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.schemas.dashboard import DashboardOverviewResponse, DashboardStats, RecentRepository, ActivityItem
from app.services.vector_service import VectorService
from app.services.chunking_service import ChunkingService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/overview", response_model=DashboardOverviewResponse)
def get_dashboard_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardOverviewResponse:
    """
    Returns aggregate statistics and recent activity for the user's dashboard.
    Currently uses mock data for some fields until all tables (chats, activity) are created.
    """
    # Fetch real counts from VectorService/ChunkingService if possible
    # For now, we will return some dynamic values mixed with mocks to unblock frontend
    
    vector_service = VectorService()
    collections = vector_service.list_collections()
    
    # Calculate some dynamic stats based on collections
    repositories_count = len(collections)
    
    # Mocking files indexed and embeddings since we don't have a global DB for it yet
    files_indexed = repositories_count * 125
    total_embeddings = repositories_count * 450
    questions_asked = 215 # Mock
    
    stats = DashboardStats(
        repositories_count=repositories_count,
        files_indexed=files_indexed,
        total_embeddings=total_embeddings,
        questions_asked=questions_asked
    )
    
    recent_repos = []
    for c in collections[:5]:
        recent_repos.append(
            RecentRepository(
                id=c,
                name=c,
                language="Python", # Mock
                is_private=False, # Mock
                last_indexed=datetime.utcnow()
            )
        )
        
    recent_activity = [
        ActivityItem(
            id="1",
            type="index",
            title="Repository Indexed",
            description="Finished indexing codepilot-ai",
            timestamp=datetime.utcnow()
        ),
        ActivityItem(
            id="2",
            type="auth",
            title="GitHub Connected",
            description="Successfully linked GitHub account",
            timestamp=datetime.utcnow()
        ),
    ]

    return DashboardOverviewResponse(
        stats=stats,
        recent_repositories=recent_repos,
        recent_activity=recent_activity
    )
