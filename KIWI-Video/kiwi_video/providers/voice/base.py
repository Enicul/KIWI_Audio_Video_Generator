"""Base voice synthesis provider interface."""

from abc import ABC, abstractmethod
from pathlib import Path


class BaseVoiceProvider(ABC):
    """
    Abstract base class for voice synthesis providers.
    
    All voice synthesis client implementations must inherit from this class.
    """

    @abstractmethod
    async def synthesize(
        self,
        text: str,
        voice_id: str,
        output_path: Path
    ) -> Path:
        """
        Synthesize speech from text.
        
        Args:
            text: Text to convert to speech
            voice_id: Voice identifier
            output_path: Path to save audio file
            
        Returns:
            Path to generated audio file
        """
        pass

