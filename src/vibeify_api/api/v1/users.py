"""User API routes."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from querymate import Querymate

from vibeify_api.models.user import User
from vibeify_api.schemas.auth import UserResponse
from vibeify_api.services.user import UserService

router = APIRouter(prefix="/users", tags=["users"])


def get_user_service() -> UserService:
    """Dependency to get user service instance."""
    return UserService()


@router.get(
    "/",
    response_model=List[UserResponse],
    summary="List users",
    description="Get a list of users with flexible querying via QueryMate",
)
async def list_users(
    query: Querymate = Depends(Querymate.fastapi_dependency),
    service: UserService = Depends(get_user_service),
    q: Optional[str] = Query(None, description="Query"),
) -> List[UserResponse]:
    """List users with filtering, sorting, pagination, and field selection.

    Query parameters (via QueryMate):
    - `q`: JSON query object with filter, sort, select, limit, offset
    - `filter`: Filter conditions (e.g., `{"email": {"eq": "user@example.com"}}`)
    - `sort`: Sort fields (e.g., `["-created_at", "username"]`)
    - `select`: Fields to include (e.g., `["id", "email", {"posts": ["title"]}]`)
    - `limit`: Maximum records (default: 10, max: 200)
    - `offset`: Skip records (default: 0)
    - `include_pagination`: Include pagination metadata (boolean)

    Examples:
    - GET /users?limit=20&offset=0
    - GET /users?filter[email][eq]=user@example.com
    - GET /users?sort=-created_at,username&limit=10
    - GET /users?select=id,email,username
    """
    return await service.query(query)


@router.get(
    "/paginated",
    summary="List users with pagination",
    response_model=List[UserResponse],
    description="Get paginated list of users with QueryMate",
)
async def list_users_paginated(
    query: Querymate = Depends(Querymate.fastapi_dependency),
    service: UserService = Depends(get_user_service),
    q: Optional[str] = Query(None, description="Query"),
) -> List[UserResponse]:
    """List users with pagination metadata.

    Same query parameters as `/users` endpoint, but returns pagination info.
    Set `include_pagination=true` in query params.
    """
    if query.include_pagination:
        return await service.query_paginated(query)
    return await service.query(query)


@router.get(
    "/{user_id}",
    response_model=User,
    summary="Get user by ID",
)
async def get_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
) -> User:
    """Get a single user by ID.

    Args:
        user_id: User ID

    Returns:
        User instance

    Raises:
        HTTPException: If user not found
    """
    user = await service.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found",
        )
    return user


@router.post(
    "/",
    response_model=User,
    status_code=status.HTTP_201_CREATED,
    summary="Create user",
)
async def create_user(
    user: User,
    service: UserService = Depends(get_user_service),
) -> User:
    """Create a new user.

    Args:
        user: User data (email, username, full_name, etc.)

    Returns:
        Created user instance

    Raises:
        HTTPException: If email or username already exists
    """
    try:
        return await service.create_user(
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            hashed_password=user.hashed_password,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.patch(
    "/{user_id}",
    response_model=User,
    summary="Update user",
)
async def update_user(
    user_id: int,
    user: User,
    service: UserService = Depends(get_user_service),
) -> User:
    """Update a user by ID.

    Args:
        user_id: User ID
        user: User data to update (only provided fields will be updated)

    Returns:
        Updated user instance

    Raises:
        HTTPException: If user not found
    """
    updated_user = await service.update(user_id, user.model_dump(exclude_unset=True))
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found",
        )
    return updated_user


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
        HTTPException: If user not found
    """
    deleted = await service.delete(user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found",
        )
