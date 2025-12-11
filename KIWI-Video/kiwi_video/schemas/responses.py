"""API response models."""

from typing import Any

from pydantic import BaseModel, Field

from kiwi_video.schemas.project import ProjectStatus


class ProjectResponse(BaseModel):
    """Response model for project creation and retrieval."""

    project_id: str = Field(
        ...,
        description="Unique project identifier"
    )

    status: ProjectStatus = Field(
        ...,
        description="Current project status"
    )

    workspace_dir: str = Field(
        ...,
        description="Path to project workspace"
    )

    message: str = Field(
        default="Project created successfully",
        description="Response message"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "project_id": "project_abc123",
                "status": "processing",
                "workspace_dir": "/workspaces/project_abc123",
                "message": "Project created and processing started"
            }
        }


class StatusResponse(BaseModel):
    """Response model for project status checks."""

    project_id: str = Field(
        ...,
        description="Project identifier"
    )

    status: ProjectStatus = Field(
        ...,
        description="Current status"
    )

    current_phase: str | None = Field(
        None,
        description="Currently executing phase"
    )

    progress: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Overall progress (0.0 to 1.0)"
    )

    phases: dict[str, Any] = Field(
        default_factory=dict,
        description="Status of each phase"
    )

    final_output: dict[str, Any] | None = Field(
        None,
        description="Final output if completed"
    )

    error: str | None = Field(
        None,
        description="Error message if failed"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "project_id": "project_abc123",
                "status": "processing",
                "current_phase": "storyboard",
                "progress": 0.35,
                "phases": {
                    "story_loader": {"status": "completed"},
                    "storyboard": {"status": "in_progress"},
                    "film_crew": {"status": "pending"}
                }
            }
        }


class ErrorResponse(BaseModel):
    """Response model for errors."""

    error: str = Field(
        ...,
        description="Error type or code"
    )

    message: str = Field(
        ...,
        description="Human-readable error message"
    )

    details: dict[str, Any] | None = Field(
        None,
        description="Additional error details"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "error": "ValidationError",
                "message": "Invalid project prompt: must be at least 10 characters",
                "details": {
                    "field": "prompt",
                    "constraint": "min_length"
                }
            }
        }


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str = Field(
        default="healthy",
        description="Service status"
    )

    version: str = Field(
        ...,
        description="API version"
    )

    uptime: float = Field(
        ...,
        description="Service uptime in seconds"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "0.1.0",
                "uptime": 3600.0
            }
        }


class ListProjectsResponse(BaseModel):
    """Response model for listing projects."""

    projects: list[ProjectResponse] = Field(
        default_factory=list,
        description="List of projects"
    )

    total: int = Field(
        ...,
        description="Total number of projects"
    )

    page: int = Field(
        default=1,
        description="Current page number"
    )

    page_size: int = Field(
        default=10,
        description="Number of items per page"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "projects": [
                    {
                        "project_id": "project_abc123",
                        "status": "completed",
                        "workspace_dir": "/workspaces/project_abc123"
                    }
                ],
                "total": 1,
                "page": 1,
                "page_size": 10
            }
        }

