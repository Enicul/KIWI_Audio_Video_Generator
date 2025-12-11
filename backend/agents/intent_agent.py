"""
Intent Agent - Understands user's video creation intent
Analyzes text input to extract video requirements
"""
from typing import Any, Dict
import json

from .base import BaseAgent


class IntentAgent(BaseAgent):
    """
    Agent responsible for understanding user's intent.
    Analyzes the transcription to extract video requirements.
    """
    
    def __init__(self):
        super().__init__(
            name="IntentAgent",
            description="Analyzes user input to understand video requirements"
        )
        self.client = None
        self._initialized = False
    
    def initialize(self, client):
        """Initialize with Gemini client"""
        self.client = client
        self._initialized = True
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process text input and extract intent.
        
        Input:
            text: User's transcribed or typed input
            
        Output:
            success: bool
            intent: dict with topic, style, mood, etc.
            error: str (if failed)
        """
        text = input_data.get("text")
        
        if not text:
            return {"success": False, "error": "No text input provided"}
        
        if not self._initialized or not self.client:
            return self._fallback_intent(text)
        
        try:
            await self.update_progress(25, "Analyzing your request...")
            
            prompt = f"""Analyze this video creation request and extract the key elements.
            
User request: "{text}"

Return a JSON object with these fields:
- topic: main subject of the video (required)
- video_type: type (explainer, story, advertisement, tutorial, etc.)
- style: visual style (cinematic, animated, documentary, etc.)
- mood: emotional tone (exciting, calm, dramatic, etc.)
- duration: suggested duration in seconds (default 8)
- key_elements: list of important visual elements to include

Return ONLY valid JSON, no markdown formatting."""

            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            
            if not response or not response.text:
                return self._fallback_intent(text)
            
            # Parse JSON response
            response_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                parts = response_text.split("```")
                if len(parts) >= 2:
                    response_text = parts[1]
            
            response_text = response_text.strip()
            
            intent = json.loads(response_text)
            intent["original_input"] = text
            
            # Ensure required fields exist
            intent.setdefault("topic", text[:100])
            intent.setdefault("video_type", "short video")
            intent.setdefault("style", "cinematic")
            intent.setdefault("mood", "engaging")
            intent.setdefault("duration", 8)
            intent.setdefault("key_elements", [])
            
            await self.send_message(f"Understood: {intent['video_type']} about {intent['topic'][:30]}")
            
            return {
                "success": True,
                "intent": intent
            }
            
        except Exception as e:
            return self._fallback_intent(text)
    
    def _fallback_intent(self, text: str) -> Dict[str, Any]:
        """Fallback intent extraction without API"""
        return {
            "success": True,
            "intent": {
                "topic": text[:100],
                "video_type": "short video",
                "style": "cinematic",
                "mood": "engaging",
                "duration": 8,
                "key_elements": [],
                "original_input": text
            }
        }


# Singleton instance
intent_agent = IntentAgent()

