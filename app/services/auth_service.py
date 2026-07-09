from fastapi import HTTPException, status

from app.core.security import hash_password
from app.repositories.user_repository import UserRepository
from app.schemas.auth import UserRegisterRequest, UserResponse


class AuthService:
    def __init__(self, user_repository: UserRepository) -> None:
        self.user_repository = user_repository

    def register_user(self, payload: UserRegisterRequest) -> UserResponse:
        if self.user_repository.get_by_email(payload.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists",
            )

        hashed_password = hash_password(payload.password)
        user = self.user_repository.create_user(
            email=str(payload.email),
            username=payload.username,
            hashed_password=hashed_password,
        )

        return UserResponse(id=user.id, email=user.email, username=user.username)
