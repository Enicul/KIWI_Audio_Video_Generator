"""
Prompt Agent - Generates optimized video prompts
Converts intent into detailed prompts for video generation
"""
from typing import Any, Dict

from .base import BaseAgent


class PromptAgent(BaseAgent):
    """
    Agent responsible for generating video prompts.
    Creates optimized prompts for Veo 3 based on user intent.
    """
    
    def __init__(self):
        super().__init__(
            name="PromptAgent",
            description="Generates optimized prompts for video generation"
        )
        self.client = None
        self._initialized = False
    
    def initialize(self, client):
        """Initialize with Gemini client"""
        self.client = client
        self._initialized = True
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process intent and generate video prompt.
        
        Input:
            intent: dict with topic, style, mood, etc.
            visual_style: dict with consistency info (for multi-scene)
            scene_number: int (current scene number)
            total_scenes: int (total number of scenes)
            
        Output:
            success: bool
            prompt: str (optimized video prompt)
            error: str (if failed)
        """
        intent = input_data.get("intent")
        visual_style = input_data.get("visual_style", {})
        scene_number = input_data.get("scene_number", 1)
        total_scenes = input_data.get("total_scenes", 1)
        
        if not intent:
            return {"success": False, "error": "No intent provided"}
        
        if not self._initialized or not self.client:
            return self._fallback_prompt(intent, visual_style)
        
        try:
            await self.update_progress(45, "Creating video prompt...")
            
            original_input = intent.get('original_input', '')
            
            # Build visual consistency section for multi-scene
            visual_consistency_section = ""
            if visual_style and total_scenes > 1:
                visual_consistency_section = f"""
VISUAL CONSISTENCY REQUIREMENTS (CRITICAL for multi-scene story):
This is Scene {scene_number} of {total_scenes}. ALL scenes must have consistent visuals.

- Main Character: {visual_style.get('main_character', 'Not specified')}
- Color Palette: {visual_style.get('color_palette', 'Cinematic natural colors')}
- Camera Style: {visual_style.get('camera_style', 'Steady cinematic shots')}
- Lighting: {visual_style.get('lighting', 'Natural lighting')}
- Visual Tone: {visual_style.get('visual_tone', 'Realistic and grounded')}

You MUST incorporate these visual elements into the prompt to ensure consistency across all scenes.
The character description is especially important - use the EXACT same character appearance."""
            
            prompt = f"""You are a video prompt generator for AI video generation (Veo 3).

TASK: Convert the scene description into a detailed video prompt.
{visual_consistency_section}

CRITICAL RULES:
1. Stay faithful to the scene description
2. Include specific visual details (camera angle, movement, lighting)
3. If this is part of a multi-scene story, ALWAYS include the character description
4. Keep the prompt 2-4 sentences long
5. Focus on visual elements that can be generated

Scene to generate: "{original_input}"

Additional context:
- Style: {intent.get('style', 'cinematic')}
- Mood: {intent.get('mood', 'neutral')}
- Key elements: {', '.join(intent.get('key_elements', []))}

Generate the video prompt now. Return ONLY the prompt text, no explanation."""

            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            
            if not response or not response.text:
                return self._fallback_prompt(intent, visual_style)
            
            video_prompt = response.text.strip()
            
            await self.send_message(f"Scene {scene_number} prompt ready")
            
            return {
                "success": True,
                "prompt": video_prompt
            }
            
        except Exception as e:
            return self._fallback_prompt(intent, visual_style)
    
    def _fallback_prompt(self, intent: Dict[str, Any], visual_style: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a simple video prompt without API"""
        topic = intent.get("topic", "beautiful scene")
        style = intent.get("style", "cinematic")
        mood = intent.get("mood", "engaging")
        
        # Add visual consistency elements if available
        character_desc = ""
        if visual_style and visual_style.get("main_character"):
            character_desc = f", featuring {visual_style.get('main_character')}"
        
        color_style = ""
        if visual_style and visual_style.get("color_palette"):
            color_style = f", {visual_style.get('color_palette')}"
        
        prompt = f"A {style} video showing {topic}{character_desc}, {mood} atmosphere{color_style}, high quality, smooth camera movement"
        
        return {
            "success": True,
            "prompt": prompt
        }


# Singleton instance
prompt_agent = PromptAgent()


