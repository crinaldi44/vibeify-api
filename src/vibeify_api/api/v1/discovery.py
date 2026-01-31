"""Discovery API routes.

Triggers a Celery orchestrator that enqueues per-URL crawl jobs.
"""

from re import S
from typing import List
from fastapi import APIRouter, Depends, status

from vibeify_api.core.dependencies import authorization
from vibeify_api.core.exceptions import ERROR_RESPONSES
from vibeify_api.models.user import User
from vibeify_api.schemas.discovery import DiscoveryJobResponse, DiscoveryRequest, ProviderDiscoveryRequest
from vibeify_api.schemas.responses import ProviderDiscoveryResponse, ProviderDiscoveryResult
from vibeify_api.services.discovery import DiscoveryService
from vibeify_api.tasks.orchestrators.discovery import orchestrate_discovery

router = APIRouter(prefix="/discovery", tags=["Discovery"])

@router.post(
    "/plan",
    status_code=status.HTTP_200_OK,
    responses=ERROR_RESPONSES,
    summary="Validates discovery request and returns a plan for the discovery process containing urls to retrieve."
)
async def validate_discovery(
    request: DiscoveryRequest
) -> None:
    pass


@router.post(
    "",
    status_code=status.HTTP_202_ACCEPTED,
    responses=ERROR_RESPONSES,
    summary="Trigger discovery crawl for a list of URLs from CommonCrawl. Loads the application-tagged results into S3.",
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
        seed_url=request.seed_url,
        match_type=request.match_type,
        max_urls=request.max_urls,
        page_size=request.page_size,
        url_regex=request.url_regex,
    )
    return DiscoveryJobResponse(job_id=result.id)

@router.post(
    "/provider-search",
    status_code=status.HTTP_200_OK,
    summary="Search via an external provider and return normalized results.",
)
async def search(requests: List[ProviderDiscoveryRequest]) -> ProviderDiscoveryResponse:
    _service = DiscoveryService()
    return await _service.discover(requests)
