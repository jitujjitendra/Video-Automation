"""Main pipeline orchestrator for the AI Video Automation Agent."""

import asyncio
from typing import Any, Callable, Optional

from .agents.script_agent import ScriptAgent
from .services.gemini_service import GeminiService
from .utils.config import get_settings
from .utils.file_manager import FileManager


class PipelineStatus:
    """Represents the current status of a generation pipeline."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    COMING_SOON = "coming_soon"


class PipelineStep:
    """Represents a single step in the generation pipeline."""

    def __init__(self, name: str, description: str, order: int):
        self.name = name
        self.description = description
        self.order = order
        self.status = PipelineStatus.PENDING
        self.result: Optional[Any] = None
        self.error: Optional[str] = None
        self.progress_percent: int = 0

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "order": self.order,
            "status": self.status,
            "progress_percent": self.progress_percent,
            "error": self.error,
        }


class Orchestrator:
    """Orchestrates the complete video generation pipeline.

    Manages the flow from idea to final video, coordinating
    between different agents and services.
    """

    def __init__(self, api_key: str):
        """Initialize the orchestrator with required services.

        Args:
            api_key: Gemini API key for AI services.
        """
        self.gemini_service = GeminiService(api_key)
        self.script_agent = ScriptAgent(self.gemini_service)
        self.file_manager = FileManager()
        self.settings = get_settings()

        # Pipeline steps
        self.steps = [
            PipelineStep("script_generation", "Generating script and screenplay", 1),
            PipelineStep("visual_generation", "Generating visual content", 2),
            PipelineStep("audio_generation", "Generating audio and music", 3),
            PipelineStep("lipsync", "Applying lip synchronization", 4),
            PipelineStep("editing", "Assembling final video", 5),
        ]

    async def run_pipeline(
        self,
        idea: str,
        language: str = "English",
        music_type: str = "song",
        video_style: str = "realistic",
        lipsync: bool = False,
        task_id: str = "",
        progress_callback: Optional[Callable] = None,
    ) -> dict[str, Any]:
        """Run the complete video generation pipeline.

        Args:
            idea: User's creative idea/concept.
            language: Target language (Hindi, English, Hinglish).
            music_type: "song" or "voiceover" (background music + voiceover).
            video_style: "realistic", "animated", or "mixed".
            lipsync: Whether to apply lip synchronization.
            task_id: Unique task identifier.
            progress_callback: Async callback for progress updates.

        Returns:
            Dictionary with pipeline results and status.
        """
        # Create task directory
        if not task_id:
            task_id, _ = self.file_manager.create_task_directory()
        else:
            self.file_manager.create_task_directory(task_id)

        result = {
            "task_id": task_id,
            "status": PipelineStatus.IN_PROGRESS,
            "idea": idea,
            "language": language,
            "music_type": music_type,
            "video_style": video_style,
            "lipsync": lipsync,
            "steps": {},
            "output": None,
        }

        # Determine content type
        content_type = "song" if music_type == "song" else "story"

        try:
            # Step 1: Script Generation (IMPLEMENTED)
            await self._update_progress(progress_callback, task_id, 0, PipelineStatus.IN_PROGRESS)
            script_result = await self._run_script_generation(
                idea, language, content_type, task_id, progress_callback
            )
            result["steps"]["script_generation"] = script_result

            # Step 2: Visual Generation (COMING SOON)
            await self._update_progress(progress_callback, task_id, 1, PipelineStatus.COMING_SOON)
            result["steps"]["visual_generation"] = {
                "status": PipelineStatus.COMING_SOON,
                "message": "Visual generation with Veo 3.1 - Coming in Phase 3",
            }

            # Step 3: Audio Generation (COMING SOON)
            await self._update_progress(progress_callback, task_id, 2, PipelineStatus.COMING_SOON)
            result["steps"]["audio_generation"] = {
                "status": PipelineStatus.COMING_SOON,
                "message": "Audio generation with Edge TTS - Coming in Phase 3",
            }

            # Step 4: Lip Sync (COMING SOON)
            if lipsync:
                await self._update_progress(progress_callback, task_id, 3, PipelineStatus.COMING_SOON)
                result["steps"]["lipsync"] = {
                    "status": PipelineStatus.COMING_SOON,
                    "message": "Lip sync with Wav2Lip - Coming in Phase 4",
                }
            else:
                result["steps"]["lipsync"] = {
                    "status": "skipped",
                    "message": "Lip sync disabled by user",
                }

            # Step 5: Editing (COMING SOON)
            await self._update_progress(progress_callback, task_id, 4, PipelineStatus.COMING_SOON)
            result["steps"]["editing"] = {
                "status": PipelineStatus.COMING_SOON,
                "message": "Auto editing with FFmpeg - Coming in Phase 4",
            }

            result["status"] = PipelineStatus.COMPLETED

        except Exception as e:
            result["status"] = PipelineStatus.FAILED
            result["error"] = str(e)

        # Save final result
        self.file_manager.save_json(task_id, "pipeline_result.json", result)

        return result

    async def _run_script_generation(
        self,
        idea: str,
        language: str,
        content_type: str,
        task_id: str,
        progress_callback: Optional[Callable] = None,
    ) -> dict[str, Any]:
        """Run the script generation step.

        Args:
            idea: User's creative idea.
            language: Target language.
            content_type: "song" or "story".
            task_id: Task identifier.
            progress_callback: Progress callback function.

        Returns:
            Script generation results.
        """
        step = self.steps[0]
        step.status = PipelineStatus.IN_PROGRESS

        try:
            # Sub-step 1: Generate content (lyrics or story)
            if progress_callback:
                await progress_callback({
                    "task_id": task_id,
                    "step": step.name,
                    "sub_step": "generating_content",
                    "message": f"Creating {content_type} from your idea...",
                    "progress_percent": 10,
                })

            if content_type == "song":
                content = await self.script_agent.generate_song_lyrics(idea, language)
            else:
                content = await self.script_agent.generate_story(idea, language)

            # Sub-step 2: Generate screenplay
            if progress_callback:
                await progress_callback({
                    "task_id": task_id,
                    "step": step.name,
                    "sub_step": "generating_screenplay",
                    "message": "Converting to visual screenplay...",
                    "progress_percent": 40,
                })

            screenplay = await self.script_agent.generate_screenplay(
                content, content_type, language
            )

            # Sub-step 3: Enhance scene descriptions
            if progress_callback:
                await progress_callback({
                    "task_id": task_id,
                    "step": step.name,
                    "sub_step": "enhancing_scenes",
                    "message": "Enhancing visual descriptions for each scene...",
                    "progress_percent": 70,
                })

            enhanced = await self.script_agent.generate_scene_descriptions(screenplay)

            # Save results
            self.file_manager.save_json(task_id, "scripts/content.json", content)
            self.file_manager.save_json(task_id, "scripts/screenplay.json", enhanced)

            step.status = PipelineStatus.COMPLETED
            step.progress_percent = 100

            if progress_callback:
                await progress_callback({
                    "task_id": task_id,
                    "step": step.name,
                    "sub_step": "completed",
                    "message": "Script generation complete!",
                    "progress_percent": 100,
                    "result": {
                        "title": content.get("title", "Untitled"),
                        "total_scenes": len(enhanced.get("scenes", [])),
                        "content_type": content_type,
                    },
                })

            return {
                "status": PipelineStatus.COMPLETED,
                "content": content,
                "screenplay": enhanced,
            }

        except Exception as e:
            step.status = PipelineStatus.FAILED
            step.error = str(e)

            if progress_callback:
                await progress_callback({
                    "task_id": task_id,
                    "step": step.name,
                    "sub_step": "error",
                    "message": f"Script generation failed: {str(e)}",
                    "progress_percent": 0,
                    "error": str(e),
                })

            return {
                "status": PipelineStatus.FAILED,
                "error": str(e),
            }

    async def _update_progress(
        self,
        callback: Optional[Callable],
        task_id: str,
        step_index: int,
        status: str,
    ) -> None:
        """Update progress for a pipeline step.

        Args:
            callback: Progress callback function.
            task_id: Task identifier.
            step_index: Index of the current step.
            status: New status for the step.
        """
        if step_index < len(self.steps):
            step = self.steps[step_index]
            step.status = status

            if callback:
                await callback({
                    "task_id": task_id,
                    "step": step.name,
                    "sub_step": "status_update",
                    "message": step.description,
                    "status": status,
                    "progress_percent": 100 if status == PipelineStatus.COMPLETED else 0,
                })

    def get_pipeline_status(self) -> list[dict]:
        """Get current status of all pipeline steps."""
        return [step.to_dict() for step in self.steps]
