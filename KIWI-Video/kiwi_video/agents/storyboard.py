"""Storyboard agent for visual scene planning."""

import json
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

from kiwi_video.core.base_agent import BaseAgent
from kiwi_video.core.state_manager import StateManager
from kiwi_video.providers.llm.base import BaseLLMClient
from kiwi_video.utils.prompt_loader import load_prompt


class StoryboardAgent(BaseAgent):
    """
    Agent responsible for creating visual storyboards.
    
    Converts script scenes into detailed shot-by-shot storyboards with
    camera work, composition, and visual specifications.
    """

    def __init__(
        self,
        agent_name: str,
        llm_client: BaseLLMClient,
        state_manager: StateManager,
        workspace_dir: Path
    ) -> None:
        """Initialize Storyboard agent."""
        super().__init__(agent_name, llm_client, state_manager, workspace_dir)

        # Load system prompt
        try:
            self._system_prompt = load_prompt("storyboard")
        except Exception:
            self._system_prompt = self._get_fallback_prompt()

    def register_tools(self) -> dict[str, Callable]:
        """Register agent tools."""
        return {
            "plan_shots": self._plan_shots_for_scene,
            "validate_storyboard": self._validate_storyboard
        }

    def get_system_prompt(self) -> str:
        """Get system prompt."""
        return self._system_prompt

    def _get_fallback_prompt(self) -> str:
        """Fallback prompt if template not found."""
        return """You are a professional storyboard artist.
Create detailed shot-by-shot breakdowns with camera work and visual specifications.
Output valid JSON format with shots array for each scene."""

    def _execute_workflow(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Execute storyboard creation workflow.
        
        Args:
            input_data: Must contain 'script' with scenes data, optionally 'audio_metadata'
            
        Returns:
            Dictionary with storyboard_path and scenes data
        """
        script_data = input_data.get("script", {})
        scenes = script_data.get("scenes", [])
        audio_metadata = input_data.get("audio_metadata", {})

        if not scenes:
            raise ValueError("Script must contain scenes")

        self.logger.info(f"Creating storyboard for {len(scenes)} scenes")

        if audio_metadata:
            self.logger.info("✅ Using actual audio durations for precise shot planning")
        else:
            self.logger.warning("⚠️  No audio metadata provided, using estimated durations")

        # Process each scene to add shot breakdowns
        storyboard_scenes = []

        for scene in scenes:
            scene_id = scene.get('scene_id')
            self.logger.info(f"Processing scene: {scene_id}")

            # Replace estimated duration with actual audio duration if available
            if scene_id in audio_metadata:
                actual_duration = audio_metadata[scene_id].get("duration")
                if actual_duration:
                    estimated_duration = scene.get("duration", 0)
                    scene = {**scene, "duration": actual_duration}
                    self.logger.info(
                        f"  ⏱️  Using actual audio duration: {actual_duration:.2f}s "
                        f"(estimated: {estimated_duration}s)"
                    )

            # Plan shots for this scene
            scene_with_shots = self._create_shot_breakdown(scene)
            storyboard_scenes.append(scene_with_shots)

        # Create complete storyboard
        storyboard_data = {
            "storyboard_id": f"storyboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "created_at": datetime.now().isoformat(),
            "scenes": storyboard_scenes
        }

        # Save storyboard
        storyboard_path = self._save_storyboard(storyboard_data)

        # Create summary
        summary_path = self._create_summary(storyboard_data)

        self.logger.info(f"Storyboard created with {len(storyboard_scenes)} scenes")

        return {
            "storyboard_path": str(storyboard_path),
            "summary_path": str(summary_path),
            "scenes_count": len(storyboard_scenes),
            "total_shots": sum(len(s.get("shots", [])) for s in storyboard_scenes),
            "scenes": storyboard_scenes  # 关键：返回 scenes 数据给 FilmCrew
        }

    def _create_shot_breakdown(self, scene: dict[str, Any]) -> dict[str, Any]:
        """
        Create shot breakdown for a scene.
        
        Args:
            scene: Scene data dictionary
            
        Returns:
            Scene with shots added
        """
        scene_duration = scene.get("duration", 8.0)
        voice_over = scene.get("voice_over_text", "")

        # Use LLM to plan shots
        shots = self._plan_shots_with_llm(scene)

        # If LLM fails, create basic shot
        if not shots:
            shots = self._create_default_shots(scene)

        # Normalize shot IDs to ensure consistent format
        shots = self._normalize_shot_ids(shots, scene.get("scene_id", "scene_001"))

        # Add shots to scene
        scene_with_shots = {**scene}
        scene_with_shots["shots"] = shots
        scene_with_shots["total_duration"] = scene_duration

        return scene_with_shots

    def _plan_shots_with_llm(self, scene: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Use LLM to plan shots for a scene.
        
        Args:
            scene: Scene data with actual audio duration
            
        Returns:
            List of shot dictionaries
        """
        scene_duration = scene.get('duration', 8)
        planning_prompt = f"""Plan detailed shots for this scene:

Scene ID: {scene.get('scene_id')}
Description: {scene.get('scene_description')}
Voice-over: {scene.get('voice_over_text')}
Duration: {scene_duration} seconds (actual audio duration)

IMPORTANT: The total duration of all shots MUST equal {scene_duration} seconds exactly.
This is the actual recorded voice-over duration, so shots must be precisely timed.

Create 1-3 shots that effectively tell this scene's story.
Output valid JSON array of shots following the structure in the system prompt."""

        try:
            response = self.llm_client.stream(
                prompt=planning_prompt,
                purpose="shot_planning"
            )

            # Parse response
            shots_data = self._parse_llm_response(response)

            # Extract shots array
            if isinstance(shots_data, dict) and "shots" in shots_data:
                return shots_data["shots"]
            elif isinstance(shots_data, list):
                return shots_data
            else:
                self.logger.warning("Unexpected LLM response format")
                return []

        except Exception as e:
            self.logger.error(f"LLM shot planning failed: {e}")
            return []

    def _normalize_shot_ids(self, shots: list[dict[str, Any]], scene_id: str) -> list[dict[str, Any]]:
        """
        Normalize shot IDs to consistent format: scene_XXX_shot_YYY
        
        Args:
            shots: List of shot dictionaries
            scene_id: Scene identifier (e.g., 'scene_001')
            
        Returns:
            List of shots with normalized IDs
        """
        normalized_shots = []

        for idx, shot in enumerate(shots, start=1):
            normalized_shot = {**shot}

            # Get current shot_id
            current_id = shot.get("shot_id", "")

            # Generate standard format: scene_XXX_shot_YYY
            standard_id = f"{scene_id}_shot_{idx:03d}"

            # Check if current ID doesn't match standard format
            if current_id != standard_id:
                self.logger.debug(f"Normalizing shot_id: '{current_id}' -> '{standard_id}'")
                normalized_shot["shot_id"] = standard_id

            normalized_shots.append(normalized_shot)

        return normalized_shots

    def _create_default_shots(self, scene: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Create default shot when LLM planning fails.
        
        Args:
            scene: Scene data
            
        Returns:
            List with single default shot
        """
        scene_id = scene.get("scene_id", "scene_001")
        return [
            {
                "shot_id": f"{scene_id}_shot_001",
                "shot_description": scene.get("scene_description", ""),
                "visual_description": scene.get("scene_description", ""),
                "voice_over_cue": scene.get("voice_over_text", ""),
                "visuals": {
                    "composition": {
                        "shot_type": "medium",
                        "camera_angle": "eye-level",
                        "camera_movement": "static"
                    },
                    "lighting": "natural",
                    "mood": scene.get("mood", "neutral"),
                    "color_palette": "balanced"
                },
                "duration": scene.get("duration", 8.0),
                "timing": {
                    "start_time": 0,
                    "end_time": scene.get("duration", 8.0)
                }
            }
        ]

    def _parse_llm_response(self, response: str) -> Any:
        """Parse LLM JSON response."""
        response = response.strip()

        # Remove markdown code blocks
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

    def _save_storyboard(self, storyboard_data: dict[str, Any]) -> Path:
        """
        Save storyboard data to JSON file.
        
        Args:
            storyboard_data: Complete storyboard data
            
        Returns:
            Path to saved storyboard file
        """
        storyboard_path = self.workspace_dir / "storyboard.json"

        try:
            with open(storyboard_path, "w", encoding="utf-8") as f:
                json.dump(storyboard_data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Storyboard saved to: {storyboard_path}")
            return storyboard_path

        except Exception as e:
            self.logger.error(f"Failed to save storyboard: {e}")
            raise

    def _create_summary(self, storyboard_data: dict[str, Any]) -> Path:
        """
        Create storyboard summary markdown file.
        
        Args:
            storyboard_data: Storyboard data
            
        Returns:
            Path to summary file
        """
        summary_path = self.workspace_dir / "storyboard_summary.md"

        content = f"""# Storyboard Summary

Generated: {datetime.now().isoformat()}

## Overview
- Storyboard ID: {storyboard_data.get('storyboard_id')}
- Total Scenes: {len(storyboard_data.get('scenes', []))}
- Total Shots: {sum(len(s.get('shots', [])) for s in storyboard_data.get('scenes', []))}

## Scenes

"""

        for scene in storyboard_data.get("scenes", []):
            content += f"""### {scene.get('scene_id')}
- Description: {scene.get('scene_description')}
- Voice-over: {scene.get('voice_over_text')}
- Duration: {scene.get('total_duration', 0)}s
- Shots: {len(scene.get('shots', []))}

"""

        content += """## Files
- Storyboard JSON: `storyboard.json`
"""

        try:
            with open(summary_path, "w", encoding="utf-8") as f:
                f.write(content)

            self.logger.info(f"Summary saved to: {summary_path}")
            return summary_path

        except Exception as e:
            self.logger.error(f"Failed to create summary: {e}")
            raise

    def _plan_shots_for_scene(self, scene_id: str) -> dict[str, Any]:
        """Plan shots for a scene (tool function)."""
        # This would be called by the LLM during agent loop
        # For now, return success
        return {"status": "success", "scene_id": scene_id}

    def _validate_storyboard(self, storyboard_path: str) -> dict[str, Any]:
        """Validate storyboard structure (tool function)."""
        file_path = self.workspace_dir / storyboard_path

        if not file_path.exists():
            return {"valid": False, "error": "Storyboard file not found"}

        try:
            with open(file_path, encoding="utf-8") as f:
                storyboard_data = json.load(f)

            # Basic validation
            if "scenes" not in storyboard_data:
                return {"valid": False, "error": "Missing scenes array"}

            return {"valid": True, "scenes_count": len(storyboard_data["scenes"])}

        except Exception as e:
            return {"valid": False, "error": str(e)}

