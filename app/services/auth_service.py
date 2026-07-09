from fastapi import HTTPException, status

from app.core.security import create_access_token, hash_password, verify_password
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, TokenResponse, UserRegisterRequest, UserResponse


class AuthService:
    def __init__(self, user_repository: UserRepository) -> None:
        self.user_repository = user_repository

    def register_user(self, payload: UserRegisterRequest) -> UserResponse:
        if self.user_repository.get_by_email(str(payload.email)):
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

    def authenticate_user(self, payload: LoginRequest) -> TokenResponse:
        user = self.user_repository.get_by_email(str(payload.email))
        if not user or not verify_password(payload.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )

        token = create_access_token({"sub": str(user.id)})
        return TokenResponse(access_token=token)
