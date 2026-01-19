"""Authentication API routes."""
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status

from vibeify_api.core.dependencies import get_current_user
from vibeify_api.core.security import create_access_token, get_password_hash, verify_password
from vibeify_api.core.config import get_settings
from vibeify_api.models.user import User
from vibeify_api.schemas.auth import Token, UserLogin, UserRegister, UserResponse
from vibeify_api.services.user import UserService

settings = get_settings()
router = APIRouter(prefix="", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
) -> UserResponse:
    """Register a new user.

    Args:
        user_data: User registration data

    Returns:
        Created user instance (without password)

    Raises:
        HTTPException: If email or username already exists
    """
    user_service = UserService()
    return await user_service.register_user(user_data)


@router.post("/login", response_model=Token)
async def login(
    user_data: UserLogin,
) -> Token:
    """Authenticate user and return JWT token.

    Args:
        user_data: User login credentials

    Returns:
        JWT access token

    Raises:
        HTTPException: If credentials are invalid
    """
    user_service = UserService()
    return await user_service.login_user(user_data)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Get current authenticated user information.

    Args:
        current_user: Current authenticated user from dependency

    Returns:
        Current user information
    """
    return UserResponse.model_validate(current_user)
