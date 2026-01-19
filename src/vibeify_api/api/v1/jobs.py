from celery.result import AsyncResult
from fastapi import APIRouter
from fastapi.params import Path

from vibeify_api.core.celery_app import celery_app

router = APIRouter(prefix="/jobs", tags=["jobs"])

@router.get("/{jobId}")
async def get_jobs(job_id: str = Path(alias="jobId", min_length=1)):
    result = AsyncResult(job_id, app=celery_app)
    return {
        "jobId": job_id,
        "status": result.status,
        "result": result.result if result.successful() else None
    }
