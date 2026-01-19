"""User API routes."""
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from querymate import PaginatedResponse, Querymate

from vibeify_api.models.user import User
from vibeify_api.schemas.auth import UserResponse
from vibeify_api.services.user import UserService

router = APIRouter(prefix="/users", tags=["users"])


def get_user_service() -> UserService:
    """Dependency to get user service instance."""
    return UserService()


@router.get(
    "",
    summary="List users with pagination",
    response_model=PaginatedResponse[UserResponse],
    description="Get paginated list of users with QueryMate",
)
async def list_users_paginated(
    query: Querymate = Depends(Querymate.fastapi_dependency),
    service: UserService = Depends(get_user_service),
    q: Optional[str] = Query(None, description="Query"),
) -> PaginatedResponse[UserResponse]:
    """List users with pagination metadata.

    Same query parameters as `/users` endpoint, but returns pagination info.
    Set `include_pagination=true` in query params.
    """
    return await service.list(query)


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update user",
)
async def update_user(
    user_id: int,
    user: UserResponse,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """Update a user by ID.

    Args:
        user_id: User ID
        user: User data to update (only provided fields will be updated)

    Returns:
        Updated user instance

    Raises:
        NotFoundError: If user not found
    """
    return await service.update(user_id, user.model_dump(exclude_unset=True))


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user",
)
async def delete_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
):
    """Delete a user by ID.

    Args:
        user_id: User ID

    Raises:
        NotFoundError: If user not found
    """
    await service.delete(user_id)
