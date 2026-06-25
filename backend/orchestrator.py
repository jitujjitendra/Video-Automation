"""Main pipeline orchestrator for the AI Video Automation Agent.

Coordinates the full video generation pipeline from idea to final output.
Manages all agents (Script, Visual, Audio, LipSync, Editor) and handles
progress reporting, error recovery, and graceful degradation.
"""

import asyncio
from pathlib import Path
from typing import Any, Callable, Optional

from .agents.script_agent import ScriptAgent
from .agents.visual_agent import VisualAgent
from .agents.audio_agent import AudioAgent
from .agents.lipsync_agent import LipsyncAgent
from .agents.editor_agent import EditorAgent
from .services.gemini_service import GeminiService
from .services.tts_service import TTSService
from .services.ffmpeg_service import FFmpegService
from .services.colab_service import ColabService
from .utils.config import get_settings
from .utils.file_manager import FileManager


class PipelineStatus:
    """Represents the current status of a generation pipeline."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"
    SKIPPED = "skipped"


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
    between all agents and services. Handles errors gracefully
    so partial results are still available if later steps fail.
    """

    def __init__(self, api_key: str):
        """Initialize the orchestrator with required services.

        Args:
            api_key: Gemini API key for AI services.
        """
        # Services
        self.gemini_service = GeminiService(api_key)
        self.tts_service = TTSService()
        self.ffmpeg_service = FFmpegService()
        self.colab_service = ColabService()

        # Agents
        self.script_agent = ScriptAgent(self.gemini_service)
        self.visual_agent = VisualAgent(self.gemini_service)
        self.audio_agent = AudioAgent(self.tts_service)
        self.lipsync_agent = LipsyncAgent(self.colab_service)
        self.editor_agent = EditorAgent(self.ffmpeg_service)

        # Utilities
        self.file_manager = FileManager()
        self.settings = get_settings()

        # Pipeline steps
        self.steps = [
            PipelineStep("script_generation", "Generating script and screenplay", 1),
            PipelineStep("visual_generation", "Generating visual prompts", 2),
            PipelineStep("audio_generation", "Generating audio and voiceover", 3),
            PipelineStep("lipsync", "Preparing lip synchronization", 4),
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
            music_type: "song" or "voiceover".
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

        # Track outputs from each step for downstream use
        screenplay = None
        visual_outputs = None
        audio_outputs = None
        lipsync_outputs = None

        try:
            # === Step 1: Script Generation ===
            await self._update_progress(
                progress_callback, task_id, 0, PipelineStatus.IN_PROGRESS
            )
            script_result = await self._run_script_generation(
                idea, language, content_type, task_id, progress_callback
            )
            result["steps"]["script_generation"] = script_result

            if script_result.get("status") == PipelineStatus.COMPLETED:
                screenplay = script_result.get("screenplay")
            else:
                # Cannot continue without a script
                result["status"] = PipelineStatus.FAILED
                result["error"] = "Script generation failed"
                self.file_manager.save_json(task_id, "pipeline_result.json", result)
                return result

            # === Step 2: Visual Generation ===
            await self._update_progress(
                progress_callback, task_id, 1, PipelineStatus.IN_PROGRESS
            )
            visual_result = await self._run_visual_generation(
                screenplay, video_style, task_id, progress_callback
            )
            result["steps"]["visual_generation"] = visual_result
            if visual_result.get("status") == PipelineStatus.COMPLETED:
                visual_outputs = visual_result.get("data", {})

            # === Step 3: Audio Generation ===
            await self._update_progress(
                progress_callback, task_id, 2, PipelineStatus.IN_PROGRESS
            )
            audio_result = await self._run_audio_generation(
                screenplay, language, music_type, task_id, progress_callback
            )
            result["steps"]["audio_generation"] = audio_result
            if audio_result.get("status") == PipelineStatus.COMPLETED:
                audio_outputs = audio_result.get("data", {})

            # === Step 4: Lip Sync ===
            if lipsync:
                await self._update_progress(
                    progress_callback, task_id, 3, PipelineStatus.IN_PROGRESS
                )
                lipsync_result = await self._run_lipsync(
                    audio_outputs, task_id, progress_callback
                )
                result["steps"]["lipsync"] = lipsync_result
                if lipsync_result.get("status") == PipelineStatus.COMPLETED:
                    lipsync_outputs = lipsync_result.get("data", {})
            else:
                result["steps"]["lipsync"] = {
                    "status": PipelineStatus.SKIPPED,
                    "message": "Lip sync disabled by user",
                }
                await self._update_progress(
                    progress_callback, task_id, 3, PipelineStatus.SKIPPED
                )

            # === Step 5: Editing/Assembly ===
            await self._update_progress(
                progress_callback, task_id, 4, PipelineStatus.IN_PROGRESS
            )
            editing_result = await self._run_editing(
                visual_outputs, audio_outputs, screenplay, task_id, progress_callback
            )
            result["steps"]["editing"] = editing_result

            # Determine overall status
            all_statuses = [
                result["steps"].get(s, {}).get("status", PipelineStatus.PENDING)
                for s in ["script_generation", "visual_generation", "audio_generation", "editing"]
            ]

            if all(s == PipelineStatus.COMPLETED for s in all_statuses):
                result["status"] = PipelineStatus.COMPLETED
            elif PipelineStatus.COMPLETED in all_statuses:
                result["status"] = PipelineStatus.PARTIAL
            else:
                result["status"] = PipelineStatus.FAILED

            # Set output info
            if editing_result.get("data", {}).get("output_path"):
                result["output"] = {
                    "video_path": editing_result["data"]["output_path"],
                    "type": "video",
                }
            elif audio_outputs:
                result["output"] = {
                    "type": "assets_package",
                    "description": "Script, visual prompts, and audio files generated",
                }

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
        """Run the script generation step."""
        step = self.steps[0]
        step.status = PipelineStatus.IN_PROGRESS

        try:
            # Sub-step 1: Generate content
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

    async def _run_visual_generation(
        self,
        screenplay: dict,
        video_style: str,
        task_id: str,
        progress_callback: Optional[Callable] = None,
    ) -> dict[str, Any]:
        """Run the visual prompt generation step."""
        step = self.steps[1]
        step.status = PipelineStatus.IN_PROGRESS

        try:
            if progress_callback:
                await progress_callback({
                    "task_id": task_id,
                    "step": step.name,
                    "sub_step": "starting",
                    "message": "Generating optimized visual prompts...",
                    "progress_percent": 5,
                })

            visual_result = await self.visual_agent.generate_visuals(
                screenplay=screenplay,
                style=video_style,
                task_id=task_id,
                progress_callback=progress_callback,
            )

            step.status = PipelineStatus.COMPLETED
            step.progress_percent = 100

            if progress_callback:
                await progress_callback({
                    "task_id": task_id,
                    "step": step.name,
                    "sub_step": "completed",
                    "message": f"Visual prompts generated for {visual_result.get('total_scenes', 0)} scenes!",
                    "progress_percent": 100,
                })

            return {
                "status": PipelineStatus.COMPLETED,
                "data": visual_result,
            }

        except Exception as e:
            step.status = PipelineStatus.FAILED
            step.error = str(e)

            if progress_callback:
                await progress_callback({
                    "task_id": task_id,
                    "step": step.name,
                    "sub_step": "error",
                    "message": f"Visual generation failed: {str(e)}",
                    "progress_percent": 0,
                    "error": str(e),
                })

            return {
                "status": PipelineStatus.FAILED,
                "error": str(e),
            }

    async def _run_audio_generation(
        self,
        screenplay: dict,
        language: str,
        music_type: str,
        task_id: str,
        progress_callback: Optional[Callable] = None,
    ) -> dict[str, Any]:
        """Run the audio generation step."""
        step = self.steps[2]
        step.status = PipelineStatus.IN_PROGRESS

        try:
            if progress_callback:
                await progress_callback({
                    "task_id": task_id,
                    "step": step.name,
                    "sub_step": "starting",
                    "message": "Starting audio generation...",
                    "progress_percent": 5,
                })

            audio_result = await self.audio_agent.generate_full_audio(
                screenplay=screenplay,
                language=language,
                music_type=music_type,
                task_id=task_id,
                progress_callback=progress_callback,
            )

            step.status = PipelineStatus.COMPLETED
            step.progress_percent = 100

            # Count successful audio files
            audio_files = audio_result.get("voiceover", {}).get("audio_files", [])
            completed_count = sum(
                1 for f in audio_files if f.get("status") == "completed"
            )

            if progress_callback:
                await progress_callback({
                    "task_id": task_id,
                    "step": step.name,
                    "sub_step": "completed",
                    "message": f"Audio generated: {completed_count} scene audio files!",
                    "progress_percent": 100,
                })

            return {
                "status": PipelineStatus.COMPLETED,
                "data": audio_result,
            }

        except Exception as e:
            step.status = PipelineStatus.FAILED
            step.error = str(e)

            if progress_callback:
                await progress_callback({
                    "task_id": task_id,
                    "step": step.name,
                    "sub_step": "error",
                    "message": f"Audio generation failed: {str(e)}",
                    "progress_percent": 0,
                    "error": str(e),
                })

            return {
                "status": PipelineStatus.FAILED,
                "error": str(e),
            }

    async def _run_lipsync(
        self,
        audio_outputs: Optional[dict],
        task_id: str,
        progress_callback: Optional[Callable] = None,
    ) -> dict[str, Any]:
        """Run the lip sync preparation step."""
        step = self.steps[3]
        step.status = PipelineStatus.IN_PROGRESS

        try:
            # Determine video and audio paths
            task_dir = self.file_manager.get_task_dir(task_id)
            video_path = task_dir / "final" / "final_output.mp4"
            audio_path = None

            # Find first available audio file
            if audio_outputs:
                audio_files = audio_outputs.get("voiceover", {}).get("audio_files", [])
                for af in audio_files:
                    if af.get("status") == "completed" and af.get("audio_path"):
                        audio_path = Path(af["audio_path"])
                        break

            if not audio_path:
                audio_path = task_dir / "audio" / "scene_01.mp3"

            lipsync_result = await self.lipsync_agent.apply_lipsync(
                video_path=video_path,
                audio_path=audio_path,
                task_id=task_id,
                progress_callback=progress_callback,
            )

            step.status = PipelineStatus.COMPLETED
            step.progress_percent = 100

            return {
                "status": PipelineStatus.COMPLETED,
                "data": lipsync_result,
            }

        except Exception as e:
            step.status = PipelineStatus.FAILED
            step.error = str(e)

            if progress_callback:
                await progress_callback({
                    "task_id": task_id,
                    "step": step.name,
                    "sub_step": "error",
                    "message": f"Lip sync preparation failed: {str(e)}",
                    "progress_percent": 0,
                    "error": str(e),
                })

            return {
                "status": PipelineStatus.FAILED,
                "error": str(e),
            }

    async def _run_editing(
        self,
        visual_outputs: Optional[dict],
        audio_outputs: Optional[dict],
        screenplay: dict,
        task_id: str,
        progress_callback: Optional[Callable] = None,
    ) -> dict[str, Any]:
        """Run the video editing/assembly step."""
        step = self.steps[4]
        step.status = PipelineStatus.IN_PROGRESS

        try:
            if progress_callback:
                await progress_callback({
                    "task_id": task_id,
                    "step": step.name,
                    "sub_step": "starting",
                    "message": "Starting video assembly...",
                    "progress_percent": 5,
                })

            editing_result = await self.editor_agent.assemble_video(
                visual_outputs=visual_outputs or {},
                audio_outputs=audio_outputs or {},
                screenplay=screenplay,
                task_id=task_id,
                progress_callback=progress_callback,
            )

            if editing_result.get("status") == "completed":
                step.status = PipelineStatus.COMPLETED
            else:
                step.status = PipelineStatus.PARTIAL

            step.progress_percent = 100

            if progress_callback:
                status_msg = (
                    "Video assembly complete!"
                    if editing_result.get("status") == "completed"
                    else "Partial assembly - some assets were not available."
                )
                await progress_callback({
                    "task_id": task_id,
                    "step": step.name,
                    "sub_step": "completed",
                    "message": status_msg,
                    "progress_percent": 100,
                })

            return {
                "status": PipelineStatus.COMPLETED if editing_result.get("status") == "completed" else PipelineStatus.PARTIAL,
                "data": editing_result,
            }

        except Exception as e:
            step.status = PipelineStatus.FAILED
            step.error = str(e)

            if progress_callback:
                await progress_callback({
                    "task_id": task_id,
                    "step": step.name,
                    "sub_step": "error",
                    "message": f"Video assembly failed: {str(e)}",
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
