"""Project data models."""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from kiwi_video.schemas.scene import Scene


class ProjectStatus(str, Enum):
    """Project status enumeration."""

    INITIALIZED = "initialized"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PhaseStatus(BaseModel):
    """Status of a single phase in the project."""

    status: str = Field(
        default="pending",
        description="Phase status ('pending', 'in_progress', 'completed', 'failed')"
    )

    started_at: str | None = Field(
        None,
        description="ISO timestamp when phase started"
    )

    completed_at: str | None = Field(
        None,
        description="ISO timestamp when phase completed"
    )

    output: dict[str, Any] = Field(
        default_factory=dict,
        description="Output data from this phase"
    )

    error: str | None = Field(
        None,
        description="Error message if phase failed"
    )


class Project(BaseModel):
    """
    Complete project model.
    
    Represents a video generation project with all its phases and outputs.
    """

    project_id: str = Field(
        ...,
        description="Unique project identifier"
    )

    status: ProjectStatus = Field(
        default=ProjectStatus.INITIALIZED,
        description="Current project status"
    )

    workspace_dir: Path = Field(
        ...,
        description="Path to project workspace directory"
    )

    user_input: str | None = Field(
        None,
        description="Original user input/prompt"
    )

    created_at: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Project creation timestamp"
    )

    updated_at: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Last update timestamp"
    )

    current_phase: str | None = Field(
        None,
        description="Currently executing phase"
    )

    phases: dict[str, Any] = Field(
        default_factory=dict,
        description="Status of each project phase"
    )

    scenes: list[Scene] = Field(
        default_factory=list,
        description="List of scenes in the project"
    )

    final_output: dict[str, Any] | None = Field(
        None,
        description="Final project output (video path, metadata, etc.)"
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional project metadata"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "project_id": "project_abc123",
                "status": "completed",
                "user_input": "Create an inspiring video about space exploration",
                "current_phase": None,
                "final_output": {
                    "final_video_path": "/workspaces/project_abc123/final_video.mp4",
                    "duration": 45.0,
                    "total_scenes": 5
                }
            }
        }


class CreateProjectRequest(BaseModel):
    """Request model for creating a new project."""

    prompt: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="Text description of the video to generate"
    )

    style: str | None = Field(
        None,
        description="Optional style specification (e.g., 'professional', 'casual', 'cinematic')"
    )

    duration: float | None = Field(
        None,
        ge=5.0,
        le=300.0,
        description="Desired video duration in seconds"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "prompt": "Create an inspiring video about space exploration, showing the journey from early rockets to interstellar travel",
                "style": "cinematic",
                "duration": 60.0
            }
        }

