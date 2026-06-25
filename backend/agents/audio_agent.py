"""Audio Agent - Handles TTS voiceover and music guidance generation.

Generates voiceover audio using Edge TTS for each scene's dialogue/lyrics.
Also provides guidance for background music and Suno AI integration.
"""

import asyncio
from pathlib import Path
from typing import Any, Callable, Optional

from ..services.tts_service import TTSService
from ..utils.file_manager import FileManager


# Voice mapping for different languages and genders
VOICE_MAP = {
    "Hindi": {
        "male": "hi-IN-MadhurNeural",
        "female": "hi-IN-SwaraNeural",
    },
    "English": {
        "male": "en-US-GuyNeural",
        "female": "en-US-AriaNeural",
    },
    "Hinglish": {
        "male": "hi-IN-MadhurNeural",
        "female": "hi-IN-SwaraNeural",
    },
}


class AudioAgent:
    """Agent responsible for generating audio content.

    Generates voiceover audio using Edge TTS and provides
    guidance for background music generation via Suno AI.
    """

    def __init__(self, tts_service: Optional[TTSService] = None):
        """Initialize Audio Agent.

        Args:
            tts_service: TTS service for voice generation.
        """
        self.tts_service = tts_service or TTSService()
        self.file_manager = FileManager()

    def select_voice(self, language: str, gender: str = "female") -> str:
        """Select the best voice for a given language and gender.

        Args:
            language: Target language ('Hindi', 'English', 'Hinglish').
            gender: Preferred gender ('male' or 'female').

        Returns:
            Voice identifier string.
        """
        lang_voices = VOICE_MAP.get(language, VOICE_MAP["English"])
        return lang_voices.get(gender, lang_voices["female"])

    async def list_available_voices(self, language: str = "English") -> list[dict]:
        """List all available voices for a language.

        Args:
            language: Language to list voices for.

        Returns:
            List of voice information dictionaries.
        """
        # Map language name to locale code
        lang_map = {
            "Hindi": "hi",
            "English": "en",
            "Hinglish": "hi",
        }
        lang_code = lang_map.get(language, "en")
        return await self.tts_service.list_voices(lang_code)

    async def generate_scene_audio(
        self,
        scene_text: str,
        voice: str,
        output_path: Path,
    ) -> dict[str, Any]:
        """Generate audio for a single scene's dialogue/lyrics.

        Args:
            scene_text: Text content (dialogue or lyrics) for the scene.
            voice: Voice identifier to use.
            output_path: Path to save the generated audio file.

        Returns:
            Dictionary with audio path and duration info.
        """
        output_path = Path(output_path)

        if not scene_text or not scene_text.strip():
            return {
                "status": "skipped",
                "reason": "No dialogue/lyrics for this scene",
                "audio_path": None,
                "duration_seconds": 0,
            }

        try:
            audio_path = await self.tts_service.generate_speech(
                text=scene_text.strip(),
                output_path=output_path,
                voice=voice,
            )

            duration = self.tts_service.get_audio_duration(audio_path)

            return {
                "status": "completed",
                "audio_path": str(audio_path),
                "duration_seconds": duration,
            }

        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "audio_path": None,
                "duration_seconds": 0,
            }

    async def generate_voiceover(
        self,
        scenes: list[dict],
        language: str = "English",
        voice: Optional[str] = None,
        task_id: str = "",
        progress_callback: Optional[Callable] = None,
    ) -> dict[str, Any]:
        """Generate voiceover audio for all scenes.

        Args:
            scenes: List of scene dictionaries with dialogue/lyrics.
            language: Target language for voice selection.
            voice: Specific voice to use (auto-selected if None).
            task_id: Task identifier.
            progress_callback: Async callback for progress updates.

        Returns:
            Dictionary with audio outputs per scene.
        """
        if not voice:
            voice = self.select_voice(language)

        total_scenes = len(scenes)
        audio_outputs = []
        task_dir = self.file_manager.get_task_dir(task_id) if task_id else Path("outputs")
        audio_dir = task_dir / "audio"
        audio_dir.mkdir(parents=True, exist_ok=True)

        for i, scene in enumerate(scenes):
            scene_num = scene.get("scene_number", i + 1)
            dialogue = scene.get("dialogue", "")
            progress_pct = int(((i + 1) / total_scenes) * 100)

            if progress_callback:
                await progress_callback({
                    "task_id": task_id,
                    "step": "audio_generation",
                    "sub_step": f"scene_{scene_num}",
                    "message": f"Generating voiceover for scene {scene_num}/{total_scenes}...",
                    "progress_percent": progress_pct,
                })

            output_path = audio_dir / f"scene_{scene_num:02d}.mp3"
            result = await self.generate_scene_audio(dialogue, voice, output_path)
            result["scene_number"] = scene_num
            audio_outputs.append(result)

        return {
            "status": "completed",
            "voice_used": voice,
            "language": language,
            "total_scenes": total_scenes,
            "audio_files": audio_outputs,
        }

    async def generate_full_audio(
        self,
        screenplay: dict,
        language: str = "English",
        music_type: str = "voiceover",
        voice: Optional[str] = None,
        task_id: str = "",
        progress_callback: Optional[Callable] = None,
    ) -> dict[str, Any]:
        """Main audio pipeline method - generates all audio content.

        Args:
            screenplay: Full screenplay dictionary.
            language: Target language.
            music_type: 'voiceover' for TTS narration, 'song' for Suno guide.
            voice: Specific voice (auto-selected if None).
            task_id: Task identifier.
            progress_callback: Async callback for progress updates.

        Returns:
            Complete audio generation results.
        """
        scenes = screenplay.get("scenes", [])

        if not scenes:
            return {"status": "error", "message": "No scenes found in screenplay"}

        result = {
            "status": "completed",
            "language": language,
            "music_type": music_type,
        }

        if music_type == "voiceover":
            # Generate TTS voiceover for narration/dialogue
            voiceover_result = await self.generate_voiceover(
                scenes=scenes,
                language=language,
                voice=voice,
                task_id=task_id,
                progress_callback=progress_callback,
            )
            result["voiceover"] = voiceover_result

            # Generate background music suggestions
            result["music_suggestion"] = self._suggest_background_music(screenplay)

        elif music_type == "song":
            # For song mode: generate guide for Suno AI + provide lyrics with TTS
            if progress_callback:
                await progress_callback({
                    "task_id": task_id,
                    "step": "audio_generation",
                    "sub_step": "suno_guide",
                    "message": "Generating Suno AI guide and TTS preview...",
                    "progress_percent": 10,
                })

            # Generate TTS preview of lyrics
            voiceover_result = await self.generate_voiceover(
                scenes=scenes,
                language=language,
                voice=voice,
                task_id=task_id,
                progress_callback=progress_callback,
            )
            result["voiceover"] = voiceover_result

            # Generate Suno AI guidance
            result["suno_guide"] = self._generate_suno_guide(screenplay, language)

        # Save results
        if task_id:
            self.file_manager.save_json(task_id, "audio/audio_result.json", result)

        return result

    def _suggest_background_music(self, screenplay: dict) -> dict[str, Any]:
        """Suggest background music based on screenplay mood.

        Args:
            screenplay: Screenplay dictionary.

        Returns:
            Music suggestion dictionary.
        """
        mood = screenplay.get("mood", "neutral")
        genre = screenplay.get("genre", "general")

        mood_music_map = {
            "happy": "Upbeat acoustic guitar, light percussion, major key",
            "sad": "Soft piano, strings, minor key, slow tempo",
            "romantic": "Gentle strings, soft guitar, warm pad synths",
            "energetic": "Electronic beats, driving bass, fast tempo",
            "mysterious": "Dark ambient pads, subtle percussion, minor key",
            "epic": "Full orchestra, powerful drums, rising crescendo",
            "peaceful": "Ambient nature sounds, soft piano, minimal",
            "dramatic": "Intense strings, timpani, dynamic contrasts",
        }

        suggestion = mood_music_map.get(
            mood.lower(),
            "Ambient background music matching the scene mood"
        )

        return {
            "mood": mood,
            "genre": genre,
            "suggestion": suggestion,
            "recommended_sources": [
                "Pixabay Music (free)",
                "YouTube Audio Library (free)",
                "Epidemic Sound (subscription)",
                "Suno AI (AI-generated)",
            ],
        }

    def _generate_suno_guide(self, screenplay: dict, language: str) -> dict[str, Any]:
        """Generate a guide for using Suno AI to create the song.

        Args:
            screenplay: Screenplay dictionary.
            language: Target language.

        Returns:
            Suno AI guide dictionary.
        """
        mood = screenplay.get("mood", "neutral")
        genre = screenplay.get("genre", "pop")
        scenes = screenplay.get("scenes", [])

        # Collect all lyrics
        lyrics_parts = []
        for scene in scenes:
            dialogue = scene.get("dialogue", "")
            if dialogue:
                section = scene.get("scene_type", "verse")
                lyrics_parts.append(f"[{section.upper()}]\n{dialogue}")

        full_lyrics = "\n\n".join(lyrics_parts)

        # Calculate tempo from scene durations
        total_duration = sum(s.get("duration_seconds", 8) for s in scenes)
        estimated_bpm = 120  # Default

        return {
            "platform": "Suno AI (suno.com)",
            "instructions": (
                "1. Go to suno.com and create an account\n"
                "2. Click 'Create' and select 'Custom'\n"
                "3. Paste the lyrics below\n"
                "4. Set the style/genre tags\n"
                "5. Generate and download the song"
            ),
            "lyrics": full_lyrics,
            "style_tags": f"{genre}, {mood}, {language.lower()}",
            "mood": mood,
            "genre": genre,
            "estimated_bpm": estimated_bpm,
            "total_duration_seconds": total_duration,
            "language": language,
        }
