"""Script Agent - Generates lyrics, stories, and screenplays using Gemini AI."""

import json
from pathlib import Path
from typing import Any

from ..services.gemini_service import GeminiService
from ..utils.file_manager import FileManager


class ScriptAgent:
    """Agent responsible for generating scripts, lyrics, stories, and screenplays.

    This agent uses Google Gemini to generate creative content based on
    user ideas and converts them into structured scene-by-scene screenplays.
    """

    def __init__(self, gemini_service: GeminiService):
        """Initialize Script Agent.

        Args:
            gemini_service: Initialized Gemini API service.
        """
        self.gemini = gemini_service
        self.file_manager = FileManager()

    async def generate_song_lyrics(self, idea: str, language: str = "English") -> dict[str, Any]:
        """Generate full song lyrics based on an idea.

        Args:
            idea: The user's song concept/idea.
            language: Target language (Hindi, English, or Hinglish).

        Returns:
            Dictionary with song title, lyrics, structure, and metadata.
        """
        system_instruction = (
            "You are a professional songwriter and lyricist. "
            "You write creative, emotionally resonant lyrics in the specified language. "
            "You always respond with properly structured JSON."
        )

        prompt = f"""Create complete song lyrics based on this idea: "{idea}"

Language: {language}

Generate a full song with the following JSON structure:
{{
    "title": "Song title",
    "language": "{language}",
    "genre": "Detected/suitable genre",
    "mood": "Overall mood",
    "bpm_suggestion": 120,
    "structure": [
        {{
            "section": "intro/verse1/chorus/verse2/bridge/outro",
            "lyrics": "The actual lyrics for this section",
            "mood": "Mood for this section",
            "duration_suggestion_seconds": 15
        }}
    ],
    "total_duration_seconds": 180,
    "notes": "Any additional notes about the song"
}}

Requirements:
- Make the lyrics creative, poetic, and emotionally engaging
- If language is Hindi, write in Devanagari script with romanized version
- If language is Hinglish, mix Hindi and English naturally
- Include at least 2 verses, 2 choruses, and a bridge
- Each section should have clear mood progression
- Suggest appropriate duration for each section"""

        result = await self.gemini.generate_json(
            prompt=prompt,
            system_instruction=system_instruction,
            temperature=0.8,
        )

        return result

    async def generate_story(self, idea: str, language: str = "English") -> dict[str, Any]:
        """Generate a narrative story based on an idea.

        Args:
            idea: The user's story concept/idea.
            language: Target language (Hindi, English, or Hinglish).

        Returns:
            Dictionary with story title, narrative, and structure.
        """
        system_instruction = (
            "You are a professional storyteller and screenwriter. "
            "You create compelling narratives with vivid imagery. "
            "You always respond with properly structured JSON."
        )

        prompt = f"""Create a compelling short story/narrative based on this idea: "{idea}"

Language: {language}

Generate a story with the following JSON structure:
{{
    "title": "Story title",
    "language": "{language}",
    "genre": "Genre of the story",
    "mood": "Overall mood",
    "synopsis": "One paragraph synopsis",
    "narrative": [
        {{
            "section": "opening/rising_action/climax/falling_action/resolution",
            "text": "The narrative text for this section",
            "mood": "Mood for this section",
            "duration_suggestion_seconds": 15
        }}
    ],
    "total_duration_seconds": 120,
    "narrator_voice_suggestion": "Male/Female, tone and style",
    "background_music_suggestion": "Type of background music"
}}

Requirements:
- Create a complete narrative arc with beginning, middle, and end
- Use vivid, visual language that translates well to video
- If language is Hindi, write in Devanagari with romanized version
- If Hinglish, mix naturally
- Keep total duration around 2-3 minutes when narrated
- Make it emotionally engaging and visually rich"""

        result = await self.gemini.generate_json(
            prompt=prompt,
            system_instruction=system_instruction,
            temperature=0.8,
        )

        return result

    async def generate_screenplay(
        self, content: dict[str, Any], content_type: str = "song", language: str = "English"
    ) -> dict[str, Any]:
        """Convert lyrics or story into a scene-by-scene screenplay.

        Args:
            content: The lyrics or story dictionary from previous generation.
            content_type: Either "song" or "story".
            language: Target language.

        Returns:
            Dictionary with structured scenes for video production.
        """
        system_instruction = (
            "You are a professional music video director and cinematographer. "
            "You create detailed visual screenplays that translate perfectly into video. "
            "Your scene descriptions are vivid, specific, and technically actionable. "
            "You always respond with properly structured JSON."
        )

        content_json = json.dumps(content, ensure_ascii=False, indent=2)

        prompt = f"""Convert this {content_type} into a detailed scene-by-scene screenplay for a music video/short film.

{content_type.title()} Content:
{content_json}

Language: {language}

Generate a screenplay with exactly this JSON structure:
{{
    "title": "{content.get('title', 'Untitled')}",
    "language": "{language}",
    "genre": "{content.get('genre', 'General')}",
    "mood": "{content.get('mood', 'Neutral')}",
    "total_duration_seconds": {content.get('total_duration_seconds', 120)},
    "scenes": [
        {{
            "scene_number": 1,
            "description": "Detailed description of what happens in this scene",
            "visual_prompt": "Highly detailed visual prompt for AI video generation. Include: setting, lighting, colors, camera angle, character description, movement, atmosphere. Be specific enough for an AI to generate this exact scene.",
            "audio_direction": "What audio plays during this scene - music mood, tempo, instruments, or specific lyrics/dialogue",
            "duration_seconds": 10,
            "dialogue": "Any voiceover narration or song lyrics for this scene",
            "scene_type": "intro/verse/chorus/bridge/outro OR opening/rising_action/climax/resolution",
            "transition": "cut/fade/dissolve/zoom - how to transition to next scene"
        }}
    ],
    "metadata": {{
        "total_scenes": 10,
        "visual_style": "Realistic/Animated/Mixed",
        "color_palette": "Dominant colors for the video",
        "camera_style": "Cinematic/Documentary/Music Video/etc"
    }}
}}

Requirements:
- Create 8-15 scenes that cover the entire {content_type}
- Each visual_prompt should be 2-3 sentences of vivid detail
- Include specific camera angles (close-up, wide shot, aerial, tracking)
- Describe lighting conditions (golden hour, neon, soft daylight, dramatic shadows)
- Include character actions and emotions
- Ensure smooth transitions between scenes
- Match audio direction to the visual mood
- Each scene should be 5-15 seconds for good pacing"""

        result = await self.gemini.generate_json(
            prompt=prompt,
            system_instruction=system_instruction,
            temperature=0.7,
        )

        return result

    async def generate_scene_descriptions(self, screenplay: dict[str, Any]) -> dict[str, Any]:
        """Enhance screenplay with detailed visual descriptions for each scene.

        Takes an existing screenplay and generates even more detailed
        visual prompts optimized for AI video/image generation.

        Args:
            screenplay: The screenplay dictionary from generate_screenplay.

        Returns:
            Enhanced screenplay with detailed visual descriptions.
        """
        system_instruction = (
            "You are an expert at writing prompts for AI image and video generation. "
            "You create highly detailed, technically specific visual descriptions. "
            "Your prompts always produce stunning, cinematic results. "
            "You always respond with properly structured JSON."
        )

        scenes_json = json.dumps(screenplay.get("scenes", []), ensure_ascii=False, indent=2)

        prompt = f"""Enhance these scene descriptions with ultra-detailed visual prompts optimized for AI video generation (Veo 3.1).

Current scenes:
{scenes_json}

For each scene, create an enhanced visual_prompt that includes ALL of these details:
- Environment: exact location, time of day, weather, architecture
- Lighting: direction, color temperature, shadows, highlights
- Camera: exact angle, lens type (wide/telephoto), movement (pan/tilt/dolly/crane)
- Characters: appearance, clothing, expression, body language, position in frame
- Colors: dominant colors, color grading style, contrast
- Atmosphere: particles (dust/rain/fog), depth of field, bokeh
- Motion: what moves and how, speed, direction

Return the enhanced scenes as JSON:
{{
    "scenes": [
        {{
            "scene_number": 1,
            "visual_prompt": "Enhanced ultra-detailed prompt...",
            "negative_prompt": "Things to avoid in generation",
            "camera_movement": "Specific camera movement description",
            "color_grading": "Color grading style"
        }}
    ]
}}"""

        enhanced = await self.gemini.generate_json(
            prompt=prompt,
            system_instruction=system_instruction,
            temperature=0.6,
        )

        # Merge enhanced descriptions back into the screenplay
        if "scenes" in enhanced:
            for enhanced_scene in enhanced["scenes"]:
                scene_num = enhanced_scene.get("scene_number", 0)
                for scene in screenplay.get("scenes", []):
                    if scene.get("scene_number") == scene_num:
                        scene["visual_prompt"] = enhanced_scene.get(
                            "visual_prompt", scene.get("visual_prompt", "")
                        )
                        scene["negative_prompt"] = enhanced_scene.get("negative_prompt", "")
                        scene["camera_movement"] = enhanced_scene.get("camera_movement", "")
                        scene["color_grading"] = enhanced_scene.get("color_grading", "")
                        break

        return screenplay

    async def run_full_pipeline(
        self,
        idea: str,
        language: str = "English",
        content_type: str = "song",
        task_id: str = "",
    ) -> dict[str, Any]:
        """Run the complete script generation pipeline.

        Args:
            idea: User's creative idea.
            language: Target language.
            content_type: "song" or "story".
            task_id: Task ID for file storage.

        Returns:
            Complete script output with all stages.
        """
        result = {
            "task_id": task_id,
            "idea": idea,
            "language": language,
            "content_type": content_type,
            "stages": {},
        }

        # Stage 1: Generate content (lyrics or story)
        if content_type == "song":
            content = await self.generate_song_lyrics(idea, language)
        else:
            content = await self.generate_story(idea, language)

        result["stages"]["content"] = content

        # Stage 2: Generate screenplay
        screenplay = await self.generate_screenplay(content, content_type, language)
        result["stages"]["screenplay"] = screenplay

        # Stage 3: Enhance scene descriptions
        enhanced = await self.generate_scene_descriptions(screenplay)
        result["stages"]["enhanced_screenplay"] = enhanced

        # Save results
        if task_id:
            self.file_manager.save_json(task_id, "scripts/full_script.json", result)
            self.file_manager.save_json(task_id, "scripts/screenplay.json", enhanced)

        return result
