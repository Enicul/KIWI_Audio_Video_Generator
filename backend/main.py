"""
KIWI-Video Backend API
Simple FastAPI application for video generation from voice
"""
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from config import settings
from api.routes import router
from api.websocket import websocket_endpoint

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="Voice to Video Generation API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware - Allow all origins in development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=False,  # Must be False when allow_origins=["*"]
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include REST routes
app.include_router(router, prefix="/api", tags=["Video Generation"])

# WebSocket endpoint
@app.websocket("/ws/{task_id}")
async def ws_endpoint(websocket: WebSocket, task_id: str):
    """WebSocket endpoint for real-time task updates"""
    await websocket_endpoint(websocket, task_id)

# Root endpoint
@app.get("/")
async def root():
    return {
        "service": settings.APP_NAME,
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs"
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )

