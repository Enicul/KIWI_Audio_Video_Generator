"""Voice Actor agent for speech synthesis with ASR support."""

from collections.abc import Callable
from pathlib import Path
from typing import Any

from mutagen.mp3 import MP3

from kiwi_video.core.base_agent import BaseAgent
from kiwi_video.core.state_manager import StateManager
from kiwi_video.providers.llm.base import BaseLLMClient
from kiwi_video.providers.voice.elevenlabs_client import ElevenLabsClient
from kiwi_video.schemas.scene import Scene


class VoiceActorAgent(BaseAgent):
    """
    Agent responsible for generating voice-overs.
    
    Uses ElevenLabs API to synthesize natural-sounding speech from text.
    """

    def __init__(
        self,
        agent_name: str,
        llm_client: BaseLLMClient,
        state_manager: StateManager,
        workspace_dir: Path,
        voice_client: ElevenLabsClient
    ) -> None:
        """
        Initialize VoiceActor agent.
        
        Args:
            agent_name: Agent name
            llm_client: LLM client
            state_manager: State manager
            workspace_dir: Workspace directory
            voice_client: Voice synthesis client
        """
        super().__init__(agent_name, llm_client, state_manager, workspace_dir)
        self.voice_client = voice_client

    def register_tools(self) -> dict[str, Callable]:
        """Register agent tools."""
        return {
            "synthesize_voice": self._synthesize_voice_tool,
            "list_voices": self._list_voices_tool
        }

    def get_system_prompt(self) -> str:
        """Get system prompt."""
        return """You are a professional voice actor specialized in narration.
Generate high-quality, natural-sounding voice-overs for video content."""

    async def _execute_workflow(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Execute voice synthesis workflow for all scenes.
        
        Args:
            input_data: Must contain 'scenes' list with Scene objects or dicts
            
        Returns:
            Dictionary with scenes_audio_metadata
        """
        scenes = input_data.get("scenes", [])

        if not scenes:
            raise ValueError("No scenes provided for voice generation")

        self.logger.info(f"🎙️ Generating voice-overs for {len(scenes)} scenes")

        scenes_metadata = {}

        for scene_data in scenes:
            # Handle both Scene objects and dicts
            if isinstance(scene_data, Scene):
                scene_id = scene_data.scene_id
                voice_text = scene_data.voice_over_text
            else:
                scene_id = scene_data.get("scene_id")
                voice_text = scene_data.get("voice_over_text", "")

            if not voice_text:
                self.logger.warning(f"Scene {scene_id} has no voice-over text, skipping")
                continue

            self.logger.info(f"Processing {scene_id}: {len(voice_text)} characters")

            # Generate audio with ASR
            metadata = await self._generate_scene_audio(scene_id, voice_text)
            scenes_metadata[scene_id] = metadata

            self.logger.info(
                f"✅ {scene_id}: audio={metadata['audio_path']}, "
                f"duration={metadata['duration']:.2f}s"
            )

        return {
            "scenes_processed": len(scenes_metadata),
            "scenes_metadata": scenes_metadata
        }

    async def _generate_scene_audio(
        self,
        scene_id: str,
        voice_text: str,
        voice_id: str | None = None,
        generate_asr: bool = True
    ) -> dict[str, Any]:
        """
        Generate audio and ASR for a single scene.
        
        Args:
            scene_id: Scene identifier
            voice_text: Text to synthesize
            voice_id: Optional specific voice ID
            generate_asr: Whether to generate ASR data
            
        Returns:
            Dictionary with audio_path, asr_path, duration
        """
        # Setup paths
        audio_dir = self.workspace_dir / "audio"
        audio_dir.mkdir(parents=True, exist_ok=True)

        audio_path = audio_dir / f"{scene_id}_voice.mp3"
        asr_path = audio_dir / f"{scene_id}_asr.json"

        # Step 1: Synthesize speech
        self.logger.info(f"  🗣️ Synthesizing speech for {scene_id}...")
        await self.voice_client.synthesize(
            text=voice_text,
            voice_id=voice_id,
            output_path=audio_path
        )

        # Step 2: Get audio duration
        duration = self._get_audio_duration(audio_path)
        self.logger.info(f"  ⏱️ Audio duration: {duration:.2f} seconds")

        # Step 3: Generate ASR (word-level timestamps)
        asr_data = None
        if generate_asr:
            self.logger.info("  📝 Generating ASR transcript...")
            try:
                asr_data = await self.voice_client.speech_to_text(
                    audio_path=audio_path,
                    output_path=asr_path
                )
                self.logger.info(f"  ✅ ASR saved: {asr_path}")
            except Exception as e:
                self.logger.warning(f"  ⚠️ ASR generation failed: {e}")
                asr_path = None

        return {
            "scene_id": scene_id,
            "audio_path": str(audio_path),
            "asr_path": str(asr_path) if asr_path and asr_path.exists() else None,
            "duration": duration,
            "text_length": len(voice_text),
            "word_count": len(voice_text.split()),
            "asr_data": asr_data
        }

    def _get_audio_duration(self, audio_path: Path) -> float:
        """
        Get duration of audio file in seconds.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Duration in seconds
        """
        try:
            audio = MP3(str(audio_path))
            return audio.info.length
        except Exception as e:
            self.logger.error(f"Failed to get audio duration: {e}")
            # Fallback: estimate based on file size
            # ~128kbps MP3 = ~16KB/second
            file_size_kb = audio_path.stat().st_size / 1024
            return file_size_kb / 16.0

    def _synthesize_voice_tool(self, text: str, voice_id: str | None = None) -> dict[str, Any]:
        """Synthesize voice (tool function)."""
        result = self._execute_workflow({
            "text": text,
            "voice_id": voice_id
        })
        return {"status": "success", **result}

    def _list_voices_tool(self) -> dict[str, Any]:
        """List available voices (tool function)."""
        try:
            voices = self.voice_client.get_voices()
            return {
                "status": "success",
                "voices": voices,
                "count": len(voices)
            }
        except Exception as e:
            return {"status": "failed", "error": str(e)}

