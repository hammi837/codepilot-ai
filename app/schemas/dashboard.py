from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional


class ActivityItem(BaseModel):
    id: str
    type: str
    title: str
    description: str
    timestamp: datetime


class RecentRepository(BaseModel):
    id: str
    name: str
    language: str
    is_private: bool
    last_indexed: Optional[datetime] = None


class DashboardStats(BaseModel):
    repositories_count: int
    files_indexed: int
    total_embeddings: int
    questions_asked: int


class DashboardOverviewResponse(BaseModel):
    stats: DashboardStats
    recent_repositories: List[RecentRepository]
    recent_activity: List[ActivityItem]
