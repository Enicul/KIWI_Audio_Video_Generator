"""Project management routes."""

import uuid

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query

from kiwi_video.core.orchestrator import DirectorOrchestrator
from kiwi_video.core.state_manager import StateManager
from kiwi_video.schemas.project import CreateProjectRequest, ProjectStatus
from kiwi_video.schemas.responses import ListProjectsResponse, ProjectResponse, StatusResponse
from kiwi_video.utils.config import settings
from kiwi_video.utils.logger import get_logger

router = APIRouter()
logger = get_logger("api.projects")


@router.post("/projects", response_model=ProjectResponse)
async def create_project(
    request: CreateProjectRequest,
    background_tasks: BackgroundTasks
):
    """
    Create a new video generation project.
    
    The project will be executed asynchronously in the background.
    Use the returned project_id to check status and retrieve results.
    
    Args:
        request: Project creation request
        background_tasks: FastAPI background tasks
        
    Returns:
        Project response with project_id and initial status
    """
    try:
        # Generate unique project ID
        project_id = f"project_{uuid.uuid4().hex[:8]}"

        logger.info(f"Creating project: {project_id}")
        logger.debug(f"Prompt: {request.prompt}")

        # Create orchestrator
        orchestrator = DirectorOrchestrator(project_id=project_id)

        # Schedule project execution in background
        background_tasks.add_task(
            _execute_project_background,
            orchestrator,
            request.prompt
        )

        # Return immediate response
        return ProjectResponse(
            project_id=project_id,
            status=ProjectStatus.PROCESSING,
            workspace_dir=str(orchestrator.workspace_dir),
            message="Project created and processing started"
        )

    except Exception as e:
        logger.error(f"Failed to create project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _execute_project_background(orchestrator: DirectorOrchestrator, user_input: str):
    """
    Execute project in background.
    
    Args:
        orchestrator: Director orchestrator instance
        user_input: User's video prompt
    """
    try:
        logger.info(f"Background execution started: {orchestrator.project_id}")
        await orchestrator.execute_project(user_input)
        logger.info(f"Background execution completed: {orchestrator.project_id}")
    except Exception as e:
        logger.error(f"Background execution failed: {e}", exc_info=True)


@router.get("/projects/{project_id}", response_model=StatusResponse)
async def get_project_status(project_id: str):
    """
    Get project status and progress.
    
    Args:
        project_id: Project identifier
        
    Returns:
        Status response with current progress
    """
    try:
        # Find project workspace
        workspace_dir = settings.workspace_dir / project_id

        if not workspace_dir.exists():
            raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")

        # Load state
        state_manager = StateManager(workspace_dir)
        state = state_manager.get_state()

        # Calculate progress
        progress = _calculate_progress(state)

        return StatusResponse(
            project_id=project_id,
            status=ProjectStatus(state.get("status", "initialized")),
            current_phase=state.get("current_phase"),
            progress=progress,
            phases=state.get("phases", {}),
            final_output=state.get("final_output"),
            error=state.get("error")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get project status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects")
async def list_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100)
):
    """
    List all projects.
    
    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page
        
    Returns:
        List of projects with pagination
    """
    try:
        workspace_dir = settings.workspace_dir

        if not workspace_dir.exists():
            return ListProjectsResponse(projects=[], total=0, page=page, page_size=page_size)

        # Find all project directories
        project_dirs = [d for d in workspace_dir.iterdir() if d.is_dir() and d.name.startswith("project_")]

        # Sort by modification time (newest first)
        project_dirs.sort(key=lambda d: d.stat().st_mtime, reverse=True)

        # Pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_dirs = project_dirs[start_idx:end_idx]

        # Build project responses
        projects = []
        for proj_dir in paginated_dirs:
            try:
                state_manager = StateManager(proj_dir)
                state = state_manager.get_state()

                projects.append(
                    ProjectResponse(
                        project_id=proj_dir.name,
                        status=ProjectStatus(state.get("status", "initialized")),
                        workspace_dir=str(proj_dir),
                        message=state.get("user_input", "")[:100]
                    )
                )
            except Exception as e:
                logger.warning(f"Failed to load project {proj_dir.name}: {e}")
                continue

        return ListProjectsResponse(
            projects=projects,
            total=len(project_dirs),
            page=page,
            page_size=page_size
        )

    except Exception as e:
        logger.error(f"Failed to list projects: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/projects/{project_id}")
async def delete_project(project_id: str):
    """
    Delete a project and all its files.
    
    Args:
        project_id: Project identifier
        
    Returns:
        Success message
    """
    try:
        workspace_dir = settings.workspace_dir / project_id

        if not workspace_dir.exists():
            raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")

        # Delete project directory
        import shutil
        shutil.rmtree(workspace_dir)

        logger.info(f"Deleted project: {project_id}")

        return {"message": f"Project {project_id} deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/result")
async def get_project_result(project_id: str):
    """
    Get final project result (video file info).
    
    Args:
        project_id: Project identifier
        
    Returns:
        Result information with video path
    """
    try:
        workspace_dir = settings.workspace_dir / project_id

        if not workspace_dir.exists():
            raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")

        # Load state
        state_manager = StateManager(workspace_dir)
        state = state_manager.get_state()

        # Check if completed
        if state.get("status") != ProjectStatus.COMPLETED.value:
            raise HTTPException(
                status_code=400,
                detail=f"Project not completed yet. Current status: {state.get('status')}"
            )

        final_output = state.get("final_output")

        if not final_output:
            raise HTTPException(status_code=404, detail="Final output not available")

        return {
            "project_id": project_id,
            "status": "completed",
            "final_output": final_output
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get project result: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _calculate_progress(state: dict) -> float:
    """
    Calculate overall project progress.
    
    Args:
        state: Project state dictionary
        
    Returns:
        Progress value between 0.0 and 1.0
    """
    phases = state.get("phases", {})

    if not phases:
        return 0.0

    # Weight for each phase
    phase_weights = {
        "story_loader": 0.2,
        "storyboard": 0.2,
        "film_crew": 0.5,
        "voice_actor": 0.1
    }

    total_progress = 0.0

    for phase_name, weight in phase_weights.items():
        phase_data = phases.get(phase_name, {})
        phase_status = phase_data.get("status", "pending")

        if phase_status == "completed":
            total_progress += weight
        elif phase_status == "in_progress":
            total_progress += weight * 0.5

    return round(total_progress, 2)

