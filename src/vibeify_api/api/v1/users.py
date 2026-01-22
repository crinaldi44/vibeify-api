"""User API routes."""
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from querymate import Querymate

from vibeify_api.core.dependencies import authorization
from vibeify_api.core.exceptions import ERROR_RESPONSES
from vibeify_api.models.enums import RoleType
from vibeify_api.models.user import User
from vibeify_api.schemas.auth import UserResponse
from vibeify_api.schemas.responses import ListResponse
from vibeify_api.services.user import UserService

router = APIRouter(prefix="/users", tags=["Users"])


def get_user_service() -> UserService:
    """Dependency to get user service instance."""
    return UserService()


@router.get(
    "",
    summary="List users with pagination",
    response_model=ListResponse[UserResponse],
    responses=ERROR_RESPONSES,
    description="Get paginated list of users with QueryMate",
)
async def list_all(
    query: Querymate = Depends(Querymate.fastapi_dependency),
    q: Optional[str] = Query(None),
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(authorization(RoleType.ADMIN)),
) -> ListResponse[UserResponse]:
    """List users with pagination metadata.
    
    Requires authentication (any authenticated user can access).

    Same query parameters as `/users` endpoint, but returns pagination info.
    Set `includePagination=true` in query params.
    """
    return await service.list(query)


@router.patch(
    "/{id}",
    response_model=UserResponse,
    responses=ERROR_RESPONSES,
    summary="Update user",
)
async def update_user(
    user: UserResponse,
    id: int,
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(authorization(RoleType.ADMIN)),
) -> UserResponse:
    """Update a user by ID.
    
    Requires ADMIN role.

    Args:
        id: User ID
        user: User data to update (only provided fields will be updated)
        current_user: Current authenticated user (must be ADMIN)

    Returns:
        Updated user instance

    Raises:
        NotFoundError: If user not found
        AuthorizationError: If user doesn't have ADMIN role
    """
    return await service.update(id, user.model_dump(exclude_unset=True))


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=ERROR_RESPONSES,
    summary="Delete user",
)
async def delete(
    id: int,
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(authorization(RoleType.ADMIN)),
):
    """Delete a user by ID.
    
    Requires ADMIN role.

    Args:
        id: User ID
        current_user: Current authenticated user (must be ADMIN)

    Raises:
        NotFoundError: If user not found
        AuthorizationError: If user doesn't have ADMIN role
    """
    await service.delete(id)
