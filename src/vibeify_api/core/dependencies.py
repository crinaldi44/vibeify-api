"""FastAPI dependencies for authentication."""
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from vibeify_api.core.security import decode_access_token
from vibeify_api.models.user import User
from vibeify_api.services.user import UserService

# HTTP Bearer token scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    """Get the current authenticated user from JWT token.

    Args:
        credentials: HTTP Bearer token credentials

    Returns:
        Current user instance

    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id: Optional[int] = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    user_service = UserService()
    user = await user_service.get(user_id)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current active user (alias for get_current_user with explicit active check).

    Args:
        current_user: Current user from get_current_user

    Returns:
        Current active user instance
    """
    return current_user
