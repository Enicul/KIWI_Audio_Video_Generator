"""
Script Analyzer Agent - Analyzes user input and segments into scenes
Detects if input describes a multi-scene story or single scene
"""
from typing import Any, Dict, List
import json

from .base import BaseAgent


class ScriptAnalyzerAgent(BaseAgent):
    """
    Agent responsible for analyzing user input and segmenting into scenes.
    Detects narrative structure and splits into logical video segments.
    """
    
    def __init__(self):
        super().__init__(
            name="ScriptAnalyzerAgent",
            description="Analyzes scripts and segments into scenes"
        )
        self.client = None
        self._initialized = False
    
    def initialize(self, client):
        """Initialize with Gemini client"""
        self.client = client
        self._initialized = True
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze user input and determine if it should be split into scenes.
        
        Input:
            text: User's video description
            intent: Parsed intent (optional)
            
        Output:
            success: bool
            is_multi_scene: bool
            scenes: List[Dict] with scene details
            total_scenes: int
        """
        text = input_data.get("text", "")
        intent = input_data.get("intent", {})
        
        if not text and not intent:
            return {"success": False, "error": "No input provided"}
        
        # Use original input if available
        description = intent.get("original_input", text) or text
        
        if not self._initialized or not self.client:
            return self._fallback_analysis(description)
        
        try:
            await self.update_progress(5, "Analyzing script structure...")
            
            prompt = f"""Analyze this video request and determine if it describes multiple scenes or a single scene.

User request: "{description}"

Rules for scene detection:
1. Multiple scenes = story with distinct time/location changes (e.g., "wake up, then go to work, then meet friends")
2. Single scene = one continuous moment or action (e.g., "a cat playing with yarn")
3. Maximum 5 scenes for practical video generation
4. Each scene should be 5-8 seconds when generated

If multi-scene, break it down into logical segments.

Return JSON:
{{
    "is_multi_scene": true/false,
    "reasoning": "why you made this decision",
    "scenes": [
        {{
            "scene_number": 1,
            "title": "Short title",
            "description": "Detailed visual description for video generation",
            "duration_seconds": 8,
            "transition_hint": "cut/fade/none"
        }}
    ],
    "total_estimated_duration": number
}}

For single scene, return just one scene in the array.
Return ONLY valid JSON."""

            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            
            if not response or not response.text:
                return self._fallback_analysis(description)
            
            # Parse response
            response_text = response.text.strip()
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]
            
            result = json.loads(response_text.strip())
            
            scenes = result.get("scenes", [])
            is_multi_scene = result.get("is_multi_scene", False) and len(scenes) > 1
            
            # Limit to 5 scenes max
            if len(scenes) > 5:
                scenes = scenes[:5]
            
            await self.send_message(
                f"Detected {'multi-scene story' if is_multi_scene else 'single scene'}: {len(scenes)} scene(s)"
            )
            
            return {
                "success": True,
                "is_multi_scene": is_multi_scene,
                "scenes": scenes,
                "total_scenes": len(scenes),
                "reasoning": result.get("reasoning", ""),
                "total_estimated_duration": result.get("total_estimated_duration", len(scenes) * 8)
            }
            
        except Exception as e:
            print(f"Script analysis failed: {e}")
            return self._fallback_analysis(description)
    
    def _fallback_analysis(self, text: str) -> Dict[str, Any]:
        """Simple fallback - treat as single scene"""
        return {
            "success": True,
            "is_multi_scene": False,
            "scenes": [{
                "scene_number": 1,
                "title": "Main Scene",
                "description": text[:500],
                "duration_seconds": 8,
                "transition_hint": "none"
            }],
            "total_scenes": 1,
            "reasoning": "Fallback mode - treating as single scene",
            "total_estimated_duration": 8
        }


# Singleton instance
script_analyzer_agent = ScriptAnalyzerAgent()

