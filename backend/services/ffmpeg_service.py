"""FFmpeg service for video/audio processing.

TODO: Implement in Phase 4
- Combine video clips
- Add audio tracks
- Apply transitions
- Export final video
"""

from pathlib import Path
from typing import Optional


class FFmpegService:
    """Video and audio processing service using FFmpeg.

    TODO: Implement the following methods:
    - combine_clips(clips, output_path) -> Path
    - add_audio(video_path, audio_path, output_path) -> Path
    - apply_transition(clip1, clip2, transition_type) -> Path
    - export_final(task_dir) -> Path
    """

    def __init__(self):
        """Initialize FFmpeg service."""
        self.ffmpeg_path = "ffmpeg"  # Assumes FFmpeg is in PATH

    async def combine_clips(self, clips: list[Path], output_path: Path) -> Path:
        """Combine multiple video clips into one.

        TODO: Implement in Phase 4.
        """
        # TODO: Implement in Phase 4
        raise NotImplementedError("FFmpeg service will be implemented in Phase 4")

    async def add_audio(
        self, video_path: Path, audio_path: Path, output_path: Path
    ) -> Path:
        """Add audio track to video.

        TODO: Implement in Phase 4.
        """
        # TODO: Implement in Phase 4
        raise NotImplementedError("FFmpeg service will be implemented in Phase 4")

    async def export_final(
        self, task_dir: Path, output_path: Optional[Path] = None
    ) -> Path:
        """Export final composed video.

        TODO: Implement in Phase 4.
        """
        # TODO: Implement in Phase 4
        raise NotImplementedError("FFmpeg service will be implemented in Phase 4")
