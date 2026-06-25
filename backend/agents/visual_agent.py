"""Visual Agent - Generates optimized image and video prompts for AI generation.

Takes screenplay scenes and generates detailed prompts optimized for
AI image generation (Imagen/DALL-E) and video generation (Veo 3.1).
Uses Gemini to enhance and adapt prompts for specific visual styles.
"""

import json
from typing import Any, Callable, Optional

from ..services.gemini_service import GeminiService
from ..utils.file_manager import FileManager


# Style configurations for different visual approaches
STYLE_CONFIGS = {
    "realistic": {
        "tags": "photorealistic, 4K, cinematic lighting, detailed textures, natural colors",
        "negative": "cartoon, anime, drawing, sketch, low quality, blurry, distorted, watermark",
        "camera_style": "cinematic, shallow depth of field",
    },
    "animated": {
        "tags": "3D animation, Pixar style, vibrant colors, stylized, smooth rendering",
        "negative": "photorealistic, live action, grainy, low resolution, ugly, deformed",
        "camera_style": "dynamic, expressive angles",
    },
    "mixed": {
        "tags": "hybrid style, semi-realistic, artistic, detailed, high quality",
        "negative": "low quality, blurry, distorted, watermark, amateur",
        "camera_style": "creative, varied perspectives",
    },
}


class VisualAgent:
    """Agent responsible for generating visual prompts for each scene.

    Generates optimized prompts for AI image/video generation tools.
    The actual image/video generation happens externally (user copies
    prompts to Veo 3.1 / Imagen in Google AI Pro).
    """

    def __init__(self, gemini_service: Optional[GeminiService] = None):
        """Initialize Visual Agent.

        Args:
            gemini_service: Gemini API service for prompt enhancement.
        """
        self.gemini = gemini_service
        self.file_manager = FileManager()

    async def generate_visuals(
        self,
        screenplay: dict,
        style: str = "realistic",
        task_id: str = "",
        progress_callback: Optional[Callable] = None,
    ) -> dict[str, Any]:
        """Generate visual prompts for all scenes in the screenplay.

        Main method that processes each scene and generates optimized
        prompts for both image and video generation.

        Args:
            screenplay: Screenplay dictionary with scenes.
            style: Visual style ('realistic', 'animated', 'mixed').
            task_id: Task identifier for file storage.
            progress_callback: Async callback for progress updates.

        Returns:
            Dictionary with visual outputs per scene.
        """
        scenes = screenplay.get("scenes", [])
        total_scenes = len(scenes)

        if not scenes:
            return {"status": "error", "message": "No scenes found in screenplay"}

        style = style if style in STYLE_CONFIGS else "realistic"
        visual_outputs = []

        for i, scene in enumerate(scenes):
            scene_num = scene.get("scene_number", i + 1)
            progress_pct = int(((i + 1) / total_scenes) * 100)

            if progress_callback:
                await progress_callback({
                    "task_id": task_id,
                    "step": "visual_generation",
                    "sub_step": f"scene_{scene_num}",
                    "message": f"Generating visual prompts for scene {scene_num}/{total_scenes}...",
                    "progress_percent": progress_pct,
                })

            # Generate prompts for this scene
            scene_output = await self._generate_scene_prompts(scene, style)
            visual_outputs.append(scene_output)

        # Save visual prompts to task directory
        result = {
            "status": "completed",
            "style": style,
            "total_scenes": total_scenes,
            "visual_prompts": visual_outputs,
        }

        if task_id:
            self.file_manager.save_json(task_id, "visuals/prompts.json", result)

        return result

    async def _generate_scene_prompts(
        self, scene: dict, style: str
    ) -> dict[str, Any]:
        """Generate image and video prompts for a single scene.

        Args:
            scene: Scene dictionary from screenplay.
            style: Visual style to apply.

        Returns:
            Structured output with all prompts for this scene.
        """
        scene_num = scene.get("scene_number", 1)
        description = scene.get("description", "")
        visual_prompt = scene.get("visual_prompt", description)
        duration = scene.get("duration_seconds", 8)
        camera_movement = scene.get("camera_movement", "")
        transition = scene.get("transition", "cut")

        # Enhance the prompt for the specific style
        image_prompt = await self._enhance_prompt_for_style(
            visual_prompt, style, "image"
        )
        video_prompt = await self._enhance_prompt_for_style(
            visual_prompt, style, "video"
        )

        # Get negative prompt for the style
        negative_prompt = self._generate_negative_prompts(style)

        # Determine camera direction
        camera_direction = camera_movement or self._suggest_camera_direction(
            scene.get("scene_type", "")
        )

        return {
            "scene_number": scene_num,
            "image_prompt": image_prompt,
            "video_prompt": video_prompt,
            "negative_prompt": negative_prompt,
            "style_tags": STYLE_CONFIGS[style]["tags"],
            "camera_direction": camera_direction,
            "duration_seconds": duration,
            "transition": transition,
            "original_description": description,
        }

    async def _enhance_prompt_for_style(
        self, prompt: str, style: str, media_type: str = "image"
    ) -> str:
        """Use Gemini to enhance and adapt a prompt for a specific style.

        Args:
            prompt: Original visual prompt.
            style: Target style ('realistic', 'animated', 'mixed').
            media_type: 'image' or 'video'.

        Returns:
            Enhanced prompt string.
        """
        if not self.gemini:
            # If no Gemini service, apply basic enhancement
            style_config = STYLE_CONFIGS.get(style, STYLE_CONFIGS["realistic"])
            return f"{prompt}, {style_config['tags']}, {style_config['camera_style']}"

        style_config = STYLE_CONFIGS[style]

        if media_type == "video":
            enhancement_instruction = (
                "You are an expert at writing prompts for AI video generation (Veo 3.1). "
                "Enhance the given scene description into an optimal video generation prompt. "
                "Include specific details about motion, camera movement, timing, and atmosphere. "
                "Keep the prompt under 200 words. Return ONLY the enhanced prompt text, nothing else."
            )
        else:
            enhancement_instruction = (
                "You are an expert at writing prompts for AI image generation (Imagen/DALL-E). "
                "Enhance the given scene description into an optimal image generation prompt. "
                "Include specific details about composition, lighting, colors, and detail level. "
                "Keep the prompt under 150 words. Return ONLY the enhanced prompt text, nothing else."
            )

        enhancement_prompt = (
            f"Style: {style} ({style_config['tags']})\n"
            f"Camera style: {style_config['camera_style']}\n\n"
            f"Original scene description:\n{prompt}\n\n"
            f"Generate an enhanced {media_type} prompt for this scene."
        )

        try:
            enhanced = await self.gemini.generate_text(
                prompt=enhancement_prompt,
                system_instruction=enhancement_instruction,
                temperature=0.6,
            )
            return enhanced.strip()
        except Exception:
            # Fallback to basic enhancement if Gemini fails
            return f"{prompt}, {style_config['tags']}"

    def _generate_negative_prompts(self, style: str) -> str:
        """Return what to avoid for each style.

        Args:
            style: Visual style.

        Returns:
            Negative prompt string.
        """
        return STYLE_CONFIGS.get(style, STYLE_CONFIGS["realistic"])["negative"]

    @staticmethod
    def _suggest_camera_direction(scene_type: str) -> str:
        """Suggest camera direction based on scene type.

        Args:
            scene_type: Type of scene (intro, verse, chorus, etc.).

        Returns:
            Camera direction suggestion.
        """
        directions = {
            "intro": "slow zoom in, establishing shot",
            "verse": "medium shot, gentle pan left to right",
            "chorus": "dynamic movement, multiple angles, energetic cuts",
            "bridge": "close-up shots, slow dolly forward",
            "outro": "slow zoom out, wide establishing shot",
            "opening": "sweeping aerial shot, slow reveal",
            "rising_action": "tracking shot, following subject",
            "climax": "rapid cuts, dynamic angles, close-ups",
            "falling_action": "slow pullback, calming movement",
            "resolution": "static wide shot, peaceful composition",
        }
        return directions.get(scene_type, "smooth pan, medium shot")

    async def generate_image_prompts(
        self, screenplay: dict, style: str = "realistic"
    ) -> list[dict]:
        """Generate optimized image prompts for all scenes.

        Args:
            screenplay: Screenplay with scenes.
            style: Visual style.

        Returns:
            List of image prompt dictionaries.
        """
        scenes = screenplay.get("scenes", [])
        prompts = []

        for scene in scenes:
            visual = scene.get("visual_prompt", scene.get("description", ""))
            enhanced = await self._enhance_prompt_for_style(visual, style, "image")
            prompts.append({
                "scene_number": scene.get("scene_number", 0),
                "prompt": enhanced,
                "negative_prompt": self._generate_negative_prompts(style),
                "style_tags": STYLE_CONFIGS[style]["tags"],
            })

        return prompts

    async def generate_video_prompts(
        self, screenplay: dict, style: str = "realistic"
    ) -> list[dict]:
        """Generate optimized video prompts for Veo 3.1.

        Args:
            screenplay: Screenplay with scenes.
            style: Visual style.

        Returns:
            List of video prompt dictionaries.
        """
        scenes = screenplay.get("scenes", [])
        prompts = []

        for scene in scenes:
            visual = scene.get("visual_prompt", scene.get("description", ""))
            enhanced = await self._enhance_prompt_for_style(visual, style, "video")
            prompts.append({
                "scene_number": scene.get("scene_number", 0),
                "prompt": enhanced,
                "negative_prompt": self._generate_negative_prompts(style),
                "camera_direction": scene.get(
                    "camera_movement",
                    self._suggest_camera_direction(scene.get("scene_type", "")),
                ),
                "duration_seconds": scene.get("duration_seconds", 8),
            })

        return prompts
