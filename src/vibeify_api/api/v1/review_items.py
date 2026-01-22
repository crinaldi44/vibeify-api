from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from starlette import status
from starlette.responses import Response

from vibeify_api.core.dependencies import authorization
from vibeify_api.core.exceptions import ERROR_RESPONSES
from vibeify_api.models import User
from vibeify_api.models.enums import RoleType, ReviewItemType
from vibeify_api.models.review_item import ReviewItem
from vibeify_api.services.review_items import ReviewItemsService

router = APIRouter(prefix="/review-items", tags=["ReviewItems"])


@router.get(
    "",
    summary="Get ReviewItem assignment",
    response_model=List[ReviewItem],
    responses=ERROR_RESPONSES,
    description="Get review item assignment.",
)
async def get_review_item_assignment(
    search_text: Optional[str] = Query(None, alias="searchText", description="Search text to filter on"),
    offset: Optional[int] = Query(0, description="Offset for pagination"),
    review_item_type: Optional[ReviewItemType] = Query(None, description="Task type to filter on", alias="reviewItemType"),
    target_app: Optional[str] = Query(None, description="Target app to filter on", alias="targetApp"),
    current_user: User = Depends(authorization()),
) -> List[ReviewItem]:
    """List users with pagination metadata.

    Requires authentication (any authenticated user can access).

    Same query parameters as `/users` endpoint, but returns pagination info.
    Set `includePagination=true` in query params.
    """
    service = ReviewItemsService()
    return await service.get_review_item_assignment(
        search_text,
        offset,
        ReviewItemType(review_item_type) if review_item_type else None,
    )

@router.post("", responses=ERROR_RESPONSES, status_code=status.HTTP_201_CREATED)
async def create(
    review_item: ReviewItem,
    current_user = Depends(authorization(RoleType.ADMIN))
):
    """ Create a new review item. Only applicable to admin users.

    :param review_item:
    :return:
    """
    review_item_service = ReviewItemsService()
    await review_item_service.create(review_item)
    return Response(
        status_code=status.HTTP_201_CREATED
    )
