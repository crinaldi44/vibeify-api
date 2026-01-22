from celery.result import AsyncResult
from fastapi import APIRouter, Depends
from fastapi.params import Path

from vibeify_api.core.celery_app import celery_app
from vibeify_api.core.exceptions import ERROR_RESPONSES
from vibeify_api.core.dependencies import authorization
from vibeify_api.schemas.jobs import JobStatus

router = APIRouter(prefix="/jobs", tags=["Jobs"])

@router.get(
    "/{jobId}",
    response_model=JobStatus,
    responses=ERROR_RESPONSES
)
async def get_jobs(
    job_id: str = Path(alias="jobId", min_length=1),
    current_user = Depends(authorization())
):
    result = AsyncResult(job_id, app=celery_app)
    return JobStatus(
        job_id=job_id,
        status=result.status,
        result=result.result if result.successful() else None
    )
