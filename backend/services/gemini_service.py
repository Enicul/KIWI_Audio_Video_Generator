"""
Gemini Service - Uses Google's new genai SDK
Supports text, audio understanding, and Veo video generation
"""
import os
import time
import asyncio
import base64
import tempfile
from typing import Optional, Dict, Any
from pathlib import Path

from config import settings


class GeminiService:
    """
    Service for interacting with Google Gemini API.
    Uses the new google-genai SDK for Veo video generation.
    """
    
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self._initialized = False
        self.client = None
        self.output_dir = Path("generated/videos")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def initialize(self):
        """Initialize the Gemini client"""
        if self._initialized:
            return
        
        if not self.api_key:
            print("Warning: Gemini API key not configured. Using fallback mode.")
            return
        
        try:
            from google import genai
            
            self.client = genai.Client(api_key=self.api_key)
            self._initialized = True
            print("Gemini service initialized successfully")
            
        except Exception as e:
            print(f"Gemini initialization failed: {e}")
            self._initialized = False
    
    async def transcribe_audio(self, audio_base64: str) -> str:
        """
        Transcribe audio to text using Gemini's multimodal capabilities.
        Uses inline data for simplicity.
        """
        if not self._initialized or not self.client:
            print("Gemini not initialized, cannot transcribe audio")
            return ""
        
        try:
            from google.genai import types
            
            # Extract mime type and base64 data
            mime_type = "audio/webm"
            base64_data = audio_base64
            
            if "," in audio_base64:
                header, base64_data = audio_base64.split(",", 1)
                if "audio/" in header:
                    mime_type = header.split(":")[1].split(";")[0]
            
            # Create inline data part
            audio_part = types.Part.from_bytes(
                data=base64.b64decode(base64_data),
                mime_type=mime_type
            )
            
            # Use Gemini to transcribe
            prompt = """Listen to this audio and transcribe exactly what the person is saying.
If they are describing a video they want to create, capture all the details.
Return ONLY the transcription, no additional commentary."""

            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[prompt, audio_part]
            )
            
            # Extract text from response
            if response and hasattr(response, 'text') and response.text:
                transcription = response.text.strip()
                print(f"Audio transcribed: {transcription[:100]}...")
                return transcription
            else:
                print("No text in response")
                return ""
                        
        except Exception as e:
            print(f"Audio transcription failed: {e}")
            return ""
    
    async def understand_intent(self, user_input: str) -> Dict[str, Any]:
        """
        Use Gemini to understand user's video intent.
        """
        if not self._initialized or not self.client:
            return self._fallback_intent(user_input)
        
        try:
            prompt = f"""Analyze this video creation request and extract the key elements.
            
User request: "{user_input}"

Return a JSON object with these fields:
- topic: main subject of the video
- video_type: type (explainer, story, advertisement, tutorial, etc.)
- style: visual style (cinematic, animated, documentary, etc.)
- mood: emotional tone (exciting, calm, dramatic, etc.)
- duration: suggested duration in seconds (default 8 for Veo)
- key_elements: list of important visual elements to include

Return ONLY valid JSON, no markdown formatting."""

            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            
            # Safely get response text
            if not response or not response.text:
                print("No text in intent response")
                return self._fallback_intent(user_input)
            
            # Parse JSON response
            text = response.text.strip()
            
            # Remove markdown code blocks if present
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                parts = text.split("```")
                if len(parts) >= 2:
                    text = parts[1]
            
            text = text.strip()
            
            import json
            intent = json.loads(text)
            intent["original_input"] = user_input
            
            # Ensure required fields exist
            intent.setdefault("topic", user_input[:100])
            intent.setdefault("video_type", "short video")
            intent.setdefault("style", "cinematic")
            intent.setdefault("mood", "engaging")
            intent.setdefault("duration", 8)
            intent.setdefault("key_elements", [])
            
            return intent
            
        except Exception as e:
            print(f"Intent understanding failed: {e}")
            return self._fallback_intent(user_input)
    
    def _fallback_intent(self, user_input: str) -> Dict[str, Any]:
        """Fallback intent extraction without API"""
        return {
            "topic": user_input[:100],
            "video_type": "short video",
            "style": "cinematic",
            "mood": "engaging",
            "duration": 8,
            "key_elements": [],
            "original_input": user_input
        }
    
    async def generate_video_prompt(self, intent: Dict[str, Any]) -> str:
        """
        Generate an optimized prompt for Veo video generation.
        """
        if not self._initialized or not self.client:
            return self._fallback_video_prompt(intent)
        
        try:
            prompt = f"""Create an optimal video generation prompt for Veo based on this intent:

Topic: {intent.get('topic', 'general')}
Type: {intent.get('video_type', 'short video')}
Style: {intent.get('style', 'cinematic')}
Mood: {intent.get('mood', 'engaging')}
Key elements: {', '.join(intent.get('key_elements', []))}
Original request: {intent.get('original_input', '')}

Create a detailed, vivid video prompt that:
1. Describes the visual scene clearly
2. Includes camera movement if appropriate
3. Specifies lighting and atmosphere
4. Is optimized for AI video generation

Return ONLY the prompt text, no explanations."""

            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            
            # Safely get response text
            if not response or not response.text:
                print("No text in video prompt response")
                return self._fallback_video_prompt(intent)
            
            video_prompt = response.text.strip()
            print(f"Generated video prompt: {video_prompt[:100]}...")
            return video_prompt
            
        except Exception as e:
            print(f"Video prompt generation failed: {e}")
            return self._fallback_video_prompt(intent)
    
    def _fallback_video_prompt(self, intent: Dict[str, Any]) -> str:
        """Create a simple video prompt without API"""
        topic = intent.get("topic", "beautiful scene")
        style = intent.get("style", "cinematic")
        mood = intent.get("mood", "engaging")
        
        return f"A {style} video showing {topic}, {mood} atmosphere, high quality, 4K, smooth camera movement"
    
    async def generate_video(
        self, 
        prompt: str, 
        task_id: str,
        on_progress: Optional[callable] = None
    ) -> Optional[str]:
        """
        Generate a video using Veo 2.
        
        Args:
            prompt: Video description prompt
            task_id: Task ID for filename
            on_progress: Optional callback for progress updates
        
        Returns:
            Path to the generated video, or None if failed
        """
        if not self._initialized or not self.client:
            print("Gemini not initialized, cannot generate video")
            return None
        
        try:
            from google.genai import types
            
            print(f"Starting video generation with Veo 2...")
            print(f"Prompt: {prompt[:100]}...")
            
            # Start video generation with Veo 2
            operation = self.client.models.generate_videos(
                model="veo-2.0-generate-001",
                prompt=prompt,
                config=types.GenerateVideosConfig(
                    person_generation="allow_adult",
                    aspect_ratio="16:9",
                    number_of_videos=1,
                )
            )
            
            # Wait for video generation to complete
            max_wait = 300  # 5 minutes max
            wait_time = 0
            
            while not operation.done and wait_time < max_wait:
                await asyncio.sleep(10)
                wait_time += 10
                operation = self.client.operations.get(operation)
                progress_pct = min(90, 60 + int(wait_time / 300 * 30))
                print(f"Video generation progress... ({wait_time}s)")
                
                if on_progress:
                    await on_progress(progress_pct, f"Generating video... ({wait_time}s)")
            
            if not operation.done:
                print("Video generation timed out")
                return None
            
            # Debug: print operation structure
            print(f"Operation done: {operation.done}")
            print(f"Operation has response: {hasattr(operation, 'response')}")
            print(f"Operation has result: {hasattr(operation, 'result')}")
            
            # Try different ways to access the result
            generated_videos = None
            
            # Try operation.response first
            if hasattr(operation, 'response') and operation.response:
                print(f"Response type: {type(operation.response)}")
                if hasattr(operation.response, 'generated_videos'):
                    generated_videos = operation.response.generated_videos
                    print(f"Found videos in response: {len(generated_videos) if generated_videos else 0}")
            
            # Try operation.result as fallback
            if not generated_videos and hasattr(operation, 'result') and operation.result:
                print(f"Result type: {type(operation.result)}")
                if hasattr(operation.result, 'generated_videos'):
                    generated_videos = operation.result.generated_videos
                    print(f"Found videos in result: {len(generated_videos) if generated_videos else 0}")
            
            if not generated_videos:
                print("No video generated in response or result")
                # Print full operation for debugging
                print(f"Full operation: {operation}")
                return None
            
            # Get the generated video
            generated_video = generated_videos[0]
            print(f"Generated video: {generated_video}")
            
            # Download and save the video
            output_path = self.output_dir / f"{task_id}.mp4"
            
            # Get the video object
            if hasattr(generated_video, 'video'):
                video_obj = generated_video.video
                print(f"Video object: {video_obj}")
                
                # Check if video has URI (download from URL)
                if hasattr(video_obj, 'uri') and video_obj.uri:
                    print(f"Downloading from URI: {video_obj.uri}")
                    import httpx
                    
                    # Download video from URI with redirect following and API key
                    headers = {
                        "x-goog-api-key": self.api_key
                    }
                    async with httpx.AsyncClient(follow_redirects=True, timeout=120) as client:
                        response = await client.get(video_obj.uri, headers=headers)
                        print(f"Download response: HTTP {response.status_code}")
                        if response.status_code == 200:
                            with open(output_path, "wb") as f:
                                f.write(response.content)
                            print(f"Video saved to: {output_path} ({len(response.content)} bytes)")
                            return str(output_path)
                        else:
                            print(f"Failed to download video: HTTP {response.status_code}")
                            print(f"Response: {response.text[:500]}")
                            return None
                
                # Check if video has bytes directly
                elif hasattr(video_obj, 'video_bytes') and video_obj.video_bytes:
                    print("Using video_bytes directly")
                    with open(output_path, "wb") as f:
                        f.write(video_obj.video_bytes)
                    print(f"Video saved to: {output_path}")
                    return str(output_path)
                
                else:
                    print(f"Cannot find way to download video: {video_obj}")
                    return None
            else:
                print(f"No video attribute found in generated_video")
                return None
            
        except Exception as e:
            print(f"Video generation failed: {e}")
            return None
    
    def get_video_url(self, task_id: str) -> Optional[str]:
        """Get the URL for a generated video"""
        video_path = self.output_dir / f"{task_id}.mp4"
        if video_path.exists():
            return f"/api/video/file/{task_id}.mp4"
        return None


# Singleton instance
gemini_service = GeminiService()
