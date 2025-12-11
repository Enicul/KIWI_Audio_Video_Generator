"""Video processing utilities using MoviePy."""

import os
from pathlib import Path

from moviepy import AudioFileClip, CompositeVideoClip, TextClip, VideoFileClip
from moviepy.video.compositing.CompositeVideoClip import concatenate_videoclips

from kiwi_video.core.exceptions import KiwiVideoError
from kiwi_video.utils.logger import get_logger


class VideoProcessor:
    """
    Video processing utilities using MoviePy.
    
    Provides methods for video manipulation, composition, and effects.
    """

    logger = get_logger("video_processor")

    @staticmethod
    async def cut_video(
        input_path: Path,
        output_path: Path,
        start: float,
        end: float
    ) -> Path:
        """
        Cut a segment from a video.
        
        Args:
            input_path: Path to input video
            output_path: Path to save output video
            start: Start time in seconds
            end: End time in seconds
            
        Returns:
            Path to output video
            
        Raises:
            KiwiVideoError: If cutting fails
        """
        try:
            VideoProcessor.logger.info(f"Cutting video from {start}s to {end}s")

            # Load video
            video_clip = VideoFileClip(str(input_path))

            # Cut segment
            cut_clip = video_clip.subclipped(start, end)

            # Create output directory
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Write output
            cut_clip.write_videofile(
                str(output_path),
                codec="libx264",
                audio_codec="aac",
                temp_audiofile=str(output_path.parent / f"temp-audio-{output_path.stem}.m4a"),
                remove_temp=True,
                threads=os.cpu_count(),
                logger=None  # Suppress MoviePy logging
            )

            # Cleanup
            cut_clip.close()
            video_clip.close()

            VideoProcessor.logger.info(f"Video cut successfully: {output_path}")
            return output_path

        except Exception as e:
            VideoProcessor.logger.error(f"Failed to cut video: {e}")
            raise KiwiVideoError(f"Video cutting failed: {e}")

    @staticmethod
    async def adjust_video_duration(
        input_path: Path,
        target_duration: float,
        output_path: Path
    ) -> Path:
        """
        Adjust video duration by changing playback speed.
        
        Args:
            input_path: Path to input video
            target_duration: Desired duration in seconds
            output_path: Path to save adjusted video
            
        Returns:
            Path to output video
            
        Raises:
            KiwiVideoError: If adjustment fails
        """
        try:
            VideoProcessor.logger.info(
                f"Adjusting video duration to {target_duration:.2f}s"
            )

            # Load video
            video_clip = VideoFileClip(str(input_path))
            original_duration = video_clip.duration

            # Calculate speed factor
            speed_factor = original_duration / target_duration

            VideoProcessor.logger.info(
                f"  Original: {original_duration:.2f}s → Target: {target_duration:.2f}s "
                f"(speed: {speed_factor:.2f}x)"
            )

            # Adjust speed by changing playback rate
            if speed_factor != 1.0:
                # MoviePy speed adjustment: use speedx or manual fps change
                try:
                    # Method 1: Use speedx (most compatible)
                    if hasattr(video_clip, 'speedx'):
                        adjusted_clip = video_clip.speedx(speed_factor)
                        VideoProcessor.logger.debug("Using speedx method")
                    # Method 2: Manual calculation (change duration)
                    else:
                        # Change duration by adjusting fps
                        new_duration = original_duration / speed_factor
                        adjusted_clip = video_clip.with_duration(new_duration)
                        VideoProcessor.logger.debug("Using with_duration method")

                except Exception as e:
                    VideoProcessor.logger.warning(
                        f"Speed adjustment failed ({e}), using original duration"
                    )
                    adjusted_clip = video_clip
            else:
                adjusted_clip = video_clip

            # Create output directory
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Write output
            adjusted_clip.write_videofile(
                str(output_path),
                codec="libx264",
                audio_codec="aac" if adjusted_clip.audio else None,
                temp_audiofile=str(output_path.parent / f"temp-audio-{output_path.stem}.m4a"),
                remove_temp=True,
                threads=os.cpu_count(),
                logger=None
            )

            # Cleanup
            adjusted_clip.close()
            video_clip.close()

            VideoProcessor.logger.info(f"Video duration adjusted: {output_path}")
            return output_path

        except Exception as e:
            VideoProcessor.logger.error(f"Failed to adjust video duration: {e}")
            raise KiwiVideoError(f"Video duration adjustment failed: {e}")

    @staticmethod
    async def concat_videos(
        video_paths: list[Path],
        output_path: Path
    ) -> Path:
        """
        Concatenate multiple videos.
        
        Args:
            video_paths: List of video file paths
            output_path: Path to save concatenated video
            
        Returns:
            Path to output video
            
        Raises:
            KiwiVideoError: If concatenation fails
        """
        try:
            VideoProcessor.logger.info(f"Concatenating {len(video_paths)} videos")

            # Load all video clips
            clips = [VideoFileClip(str(path)) for path in video_paths]

            # Concatenate clips
            final_clip = concatenate_videoclips(clips, method="compose")

            # Create output directory
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Write output
            final_clip.write_videofile(
                str(output_path),
                codec="libx264",
                audio_codec="aac",
                temp_audiofile=str(output_path.parent / "temp-concat-audio.m4a"),
                remove_temp=True,
                threads=os.cpu_count(),
                logger=None
            )

            # Cleanup
            final_clip.close()
            for clip in clips:
                clip.close()

            VideoProcessor.logger.info(f"Videos concatenated successfully: {output_path}")
            return output_path

        except Exception as e:
            VideoProcessor.logger.error(f"Failed to concatenate videos: {e}")
            raise KiwiVideoError(f"Video concatenation failed: {e}")

    @staticmethod
    async def add_audio_to_video(
        video_path: Path,
        audio_path: Path,
        output_path: Path
    ) -> Path:
        """
        Add audio track to video.
        
        Args:
            video_path: Path to input video
            audio_path: Path to audio file
            output_path: Path to save output video
            
        Returns:
            Path to output video
            
        Raises:
            KiwiVideoError: If operation fails
        """
        try:
            VideoProcessor.logger.info("Adding audio to video")

            # Load video and audio
            video_clip = VideoFileClip(str(video_path))
            audio_clip = AudioFileClip(str(audio_path))

            # Set audio
            final_clip = video_clip.with_audio(audio_clip)

            # Create output directory
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Write output
            final_clip.write_videofile(
                str(output_path),
                codec="libx264",
                audio_codec="aac",
                temp_audiofile=str(output_path.parent / "temp-audio.m4a"),
                remove_temp=True,
                threads=os.cpu_count(),
                logger=None
            )

            # Cleanup
            final_clip.close()
            audio_clip.close()
            video_clip.close()

            VideoProcessor.logger.info(f"Audio added successfully: {output_path}")
            return output_path

        except Exception as e:
            VideoProcessor.logger.error(f"Failed to add audio: {e}")
            raise KiwiVideoError(f"Adding audio failed: {e}")

    @staticmethod
    async def add_subtitle_overlay(
        video_path: Path,
        text: str,
        output_path: Path,
        font_size: int = 24,
        position: str = "bottom",
        font_path: Path | None = None
    ) -> Path:
        """
        Add text subtitle overlay to video.
        
        Args:
            video_path: Path to input video
            text: Subtitle text
            output_path: Path to save output video
            font_size: Font size in pixels
            position: Text position ("top", "center", "bottom")
            font_path: Optional path to custom font
            
        Returns:
            Path to output video
            
        Raises:
            KiwiVideoError: If operation fails
        """
        try:
            VideoProcessor.logger.info("Adding subtitle overlay to video")

            # Load video
            video_clip = VideoFileClip(str(video_path))

            # Create text clip
            text_clip = TextClip(
                font=str(font_path) if font_path else None,
                text=text,
                font_size=font_size,
                color="white",
                bg_color=(0, 0, 0, 128),  # Semi-transparent black background
                size=(video_clip.size[0] - 20, None),  # Fit to video width with margin
                method="caption",
                margin=(10, 10)
            )

            # Position text clip
            if position == "top":
                text_clip = text_clip.with_position(("center", "top"))
            elif position == "center":
                text_clip = text_clip.with_position("center")
            else:  # bottom
                text_clip = text_clip.with_position(("center", "bottom"))

            # Set duration to match video
            text_clip = text_clip.with_duration(video_clip.duration)

            # Composite video with text
            final_clip = CompositeVideoClip([video_clip, text_clip])

            # Create output directory
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Write output
            final_clip.write_videofile(
                str(output_path),
                codec="libx264",
                audio_codec="aac",
                temp_audiofile=str(output_path.parent / "temp-subtitle-audio.m4a"),
                remove_temp=True,
                threads=os.cpu_count(),
                logger=None
            )

            # Cleanup
            final_clip.close()
            text_clip.close()
            video_clip.close()

            VideoProcessor.logger.info(f"Subtitle added successfully: {output_path}")
            return output_path

        except Exception as e:
            VideoProcessor.logger.error(f"Failed to add subtitle: {e}")
            raise KiwiVideoError(f"Adding subtitle failed: {e}")

    @staticmethod
    async def merge_video_audio(
        video_path: Path,
        audio_path: Path,
        text: str | None,
        output_path: Path,
        font_path: Path | None = None
    ) -> Path:
        """
        Merge video with audio and optional text overlay.
        
        Args:
            video_path: Path to input video
            audio_path: Path to audio file
            text: Optional subtitle text
            output_path: Path to save output video
            font_path: Optional path to custom font
            
        Returns:
            Path to output video
            
        Raises:
            KiwiVideoError: If operation fails
        """
        try:
            VideoProcessor.logger.info("Merging video with audio and text")

            # Load video and audio
            video_clip = VideoFileClip(str(video_path))
            audio_clip = AudioFileClip(str(audio_path))

            # Set audio
            video_with_audio = video_clip.with_audio(audio_clip)

            # Add text overlay if provided
            if text and text.strip():
                text_clip = TextClip(
                    font=str(font_path) if font_path else None,
                    text=text,
                    font_size=24,
                    color="white",
                    bg_color=(0, 0, 0, 128),
                    size=(video_clip.size[0] - 20, None),
                    method="caption",
                    margin=(10, 10)
                )

                text_clip = text_clip.with_position(("center", "bottom"))
                text_clip = text_clip.with_duration(video_with_audio.duration)

                final_clip = CompositeVideoClip([video_with_audio, text_clip])
                text_clip.close()
            else:
                final_clip = video_with_audio

            # Create output directory
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Write output
            final_clip.write_videofile(
                str(output_path),
                codec="libx264",
                audio_codec="aac",
                temp_audiofile=str(output_path.parent / f"temp-merge-audio-{output_path.stem}.m4a"),
                remove_temp=True,
                threads=os.cpu_count(),
                logger=None
            )

            # Cleanup
            final_clip.close()
            audio_clip.close()
            video_clip.close()

            VideoProcessor.logger.info(f"Video merged successfully: {output_path}")
            return output_path

        except Exception as e:
            VideoProcessor.logger.error(f"Failed to merge video: {e}")
            raise KiwiVideoError(f"Video merging failed: {e}")

    @staticmethod
    def get_video_info(video_path: Path) -> dict:
        """
        Get video information.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Dictionary with video information
        """
        try:
            clip = VideoFileClip(str(video_path))
            info = {
                "duration": clip.duration,
                "fps": clip.fps,
                "size": clip.size,
                "width": clip.size[0],
                "height": clip.size[1],
                "has_audio": clip.audio is not None
            }
            clip.close()
            return info

        except Exception as e:
            VideoProcessor.logger.error(f"Failed to get video info: {e}")
            raise KiwiVideoError(f"Getting video info failed: {e}")

