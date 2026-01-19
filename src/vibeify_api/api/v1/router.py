"""API v1 router."""
from fastapi import APIRouter

from vibeify_api.api.v1 import auth, users

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(users.router)
