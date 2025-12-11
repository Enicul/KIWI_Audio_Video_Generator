"""FilmCrew agent for video generation."""

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from kiwi_video.core.base_agent import BaseAgent
from kiwi_video.core.state_manager import StateManager
from kiwi_video.providers.llm.base import BaseLLMClient
from kiwi_video.providers.video.veo_client import VeoClient
from kiwi_video.providers.voice.elevenlabs_client import ElevenLabsClient
from kiwi_video.utils.prompt_loader import load_prompt
from kiwi_video.utils.video_processor import VideoProcessor


class FilmCrewAgent(BaseAgent):
    """
    Agent responsible for generating video clips for scenes.
    
    Workflow:
    1. Generate high-level production plan
    2. Create video assets using Veo (no quality judgment loop)
    3. Generate voice-over using ElevenLabs
    4. Compose final scene clip with video + audio + optional subtitles
    """

    def __init__(
        self,
        agent_name: str,
        llm_client: BaseLLMClient,
        state_manager: StateManager,
        workspace_dir: Path,
        veo_client: VeoClient,
        voice_client: ElevenLabsClient
    ) -> None:
        """
        Initialize FilmCrew agent.
        
        Args:
            agent_name: Agent name
            llm_client: LLM client
            state_manager: State manager
            workspace_dir: Workspace directory
            veo_client: Veo video generation client
            voice_client: Voice synthesis client
        """
        super().__init__(agent_name, llm_client, state_manager, workspace_dir)

        self.veo_client = veo_client
        self.voice_client = voice_client
        self.asset_counter = 0

        # Load planning prompt
        try:
            self._planning_prompt = load_prompt("film_crew_planning")
        except Exception:
            self._planning_prompt = self._get_fallback_planning_prompt()

        # Load veo prompt template
        try:
            self._veo_prompt_template = load_prompt("veo_prompt")
        except Exception:
            self._veo_prompt_template = ""

    def register_tools(self) -> dict[str, Callable]:
        """Register agent tools."""
        return {
            "generate_plan": self._generate_high_level_plan_tool,
            "create_asset": self._create_video_asset_tool
        }

    def get_system_prompt(self) -> str:
        """Get system prompt."""
        return self._planning_prompt

    def _get_fallback_planning_prompt(self) -> str:
        """Fallback planning prompt."""
        return """You are a professional video production crew.
Create production plans and generate video assets."""

    async def _execute_workflow(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Execute video production workflow for a single scene.
        
        Args:
            input_data: Must contain 'scene' dictionary and 'audio_metadata'
            
        Returns:
            Dictionary with clip_path and scene metadata
        """
        scene = input_data.get("scene", {})
        audio_metadata = input_data.get("audio_metadata", {})
        scene_id = scene.get("scene_id", "scene_001")

        self.logger.info(f"🎬 Starting video production for scene: {scene_id}")

        # Get audio duration and paths from metadata
        audio_duration = audio_metadata.get("duration", scene.get("duration", 8.0))
        audio_path_str = audio_metadata.get("audio_path")
        asr_path = audio_metadata.get("asr_path")

        # Convert audio_path to Path object
        audio_path = Path(audio_path_str) if audio_path_str else None

        self.logger.info(f"  📊 Audio duration: {audio_duration:.2f}s")
        self.logger.info(f"  🎙️ Audio path: {audio_path}")
        if asr_path:
            self.logger.info(f"  📝 ASR path: {asr_path}")

        # Step 1: Generate high-level production plan (based on audio duration)
        plan = self._generate_high_level_plan(scene, audio_duration, asr_path)

        # Step 2: Create video assets for each shot
        shot_assets = []  # List of (shot, asset_path) tuples
        for shot in plan.get("shots", []):
            asset_path = await self._create_video_asset(shot, scene_id)
            if asset_path:
                shot_assets.append((shot, asset_path))

        # Step 3: Compose final scene clip (using pre-generated audio)
        final_clip_path = await self._compose_scene_clip(
            scene_id=scene_id,
            shot_assets=shot_assets,
            voice_path=audio_path,
            voice_text=scene.get("voice_over_text", "")
        )

        self.logger.info(f"✅ Scene production completed: {final_clip_path}")

        return {
            "scene_id": scene_id,
            "clip_path": str(final_clip_path),
            "assets_created": len(shot_assets),
            "audio_path": str(audio_path) if audio_path else None,
            "audio_duration": audio_duration
        }

    def _generate_high_level_plan(
        self,
        scene: dict[str, Any],
        audio_duration: float,
        asr_path: str | None = None
    ) -> dict[str, Any]:
        """
        Generate high-level production plan using LLM.
        
        Args:
            scene: Scene data with shots from storyboard
            audio_duration: Actual duration of generated audio
            asr_path: Path to ASR data with word-level timestamps
            
        Returns:
            Production plan dictionary
        """
        self.logger.info("Generating high-level production plan")

        # Load ASR data if available
        asr_data = None
        if asr_path and Path(asr_path).exists():
            try:
                with open(asr_path, encoding="utf-8") as f:
                    asr_data = json.load(f)
                self.logger.info("  ✅ Loaded ASR data for time-aligned planning")
            except Exception as e:
                self.logger.warning(f"  ⚠️ Failed to load ASR data: {e}")

        # Get shots from storyboard
        storyboard_shots = scene.get('shots', [])

        # If storyboard has shots, use them directly (preferred!)
        if storyboard_shots:
            self.logger.info(f"  📋 Using {len(storyboard_shots)} shots from storyboard")
            plan_data = {
                "scene_id": scene.get("scene_id"),
                "plan_name": f"Production plan for {scene.get('scene_id')}",
                "total_duration": audio_duration,
                "shots": storyboard_shots,
                "composition_strategy": "Follow storyboard shot sequence",
                "audio_plan": {
                    "voice_over_path": str(asr_path) if asr_path else "",
                    "background_music": "",
                    "sound_effects": []
                }
            }
            # Save and return
            self._save_production_plan(plan_data, scene.get("scene_id", "scene_001"))
            return plan_data

        # Fallback: Build planning prompt for LLM (only if no storyboard shots)
        self.logger.warning("  ⚠️  No storyboard shots found, generating plan with LLM")
        planning_request = f"""Generate a production plan for this scene:

Scene ID: {scene.get('scene_id')}
Description: {scene.get('scene_description')}
Voice-over: {scene.get('voice_over_text')}
Audio Duration: {audio_duration:.2f} seconds (ACTUAL, must match exactly)

ASR Data: {json.dumps(asr_data, indent=2) if asr_data else "Not available"}

IMPORTANT: 
- Plan video timing based on the ACTUAL audio duration of {audio_duration:.2f}s.
- Create 1-3 shots that align with the voice-over.
- Each shot duration must sum to exactly {audio_duration:.2f}s total.
- Output ONLY valid JSON, no additional text.

Create a detailed plan following the JSON format in the system prompt."""

        try:
            response = self.llm_client.stream(
                prompt=planning_request,
                purpose="production_planning"
            )

            # Debug: log raw response
            self.logger.debug(f"Raw LLM response: {response[:500]}...")

            plan_data = self._parse_llm_response(response)

            # Debug: log parsed plan keys
            self.logger.debug(f"Parsed plan keys: {list(plan_data.keys())}")

            # Validate plan structure
            if not self._validate_plan_structure(plan_data):
                self.logger.warning(f"Generated plan has invalid structure: {plan_data.keys()}")
                self.logger.warning(f"Shots count: {len(plan_data.get('shots', []))}")
                plan_data = self._create_default_plan(scene)

            # Save plan to JSON file
            self._save_production_plan(plan_data, scene.get("scene_id", "scene_001"))

            return plan_data

        except Exception as e:
            self.logger.error(f"Plan generation failed: {e}")
            plan_data = self._create_default_plan(scene)
            self._save_production_plan(plan_data, scene.get("scene_id", "scene_001"))
            return plan_data

    def _create_default_plan(self, scene: dict[str, Any]) -> dict[str, Any]:
        """Create default production plan."""
        scene_id = scene.get("scene_id", "scene_001")
        duration = scene.get("total_duration", scene.get("duration", 8.0))

        return {
            "scene_id": scene_id,
            "plan_name": f"Production plan for {scene_id}",
            "total_duration": duration,
            "shots": [
                {
                    "shot_id": f"S{scene_id.split('_')[1]}_S1",
                    "shot_description": scene.get("scene_description", ""),
                    "visual_description": scene.get("scene_description", ""),
                    "duration": duration,
                    "voice_over_cue": scene.get("voice_over_text", ""),
                    "assets_required": [
                        {
                            "asset_type": "video",
                            "description": scene.get("scene_description", ""),
                            "generation_method": "text_to_video"
                        }
                    ]
                }
            ]
        }

    def _save_production_plan(self, plan_data: dict[str, Any], scene_id: str) -> Path:
        """
        Save production plan to JSON file.
        
        Args:
            plan_data: Production plan dictionary
            scene_id: Scene identifier
            
        Returns:
            Path to saved plan file
        """
        plan_path = self.workspace_dir / "plans" / f"{scene_id}_production_plan.json"
        plan_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(plan_path, "w", encoding="utf-8") as f:
                json.dump(plan_data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"  💾 Production plan saved: {plan_path}")
            return plan_path

        except Exception as e:
            self.logger.error(f"Failed to save production plan: {e}")
            return plan_path

    async def _create_video_asset(self, shot: dict[str, Any], scene_id: str) -> Path | None:
        """
        Create video asset for a shot using Veo.
        
        Args:
            shot: Shot data dictionary
            scene_id: Scene identifier
            
        Returns:
            Path to generated video or None if failed
        """
        shot_id = shot.get("shot_id", "S1_S1")

        self.logger.info(f"Creating video asset for shot: {shot_id}")

        # Build Veo prompt
        veo_prompt = self._build_veo_prompt(shot)

        # Generate video (no quality judgment loop)
        try:
            # Create output path
            asset_id = f"{shot_id}_V{self.asset_counter}"
            self.asset_counter += 1

            output_path = self.workspace_dir / "assets" / scene_id / f"{asset_id}.mp4"

            # Generate and download video
            video_path = await self.veo_client.generate_and_download(
                prompt=veo_prompt["veo_prompt"],
                output_path=output_path,
                negative_prompt=veo_prompt["negative_prompt"],
                duration=int(shot.get("duration", 8))
            )

            self.logger.info(f"✅ Video asset created: {video_path}")
            return video_path

        except Exception as e:
            self.logger.error(f"Failed to create video asset for {shot_id}: {e}")
            return None

    def _build_veo_prompt(self, shot: dict[str, Any]) -> dict[str, str]:
        """
        Build Veo generation prompt from shot data.
        
        Args:
            shot: Shot data with visual description and camera work
            
        Returns:
            Dictionary with 'veo_prompt' and 'negative_prompt'
        """
        # Extract visual description (try multiple field names)
        visual_desc = (
            shot.get("visual_description") or
            shot.get("description") or
            shot.get("shot_description") or
            ""
        )

        # Extract camera specifications (support both nested and flat structure)
        camera_work = shot.get("camera_work", {})
        
        # Try nested structure first, then flat structure
        camera_movement = (
            camera_work.get("movement") or
            shot.get("camera_movement") or
            "static"
        )
        camera_angle = (
            camera_work.get("angle") or
            shot.get("camera_angle") or
            "eye-level"
        )
        shot_type = (
            camera_work.get("shot_type") or
            shot.get("shot_type") or
            "medium"
        )

        # Build comprehensive prompt
        veo_prompt = f"{visual_desc}"
        
        # Add camera work
        if camera_movement or camera_angle or shot_type:
            veo_prompt += f", camera: {camera_movement} {camera_angle} {shot_type}"

        # Add lighting (check both nested and flat)
        lighting = shot.get("visuals", {}).get("lighting") or shot.get("lighting")
        if lighting:
            veo_prompt += f", lighting: {lighting}"

        # Add mood
        mood = shot.get("visuals", {}).get("mood") or shot.get("mood")
        if mood:
            veo_prompt += f", mood: {mood}"

        # Professional quality specifications
        veo_prompt += ", cinematic quality, professional production, smooth camera work"

        # Build negative prompt
        negative_prompt = (
            "blurry, low quality, amateur, shaky camera, poorly lit, pixelated, "
            "distorted, text overlay, subtitles, captions, watermarks, titles, labels"
        )

        self.logger.debug(f"Built Veo prompt: {veo_prompt[:200]}...")

        return {
            "veo_prompt": veo_prompt,
            "negative_prompt": negative_prompt
        }

    def _generate_voice_over(self, scene: dict[str, Any]) -> Path:
        """
        Generate voice-over audio for scene.
        
        Args:
            scene: Scene data with voice_over_text
            
        Returns:
            Path to generated audio file
        """
        scene_id = scene.get("scene_id", "scene_001")
        voice_text = scene.get("voice_over_text", "")

        if not voice_text:
            self.logger.warning(f"No voice-over text for scene {scene_id}")
            # Create empty placeholder
            audio_path = self.workspace_dir / "audio" / f"{scene_id}_voice.mp3"
            audio_path.parent.mkdir(parents=True, exist_ok=True)
            audio_path.touch()
            return audio_path

        self.logger.info(f"Generating voice-over for scene: {scene_id}")

        try:
            audio_path = self.workspace_dir / "audio" / f"{scene_id}_voice.mp3"

            # Generate voice-over
            self.voice_client.synthesize(
                text=voice_text,
                output_path=audio_path
            )

            self.logger.info(f"✅ Voice-over generated: {audio_path}")
            return audio_path

        except Exception as e:
            self.logger.error(f"Voice generation failed: {e}")
            # Create placeholder
            audio_path = self.workspace_dir / "audio" / f"{scene_id}_voice.mp3"
            audio_path.parent.mkdir(parents=True, exist_ok=True)
            audio_path.touch()
            return audio_path

    async def _compose_scene_clip(
        self,
        scene_id: str,
        shot_assets: list[tuple[dict[str, Any], Path]],
        voice_path: Path | None,
        voice_text: str = ""
    ) -> Path:
        """
        Compose final scene clip from assets.
        
        Args:
            scene_id: Scene identifier
            shot_assets: List of (shot_data, asset_path) tuples
            voice_path: Path to voice-over audio (can be None)
            voice_text: Voice-over text for subtitles
            
        Returns:
            Path to final composed clip
        """
        self.logger.info(f"Composing final clip for scene: {scene_id}")

        clip_path = self.workspace_dir / "clips" / f"{scene_id}_clip.mp4"
        clip_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            if not shot_assets:
                self.logger.error("No video assets to compose")
                # Create placeholder
                clip_path.touch()
                return clip_path

            # Step 1: Adjust each video to its target duration
            adjusted_videos = []
            adjusted_dir = self.workspace_dir / "temp" / "adjusted"
            adjusted_dir.mkdir(parents=True, exist_ok=True)

            for idx, (shot, asset_path) in enumerate(shot_assets):
                target_duration = shot.get("duration", 8.0)
                shot_id = shot.get("shot_id", f"shot_{idx}")

                # Create adjusted video path
                adjusted_path = adjusted_dir / f"{scene_id}_{shot_id}_adjusted.mp4"

                self.logger.info(
                    f"  🎞️ Adjusting {shot_id} to target duration: {target_duration:.2f}s"
                )

                # Adjust video duration to match storyboard plan
                await VideoProcessor.adjust_video_duration(
                    input_path=asset_path,
                    target_duration=target_duration,
                    output_path=adjusted_path
                )

                adjusted_videos.append(adjusted_path)

            # Step 2: Concatenate adjusted videos if multiple
            if len(adjusted_videos) > 1:
                concatenated_path = self.workspace_dir / "temp" / f"{scene_id}_concat.mp4"
                await VideoProcessor.concat_videos(adjusted_videos, concatenated_path)
                base_video = concatenated_path
            else:
                base_video = adjusted_videos[0]

            # Step 3: Add audio if voice file exists and is not empty
            if voice_path and voice_path.exists() and voice_path.stat().st_size > 0:
                self.logger.info("  🎵 Merging audio with adjusted video")
                # Merge video with audio and optional subtitles
                await VideoProcessor.merge_video_audio(
                    video_path=base_video,
                    audio_path=voice_path,
                    text=voice_text if voice_text else None,
                    output_path=clip_path
                )
            else:
                # Just copy/move the video
                import shutil
                shutil.copy2(base_video, clip_path)

            self.logger.info(f"✅ Final clip composed: {clip_path}")
            return clip_path

        except Exception as e:
            self.logger.error(f"Clip composition failed: {e}")
            # Create placeholder on error
            clip_path.touch()
            return clip_path

    def _parse_llm_response(self, response: str) -> dict[str, Any]:
        """Parse LLM JSON response."""
        response = response.strip()

        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]

        response = response.strip()

        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse LLM JSON: {e}")
            raise

    def _validate_plan_structure(self, plan: dict[str, Any]) -> bool:
        """Validate production plan structure."""
        required_fields = ["scene_id", "shots"]

        for field in required_fields:
            if field not in plan:
                return False

        if not isinstance(plan["shots"], list) or len(plan["shots"]) == 0:
            return False

        return True

    def _generate_high_level_plan_tool(self, scene_data: dict[str, Any]) -> dict[str, Any]:
        """Generate high-level plan (tool function)."""
        plan = self._generate_high_level_plan(scene_data)
        return {"status": "success", "plan": plan}

    def _create_video_asset_tool(self, shot: dict[str, Any], scene_id: str) -> dict[str, Any]:
        """Create video asset (tool function)."""
        asset_path = self._create_video_asset(shot, scene_id)

        if asset_path:
            return {"status": "success", "asset_path": str(asset_path)}
        else:
            return {"status": "failed", "error": "Asset creation failed"}

