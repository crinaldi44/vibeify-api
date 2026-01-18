"""API v1 router."""
from fastapi import APIRouter

api_router = APIRouter()


@api_router.get("/")
async def api_root():
    """API root endpoint."""
    return {"message": "Vibeify API v1"}
