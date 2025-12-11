"""
Video Stitch Agent - Concatenates multiple video clips into one
Uses MoviePy with imageio-ffmpeg (bundled FFmpeg)
Version: 1.1
"""
from typing import Any, Dict, List
from pathlib import Path
import shutil

from .base import BaseAgent


class VideoStitchAgent(BaseAgent):
    """
    Agent responsible for stitching multiple video clips together.
    Uses MoviePy which includes bundled FFmpeg via imageio-ffmpeg.
    """
    
    def __init__(self):
        super().__init__(
            name="VideoStitchAgent",
            description="Concatenates multiple videos into one"
        )
        self.output_dir = Path("generated/videos")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._moviepy_available = self._check_moviepy()
        
        if self._moviepy_available:
            print("✓ MoviePy available for video stitching")
        else:
            print("⚠ MoviePy not available - will return first video only")
    
    def _check_moviepy(self) -> bool:
        """Check if MoviePy is available"""
        try:
            from moviepy.editor import VideoFileClip
            return True
        except ImportError as e:
            print(f"MoviePy import error: {e}")
            return False
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Stitch multiple videos together.
        """
        video_paths = input_data.get("video_paths", [])
        task_id = input_data.get("task_id", "output")
        
        if not video_paths:
            return {"success": False, "error": "No video paths provided"}
        
        # Filter to only existing files
        existing_paths = []
        for p in video_paths:
            path = Path(p)
            if path.exists():
                existing_paths.append(str(path))
                print(f"[VideoStitch] Found video: {path}")
            else:
                print(f"[VideoStitch] Video not found: {path}")
        
        if not existing_paths:
            return {"success": False, "error": "No valid video files found"}
        
        print(f"[VideoStitch] Stitching {len(existing_paths)} videos...")
        
        output_path = self.output_dir / f"{task_id}_final.mp4"
        
        if len(existing_paths) == 1:
            # Only one video, just copy it
            shutil.copy(existing_paths[0], output_path)
            print(f"[VideoStitch] Single video, copied to {output_path}")
            return {
                "success": True,
                "output_path": str(output_path),
                "video_url": f"/api/video/file/{output_path.name}"
            }
        
        await self.update_progress(92, f"Stitching {len(existing_paths)} video clips...")
        
        # Use MoviePy if available
        if self._moviepy_available:
            result = await self._stitch_with_moviepy(existing_paths, output_path)
        else:
            result = await self._stitch_fallback(existing_paths, output_path)
        
        if result.get("success"):
            await self.send_message(f"✓ Successfully stitched {len(existing_paths)} clips!")
        
        return result
    
    async def _stitch_with_moviepy(
        self, 
        video_paths: List[str], 
        output_path: Path
    ) -> Dict[str, Any]:
        """Stitch videos using MoviePy"""
        try:
            from moviepy.editor import VideoFileClip, concatenate_videoclips
            import asyncio
            
            print(f"[VideoStitch] Loading {len(video_paths)} clips with MoviePy...")
            
            # Load all clips
            clips = []
            for i, path in enumerate(video_paths):
                try:
                    print(f"[VideoStitch] Loading clip {i+1}: {path}")
                    clip = VideoFileClip(str(path))
                    clips.append(clip)
                    print(f"[VideoStitch] Clip {i+1} loaded: {clip.duration}s, {clip.size}")
                except Exception as e:
                    print(f"[VideoStitch] Failed to load clip {path}: {e}")
            
            if not clips:
                return {"success": False, "error": "No clips could be loaded"}
            
            if len(clips) == 1:
                # Just one clip loaded successfully
                print(f"[VideoStitch] Only one clip loaded, writing directly...")
                
                def write_single():
                    clips[0].write_videofile(
                        str(output_path), 
                        codec="libx264", 
                        audio_codec="aac",
                        verbose=False,
                        logger=None
                    )
                
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, write_single)
            else:
                # Concatenate all clips
                print(f"[VideoStitch] Concatenating {len(clips)} clips...")
                final_clip = concatenate_videoclips(clips, method="compose")
                print(f"[VideoStitch] Final duration: {final_clip.duration}s")
                
                def write_final():
                    final_clip.write_videofile(
                        str(output_path), 
                        codec="libx264", 
                        audio_codec="aac",
                        verbose=False,
                        logger=None
                    )
                
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, write_final)
                final_clip.close()
            
            # Clean up
            for clip in clips:
                clip.close()
            
            if output_path.exists() and output_path.stat().st_size > 0:
                print(f"[VideoStitch] Successfully created: {output_path}")
                return {
                    "success": True,
                    "output_path": str(output_path),
                    "video_url": f"/api/video/file/{output_path.name}"
                }
            
            return {"success": False, "error": "MoviePy output failed"}
                
        except Exception as e:
            print(f"[VideoStitch] MoviePy stitch failed: {e}")
            import traceback
            traceback.print_exc()
            return await self._stitch_fallback(video_paths, output_path)
    
    async def _stitch_fallback(
        self, 
        video_paths: List[str], 
        output_path: Path
    ) -> Dict[str, Any]:
        """Fallback: just copy the first video"""
        print("[VideoStitch] Using fallback: copying first video only")
        first_video = video_paths[0]
        shutil.copy(first_video, output_path)
        
        return {
            "success": True,
            "output_path": str(output_path),
            "video_url": f"/api/video/file/{output_path.name}",
            "warning": "Only first scene included (video stitching failed)"
        }


# Singleton instance
video_stitch_agent = VideoStitchAgent()
