from fastapi import APIRouter, Depends

from app.core.auth import get_current_user
from app.models.user import User
from app.schemas.user import UserProfile

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserProfile)
def read_current_user(current_user: User = Depends(get_current_user)) -> UserProfile:
    return UserProfile(id=current_user.id, email=current_user.email, username=current_user.username)
