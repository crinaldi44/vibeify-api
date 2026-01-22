"""FastAPI dependencies for authentication and authorization."""
from typing import Optional, Union
from querymate import Querymate

from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from vibeify_api.core.exceptions import AuthenticationError, AuthorizationError
from vibeify_api.core.security import decode_access_token
from vibeify_api.models.user import User
from vibeify_api.models.enums import RoleType
from vibeify_api.services.user import UserService
from vibeify_api.core.context import set_current_user

# HTTP Bearer token scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    """Get the current authenticated user from JWT token.
    
    Also sets the user in request context for service access.
    Loads the user's role relationship.
    """
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if payload is None:
        raise AuthenticationError("Could not validate credentials")
    
    user_id: Optional[int] = payload.get("sub")
    if user_id is None:
        raise AuthenticationError("Could not validate credentials")
    
    user_service = UserService()
    users = await user_service.query_raw(
        Querymate(
            filter={"id": {"eq": int(user_id)}},
            select=["*", {"role": ["*"]}],
            limit=1
        )
    )
    
    if not users:
        raise AuthenticationError("Could not validate credentials")
    
    user = users[0]
    
    if not user.is_active:
        raise AuthorizationError("Inactive user")
    
    set_current_user(user)
    
    return user


def authorization(*required_roles: Union[RoleType, str]):
    """Create a dependency that authenticates the user and optionally checks roles.
    
    This dependency consolidates authentication and authorization into a single call.
    It always authenticates the user and sets the user context. If roles are provided,
    it also checks that the user has at least one of the required roles.
    
    Args:
        *required_roles: Optional role names (RoleType enum or string). If provided,
                        user must have at least one of these roles. If not provided,
                        only authentication is performed.
        
    Returns:
        Dependency function that authenticates and optionally checks roles
        
    Examples:
        # Just authenticate (no role check):
        @router.get("/profile")
        async def get_profile(
            current_user: User = Depends(authorization())
        ):
            ...
        
        # Authenticate and require specific role:
        @router.delete("/users/{id}")
        async def delete_user(
            current_user: User = Depends(authorization(RoleType.ADMIN))
        ):
            ...
        
        # Authenticate and require any of multiple roles:
        @router.patch("/users/{id}")
        async def update_user(
            current_user: User = Depends(authorization(RoleType.ADMIN, RoleType.MODERATOR))
        ):
            ...
    """
    async def auth_and_role_checker(
        credentials: HTTPAuthorizationCredentials = Depends(security),
    ) -> User:
        """Authenticate user and optionally check roles."""
        # Authenticate user (same logic as get_current_user)
        token = credentials.credentials
        payload = decode_access_token(token)
        
        if payload is None:
            raise AuthenticationError("Could not validate credentials")
        
        user_id: Optional[int] = payload.get("sub")
        if user_id is None:
            raise AuthenticationError("Could not validate credentials")
        
        user_service = UserService()
        users = await user_service.query_raw(
            Querymate(
                filter={"id": {"eq": int(user_id)}},
                select=["*", {"role": ["*"]}],
                limit=1
            )
        )
        
        if not users:
            raise AuthenticationError("Could not validate credentials")
        
        user = users[0]
        
        if not user.is_active:
            raise AuthorizationError("Inactive user")
        
        # Set user context
        set_current_user(user)
        
        # If roles are specified, check authorization
        if required_roles:
            if not user.role:
                raise AuthorizationError("User role not found")
            
            # Convert RoleType enums to strings
            role_names = [
                role.value if isinstance(role, RoleType) else role
                for role in required_roles
            ]
            
            if user.role.name not in role_names:
                raise AuthorizationError()

        return user
    
    return auth_and_role_checker


def require_all_roles(*required_roles: Union[RoleType, str]) -> callable:
    """Create a dependency that requires the user to have all of the specified roles.
    
    Note: This is typically used when a user can have multiple roles. If your system
    only supports one role per user, use require_role or require_any_role instead.
    
    Args:
        *required_roles: One or more role names (RoleName enum or string) - user must have all
        
    Returns:
        Dependency function that checks if the user has all required roles
        
    Example:
        @router.get("/super-admin")
        async def super_admin_endpoint(
            current_user: User = Depends(require_all_roles(RoleName.ADMIN, RoleName.MODERATOR))
        ):
            ...
    """
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        """Check if the current user has all of the required roles."""
        if not current_user.role:
            raise AuthorizationError("User role not found")
        
        # Convert RoleName enums to strings
        role_names = [
            role.value if isinstance(role, RoleType) else role
            for role in required_roles
        ]
        
        # Since users typically have one role, this checks if the user's role
        # matches all required roles (which means it must be one role that satisfies all)
        # For a true multi-role system, you'd need to check user.roles (plural)
        user_role_name = current_user.role.name
        
        if user_role_name not in role_names or len(role_names) > 1:
            raise AuthorizationError(
                f"Access denied. Required all of: {', '.join(role_names)}, "
                f"User role: {user_role_name}"
            )
        
        return current_user
    
    return role_checker
