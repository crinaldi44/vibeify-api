"""Discovery API routes.

Triggers a Celery orchestrator that enqueues per-URL crawl jobs.
"""

from fastapi import APIRouter, Depends, status

from vibeify_api.core.dependencies import authorization
from vibeify_api.core.exceptions import ERROR_RESPONSES
from vibeify_api.models.user import User
from vibeify_api.schemas.discovery import DiscoveryJobResponse, DiscoveryRequest
from vibeify_api.tasks.orchestrators.discovery import orchestrate_discovery

router = APIRouter(prefix="/discovery", tags=["Discovery"])


@router.post(
    "",
    status_code=status.HTTP_202_ACCEPTED,
    responses=ERROR_RESPONSES,
    summary="Trigger discovery crawl for a list of URLs",
)
async def start_discovery(
    request: DiscoveryRequest,
    # current_user: User = Depends(authorization()),
) -> DiscoveryJobResponse:
    result = orchestrate_discovery.delay(
        urls=request.urls,
        data_origin=request.data_origin,
        target_application=request.target_application,
        crawl=request.crawl,
        user_id=None,
    )
    return DiscoveryJobResponse(job_id=result.id)
