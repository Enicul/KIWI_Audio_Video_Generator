"""FastAPI application for KIWI-Video."""

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from kiwi_video import __version__
from kiwi_video.api.routes import health, projects
from kiwi_video.core.exceptions import KiwiVideoError
from kiwi_video.utils.config import settings
from kiwi_video.utils.logger import get_logger

logger = get_logger("api")

# Application startup time
start_time = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for application startup and shutdown.
    
    Args:
        app: FastAPI application instance
    """
    # Startup
    logger.info("🚀 Starting KIWI-Video API")
    logger.info(f"Version: {__version__}")
    logger.info(f"Workspace directory: {settings.workspace_dir}")
    
    # Ensure workspace directory exists
    settings.workspace_dir.mkdir(parents=True, exist_ok=True)
    
    yield
    
    # Shutdown
    logger.info("👋 Shutting down KIWI-Video API")


# Create FastAPI application
app = FastAPI(
    title="KIWI-Video API",
    description="Multi-Agent Text-to-Video Generation Framework",
    version=__version__,
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(KiwiVideoError)
async def kiwi_video_exception_handler(request, exc: KiwiVideoError):
    """Handle KIWI-Video specific exceptions."""
    logger.error(f"KIWI-Video error: {exc}")
    
    return JSONResponse(
        status_code=500,
        content={
            "error": exc.__class__.__name__,
            "message": str(exc),
            "details": {}
        }
    )


@app.exception_handler(ValueError)
async def value_error_handler(request, exc: ValueError):
    """Handle validation errors."""
    logger.warning(f"Validation error: {exc}")
    
    return JSONResponse(
        status_code=400,
        content={
            "error": "ValidationError",
            "message": str(exc),
            "details": {}
        }
    )


# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(projects.router, prefix="/api/v1", tags=["Projects"])


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "KIWI-Video API",
        "version": __version__,
        "description": "Multi-Agent Text-to-Video Generation Framework",
        "docs_url": "/docs",
        "health_url": "/health",
        "uptime": time.time() - start_time
    }

