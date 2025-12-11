"""
Speech Agent - Handles audio transcription
Converts voice input to text using Gemini
"""
from typing import Any, Dict
import base64
import os

from .base import BaseAgent


class SpeechAgent(BaseAgent):
    """
    Agent responsible for transcribing audio to text.
    Uses Gemini's multimodal capabilities for transcription.
    """
    
    def __init__(self):
        super().__init__(
            name="SpeechAgent",
            description="Transcribes audio input to text"
        )
        self.client = None
        self._initialized = False
    
    def initialize(self, client):
        """Initialize with Gemini client"""
        self.client = client
        self._initialized = True
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process audio data and return transcription.
        
        Input:
            audio_data: Base64 encoded audio data
            
        Output:
            success: bool
            transcription: str (if successful)
            error: str (if failed)
        """
        audio_data = input_data.get("audio_data")
        
        if not audio_data:
            return {"success": False, "error": "No audio data provided"}
        
        if not self._initialized or not self.client:
            return {"success": False, "error": "SpeechAgent not initialized"}
        
        try:
            from google.genai import types
            
            await self.update_progress(10, "Processing audio...")
            
            # Extract base64 data
            base64_data = audio_data
            mime_type = "audio/webm"
            
            if "," in audio_data:
                header, base64_data = audio_data.split(",", 1)
                if "audio/" in header:
                    mime_type = header.split(":")[1].split(";")[0]
            
            # Create inline data part
            audio_part = types.Part.from_bytes(
                data=base64.b64decode(base64_data),
                mime_type=mime_type
            )
            
            await self.update_progress(15, "Transcribing with AI...")
            
            # Use Gemini to transcribe
            prompt = """Listen to this audio and transcribe exactly what the person is saying.
If they are describing a video they want to create, capture all the details.
Return ONLY the transcription, no additional commentary."""

            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[prompt, audio_part]
            )
            
            # Extract text from response
            if response and response.text:
                transcription = response.text.strip()
                await self.send_message(f"Transcribed: \"{transcription[:50]}...\"")
                return {
                    "success": True,
                    "transcription": transcription
                }
            else:
                return {
                    "success": False,
                    "error": "No transcription returned"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Transcription failed: {str(e)}"
            }


# Singleton instance
speech_agent = SpeechAgent()

