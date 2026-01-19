"""API v1 router."""
from fastapi import APIRouter

from vibeify_api.api.v1 import users

api_router = APIRouter()

# Include all API routers
api_router.include_router(users.router)


@api_router.get("/")
async def api_root():
    """API root endpoint."""
    return {"message": "Vibeify API v1"}
