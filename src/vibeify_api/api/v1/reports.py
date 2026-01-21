from typing import Optional

from fastapi import APIRouter, Depends, Query
from querymate.core.querymate import Querymate

from vibeify_api.core.dependencies import get_current_user
from vibeify_api.core.exceptions import ERROR_RESPONSES
from vibeify_api.models.reports import Report
from vibeify_api.schemas.responses import ListResponse
from vibeify_api.services.reports import ReportService

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get(
    "",
    summary="List reports with pagination",
    response_model=ListResponse[Report],
    responses=ERROR_RESPONSES,
    description="Get paginated list of reports with QueryMate",
)
async def list_all(
    query: Querymate = Depends(Querymate.fastapi_dependency),
    q: Optional[str] = Query(None),
    current_user = Depends(get_current_user)
) -> ListResponse[Report]:
    """List users with pagination metadata.

    Same query parameters as `/users` endpoint, but returns pagination info.
    Set `include_pagination=true` in query params.
    """
    service = ReportService()
    return await service.list(query)