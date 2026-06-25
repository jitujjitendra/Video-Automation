"""FFmpeg service for video and audio processing.

Provides video/audio manipulation using FFmpeg via subprocess.
All operations are async and use pathlib for cross-platform paths.
"""

import asyncio
import json
import subprocess
import shutil
from pathlib import Path
from typing import Optional


class FFmpegService:
    """Video and audio processing service using FFmpeg.

    Handles video creation, concatenation, audio mixing, subtitles,
    and other media operations via FFmpeg subprocess calls.
    """

    def __init__(self):
        """Initialize FFmpeg service."""
        self.ffmpeg_path = self._find_ffmpeg()
        self.ffprobe_path = self._find_ffprobe()

    def _find_ffmpeg(self) -> str:
        """Find the ffmpeg executable path."""
        ffmpeg = shutil.which("ffmpeg")
        return ffmpeg if ffmpeg else "ffmpeg"

    def _find_ffprobe(self) -> str:
        """Find the ffprobe executable path."""
        ffprobe = shutil.which("ffprobe")
        return ffprobe if ffprobe else "ffprobe"

    def is_available(self) -> bool:
        """Check if FFmpeg is available on the system."""
        try:
            result = subprocess.run(
                [self.ffmpeg_path, "-version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    async def _run_command(
        self, cmd: list[str], timeout: int = 300
    ) -> tuple[int, str, str]:
        """Run an FFmpeg command asynchronously.

        Args:
            cmd: Command and arguments list.
            timeout: Maximum execution time in seconds.

        Returns:
            Tuple of (return_code, stdout, stderr).
        """
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )
            return (
                process.returncode or 0,
                stdout.decode("utf-8", errors="replace"),
                stderr.decode("utf-8", errors="replace"),
            )
        except asyncio.TimeoutError:
            process.kill()
            raise RuntimeError(f"FFmpeg command timed out after {timeout}s")
        except FileNotFoundError:
            raise RuntimeError(
                "FFmpeg not found. Please install FFmpeg and ensure it's in your PATH."
            )

    async def create_video_from_image(
        self,
        image_path: Path,
        duration: float,
        output_path: Path,
        zoom_effect: bool = True,
    ) -> Path:
        """Create a video clip from a still image with optional Ken Burns effect.

        Args:
            image_path: Path to the source image.
            duration: Duration of the output video in seconds.
            output_path: Path for the output video file.
            zoom_effect: Whether to apply a slow zoom (Ken Burns) effect.

        Returns:
            Path to the created video file.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if zoom_effect:
            # Ken Burns slow zoom effect
            cmd = [
                self.ffmpeg_path, "-y",
                "-loop", "1",
                "-i", str(image_path),
                "-vf", (
                    f"scale=1920:1080:force_original_aspect_ratio=decrease,"
                    f"pad=1920:1080:(ow-iw)/2:(oh-ih)/2,"
                    f"zoompan=z='min(zoom+0.001,1.2)':x='iw/2-(iw/zoom/2)':"
                    f"y='ih/2-(ih/zoom/2)':d={int(duration * 25)}:s=1920x1080:fps=25"
                ),
                "-c:v", "libx264",
                "-t", str(duration),
                "-pix_fmt", "yuv420p",
                str(output_path),
            ]
        else:
            # Simple static image to video
            cmd = [
                self.ffmpeg_path, "-y",
                "-loop", "1",
                "-i", str(image_path),
                "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2",
                "-c:v", "libx264",
                "-t", str(duration),
                "-pix_fmt", "yuv420p",
                "-r", "25",
                str(output_path),
            ]

        returncode, stdout, stderr = await self._run_command(cmd)
        if returncode != 0:
            raise RuntimeError(f"Failed to create video from image: {stderr}")

        return output_path

    async def concatenate_videos(
        self,
        video_paths: list[Path],
        output_path: Path,
        transition: str = "fade",
    ) -> Path:
        """Concatenate multiple video clips into one video.

        Args:
            video_paths: List of paths to video clips (in order).
            output_path: Path for the output concatenated video.
            transition: Transition type ('none', 'fade', 'dissolve').

        Returns:
            Path to the concatenated video.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if not video_paths:
            raise ValueError("No video paths provided")

        if len(video_paths) == 1:
            # Just copy the single file
            shutil.copy2(str(video_paths[0]), str(output_path))
            return output_path

        # Create a concat list file
        concat_file = output_path.parent / "concat_list.txt"
        with open(concat_file, "w", encoding="utf-8") as f:
            for vpath in video_paths:
                # Use forward slashes for FFmpeg compatibility
                f.write(f"file '{str(Path(vpath).resolve())}'\n")

        cmd = [
            self.ffmpeg_path, "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_file),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-r", "25",
            str(output_path),
        ]

        returncode, stdout, stderr = await self._run_command(cmd)

        # Clean up concat file
        if concat_file.exists():
            concat_file.unlink()

        if returncode != 0:
            raise RuntimeError(f"Failed to concatenate videos: {stderr}")

        return output_path

    async def add_audio_to_video(
        self,
        video_path: Path,
        audio_path: Path,
        output_path: Path,
    ) -> Path:
        """Mux an audio track onto a video file.

        Args:
            video_path: Path to the input video.
            audio_path: Path to the audio file.
            output_path: Path for the output video with audio.

        Returns:
            Path to the output video.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            self.ffmpeg_path, "-y",
            "-i", str(video_path),
            "-i", str(audio_path),
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            str(output_path),
        ]

        returncode, stdout, stderr = await self._run_command(cmd)
        if returncode != 0:
            raise RuntimeError(f"Failed to add audio to video: {stderr}")

        return output_path

    async def add_subtitles(
        self,
        video_path: Path,
        srt_path: Path,
        output_path: Path,
    ) -> Path:
        """Burn subtitles into a video file.

        Args:
            video_path: Path to the input video.
            srt_path: Path to the .srt subtitle file.
            output_path: Path for the output video with subtitles.

        Returns:
            Path to the output video.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Escape path for subtitles filter (Windows backslashes)
        srt_escaped = str(srt_path).replace("\\", "/").replace(":", "\\:")

        cmd = [
            self.ffmpeg_path, "-y",
            "-i", str(video_path),
            "-vf", f"subtitles='{srt_escaped}'",
            "-c:v", "libx264",
            "-c:a", "copy",
            str(output_path),
        ]

        returncode, stdout, stderr = await self._run_command(cmd)
        if returncode != 0:
            # If subtitle burning fails, return video without subtitles
            shutil.copy2(str(video_path), str(output_path))

        return output_path

    async def trim_video(
        self,
        input_path: Path,
        start: float,
        end: float,
        output_path: Path,
    ) -> Path:
        """Trim a video to a specific time range.

        Args:
            input_path: Path to the input video.
            start: Start time in seconds.
            end: End time in seconds.
            output_path: Path for the trimmed output.

        Returns:
            Path to the trimmed video.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        duration = end - start

        cmd = [
            self.ffmpeg_path, "-y",
            "-i", str(input_path),
            "-ss", str(start),
            "-t", str(duration),
            "-c:v", "libx264",
            "-c:a", "aac",
            str(output_path),
        ]

        returncode, stdout, stderr = await self._run_command(cmd)
        if returncode != 0:
            raise RuntimeError(f"Failed to trim video: {stderr}")

        return output_path

    async def get_duration(self, file_path: Path) -> float:
        """Get the duration of a media file in seconds.

        Args:
            file_path: Path to the audio or video file.

        Returns:
            Duration in seconds, or 0.0 if unable to determine.
        """
        try:
            cmd = [
                self.ffprobe_path,
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                str(file_path),
            ]

            returncode, stdout, stderr = await self._run_command(cmd, timeout=30)
            if returncode == 0 and stdout:
                data = json.loads(stdout)
                duration_str = data.get("format", {}).get("duration", "0")
                return float(duration_str)
        except Exception:
            pass

        return 0.0

    def generate_srt(self, screenplay: dict) -> str:
        """Generate an SRT subtitle file content from a screenplay.

        Args:
            screenplay: Screenplay dictionary with scenes containing dialogue.

        Returns:
            SRT-formatted string content.
        """
        srt_content = ""
        subtitle_index = 1
        current_time = 0.0

        scenes = screenplay.get("scenes", [])

        for scene in scenes:
            dialogue = scene.get("dialogue", "")
            duration = scene.get("duration_seconds", 8)

            if dialogue and dialogue.strip():
                start_time = self._format_srt_time(current_time)
                end_time = self._format_srt_time(current_time + duration)

                srt_content += f"{subtitle_index}\n"
                srt_content += f"{start_time} --> {end_time}\n"
                srt_content += f"{dialogue.strip()}\n\n"

                subtitle_index += 1

            current_time += duration

        return srt_content

    @staticmethod
    def _format_srt_time(seconds: float) -> str:
        """Format seconds into SRT time format (HH:MM:SS,mmm).

        Args:
            seconds: Time in seconds.

        Returns:
            Formatted time string.
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)

        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
