"""Lip Sync Agent - Prepares data and generates Colab notebooks for lip sync.

Since the user's system cannot run Wav2Lip locally (requires GPU),
this agent prepares all necessary files and generates a ready-to-run
Google Colab notebook for lip sync processing.
"""

import platform
from pathlib import Path
from typing import Any, Callable, Optional

from ..services.colab_service import ColabService
from ..utils.file_manager import FileManager


class LipsyncAgent:
    """Agent responsible for lip synchronization preparation.

    Prepares video and audio data for lip sync processing and
    generates a Google Colab notebook that the user can run on
    cloud GPU for actual Wav2Lip inference.
    """

    def __init__(self, colab_service: Optional[ColabService] = None):
        """Initialize Lip Sync Agent.

        Args:
            colab_service: Colab service for notebook generation.
        """
        self.colab_service = colab_service or ColabService()
        self.file_manager = FileManager()

    def check_lipsync_available(self) -> dict[str, Any]:
        """Check if local lip sync processing is possible.

        Checks for GPU availability and required dependencies.
        On most consumer hardware (especially without dedicated GPU),
        this will return False, directing to Colab processing.

        Returns:
            Dictionary with availability status and system info.
        """
        system_info = {
            "platform": platform.system(),
            "processor": platform.processor(),
            "machine": platform.machine(),
        }

        # Check for CUDA/GPU (basic check)
        gpu_available = False
        gpu_name = "None detected"

        try:
            import torch
            gpu_available = torch.cuda.is_available()
            if gpu_available:
                gpu_name = torch.cuda.get_device_name(0)
        except ImportError:
            pass

        can_process_locally = gpu_available

        return {
            "local_processing_available": can_process_locally,
            "gpu_available": gpu_available,
            "gpu_name": gpu_name,
            "system_info": system_info,
            "recommendation": (
                "Local processing available with GPU."
                if can_process_locally
                else "Local GPU not available. Use the generated Google Colab notebook for lip sync processing."
            ),
        }

    async def prepare_lipsync_data(
        self,
        video_path: Path,
        audio_path: Path,
        task_id: str = "",
    ) -> dict[str, Any]:
        """Prepare data files needed for lip sync processing.

        Organizes video and audio files and generates metadata
        needed for Colab processing.

        Args:
            video_path: Path to the input video.
            audio_path: Path to the audio file.
            task_id: Task identifier.

        Returns:
            Dictionary with prepared data info.
        """
        task_dir = self.file_manager.get_task_dir(task_id) if task_id else Path("outputs")
        lipsync_dir = task_dir / "lipsync"
        lipsync_dir.mkdir(parents=True, exist_ok=True)

        # Prepare metadata
        metadata = {
            "task_id": task_id,
            "video_path": str(video_path),
            "audio_path": str(audio_path),
            "video_exists": Path(video_path).exists() if video_path else False,
            "audio_exists": Path(audio_path).exists() if audio_path else False,
            "instructions": (
                "Upload the video and audio files to Google Colab "
                "and run the generated notebook."
            ),
        }

        # Save metadata
        if task_id:
            self.file_manager.save_json(task_id, "lipsync/metadata.json", metadata)

        return metadata

    async def generate_colab_notebook(
        self,
        video_path: Path,
        audio_path: Path,
        task_id: str = "",
    ) -> dict[str, Any]:
        """Generate a ready-to-run Google Colab notebook for lip sync.

        Args:
            video_path: Path to the input video.
            audio_path: Path to the audio file.
            task_id: Task identifier.

        Returns:
            Dictionary with notebook path and instructions.
        """
        task_dir = self.file_manager.get_task_dir(task_id) if task_id else Path("outputs")
        lipsync_dir = task_dir / "lipsync"

        # Generate the Colab notebook
        notebook_path = self.colab_service.generate_lipsync_notebook(
            video_url=str(video_path),
            audio_url=str(audio_path),
            task_id=task_id,
            output_dir=lipsync_dir,
        )

        return {
            "status": "completed",
            "notebook_path": str(notebook_path),
            "instructions": [
                "1. Open the notebook in Google Colab (colab.research.google.com)",
                "2. Select a GPU runtime (Runtime > Change runtime type > T4 GPU)",
                "3. Upload your video and audio files when prompted",
                "4. Click 'Runtime > Run All' to process",
                "5. Download the result when complete",
            ],
            "requirements": [
                "Google account with Colab access",
                "GPU runtime (free tier T4 is sufficient)",
                "Video file (MP4 format recommended)",
                "Audio file (MP3/WAV format)",
            ],
        }

    async def apply_lipsync(
        self,
        video_path: Path,
        audio_path: Path,
        task_id: str = "",
        progress_callback: Optional[Callable] = None,
    ) -> dict[str, Any]:
        """Main method for lip sync processing.

        Checks local capability, prepares data, and generates
        a Colab notebook for processing.

        Args:
            video_path: Path to the input video.
            audio_path: Path to the audio file.
            task_id: Task identifier.
            progress_callback: Async callback for progress.

        Returns:
            Complete lip sync processing results.
        """
        if progress_callback:
            await progress_callback({
                "task_id": task_id,
                "step": "lipsync",
                "sub_step": "checking",
                "message": "Checking lip sync capabilities...",
                "progress_percent": 10,
            })

        # Check if local processing is possible
        availability = self.check_lipsync_available()

        if progress_callback:
            await progress_callback({
                "task_id": task_id,
                "step": "lipsync",
                "sub_step": "preparing",
                "message": "Preparing lip sync data...",
                "progress_percent": 30,
            })

        # Prepare data
        prep_result = await self.prepare_lipsync_data(
            video_path=video_path,
            audio_path=audio_path,
            task_id=task_id,
        )

        if progress_callback:
            await progress_callback({
                "task_id": task_id,
                "step": "lipsync",
                "sub_step": "generating_notebook",
                "message": "Generating Colab notebook for lip sync...",
                "progress_percent": 60,
            })

        # Generate Colab notebook
        notebook_result = await self.generate_colab_notebook(
            video_path=video_path,
            audio_path=audio_path,
            task_id=task_id,
        )

        if progress_callback:
            await progress_callback({
                "task_id": task_id,
                "step": "lipsync",
                "sub_step": "completed",
                "message": "Lip sync notebook generated! Upload to Colab to process.",
                "progress_percent": 100,
            })

        result = {
            "status": "completed",
            "processing_mode": "colab",
            "local_available": availability["local_processing_available"],
            "system_check": availability,
            "preparation": prep_result,
            "notebook": notebook_result,
        }

        # Save result
        if task_id:
            self.file_manager.save_json(task_id, "lipsync/lipsync_result.json", result)

        return result
