"""
Video Agent - Generates videos using Veo
Handles the actual video generation process with retry support
"""
from typing import Any, Dict, Optional
from pathlib import Path
import asyncio

from .base import BaseAgent


class VideoAgent(BaseAgent):
    """
    Agent responsible for video generation.
    Uses Veo 2 to create videos from prompts with retry support.
    """
    
    def __init__(self):
        super().__init__(
            name="VideoAgent",
            description="Generates videos using Veo 2"
        )
        self.client = None
        self.api_key = None
        self._initialized = False
        self.output_dir = Path("generated/videos")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.max_retries = 2
    
    def initialize(self, client, api_key: str):
        """Initialize with Gemini client and API key"""
        self.client = client
        self.api_key = api_key
        self._initialized = True
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process prompt and generate video with retry support.
        
        Input:
            prompt: Video generation prompt
            task_id: Unique task identifier
            
        Output:
            success: bool
            video_path: str (path to generated video)
            video_url: str (URL to access video)
            error: str (if failed)
        """
        prompt = input_data.get("prompt")
        task_id = input_data.get("task_id")
        
        if not prompt:
            return {"success": False, "error": "No prompt provided"}
        
        if not task_id:
            return {"success": False, "error": "No task_id provided"}
        
        if not self._initialized or not self.client:
            return {"success": False, "error": "VideoAgent not initialized"}
        
        # Try with retries
        last_error = None
        for attempt in range(self.max_retries + 1):
            if attempt > 0:
                await self.update_progress(60, f"Retrying video generation (attempt {attempt + 1})...")
                await asyncio.sleep(5)  # Brief pause before retry
            
            result = await self._generate_video(prompt, task_id)
            
            if result.get("success"):
                return result
            
            last_error = result.get("error", "Unknown error")
            print(f"Video generation attempt {attempt + 1} failed: {last_error}")
        
        return {"success": False, "error": f"Video generation failed after {self.max_retries + 1} attempts: {last_error}"}
    
    async def _generate_video(self, prompt: str, task_id: str) -> Dict[str, Any]:
        """Internal method to generate a single video"""
        
        try:
            from google.genai import types
            
            await self.update_progress(60, "Starting video generation...")
            await self.send_message(f"Generating video with Veo 2...")
            
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
                progress = min(90, 60 + int(wait_time / 300 * 30))
                await self.update_progress(progress, f"Generating video... ({wait_time}s)")
            
            if not operation.done:
                return {"success": False, "error": "Video generation timed out"}
            
            # Get generated videos
            generated_videos = None
            
            if hasattr(operation, 'response') and operation.response:
                if hasattr(operation.response, 'generated_videos'):
                    generated_videos = operation.response.generated_videos
            
            if not generated_videos:
                if hasattr(operation, 'result') and operation.result:
                    if hasattr(operation.result, 'generated_videos'):
                        generated_videos = operation.result.generated_videos
            
            if not generated_videos:
                # Check for errors in operation
                error_info = ""
                if hasattr(operation, 'error') and operation.error:
                    error_info = f": {operation.error}"
                print(f"[VideoAgent] No videos generated{error_info}")
                return {"success": False, "error": f"No video generated{error_info}"}
            
            # Download the video
            generated_video = generated_videos[0]
            output_path = self.output_dir / f"{task_id}.mp4"
            
            if hasattr(generated_video, 'video'):
                video_obj = generated_video.video
                
                if hasattr(video_obj, 'uri') and video_obj.uri:
                    await self.update_progress(92, "Downloading video...")
                    
                    import httpx
                    headers = {"x-goog-api-key": self.api_key}
                    
                    async with httpx.AsyncClient(follow_redirects=True, timeout=120) as http_client:
                        response = await http_client.get(video_obj.uri, headers=headers)
                        
                        if response.status_code == 200:
                            with open(output_path, "wb") as f:
                                f.write(response.content)
                            
                            await self.send_message("Video generated successfully!")
                            
                            return {
                                "success": True,
                                "video_path": str(output_path),
                                "video_url": f"/api/video/file/{task_id}.mp4"
                            }
                        else:
                            return {
                                "success": False,
                                "error": f"Failed to download video: HTTP {response.status_code}"
                            }
                
                elif hasattr(video_obj, 'video_bytes') and video_obj.video_bytes:
                    with open(output_path, "wb") as f:
                        f.write(video_obj.video_bytes)
                    
                    return {
                        "success": True,
                        "video_path": str(output_path),
                        "video_url": f"/api/video/file/{task_id}.mp4"
                    }
            
            return {"success": False, "error": "Could not extract video from response"}
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Video generation failed: {str(e)}"
            }
    
    def get_video_url(self, task_id: str) -> Optional[str]:
        """Get the URL for a generated video"""
        video_path = self.output_dir / f"{task_id}.mp4"
        if video_path.exists():
            return f"/api/video/file/{task_id}.mp4"
        return None


# Singleton instance
video_agent = VideoAgent()

