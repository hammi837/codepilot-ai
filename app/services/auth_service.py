from datetime import timedelta

from fastapi import HTTPException, status

from app.core.security import create_access_token, hash_password, verify_password, verify_token
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserRegisterRequest,
    UserResponse,
)


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

    def forgot_password(self, payload: ForgotPasswordRequest) -> ForgotPasswordResponse:
        """
        Generates a short-lived (15 min) password-reset token.
        In production this token would be emailed; for now it's returned in the response.
        The token type is distinguished by the 'purpose' claim so it can't be used as an access token.
        """
        user = self.user_repository.get_by_email(str(payload.email))
        # Always return 200 — don't leak whether the email exists
        if not user:
            return ForgotPasswordResponse(
                message="If that email exists, a reset link has been sent."
            )

        reset_token = create_access_token(
            data={"sub": str(user.id), "purpose": "password_reset"},
            expires_delta=timedelta(minutes=15),
        )
        # TODO: send email with reset_token link in production
        return ForgotPasswordResponse(
            message="If that email exists, a reset link has been sent.",
            # Return token only in debug for testing (remove when email is wired)
        )

    def reset_password(self, payload: ResetPasswordRequest) -> ForgotPasswordResponse:
        """Validates the reset token and updates the user's password."""
        try:
            token_data = verify_token(payload.token)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token",
            )

        if token_data.get("purpose") != "password_reset":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token purpose",
            )

        user_id = token_data.get("sub")
        user = self.user_repository.get_by_id(int(user_id))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        hashed = hash_password(payload.new_password)
        self.user_repository.update_password(user, hashed)
        return ForgotPasswordResponse(message="Password reset successfully.")
