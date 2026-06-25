"""Editor Agent - Auto editing and video assembly.

Assembles final video from generated visuals and audio assets.
Uses FFmpeg for video processing, optimized for low-spec systems.
Handles transitions, subtitles, and audio mixing.
"""

import shutil
from pathlib import Path
from typing import Any, Callable, Optional

from ..services.ffmpeg_service import FFmpegService
from ..utils.file_manager import FileManager


class EditorAgent:
    """Agent responsible for final video assembly and editing.

    Takes generated visual and audio assets and assembles them into
    a final video with transitions, subtitles, and proper audio mixing.
    Designed to work efficiently on low-spec hardware (i3, 6GB RAM).
    """

    def __init__(self, ffmpeg_service: Optional[FFmpegService] = None):
        """Initialize Editor Agent.

        Args:
            ffmpeg_service: FFmpeg service for video processing.
        """
        self.ffmpeg = ffmpeg_service or FFmpegService()
        self.file_manager = FileManager()

    async def assemble_video(
        self,
        visual_outputs: dict,
        audio_outputs: dict,
        screenplay: dict,
        task_id: str = "",
        progress_callback: Optional[Callable] = None,
    ) -> dict[str, Any]:
        """Assemble final video from visual and audio assets.

        Main method that combines all generated content into a final video.
        Handles cases where some assets may be missing (graceful degradation).

        Args:
            visual_outputs: Output from Visual Agent (prompts/images).
            audio_outputs: Output from Audio Agent (audio files).
            screenplay: Original screenplay data.
            task_id: Task identifier.
            progress_callback: Async callback for progress.

        Returns:
            Dictionary with assembly results and output paths.
        """
        if not self.ffmpeg.is_available():
            return {
                "status": "partial",
                "message": (
                    "FFmpeg not available on this system. "
                    "Video assembly requires FFmpeg to be installed. "
                    "Audio files and prompts are still available."
                ),
                "assets_available": self._list_available_assets(
                    visual_outputs, audio_outputs, task_id
                ),
            }

        task_dir = self.file_manager.get_task_dir(task_id) if task_id else Path("outputs")
        video_dir = task_dir / "video"
        final_dir = task_dir / "final"
        video_dir.mkdir(parents=True, exist_ok=True)
        final_dir.mkdir(parents=True, exist_ok=True)

        result = {
            "status": "in_progress",
            "steps_completed": [],
            "output_path": None,
        }

        try:
            if progress_callback:
                await progress_callback({
                    "task_id": task_id,
                    "step": "editing",
                    "sub_step": "checking_assets",
                    "message": "Checking available assets for assembly...",
                    "progress_percent": 5,
                })

            # Check what assets we have to work with
            image_paths = self._find_image_assets(task_dir)
            audio_files = self._get_audio_file_paths(audio_outputs)
            scenes = screenplay.get("scenes", [])

            # Step 1: Create video clips from available images
            if image_paths:
                if progress_callback:
                    await progress_callback({
                        "task_id": task_id,
                        "step": "editing",
                        "sub_step": "creating_clips",
                        "message": "Creating video clips from images...",
                        "progress_percent": 20,
                    })

                clip_paths = await self.create_slideshow(
                    images=image_paths,
                    durations=[s.get("duration_seconds", 8) for s in scenes[:len(image_paths)]],
                    output_dir=video_dir,
                )
                result["steps_completed"].append("slideshow_created")
            else:
                clip_paths = []

            # Step 2: Concatenate clips if we have multiple
            if len(clip_paths) > 1:
                if progress_callback:
                    await progress_callback({
                        "task_id": task_id,
                        "step": "editing",
                        "sub_step": "concatenating",
                        "message": "Joining video clips with transitions...",
                        "progress_percent": 45,
                    })

                video_path = await self.add_transitions(
                    clips=clip_paths,
                    transition_type="fade",
                    output_path=video_dir / "assembled.mp4",
                )
                result["steps_completed"].append("clips_concatenated")
            elif len(clip_paths) == 1:
                video_path = clip_paths[0]
            else:
                video_path = None

            # Step 3: Mix audio with video
            if video_path and audio_files:
                if progress_callback:
                    await progress_callback({
                        "task_id": task_id,
                        "step": "editing",
                        "sub_step": "mixing_audio",
                        "message": "Adding audio track to video...",
                        "progress_percent": 65,
                    })

                # Concatenate audio files first or use the first one
                combined_audio = self._get_combined_audio_path(audio_files, task_dir)
                if combined_audio:
                    output_with_audio = final_dir / "video_with_audio.mp4"
                    video_path = await self.mix_audio_video(
                        video_path=video_path,
                        audio_path=combined_audio,
                        output_path=output_with_audio,
                    )
                    result["steps_completed"].append("audio_mixed")

            # Step 4: Add subtitles
            if video_path and scenes:
                if progress_callback:
                    await progress_callback({
                        "task_id": task_id,
                        "step": "editing",
                        "sub_step": "subtitles",
                        "message": "Adding subtitles...",
                        "progress_percent": 80,
                    })

                srt_path = self._generate_srt_file(screenplay, task_dir)
                if srt_path:
                    final_output = final_dir / "final_video.mp4"
                    video_path = await self.add_subtitles(
                        video_path=video_path,
                        screenplay=screenplay,
                        output_path=final_output,
                    )
                    result["steps_completed"].append("subtitles_added")

            # Step 5: Final render/copy
            if video_path:
                final_path = final_dir / "final_output.mp4"
                if video_path != final_path:
                    shutil.copy2(str(video_path), str(final_path))
                result["output_path"] = str(final_path)
                result["status"] = "completed"

                if progress_callback:
                    await progress_callback({
                        "task_id": task_id,
                        "step": "editing",
                        "sub_step": "completed",
                        "message": "Video assembly complete!",
                        "progress_percent": 100,
                    })
            else:
                result["status"] = "partial"
                result["message"] = (
                    "No visual assets available for video assembly. "
                    "Audio files and prompts are ready for manual assembly."
                )
                result["assets_available"] = self._list_available_assets(
                    visual_outputs, audio_outputs, task_id
                )

        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)

            if progress_callback:
                await progress_callback({
                    "task_id": task_id,
                    "step": "editing",
                    "sub_step": "error",
                    "message": f"Assembly error: {str(e)}",
                    "progress_percent": 0,
                })

        # Save result
        if task_id:
            self.file_manager.save_json(task_id, "final/assembly_result.json", result)

        return result

    async def add_transitions(
        self,
        clips: list[Path],
        transition_type: str = "fade",
        output_path: Optional[Path] = None,
    ) -> Path:
        """Add transitions between video clips and concatenate.

        Args:
            clips: List of video clip paths.
            transition_type: Type of transition ('cut', 'fade', 'dissolve').
            output_path: Output path for the final video.

        Returns:
            Path to the concatenated video with transitions.
        """
        if not output_path:
            output_path = clips[0].parent / "concatenated.mp4"

        # For simple transitions, use FFmpeg concat
        return await self.ffmpeg.concatenate_videos(
            video_paths=clips,
            output_path=output_path,
            transition=transition_type,
        )

    async def add_subtitles(
        self,
        video_path: Path,
        screenplay: dict,
        output_path: Path,
    ) -> Path:
        """Add subtitles to a video from screenplay dialogue.

        Args:
            video_path: Path to the input video.
            screenplay: Screenplay dictionary with scene dialogue.
            output_path: Path for the output video.

        Returns:
            Path to the video with subtitles.
        """
        # Generate SRT content
        srt_content = self.ffmpeg.generate_srt(screenplay)

        if not srt_content.strip():
            # No dialogue to subtitle, return original
            shutil.copy2(str(video_path), str(output_path))
            return output_path

        # Write SRT file
        srt_path = output_path.parent / "subtitles.srt"
        with open(srt_path, "w", encoding="utf-8") as f:
            f.write(srt_content)

        # Burn subtitles into video
        return await self.ffmpeg.add_subtitles(
            video_path=video_path,
            srt_path=srt_path,
            output_path=output_path,
        )

    async def create_slideshow(
        self,
        images: list[Path],
        durations: list[float],
        output_dir: Path,
    ) -> list[Path]:
        """Create video clips from images with Ken Burns effect.

        Args:
            images: List of image file paths.
            durations: Duration for each image clip.
            output_dir: Directory to save output clips.

        Returns:
            List of paths to created video clips.
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        clip_paths = []
        for i, (img_path, duration) in enumerate(zip(images, durations)):
            output_path = output_dir / f"clip_{i:03d}.mp4"
            try:
                clip = await self.ffmpeg.create_video_from_image(
                    image_path=img_path,
                    duration=duration,
                    output_path=output_path,
                    zoom_effect=True,
                )
                clip_paths.append(clip)
            except Exception:
                # Skip failed clips
                continue

        return clip_paths

    async def mix_audio_video(
        self,
        video_path: Path,
        audio_path: Path,
        output_path: Path,
    ) -> Path:
        """Combine audio and video tracks.

        Args:
            video_path: Path to the video file.
            audio_path: Path to the audio file.
            output_path: Path for the output.

        Returns:
            Path to the combined video.
        """
        return await self.ffmpeg.add_audio_to_video(
            video_path=video_path,
            audio_path=audio_path,
            output_path=output_path,
        )

    async def render_final(self, task_id: str) -> dict[str, Any]:
        """Perform final render for a task (re-assemble if needed).

        Args:
            task_id: Task identifier.

        Returns:
            Render result dictionary.
        """
        task_dir = self.file_manager.get_task_dir(task_id)
        final_dir = task_dir / "final"

        # Check if final output already exists
        final_path = final_dir / "final_output.mp4"
        if final_path.exists():
            return {
                "status": "completed",
                "output_path": str(final_path),
            }

        return {
            "status": "no_output",
            "message": "No assembled video found. Run the full pipeline first.",
        }

    def _find_image_assets(self, task_dir: Path) -> list[Path]:
        """Find available image assets in the task directory."""
        image_extensions = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
        images = []

        # Check visuals directory
        visuals_dir = task_dir / "visuals"
        if visuals_dir.exists():
            for ext in image_extensions:
                images.extend(sorted(visuals_dir.glob(f"*{ext}")))

        # Also check video directory for any images
        video_dir = task_dir / "video"
        if video_dir.exists():
            for ext in image_extensions:
                images.extend(sorted(video_dir.glob(f"*{ext}")))

        return images

    def _get_audio_file_paths(self, audio_outputs: dict) -> list[Path]:
        """Extract audio file paths from audio outputs."""
        paths = []
        audio_files = audio_outputs.get("voiceover", {}).get("audio_files", [])

        for audio_info in audio_files:
            audio_path = audio_info.get("audio_path")
            if audio_path and Path(audio_path).exists():
                paths.append(Path(audio_path))

        return paths

    def _get_combined_audio_path(
        self, audio_files: list[Path], task_dir: Path
    ) -> Optional[Path]:
        """Get a single combined audio file path.

        If multiple audio files exist, returns the first one.
        Full concatenation would require FFmpeg audio concat.
        """
        if not audio_files:
            return None

        # For simplicity, use the first available audio file
        # In a full implementation, concatenate all scene audio
        for audio_path in audio_files:
            if audio_path.exists():
                return audio_path

        return None

    def _generate_srt_file(self, screenplay: dict, task_dir: Path) -> Optional[Path]:
        """Generate and save an SRT subtitle file."""
        srt_content = self.ffmpeg.generate_srt(screenplay)
        if not srt_content.strip():
            return None

        srt_path = task_dir / "final" / "subtitles.srt"
        srt_path.parent.mkdir(parents=True, exist_ok=True)
        with open(srt_path, "w", encoding="utf-8") as f:
            f.write(srt_content)

        return srt_path

    def _list_available_assets(
        self, visual_outputs: dict, audio_outputs: dict, task_id: str
    ) -> dict[str, Any]:
        """List all available assets for the task."""
        assets = {
            "visual_prompts": bool(
                visual_outputs and visual_outputs.get("visual_prompts")
            ),
            "audio_files": [],
            "has_screenplay": True,
        }

        audio_files = audio_outputs.get("voiceover", {}).get("audio_files", [])
        for af in audio_files:
            if af.get("status") == "completed" and af.get("audio_path"):
                assets["audio_files"].append(af["audio_path"])

        return assets
