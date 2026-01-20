"""User API routes."""
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status, Path
from querymate import PaginatedResponse, Querymate

from vibeify_api.core.dependencies import get_current_user
from vibeify_api.core.exceptions import ERROR_RESPONSES
from vibeify_api.schemas.auth import UserResponse
from vibeify_api.schemas.requests import ListQueryParams
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
async def list_users(
    q: ListQueryParams = Query(description="Query"),
    service: UserService = Depends(get_user_service),
    current_user = Depends(get_current_user)
) -> ListResponse[UserResponse]:
    """List users with pagination metadata.

    Same query parameters as `/users` endpoint, but returns pagination info.
    Set `include_pagination=true` in query params.
    """
    return await service.list(q)


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
) -> UserResponse:
    """Update a user by ID.

    Args:
        id: User ID
        user: User data to update (only provided fields will be updated)

    Returns:
        Updated user instance

    Raises:
        NotFoundError: If user not found
    """
    return await service.update(id, user.model_dump(exclude_unset=True))


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=ERROR_RESPONSES,
    summary="Delete user",
)
async def delete_user(
    id: int,
    service: UserService = Depends(get_user_service),
):
    """Delete a user by ID.

    Args:
        id: User ID

    Raises:
        NotFoundError: If user not found
    """
    await service.delete(id)
