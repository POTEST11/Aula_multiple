"""FastAPI application factory with CORS and OpenAPI documentation."""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Sets up:
    - OpenAPI metadata (title, description, version)
    - CORS middleware for frontend integration
    - Main API router under /api/v1

    Returns:
        Configured FastAPI application instance.
    """
    app = FastAPI(
        title="Aula Múltiple API",
        description=(
            "API para la generación de actividades pedagógicas multigrado "
            "con inteligencia artificial y alineación curricular."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        redirect_slashes=False,
    )

    # CORS configuration for frontend integration
    # Use FRONTEND_URL env var in production; default to allow all for dev
    frontend_url = os.getenv("FRONTEND_URL", "")
    allowed_origins = [frontend_url] if frontend_url else ["*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount the main API router with all sub-routers
    app.include_router(api_router)

    return app


app = create_app()
