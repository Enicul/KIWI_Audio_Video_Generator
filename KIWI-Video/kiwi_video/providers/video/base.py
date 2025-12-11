"""Base video generation provider interface."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional


class BaseVideoProvider(ABC):
    """
    Abstract base class for video generation providers.
    
    All video generation client implementations must inherit from this class.
    """

    @abstractmethod
    async def generate_video(
        self,
        prompt: str,
        negative_prompt: str,
        duration: int = 8,
        aspect_ratio: str = "16:9"
    ) -> str:
        """
        Generate video from text prompt.
        
        Args:
            prompt: Text description of video to generate
            negative_prompt: Things to avoid in generation
            duration: Video duration in seconds
            aspect_ratio: Video aspect ratio
            
        Returns:
            URI or path to generated video
        """
        pass

    @abstractmethod
    async def download_video(self, video_uri: str, output_path: Path) -> Path:
        """
        Download video from URI to local path.
        
        Args:
            video_uri: URI of video to download
            output_path: Local path to save video
            
        Returns:
            Path to downloaded video
        """
        pass

