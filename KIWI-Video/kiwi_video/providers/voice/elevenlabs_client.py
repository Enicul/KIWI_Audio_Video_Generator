"""ElevenLabs text-to-speech client with ASR support."""

import asyncio
import json
from pathlib import Path

import httpx
from elevenlabs import ElevenLabs as ElevenLabsSDK

from kiwi_video.core.exceptions import ProviderError
from kiwi_video.providers.voice.base import BaseVoiceProvider
from kiwi_video.utils.config import settings
from kiwi_video.utils.logger import get_logger


class ElevenLabsClient(BaseVoiceProvider):
    """
    ElevenLabs text-to-speech client implementation.
    """

    def __init__(
        self,
        api_key: str | None = None,
        voice_id: str | None = None
    ) -> None:
        """
        Initialize ElevenLabs client.

        Args:
            api_key: ElevenLabs API key (uses settings if not provided)
            voice_id: Default voice ID (uses settings if not provided)
        """
        self.api_key = api_key or settings.elevenlabs_api_key
        self.default_voice_id = voice_id or settings.elevenlabs_voice_id
        self.logger = get_logger("elevenlabs_client")

        # Initialize ElevenLabs SDK client
        self.sdk_client = ElevenLabsSDK(api_key=self.api_key)

        self.base_url = "https://api.elevenlabs.io/v1"
        self.headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }

    async def synthesize(
        self,
        text: str,
        voice_id: str | None = None,
        output_path: Path | None = None
    ) -> Path:
        """
        Synthesize speech from text.

        Args:
            text: Text to convert to speech
            voice_id: Voice ID (uses default if not provided)
            output_path: Path to save audio (generates if not provided)

        Returns:
            Path to generated audio file

        Raises:
            ProviderError: If synthesis fails
        """
        try:
            voice = voice_id or self.default_voice_id
            self.logger.info(f"Synthesizing speech with voice: {voice}")

            # Prepare request
            url = f"{self.base_url}/text-to-speech/{voice}"

            payload = {
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75
                }
            }

            # Make async request with longer timeout
            timeout = httpx.Timeout(120.0, connect=30.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=self.headers
                )

                response.raise_for_status()

                # Save audio file
                if output_path is None:
                    output_path = Path(f"speech_{voice}.mp3")

                output_path.parent.mkdir(parents=True, exist_ok=True)

                with open(output_path, "wb") as f:
                    f.write(response.content)

                self.logger.info(f"Speech synthesized: {output_path}")
                return output_path

        except httpx.HTTPError as e:
            self.logger.error(f"HTTP error during synthesis: {e}")
            raise ProviderError("elevenlabs", f"Synthesis failed: {e}")
        except Exception as e:
            self.logger.error(f"Synthesis failed: {e}")
            raise ProviderError("elevenlabs", f"Synthesis failed: {e}")

    async def get_voices(self) -> list:
        """
        Get list of available voices.

        Returns:
            List of voice dictionaries

        Raises:
            ProviderError: If request fails
        """
        try:
            url = f"{self.base_url}/voices"

            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()

                data = response.json()
                return data.get("voices", [])

        except Exception as e:
            self.logger.error(f"Failed to get voices: {e}")
            raise ProviderError("elevenlabs", f"Get voices failed: {e}")

    async def speech_to_text(
        self,
        audio_path: Path,
        output_path: Path | None = None,
        model_id: str = "scribe_v1",
        language_code: str = "eng",
        diarize: bool = True
    ) -> dict:
        """
        Convert speech to text with word-level timestamps (ASR).

        Args:
            audio_path: Path to audio file
            output_path: Path to save ASR JSON (generates if not provided)
            model_id: Scribe model ID
            language_code: ISO 639-3 language code
            diarize: Whether to perform speaker diarization

        Returns:
            Dictionary with ASR data including word-level timestamps

        Raises:
            ProviderError: If transcription fails
        """
        try:
            self.logger.info(f"Generating ASR for: {audio_path}")

            # Use ElevenLabs SDK for speech-to-text (run in thread since it's synchronous)
            def _call_sdk():
                with open(audio_path, "rb") as audio_file:
                    return self.sdk_client.speech_to_text.convert(
                        model_id=model_id,
                        file=audio_file,
                        diarize=diarize
                    )

            # Run SDK call in thread to avoid blocking
            asr_response = await asyncio.to_thread(_call_sdk)

            # Convert SDK response to dict
            asr_data = {
                "text": asr_response.text,
                "language_code": asr_response.language_code,
                "language_probability": asr_response.language_probability,
                "words": [
                    {
                        "text": word.text,
                        "start": word.start,
                        "end": word.end,
                        "type": word.type,
                        "speaker_id": getattr(word, "speaker_id", None),
                        "logprob": word.logprob
                    }
                    for word in asr_response.words
                ]
            }

            # Save ASR data
            if output_path:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(asr_data, f, indent=2, ensure_ascii=False)
                self.logger.info(f"ASR saved: {output_path}")

            return asr_data

        except Exception as e:
            self.logger.error(f"ASR failed: {e}")
            raise ProviderError("elevenlabs", f"ASR failed: {e}")

    # Synchronous wrappers for backward compatibility

    def synthesize_sync(
        self,
        text: str,
        voice_id: str | None = None,
        output_path: Path | None = None
    ) -> Path:
        """Synchronous wrapper for synthesize."""
        return asyncio.run(self.synthesize(text, voice_id, output_path))

    def speech_to_text_sync(
        self,
        audio_path: Path,
        output_path: Path | None = None,
        model_id: str = "scribe_v1",
        language_code: str = "eng",
        diarize: bool = True
    ) -> dict:
        """Synchronous wrapper for speech_to_text."""
        return asyncio.run(
            self.speech_to_text(audio_path, output_path, model_id, language_code, diarize)
        )

