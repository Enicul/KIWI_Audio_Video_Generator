"""
Video Agent - Generates videos using Veo
Handles both text-to-video and image-to-video generation with retry support
"""
from typing import Any, Dict, Optional
from pathlib import Path
import asyncio
import base64

from .base import BaseAgent


class VideoAgent(BaseAgent):
    """
    Agent responsible for video generation.
    Uses Veo 3 to create videos from prompts or images with retry support.
    Supports:
    - Text-to-Video: Generate video from text prompt
    - Image-to-Video: Generate video from starting image + prompt
    """
    
    def __init__(self):
        super().__init__(
            name="VideoAgent",
            description="Generates videos using Veo 3 (text-to-video and image-to-video)"
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
            image_path: Optional path to first-frame image (for image-to-video)
            
        Output:
            success: bool
            video_path: str (path to generated video)
            video_url: str (URL to access video)
            error: str (if failed)
        """
        prompt = input_data.get("prompt")
        task_id = input_data.get("task_id")
        image_path = input_data.get("image_path")  # Optional: for image-to-video
        
        if not prompt:
            return {"success": False, "error": "No prompt provided"}
        
        if not task_id:
            return {"success": False, "error": "No task_id provided"}
        
        if not self._initialized or not self.client:
            return {"success": False, "error": "VideoAgent not initialized"}
        
        # Determine generation mode
        use_image = image_path and Path(image_path).exists()
        mode = "image-to-video" if use_image else "text-to-video"
        
        # Try with retries
        last_error = None
        for attempt in range(self.max_retries + 1):
            if attempt > 0:
                await self.update_progress(60, f"Retrying {mode} (attempt {attempt + 1})...")
                await asyncio.sleep(5)
            
            if use_image:
                result = await self._generate_video_from_image(prompt, task_id, image_path)
            else:
                result = await self._generate_video(prompt, task_id)
            
            if result.get("success"):
                return result
            
            last_error = result.get("error", "Unknown error")
            print(f"{mode} attempt {attempt + 1} failed: {last_error}")
        
        return {"success": False, "error": f"{mode} failed after {self.max_retries + 1} attempts: {last_error}"}
    
    async def _generate_video(self, prompt: str, task_id: str) -> Dict[str, Any]:
        """Internal method to generate a single video"""
        
        try:
            from google.genai import types
            
            await self.update_progress(60, "Starting video generation...")
            await self.send_message(f"Generating video with Veo 3...")
            
            # Start video generation with Veo 3
            operation = self.client.models.generate_videos(
                model="veo-3.0-generate-001",
                prompt=prompt,
                config=types.GenerateVideosConfig(
                    person_generation="allow_all",
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
    
    async def _generate_video_from_image(
        self, 
        prompt: str, 
        task_id: str, 
        image_path: str
    ) -> Dict[str, Any]:
        """Generate video from a starting image (Image-to-Video)"""
        
        try:
            from google.genai import types
            
            await self.update_progress(60, "Starting image-to-video generation...")
            await self.send_message(f"Generating video from first frame with Veo 3...")
            
            # Read and encode the image
            image_file = Path(image_path)
            if not image_file.exists():
                return {"success": False, "error": f"Image not found: {image_path}"}
            
            with open(image_file, "rb") as f:
                image_bytes = f.read()
            
            # Determine mime type
            suffix = image_file.suffix.lower()
            mime_type = {
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".webp": "image/webp"
            }.get(suffix, "image/png")
            
            print(f"[VideoAgent] Image-to-Video: {image_path} ({mime_type})")
            
            # Create image part for the request
            image_part = types.Part.from_bytes(
                data=image_bytes,
                mime_type=mime_type
            )
            
            # Start image-to-video generation
            operation = self.client.models.generate_videos(
                model="veo-3.0-generate-001",
                prompt=prompt,
                image=image_part,  # First frame image
                config=types.GenerateVideosConfig(
                    person_generation="allow_all",
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
                try:
                    operation = self.client.operations.get(operation)
                except Exception as e:
                    print(f"[VideoAgent] Operation status check failed: {e}")
                progress = min(90, 60 + int(wait_time / 300 * 30))
                await self.update_progress(progress, f"Generating from image... ({wait_time}s)")
            
            if not operation.done:
                return {"success": False, "error": "Image-to-video generation timed out"}
            
            # Get generated videos (same as text-to-video)
            generated_videos = None
            
            if hasattr(operation, 'response') and operation.response:
                if hasattr(operation.response, 'generated_videos'):
                    generated_videos = operation.response.generated_videos
            
            if not generated_videos:
                if hasattr(operation, 'result') and operation.result:
                    if hasattr(operation.result, 'generated_videos'):
                        generated_videos = operation.result.generated_videos
            
            if not generated_videos:
                error_info = ""
                if hasattr(operation, 'error') and operation.error:
                    error_info = f": {operation.error}"
                print(f"[VideoAgent] No videos generated from image{error_info}")
                return {"success": False, "error": f"No video generated from image{error_info}"}
            
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
                            
                            await self.send_message("Video generated from image successfully!")
                            
                            return {
                                "success": True,
                                "video_path": str(output_path),
                                "video_url": f"/api/video/file/{task_id}.mp4",
                                "mode": "image-to-video"
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
                        "video_url": f"/api/video/file/{task_id}.mp4",
                        "mode": "image-to-video"
                    }
            
            return {"success": False, "error": "Could not extract video from response"}
            
        except Exception as e:
            print(f"[VideoAgent] Image-to-video failed: {e}")
            return {
                "success": False,
                "error": f"Image-to-video failed: {str(e)}"
            }
    
    def get_video_url(self, task_id: str) -> Optional[str]:
        """Get the URL for a generated video"""
        video_path = self.output_dir / f"{task_id}.mp4"
        if video_path.exists():
            return f"/api/video/file/{task_id}.mp4"
        return None


# Singleton instance
video_agent = VideoAgent()

