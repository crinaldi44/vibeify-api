"""User service for business logic."""
from datetime import timedelta

from fastapi import HTTPException, status
from querymate import Querymate

from vibeify_api.core.security import create_access_token, get_password_hash, settings, verify_password
from vibeify_api.models.user import User
from vibeify_api.schemas.auth import Token, UserLogin, UserRegister, UserResponse
from vibeify_api.services.base import BaseService


class UserService(BaseService[User]):
    """Service for user-related business logic."""

    def __init__(self):
        """Initialize user service."""
        super().__init__(User)

    async def login_user(self, user_data: UserLogin) -> Token:
        user = await self.query(
            Querymate(filter={"email": {"eq": user_data.email}})
        )
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Verify password
        if not user.hashed_password or not verify_password(user_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user",
            )

        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id)},
            expires_delta=access_token_expires,
        )

        return Token(access_token=access_token, token_type="bearer")

    async def register_user(self, user_data: UserRegister) -> UserResponse:
        existing_user = await self.query(
            Querymate(filter={"email": {"eq": user_data.email}})
        )
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        # Check if username exists
        existing_user = await self.query(
            Querymate(filter={"username": {"eq": user_data.username}})
        )
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken",
            )

        # Hash password
        hashed_password = get_password_hash(user_data.password)

        # Create user
        try:
            user = await self.create(
                User(
                    email=user_data.email,
                    username=user_data.username,
                    full_name=user_data.full_name,
                    hashed_password=hashed_password,
                )
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            ) from e

        return UserResponse.model_validate(user)
