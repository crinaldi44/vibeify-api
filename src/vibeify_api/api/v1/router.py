"""API v1 router."""
from fastapi import APIRouter

from vibeify_api.api.v1 import auth, documents, users, jobs

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(documents.router)
api_router.include_router(jobs.router)
