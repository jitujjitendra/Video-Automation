"""Edge TTS service for text-to-speech generation.

Provides text-to-speech functionality using the edge-tts library.
Supports multiple voices and languages including Hindi, English, and Hinglish.
"""

import asyncio
import json
import struct
import wave
from pathlib import Path
from typing import Optional

try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False


class TTSService:
    """Text-to-Speech service using Microsoft Edge TTS.

    Generates high-quality speech audio from text using edge-tts.
    Supports word-level timestamps for lip sync alignment.
    """

    def __init__(self):
        """Initialize TTS service."""
        self.supported_languages = ["hi", "en", "hi-en"]
        self.default_voices = {
            "hi": "hi-IN-MadhurNeural",
            "en": "en-US-AriaNeural",
            "hi-en": "hi-IN-MadhurNeural",
        }

    async def generate_speech(
        self,
        text: str,
        output_path: Path,
        voice: Optional[str] = None,
        rate: str = "+0%",
        pitch: str = "+0Hz",
    ) -> Path:
        """Generate speech audio from text using edge-tts.

        Args:
            text: Text to convert to speech.
            output_path: Path to save the output audio file (.mp3).
            voice: Voice name (e.g., 'en-US-AriaNeural'). Uses default if None.
            rate: Speech rate adjustment (e.g., '+10%', '-5%').
            pitch: Pitch adjustment (e.g., '+5Hz', '-2Hz').

        Returns:
            Path to the generated audio file.

        Raises:
            RuntimeError: If edge-tts is not available or generation fails.
        """
        if not EDGE_TTS_AVAILABLE:
            raise RuntimeError(
                "edge-tts library is not installed. "
                "Install it with: pip install edge-tts"
            )

        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        # Use default voice if not specified
        if not voice:
            voice = self.default_voices.get("en", "en-US-AriaNeural")

        # Ensure output directory exists
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        max_retries = 3
        last_error = None

        for attempt in range(max_retries):
            try:
                communicate = edge_tts.Communicate(
                    text=text,
                    voice=voice,
                    rate=rate,
                    pitch=pitch,
                )
                await communicate.save(str(output_path))

                if output_path.exists() and output_path.stat().st_size > 0:
                    return output_path

                raise RuntimeError("Generated audio file is empty")

            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)

        raise RuntimeError(
            f"Failed to generate speech after {max_retries} retries: {last_error}"
        )

    async def generate_speech_with_timing(
        self,
        text: str,
        output_path: Path,
        voice: Optional[str] = None,
    ) -> dict:
        """Generate speech with word-level timestamps for lip sync.

        Args:
            text: Text to convert to speech.
            output_path: Path to save the output audio file.
            voice: Voice name to use.

        Returns:
            Dictionary with 'audio_path' and 'word_timings' list.
        """
        if not EDGE_TTS_AVAILABLE:
            raise RuntimeError("edge-tts library is not installed.")

        if not voice:
            voice = self.default_voices.get("en", "en-US-AriaNeural")

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        word_timings = []

        communicate = edge_tts.Communicate(text=text, voice=voice)

        # Collect audio data and word boundaries
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
            elif chunk["type"] == "WordBoundary":
                word_timings.append({
                    "word": chunk["text"],
                    "offset_ms": chunk["offset"] // 10000,  # Convert from 100ns to ms
                    "duration_ms": chunk["duration"] // 10000,
                })

        # Save audio
        with open(output_path, "wb") as f:
            f.write(audio_data)

        return {
            "audio_path": str(output_path),
            "word_timings": word_timings,
        }

    async def list_voices(self, language_filter: Optional[str] = None) -> list[dict]:
        """List available voices, optionally filtered by language.

        Args:
            language_filter: Language code to filter by (e.g., 'hi', 'en').

        Returns:
            List of voice dictionaries with name, gender, and language info.
        """
        if not EDGE_TTS_AVAILABLE:
            # Return a static list if edge-tts is not available
            return self._get_default_voice_list(language_filter)

        try:
            voices = await edge_tts.list_voices()

            if language_filter:
                # Map short codes to locale prefixes
                locale_map = {
                    "hi": "hi-IN",
                    "en": "en-US",
                    "hi-en": "hi-IN",
                }
                locale_prefix = locale_map.get(language_filter, language_filter)
                voices = [
                    v for v in voices
                    if v.get("Locale", "").startswith(locale_prefix)
                ]

            return [
                {
                    "name": v.get("ShortName", ""),
                    "gender": v.get("Gender", ""),
                    "locale": v.get("Locale", ""),
                    "friendly_name": v.get("FriendlyName", ""),
                }
                for v in voices
            ]

        except Exception:
            return self._get_default_voice_list(language_filter)

    def get_audio_duration(self, file_path: Path) -> float:
        """Get the duration of an audio file in seconds.

        Supports .wav files directly. For .mp3, returns an estimate
        based on file size.

        Args:
            file_path: Path to the audio file.

        Returns:
            Duration in seconds.
        """
        file_path = Path(file_path)

        if not file_path.exists():
            return 0.0

        if file_path.suffix.lower() == ".wav":
            try:
                with wave.open(str(file_path), "rb") as wav_file:
                    frames = wav_file.getnframes()
                    rate = wav_file.getframerate()
                    return frames / float(rate)
            except Exception:
                return 0.0

        elif file_path.suffix.lower() == ".mp3":
            # Estimate duration from file size
            # Average mp3 bitrate ~128kbps = 16KB/s
            file_size = file_path.stat().st_size
            return file_size / 16000.0

        return 0.0

    def _get_default_voice_list(self, language_filter: Optional[str] = None) -> list[dict]:
        """Return a static default voice list when edge-tts is unavailable."""
        all_voices = [
            {"name": "hi-IN-MadhurNeural", "gender": "Male", "locale": "hi-IN", "friendly_name": "Madhur (Hindi, India)"},
            {"name": "hi-IN-SwaraNeural", "gender": "Female", "locale": "hi-IN", "friendly_name": "Swara (Hindi, India)"},
            {"name": "en-US-GuyNeural", "gender": "Male", "locale": "en-US", "friendly_name": "Guy (English, US)"},
            {"name": "en-US-AriaNeural", "gender": "Female", "locale": "en-US", "friendly_name": "Aria (English, US)"},
            {"name": "en-US-JennyNeural", "gender": "Female", "locale": "en-US", "friendly_name": "Jenny (English, US)"},
            {"name": "en-IN-NeerjaNeural", "gender": "Female", "locale": "en-IN", "friendly_name": "Neerja (English, India)"},
            {"name": "en-IN-PrabhatNeural", "gender": "Male", "locale": "en-IN", "friendly_name": "Prabhat (English, India)"},
        ]

        if language_filter:
            locale_map = {"hi": "hi-IN", "en": "en-US", "hi-en": "hi-IN"}
            locale_prefix = locale_map.get(language_filter, language_filter)
            all_voices = [v for v in all_voices if v["locale"].startswith(locale_prefix)]

        return all_voices
