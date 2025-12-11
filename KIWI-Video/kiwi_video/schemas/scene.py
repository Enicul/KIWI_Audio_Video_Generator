"""Scene and Shot data models."""


from pydantic import BaseModel, Field


class Shot(BaseModel):
    """
    Represents a single shot within a scene.
    
    A shot is the smallest unit of video, typically focusing on one specific visual element.
    """

    shot_id: int = Field(
        ...,
        description="Unique identifier for the shot within the scene"
    )

    voice_over_cue: str = Field(
        ...,
        description="Voice-over text snippet that cues this shot"
    )

    visual_description: str = Field(
        ...,
        description="Detailed description of what appears in this shot"
    )

    camera_angle: str = Field(
        default="eye-level",
        description="Camera angle (e.g., 'high-angle', 'low-angle', 'eye-level')"
    )

    camera_movement: str = Field(
        default="static",
        description="Camera movement (e.g., 'pan', 'tilt', 'zoom', 'dolly', 'static')"
    )

    duration: float = Field(
        default=5.0,
        ge=1.0,
        le=30.0,
        description="Duration of the shot in seconds"
    )

    start_time: float | None = Field(
        None,
        ge=0.0,
        description="Start time of the shot relative to scene audio (seconds)"
    )

    end_time: float | None = Field(
        None,
        ge=0.0,
        description="End time of the shot relative to scene audio (seconds)"
    )

    shot_type: str = Field(
        default="medium_shot",
        description="Type of shot (e.g., 'wide', 'medium', 'closeup', 'extreme_closeup')"
    )

    lighting: str = Field(
        default="natural",
        description="Lighting style for the shot"
    )

    mood: str = Field(
        default="neutral",
        description="Emotional mood/tone of the shot"
    )

    transition: str | None = Field(
        None,
        description="Transition effect to next shot (e.g., 'cut', 'dissolve', 'fade')"
    )


class Scene(BaseModel):
    """
    Represents a complete scene in the video.
    
    A scene consists of multiple shots that together convey a narrative beat.
    """

    scene_id: str = Field(
        ...,
        description="Unique identifier for the scene (e.g., 'scene_001')"
    )

    scene_description: str = Field(
        ...,
        description="Overall description of the scene's narrative and visual elements"
    )

    voice_over_text: str = Field(
        ...,
        description="Complete voice-over script for this scene"
    )

    duration: float = Field(
        default=10.0,
        ge=1.0,
        description="Total duration of the scene in seconds"
    )

    shots: list[Shot] = Field(
        default_factory=list,
        description="List of shots that make up this scene"
    )

    status: str = Field(
        default="pending",
        description="Status of scene processing ('pending', 'in_progress', 'completed', 'failed')"
    )

    clip_path: str | None = Field(
        None,
        description="Path to the generated video clip for this scene"
    )

    audio_path: str | None = Field(
        None,
        description="Path to the generated audio/voice-over for this scene"
    )

    audio_duration: float | None = Field(
        None,
        ge=0.0,
        description="Actual duration of the generated audio in seconds"
    )

    asr_path: str | None = Field(
        None,
        description="Path to the ASR (Automatic Speech Recognition) JSON file with word-level timestamps"
    )

    storyboard_image_path: str | None = Field(
        None,
        description="Path to the storyboard visualization for this scene"
    )

    metadata: dict = Field(
        default_factory=dict,
        description="Additional metadata for the scene"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "scene_id": "scene_001",
                "scene_description": "Opening shot of a futuristic cityscape at dawn",
                "voice_over_text": "In the year 2099, humanity has reached for the stars",
                "duration": 8.0,
                "status": "completed",
                "shots": [
                    {
                        "shot_id": 1,
                        "voice_over_cue": "In the year 2099",
                        "visual_description": "Wide aerial view of gleaming skyscrapers",
                        "camera_angle": "high-angle",
                        "camera_movement": "slow_pan",
                        "duration": 4.0,
                        "shot_type": "wide",
                        "lighting": "golden_hour",
                        "mood": "hopeful"
                    }
                ]
            }
        }

