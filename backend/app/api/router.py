"""Main API router that mounts all sub-routers under /api/v1."""

from fastapi import APIRouter

from app.api.activities import router as activities_router
from app.api.auth import router as auth_router
from app.api.classes import router as classes_router
from app.api.history import router as history_router
from app.api.subjects import router as subjects_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(classes_router)
api_router.include_router(subjects_router)
api_router.include_router(activities_router)
api_router.include_router(history_router)
