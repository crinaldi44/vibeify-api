"""FastAPI dependencies for authentication."""
from typing import Optional

from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from vibeify_api.core.exceptions import AuthenticationError, AuthorizationError
from vibeify_api.core.security import decode_access_token
from vibeify_api.models.user import User
from vibeify_api.services.user import UserService

# HTTP Bearer token scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    """Get the current authenticated user from JWT token.
    
    Also sets the user in request context for service access.
    """
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if payload is None:
        raise AuthenticationError("Could not validate credentials")
    
    user_id: Optional[int] = payload.get("sub")
    if user_id is None:
        raise AuthenticationError("Could not validate credentials")
    
    user_service = UserService()
    user = await user_service.get(int(user_id))
    
    if not user.is_active:
        raise AuthorizationError("Inactive user")
    
    from vibeify_api.core.context import set_current_user
    set_current_user(user)
    
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
