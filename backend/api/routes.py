"""
REST API Routes - Simple and direct
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from typing import List
from pathlib import Path

from models.schemas import (
    VideoRequest, 
    TaskResponse, 
    TaskStatusResponse,
    TaskStatus,
    TaskPhase
)
from services.task_manager import task_manager
from agents.orchestrator import orchestrator

router = APIRouter()

# Video files directory
VIDEO_DIR = Path("generated/videos")


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "KIWI-Video API"}


@router.post("/video/create", response_model=TaskResponse)
async def create_video(request: VideoRequest, background_tasks: BackgroundTasks):
    """
    Create a new video generation task.
    Returns immediately with task_id, processing happens in background.
    """
    # Validate input
    if not request.audio_data and not request.text_input:
        raise HTTPException(
            status_code=400, 
            detail="Either audio_data or text_input is required"
        )
    
    # Create task
    task = task_manager.create_task({
        "audio_data": request.audio_data,
        "text_input": request.text_input
    })
    
    # Define the processor function
    async def process_video(on_status_update):
        orchestrator.set_status_handler(on_status_update)
        return await orchestrator.process_video_request(
            task_id=task.id,
            audio_data=request.audio_data,
            text_input=request.text_input
        )
    
    # Start processing in background
    task_manager.start_task_async(task.id, process_video)
    
    return TaskResponse(
        task_id=task.id,
        status=TaskStatus.PENDING,
        message="Video generation task created. Use WebSocket or polling to track progress."
    )


@router.get("/video/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """Get the status of a video generation task"""
    task = task_manager.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return TaskStatusResponse(
        task_id=task.id,
        status=task.status,
        phase=task.phase,
        progress=task.progress,
        message=task.message,
        result=task.result,
        error=task.error,
        created_at=task.created_at,
        updated_at=task.updated_at
    )


@router.get("/video/tasks", response_model=List[dict])
async def list_tasks():
    """List all tasks (for debugging)"""
    return task_manager.get_all_tasks()


@router.delete("/video/task/{task_id}")
async def delete_task(task_id: str):
    """Delete a task (for cleanup)"""
    task = task_manager.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    del task_manager.tasks[task_id]
    
    return {"message": f"Task {task_id} deleted"}


@router.get("/video/file/{filename}")
async def get_video_file(filename: str):
    """Serve generated video files"""
    # Security: only allow mp4 files, prevent directory traversal
    if not filename.endswith(".mp4") or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    video_path = VIDEO_DIR / filename
    
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video not found")
    
    return FileResponse(
        path=str(video_path),
        media_type="video/mp4",
        filename=filename
    )

