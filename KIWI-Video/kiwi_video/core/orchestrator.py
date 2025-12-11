"""Director orchestrator for managing the complete video generation workflow."""

import uuid
from pathlib import Path
from typing import Any

from kiwi_video.core.exceptions import KiwiVideoError
from kiwi_video.core.state_manager import StateManager
from kiwi_video.providers.llm.gemini_client import GeminiClient
from kiwi_video.schemas.project import Project, ProjectStatus
from kiwi_video.utils.config import settings
from kiwi_video.utils.logger import get_logger


class DirectorOrchestrator:
    """
    Director orchestrator that manages the complete video generation workflow.
    
    This is the main controller that coordinates all agents in a sequential manner:
    1. StoryLoader Agent - Generate script
    2. Storyboard Agent - Create visual storyboard
    3. VoiceActor Agent - Generate audio for each scene
    4. FilmCrew Agent - Produce video clips based on audio duration
    5. Final compilation - Merge all clips into final video
    """

    def __init__(
        self,
        project_id: str | None = None,
        workspace_dir: Path | None = None
    ) -> None:
        """
        Initialize the director orchestrator.
        
        Args:
            project_id: Unique project identifier (generated if not provided)
            workspace_dir: Working directory (uses config default if not provided)
        """
        self.project_id = project_id or f"project_{uuid.uuid4().hex[:8]}"
        self.workspace_dir = workspace_dir or (settings.workspace_dir / self.project_id)
        self.workspace_dir.mkdir(parents=True, exist_ok=True)

        self.logger = get_logger("director")
        self.logger.info(f"Initializing Director for project: {self.project_id}")

        # Initialize state manager
        self.state_manager = StateManager(self.workspace_dir)

        # Initialize LLM client
        self.llm_client = GeminiClient(
            api_key=settings.gemini_api_key,
            model_name="gemini-2.5-pro"
        )

        # Agents will be initialized lazily when needed
        self._story_loader = None
        self._storyboard = None
        self._film_crew = None
        self._voice_actor = None

    async def execute_project(self, user_input: str) -> dict[str, Any]:
        """
        Execute the complete video generation workflow.
        
        Args:
            user_input: User's text description of desired video
            
        Returns:
            Dictionary containing final video path and metadata
            
        Raises:
            KiwiVideoError: If workflow execution fails
        """
        try:
            self.logger.info(f"Starting project execution: {user_input}")

            # Update state to processing
            self.state_manager.update_state({
                "status": ProjectStatus.PROCESSING.value,
                "user_input": user_input
            })

            # Phase 1: Generate script
            self.logger.info("Phase 1: Script generation")
            script_result = await self._run_story_loader(user_input)

            # Phase 2: Generate audio for all scenes (BEFORE storyboard!)
            # This gives us actual audio durations for precise shot planning
            self.logger.info("Phase 2: Audio generation (audio-first workflow)")
            audio_result = await self._run_voice_actor(script_result)

            # Phase 3: Create storyboard (using ACTUAL audio durations)
            self.logger.info("Phase 3: Storyboard creation (with actual audio durations)")
            storyboard_result = await self._run_storyboard(script_result, audio_result)

            # Phase 4: Generate video clips (perfectly synchronized!)
            self.logger.info("Phase 4: Video clip generation")
            clips_results = await self._run_film_crew(storyboard_result, audio_result)

            # Phase 5: Compile final video
            self.logger.info("Phase 5: Final video compilation")
            final_video = await self._compile_final_video(clips_results)

            # Update state with final output
            self.state_manager.set_final_output({
                "final_video_path": str(final_video),
                "user_input": user_input,
                "total_scenes": len(clips_results),
                "workspace": str(self.workspace_dir)
            })

            self.logger.info(f"Project completed successfully: {final_video}")

            return {
                "status": "success",
                "project_id": self.project_id,
                "final_video_path": str(final_video),
                "workspace_dir": str(self.workspace_dir)
            }

        except Exception as e:
            self.logger.error(f"Project execution failed: {e}", exc_info=True)
            self.state_manager.update_state({
                "status": ProjectStatus.FAILED.value,
                "error": str(e)
            })
            raise KiwiVideoError(f"Project execution failed: {e}")

    async def _run_story_loader(self, user_input: str) -> dict[str, Any]:
        """
        Run the StoryLoader agent to generate script.
        
        Args:
            user_input: User's text input
            
        Returns:
            Dictionary containing script and style guide paths
        """
        self.state_manager.start_phase("story_loader")

        try:
            # Import here to avoid circular dependencies
            from kiwi_video.agents.story_loader import StoryLoaderAgent

            if self._story_loader is None:
                self._story_loader = StoryLoaderAgent(
                    agent_name="story_loader",
                    llm_client=self.llm_client,
                    state_manager=self.state_manager,
                    workspace_dir=self.workspace_dir
                )

            # Run the agent
            result = await self._story_loader.run({
                "topic": user_input,
                "style": "professional"
            })

            self.state_manager.complete_phase("story_loader", result)
            return result

        except Exception as e:
            self.state_manager.fail_phase("story_loader", str(e))
            raise

    async def _run_storyboard(
        self,
        script_data: dict[str, Any],
        audio_result: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Run the Storyboard agent to create visual storyboard.
        
        Args:
            script_data: Script data from StoryLoader
            audio_result: Audio metadata with actual durations
            
        Returns:
            Dictionary containing storyboard data and images
        """
        self.state_manager.start_phase("storyboard")

        try:
            # Import here to avoid circular dependencies
            from kiwi_video.agents.storyboard import StoryboardAgent

            if self._storyboard is None:
                self._storyboard = StoryboardAgent(
                    agent_name="storyboard",
                    llm_client=self.llm_client,
                    state_manager=self.state_manager,
                    workspace_dir=self.workspace_dir
                )

            # Run the agent with script and actual audio durations
            result = await self._storyboard.run({
                "script": script_data,
                "audio_metadata": audio_result.get("scenes_metadata", {})
            })

            self.state_manager.complete_phase("storyboard", result)
            return result

        except Exception as e:
            self.state_manager.fail_phase("storyboard", str(e))
            raise

    async def _run_voice_actor(self, script_data: dict[str, Any]) -> dict[str, Any]:
        """
        Run the VoiceActor agent to generate audio for all scenes.
        
        Args:
            script_data: Script data with scenes (from StoryLoader)
            
        Returns:
            Dictionary containing audio metadata for each scene
        """
        self.state_manager.start_phase("voice_actor")

        try:
            # Import here to avoid circular dependencies
            from kiwi_video.agents.voice_actor import VoiceActorAgent
            from kiwi_video.providers.voice.elevenlabs_client import ElevenLabsClient

            # Initialize voice client
            voice_client = ElevenLabsClient()

            if self._voice_actor is None:
                self._voice_actor = VoiceActorAgent(
                    agent_name="voice_actor",
                    llm_client=self.llm_client,
                    state_manager=self.state_manager,
                    workspace_dir=self.workspace_dir,
                    voice_client=voice_client
                )

            # Run the agent with scenes from script
            result = await self._voice_actor.run({
                "scenes": script_data.get("scenes", [])
            })

            # Update scene metadata in state
            scenes_metadata = result.get("scenes_metadata", {})
            for scene_id, metadata in scenes_metadata.items():
                self.state_manager.update_state({
                    f"scenes.{scene_id}.audio_path": metadata.get("audio_path"),
                    f"scenes.{scene_id}.audio_duration": metadata.get("duration"),
                    f"scenes.{scene_id}.asr_path": metadata.get("asr_path")
                })

            self.state_manager.complete_phase("voice_actor", result)
            return result

        except Exception as e:
            self.state_manager.fail_phase("voice_actor", str(e))
            raise

    async def _run_film_crew(
        self,
        storyboard_data: dict[str, Any],
        audio_data: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """
        Run the FilmCrew agent for each scene.
        
        Args:
            storyboard_data: Storyboard data with scenes
            audio_data: Audio metadata for each scene
            
        Returns:
            List of dictionaries containing clip paths for each scene
        """
        self.state_manager.start_phase("film_crew")

        try:
            # Import here to avoid circular dependencies
            from kiwi_video.agents.film_crew import FilmCrewAgent
            from kiwi_video.providers.video.veo_client import VeoClient
            from kiwi_video.providers.voice.elevenlabs_client import ElevenLabsClient

            # Initialize providers
            veo_client = VeoClient()
            voice_client = ElevenLabsClient()

            if self._film_crew is None:
                self._film_crew = FilmCrewAgent(
                    agent_name="film_crew",
                    llm_client=self.llm_client,
                    state_manager=self.state_manager,
                    workspace_dir=self.workspace_dir,
                    veo_client=veo_client,
                    voice_client=voice_client
                )

            # Process each scene
            scenes = storyboard_data.get("scenes", [])
            scenes_metadata = audio_data.get("scenes_metadata", {})
            clips_results = []

            for i, scene in enumerate(scenes):
                scene_id = scene.get('scene_id')
                self.logger.info(f"Processing scene {i + 1}/{len(scenes)}: {scene_id}")

                # Get audio metadata for this scene
                audio_metadata = scenes_metadata.get(scene_id, {})

                # Run film crew for this scene with audio metadata
                result = await self._film_crew.run({
                    "scene": scene,
                    "audio_metadata": audio_metadata  # Pass audio duration and ASR
                })

                clips_results.append(result)

                # Update scene state
                self.state_manager.update_scene_state(
                    scene_id=scene.get("scene_id"),
                    scene_data={
                        "status": "completed",
                        "clip_path": result.get("clip_path")
                    }
                )

            self.state_manager.complete_phase("film_crew", {
                "total_scenes": len(scenes),
                "clips": clips_results
            })

            return clips_results

        except Exception as e:
            self.state_manager.fail_phase("film_crew", str(e))
            raise

    async def _compile_final_video(self, clips_results: list[dict[str, Any]]) -> Path:
        """
        Compile all scene clips into final video.
        
        Args:
            clips_results: List of clip results from film crew
            
        Returns:
            Path to final compiled video
        """
        try:
            from kiwi_video.utils.video_processor import VideoProcessor

            self.logger.info(f"Compiling final video from {len(clips_results)} clips")

            # Extract clip paths
            clip_paths = [
                Path(result["clip_path"])
                for result in clips_results
                if result.get("clip_path")
            ]

            if not clip_paths:
                raise KiwiVideoError("No video clips to compile")

            # Concatenate all clips
            final_video_path = self.workspace_dir / "final_video.mp4"

            await VideoProcessor.concat_videos(
                video_paths=clip_paths,
                output_path=final_video_path
            )

            self.logger.info(f"Final video compiled: {final_video_path}")

            return final_video_path

        except Exception as e:
            self.logger.error(f"Failed to compile final video: {e}")
            raise KiwiVideoError(f"Video compilation failed: {e}")

    def get_status(self) -> dict[str, Any]:
        """
        Get current project status.
        
        Returns:
            Dictionary containing project status and progress
        """
        state = self.state_manager.get_state()

        return {
            "project_id": self.project_id,
            "status": state.get("status"),
            "current_phase": state.get("current_phase"),
            "phases": state.get("phases"),
            "final_output": state.get("final_output")
        }

    def get_project(self) -> Project:
        """
        Get project information as a Pydantic model.
        
        Returns:
            Project model instance
        """
        state = self.state_manager.get_state()

        return Project(
            project_id=self.project_id,
            status=ProjectStatus(state.get("status", "initialized")),
            workspace_dir=self.workspace_dir,
            user_input=state.get("user_input"),
            created_at=state.get("created_at"),
            updated_at=state.get("updated_at"),
            phases=state.get("phases", {}),
            final_output=state.get("final_output")
        )

