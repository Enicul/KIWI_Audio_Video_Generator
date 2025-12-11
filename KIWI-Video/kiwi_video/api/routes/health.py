"""Health check routes."""

import time

from fastapi import APIRouter

from kiwi_video import __version__
from kiwi_video.schemas.responses import HealthResponse

router = APIRouter()

# Track startup time
_start_time = time.time()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    
    Returns service status and uptime.
    """
    uptime = time.time() - _start_time

    return HealthResponse(
        status="healthy",
        version=__version__,
        uptime=uptime
    )


@router.get("/version")
async def get_version():
    """Get API version information."""
    return {
        "version": __version__,
        "name": "KIWI-Video API"
    }

