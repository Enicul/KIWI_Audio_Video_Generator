"""
Prompt Agent - Generates optimized video prompts
Converts intent into detailed prompts for video generation
"""
from typing import Any, Dict

from .base import BaseAgent


class PromptAgent(BaseAgent):
    """
    Agent responsible for generating video prompts.
    Creates optimized prompts for Veo based on user intent.
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
            
        Output:
            success: bool
            prompt: str (optimized video prompt)
            error: str (if failed)
        """
        intent = input_data.get("intent")
        
        if not intent:
            return {"success": False, "error": "No intent provided"}
        
        if not self._initialized or not self.client:
            return self._fallback_prompt(intent)
        
        try:
            await self.update_progress(45, "Creating video prompt...")
            
            original_input = intent.get('original_input', '')
            
            prompt = f"""You are a video prompt generator. Your task is to convert the user's request into a clear video description for AI video generation.

CRITICAL RULES:
1. You MUST stay faithful to what the user actually requested
2. Do NOT add unrelated content or change the subject
3. If the user's request is vague, describe a simple scene based on the topic
4. Add visual details (camera angle, lighting) but keep the SUBJECT the same

User's original request: "{original_input}"

Extracted intent:
- Topic: {intent.get('topic', 'general')}
- Type: {intent.get('video_type', 'short video')}
- Style: {intent.get('style', 'cinematic')}
- Mood: {intent.get('mood', 'neutral')}
- Key elements: {', '.join(intent.get('key_elements', []))}

Generate a video prompt that:
1. Matches the user's request exactly
2. Adds appropriate visual details
3. Is 1-3 sentences long
4. Does NOT invent new subjects

Return ONLY the prompt text."""

            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            
            if not response or not response.text:
                return self._fallback_prompt(intent)
            
            video_prompt = response.text.strip()
            
            await self.send_message(f"Prompt ready: {video_prompt[:50]}...")
            
            return {
                "success": True,
                "prompt": video_prompt
            }
            
        except Exception as e:
            return self._fallback_prompt(intent)
    
    def _fallback_prompt(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        """Create a simple video prompt without API"""
        topic = intent.get("topic", "beautiful scene")
        style = intent.get("style", "cinematic")
        mood = intent.get("mood", "engaging")
        
        prompt = f"A {style} video showing {topic}, {mood} atmosphere, high quality, smooth camera movement"
        
        return {
            "success": True,
            "prompt": prompt
        }


# Singleton instance
prompt_agent = PromptAgent()

