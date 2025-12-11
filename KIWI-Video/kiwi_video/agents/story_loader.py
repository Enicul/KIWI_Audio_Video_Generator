"""StoryLoader agent for script generation."""

import json
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

from kiwi_video.core.base_agent import BaseAgent
from kiwi_video.core.state_manager import StateManager
from kiwi_video.providers.llm.base import BaseLLMClient
from kiwi_video.utils.prompt_loader import load_prompt


class StoryLoaderAgent(BaseAgent):
    """
    Agent responsible for generating video scripts from user input.
    
    Converts user prompts into structured scripts with scenes and narration.
    Simplified version: text input → structured scenes (no multi-source input).
    """

    def __init__(
        self,
        agent_name: str,
        llm_client: BaseLLMClient,
        state_manager: StateManager,
        workspace_dir: Path
    ) -> None:
        """Initialize StoryLoader agent."""
        super().__init__(agent_name, llm_client, state_manager, workspace_dir)

        # Load system prompt from template
        try:
            self._system_prompt = load_prompt("story_loader")
        except Exception:
            # Fallback to hardcoded prompt
            self._system_prompt = self._get_fallback_prompt()

    def register_tools(self) -> dict[str, Callable]:
        """Register agent tools."""
        return {
            "write_script": self._write_script,
            "validate_script": self._validate_script
        }

    def get_system_prompt(self) -> str:
        """Get system prompt."""
        return self._system_prompt

    def _get_fallback_prompt(self) -> str:
        """Fallback prompt if template file not found."""
        return """You are a professional video scriptwriter.
Convert user input into structured video scripts with clear scenes and narration.
Output valid JSON format with scenes array."""

    def _execute_workflow(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Execute StoryLoader workflow.
        
        Args:
            input_data: Must contain 'topic' and optional 'style'
            
        Returns:
            Dictionary with script_path, style_guide_path, scenes data
        """
        topic = input_data.get("topic", "")
        style = input_data.get("style", "professional")

        if not topic:
            raise ValueError("Topic is required for script generation")

        self.logger.info(f"Generating script for: {topic} (style: {style})")

        # Generate script using LLM
        script_data = self._generate_script_with_llm(topic, style)

        # Save script files
        script_path = self._save_script(script_data)
        style_guide_path = self._save_style_guide(topic, style)

        self.logger.info(f"Script generated with {len(script_data['scenes'])} scenes")

        return {
            "script_path": str(script_path),
            "style_guide_path": str(style_guide_path),
            "scenes_count": len(script_data["scenes"]),
            "scenes": script_data["scenes"],
            "total_duration": script_data.get("total_duration", 0)
        }

    def _generate_script_with_llm(self, topic: str, style: str) -> dict[str, Any]:
        """
        Generate structured script using LLM.
        
        Args:
            topic: User's video topic
            style: Video style (professional, casual, cinematic, etc.)
            
        Returns:
            Dictionary with structured script data
        """
        # Build generation prompt with explicit format requirements
        generation_prompt = f"""Generate a video script for the following topic:

Topic: {topic}
Style: {style}

Create 1-2 scenes that tell a compelling story.
Output ONLY valid JSON with this EXACT structure (no extra text):

{{
  "topic": "{topic}",
  "style": "{style}",
  "total_duration": <number between 30-90>,
  "scenes": [
    {{
      "scene_id": "scene_001",
      "scene_description": "<visual description>",
      "voice_over_text": "<narration text>",
      "duration": <seconds>,
      "mood": "<mood description>",
      "visual_style": "{style}"
    }}
  ]
}}

IMPORTANT: Return ONLY the JSON object, no markdown formatting, no explanation."""

        try:
            # Call LLM
            response = self.llm_client.stream(
                prompt=generation_prompt,
                purpose="script_generation"
            )

            # Debug: log raw response
            self.logger.debug(f"Raw LLM response: {response[:500]}...")

            # Parse JSON response
            script_data = self._parse_llm_response(response)

            # Debug: log parsed data structure
            self.logger.debug(f"Parsed data keys: {list(script_data.keys())}")

            # Auto-fill topic and style if missing (LLM might only return scenes)
            if "topic" not in script_data:
                script_data["topic"] = topic
            if "style" not in script_data:
                script_data["style"] = style

            # Validate structure
            if not self._validate_script_structure(script_data):
                self.logger.warning(f"Invalid structure. Data: {script_data}")
                raise ValueError("Generated script has invalid structure")

            return script_data

        except Exception as e:
            self.logger.error(f"LLM script generation failed: {e}")
            # Return fallback script
            return self._create_fallback_script(topic, style)

    def _parse_llm_response(self, response: str) -> dict[str, Any]:
        """
        Parse LLM JSON response.
        
        Args:
            response: Raw LLM output
            
        Returns:
            Parsed JSON dictionary
        """
        # Clean up response
        response = response.strip()

        # Remove markdown code blocks if present
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]

        response = response.strip()

        # Parse JSON
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse LLM JSON: {e}")
            raise

    def _validate_script_structure(self, script_data: dict[str, Any]) -> bool:
        """
        Validate script has required structure.
        
        Args:
            script_data: Script dictionary
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = ["topic", "style", "scenes"]

        for field in required_fields:
            if field not in script_data:
                self.logger.error(f"Missing required field: {field}")
                return False

        if not isinstance(script_data["scenes"], list) or len(script_data["scenes"]) == 0:
            self.logger.error("Scenes must be a non-empty list")
            return False

        # Validate each scene
        for i, scene in enumerate(script_data["scenes"]):
            required_scene_fields = ["scene_id", "scene_description", "voice_over_text"]

            for field in required_scene_fields:
                if field not in scene:
                    self.logger.error(f"Scene {i} missing field: {field}")
                    return False

        return True

    def _create_fallback_script(self, topic: str, style: str) -> dict[str, Any]:
        """
        Create a fallback script when LLM generation fails.
        
        Args:
            topic: Video topic
            style: Video style
            
        Returns:
            Basic script structure
        """
        self.logger.warning("Using fallback script generation")

        return {
            "topic": topic,
            "style": style,
            "total_duration": 24,
            "scenes": [
                {
                    "scene_id": "scene_001",
                    "scene_description": f"Opening scene introducing {topic}",
                    "voice_over_text": f"Welcome to our exploration of {topic}",
                    "duration": 8.0,
                    "mood": "engaging",
                    "visual_style": style
                },
                {
                    "scene_id": "scene_002",
                    "scene_description": f"Main content about {topic}",
                    "voice_over_text": f"Let's dive deeper into {topic} and understand its importance",
                    "duration": 10.0,
                    "mood": "informative",
                    "visual_style": style
                },
                {
                    "scene_id": "scene_003",
                    "scene_description": f"Closing scene summarizing {topic}",
                    "voice_over_text": f"This is just the beginning of understanding {topic}",
                    "duration": 6.0,
                    "mood": "inspiring",
                    "visual_style": style
                }
            ]
        }

    def _save_script(self, script_data: dict[str, Any]) -> Path:
        """
        Save script data to JSON file.
        
        Args:
            script_data: Script dictionary
            
        Returns:
            Path to saved script file
        """
        script_path = self.workspace_dir / "annotated_script.json"

        try:
            with open(script_path, "w", encoding="utf-8") as f:
                json.dump(script_data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Script saved to: {script_path}")
            return script_path

        except Exception as e:
            self.logger.error(f"Failed to save script: {e}")
            raise

    def _save_style_guide(self, topic: str, style: str) -> Path:
        """
        Save style guide file.
        
        Args:
            topic: Video topic
            style: Video style
            
        Returns:
            Path to saved style guide
        """
        style_guide_path = self.workspace_dir / "style_guide.txt"

        content = f"""# Style Guide

## Topic
{topic}

## Visual Style
{style}

## Production Guidelines
- Maintain consistent {style} tone throughout
- Use clear, engaging visuals
- Ensure smooth transitions between scenes
- Focus on professional quality

## Generated
{datetime.now().isoformat()}
"""

        try:
            with open(style_guide_path, "w", encoding="utf-8") as f:
                f.write(content)

            self.logger.info(f"Style guide saved to: {style_guide_path}")
            return style_guide_path

        except Exception as e:
            self.logger.error(f"Failed to save style guide: {e}")
            raise

    def _write_script(self, content: str, path: str) -> dict[str, Any]:
        """Write script to file (tool function)."""
        file_path = self.workspace_dir / path
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return {"status": "success", "path": str(file_path)}

    def _validate_script(self, script_path: str) -> dict[str, Any]:
        """Validate script structure (tool function)."""
        file_path = self.workspace_dir / script_path

        if not file_path.exists():
            return {"valid": False, "error": "Script file not found"}

        try:
            with open(file_path, encoding="utf-8") as f:
                script_data = json.load(f)

            is_valid = self._validate_script_structure(script_data)

            return {"valid": is_valid}

        except Exception as e:
            return {"valid": False, "error": str(e)}

