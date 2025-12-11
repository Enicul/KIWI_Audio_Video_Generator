"""Google Vertex AI Veo video generation client."""

import time
from pathlib import Path
from typing import Literal

from google import genai
from google.api_core import exceptions as gcp_exceptions
from google.cloud import storage
from google.genai import types

from kiwi_video.core.exceptions import ProviderError
from kiwi_video.providers.video.base import BaseVideoProvider
from kiwi_video.utils.config import settings
from kiwi_video.utils.logger import get_logger


class VeoClient(BaseVideoProvider):
    """
    Google Vertex AI Veo video generation client.
    
    Supports text-to-video generation with Veo 2.0 and Veo 3.0 models.
    """

    # Supported durations for Veo text-to-video
    SUPPORTED_DURATIONS = [4, 6, 8]

    @staticmethod
    def normalize_duration(duration: int | float) -> int:
        """
        Normalize duration to the closest supported value.

        Args:
            duration: Desired duration in seconds

        Returns:
            Closest supported duration (4, 6, or 8 seconds)
        """
        supported = VeoClient.SUPPORTED_DURATIONS
        duration_int = int(round(duration))

        # Clamp to supported range
        if duration_int < supported[0]:
            return supported[0]  # Minimum 4 seconds
        if duration_int > supported[-1]:
            return supported[-1]  # Maximum 8 seconds

        # Find closest supported duration
        return min(supported, key=lambda x: abs(x - duration_int))

    def __init__(
        self,
        project_id: str | None = None,
        location: str | None = None,
        storage_uri: str | None = None
    ) -> None:
        """
        Initialize Veo client.
        
        Args:
            project_id: GCP project ID (uses settings if not provided)
            location: Vertex AI location (uses settings if not provided)
            storage_uri: Base GCS URI for video storage
        """
        self.logger = get_logger("veo_client")

        self.project_id = project_id or settings.gcp_project_id
        self.location = location or settings.veo_location
        self.gcs_bucket = settings.gcs_bucket
        self.storage_uri = storage_uri or f"gs://{self.gcs_bucket}/veo_outputs"

        # Initialize Vertex AI genai client
        try:
            self.genai_client = genai.Client(
                vertexai=True,
                project=self.project_id,
                location=self.location
            )
            self.logger.info(f"Initialized Veo client: project={self.project_id}, location={self.location}")
        except Exception as e:
            self.logger.error(f"Failed to initialize Vertex AI client: {e}")
            raise ProviderError("veo", f"Vertex AI initialization failed: {e}")

        # Initialize GCS client for downloads
        try:
            self.storage_client = storage.Client(project=self.project_id)
            self.logger.info(f"Initialized GCS client with bucket: {self.gcs_bucket}")
        except Exception as e:
            self.logger.error(f"Failed to initialize GCS client: {e}")
            raise ProviderError("veo", f"GCS initialization failed: {e}")

    async def generate_video(
        self,
        prompt: str,
        negative_prompt: str = "",
        duration: int = 8,
        aspect_ratio: str = "16:9",
        model: Literal["veo-2.0-generate-001", "veo-3.0-generate-preview"] = "veo-3.0-generate-preview",
        num_videos: int = 1,
        poll_interval: int = 15,
    ) -> str:
        """
        Generate video using Vertex AI Veo.
        
        Args:
            prompt: Video generation prompt
            negative_prompt: Things to avoid in generation
            duration: Video duration in seconds (max 8 for Veo 2.0)
            aspect_ratio: Video aspect ratio ("16:9", "9:16", "1:1")
            model: Veo model version
            num_videos: Number of videos to generate
            poll_interval: Seconds between status checks
            
        Returns:
            GCS URI of generated video
            
        Raises:
            ProviderError: If generation fails
        """
        try:
            # Normalize duration to supported values
            normalized_duration = self.normalize_duration(duration)
            if normalized_duration != duration:
                self.logger.warning(
                    f"Duration {duration}s not supported, using {normalized_duration}s instead. "
                    f"Supported durations: [4, 6, 8] seconds"
                )

            self.logger.info(f"Generating video with Veo {model} (duration: {normalized_duration}s)")
            self.logger.debug(f"Prompt: {prompt[:200]}...")

            # Call Veo API
            operation = self.genai_client.models.generate_videos(
                model=model,
                prompt=prompt,
                config=types.GenerateVideosConfig(
                    negative_prompt=negative_prompt,
                    aspect_ratio=aspect_ratio,
                    duration_seconds=normalized_duration,
                    number_of_videos=num_videos,
                    person_generation="allow_adult",
                    output_gcs_uri=self.storage_uri
                )
            )

            # Poll for completion
            self.logger.info("Video generation started, polling for completion...")
            while not operation.done:
                time.sleep(poll_interval)
                operation = self.genai_client.operations.get(operation)
                self.logger.debug(f"[{time.strftime('%X')}] Video generation in progress...")

            # Check result
            if operation.response:
                video_uris = operation.result.generated_videos
                self.logger.info("✅ Video generated successfully")

                # Extract URI
                if isinstance(video_uris, list) and len(video_uris) > 0:
                    uri = video_uris[0].video.uri
                else:
                    uri = video_uris.video.uri

                self.logger.info(f"Video saved at: {uri}")
                return uri

            if operation.error:
                # Handle different error formats
                if hasattr(operation.error, "message"):
                    error_message = operation.error.message
                elif isinstance(operation.error, dict):
                    error_message = operation.error.get("message", str(operation.error))
                else:
                    error_message = str(operation.error)

                error_msg = f"Veo generation failed: {error_message}"
                self.logger.error(error_msg)
                raise ProviderError("veo", error_msg)

            raise ProviderError("veo", "Video generation finished with unknown state")

        except gcp_exceptions.GoogleAPICallError as e:
            self.logger.error(f"GCP API error: {e}")
            raise ProviderError("veo", f"GCP API error: {e}")
        except Exception as e:
            self.logger.error(f"Video generation failed: {e}")
            raise ProviderError("veo", f"Video generation failed: {e}")

    async def download_video(self, video_uri: str, output_path: Path) -> Path:
        """
        Download video from GCS URI.
        
        Args:
            video_uri: GCS URI (gs://bucket/path)
            output_path: Local path to save video
            
        Returns:
            Path to downloaded video
            
        Raises:
            ProviderError: If download fails
        """
        try:
            self.logger.info(f"Downloading video from: {video_uri}")

            # Parse GCS URI
            if not video_uri.startswith("gs://"):
                raise ValueError(f"Invalid GCS URI: {video_uri}")

            if "/" not in video_uri[5:]:
                raise ValueError(f"GCS URI must include path: {video_uri}")

            # Remove gs:// prefix and split bucket/path
            bucket_name, blob_path = video_uri[5:].split("/", 1)

            # Download from GCS
            bucket = self.storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_path)

            output_path.parent.mkdir(parents=True, exist_ok=True)
            blob.download_to_filename(str(output_path))

            self.logger.info(f"✅ Video downloaded to: {output_path}")
            return output_path

        except Exception as e:
            self.logger.error(f"Video download failed: {e}")
            raise ProviderError("veo", f"Video download failed: {e}")

    async def upload_to_gcs(self, local_path: Path, gcs_uri: str) -> str:
        """
        Upload local file to GCS.
        
        Args:
            local_path: Path to local file
            gcs_uri: Target GCS URI (gs://bucket/path/filename)
            
        Returns:
            GCS URI of uploaded file
            
        Raises:
            ProviderError: If upload fails
        """
        try:
            local_path = Path(local_path).expanduser().resolve()

            if not local_path.exists():
                raise FileNotFoundError(f"Local file not found: {local_path}")

            if not gcs_uri.startswith("gs://") or "/" not in gcs_uri[5:]:
                raise ValueError(f'GCS URI must be in format "gs://bucket/path": {gcs_uri}')

            # Parse GCS URI
            bucket_name, blob_name = gcs_uri[5:].split("/", 1)

            # Upload to GCS
            bucket = self.storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)

            self.logger.info(f"📤 Uploading {local_path} → {gcs_uri}")
            blob.upload_from_filename(str(local_path))

            self.logger.info("✅ File uploaded successfully")
            return gcs_uri

        except Exception as e:
            self.logger.error(f"File upload failed: {e}")
            raise ProviderError("veo", f"GCS upload failed: {e}")

    async def download_multiple_videos(
        self,
        video_uris: list[str],
        output_dir: Path
    ) -> list[Path]:
        """
        Download multiple videos from GCS URIs.
        
        Args:
            video_uris: List of GCS URIs
            output_dir: Local directory to save videos
            
        Returns:
            List of paths to downloaded videos
            
        Raises:
            ProviderError: If any download fails
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        local_paths: list[Path] = []

        for uri in video_uris:
            try:
                if not uri.startswith("gs://") or "/" not in uri[5:]:
                    self.logger.warning(f"Skipping malformed URI: {uri}")
                    continue

                # Use blob basename as local filename
                bucket_name, blob_path = uri[5:].split("/", 1)
                local_path = output_dir / Path(blob_path).name

                # Download
                bucket = self.storage_client.bucket(bucket_name)
                blob = bucket.blob(blob_path)

                self.logger.info(f"📥 Downloading {uri}")
                blob.download_to_filename(str(local_path))

                local_paths.append(local_path)

            except Exception as e:
                self.logger.error(f"Failed to download {uri}: {e}")
                # Continue with other downloads

        self.logger.info(f"✅ Downloaded {len(local_paths)}/{len(video_uris)} videos")
        return local_paths

    async def generate_and_download(
        self,
        prompt: str,
        output_path: Path,
        negative_prompt: str = "",
        duration: int = 8,
        aspect_ratio: str = "16:9",
        model: Literal["veo-2.0-generate-001", "veo-3.0-generate-preview"] = "veo-3.0-generate-preview",
    ) -> Path:
        """
        Generate video and automatically download it.
        
        Args:
            prompt: Video generation prompt
            output_path: Where to save the downloaded video
            negative_prompt: Negative prompt
            duration: Video duration
            aspect_ratio: Aspect ratio
            model: Veo model version
            
        Returns:
            Path to downloaded video file
            
        Raises:
            ProviderError: If generation or download fails
        """
        # Generate video
        video_uri = await self.generate_video(
            prompt=prompt,
            negative_prompt=negative_prompt,
            duration=duration,
            aspect_ratio=aspect_ratio,
            model=model
        )

        # Download video
        return await self.download_video(video_uri, output_path)

