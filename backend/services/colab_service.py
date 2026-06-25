"""Google Colab integration service for GPU-heavy processing.

Generates ready-to-run Colab notebooks for tasks that require
GPU processing (Wav2Lip lip sync, video enhancement, etc.).
"""

import json
from pathlib import Path
from typing import Optional


class ColabService:
    """Service for generating Google Colab notebooks for GPU tasks.

    Since the user's local machine has limited GPU capability,
    heavy processing (Wav2Lip, video upscaling) is offloaded to
    Google Colab via pre-configured notebooks.
    """

    def __init__(self):
        """Initialize Colab service."""
        self.colab_url: Optional[str] = None

    def generate_lipsync_notebook(
        self,
        video_url: str,
        audio_url: str,
        task_id: str,
        output_dir: Optional[Path] = None,
    ) -> Path:
        """Generate a Colab notebook for Wav2Lip lip sync processing.

        Creates a .ipynb file with all cells pre-configured so the user
        can just click 'Run All' in Google Colab.

        Args:
            video_url: URL or path to the input video.
            audio_url: URL or path to the audio file.
            task_id: Task identifier for organizing outputs.
            output_dir: Directory to save the notebook.

        Returns:
            Path to the generated .ipynb notebook file.
        """
        notebook = self._create_lipsync_notebook_content(
            video_url, audio_url, task_id
        )

        if output_dir is None:
            output_dir = Path("outputs") / task_id

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        notebook_path = output_dir / f"lipsync_{task_id}.ipynb"
        with open(notebook_path, "w", encoding="utf-8") as f:
            json.dump(notebook, f, indent=2)

        return notebook_path

    def generate_video_enhance_notebook(
        self,
        video_path: str,
        task_id: str,
        output_dir: Optional[Path] = None,
    ) -> Path:
        """Generate a Colab notebook for video upscaling/enhancement.

        Args:
            video_path: Path or URL to the video to enhance.
            task_id: Task identifier.
            output_dir: Directory to save the notebook.

        Returns:
            Path to the generated .ipynb notebook file.
        """
        notebook = self._create_enhance_notebook_content(video_path, task_id)

        if output_dir is None:
            output_dir = Path("outputs") / task_id

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        notebook_path = output_dir / f"enhance_{task_id}.ipynb"
        with open(notebook_path, "w", encoding="utf-8") as f:
            json.dump(notebook, f, indent=2)

        return notebook_path

    def _create_lipsync_notebook_content(
        self, video_url: str, audio_url: str, task_id: str
    ) -> dict:
        """Create the Jupyter notebook JSON for Wav2Lip processing."""
        cells = [
            self._markdown_cell(
                "# Wav2Lip Lip Sync Processing\n\n"
                f"**Task ID:** `{task_id}`\n\n"
                "This notebook will apply lip synchronization to your video "
                "using the Wav2Lip model. Just click **Runtime > Run All** to start.\n\n"
                "**Requirements:** Google Colab with GPU runtime (T4 or better)."
            ),
            self._markdown_cell("## 1. Setup Environment"),
            self._code_cell(
                "# Check GPU availability\n"
                "!nvidia-smi\n"
                "import torch\n"
                "print(f'CUDA available: {torch.cuda.is_available()}')\n"
                "print(f'GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"None\"}')"
            ),
            self._code_cell(
                "# Clone Wav2Lip repository\n"
                "!git clone https://github.com/Rudrabha/Wav2Lip.git\n"
                "%cd Wav2Lip\n"
                "\n"
                "# Install dependencies\n"
                "!pip install -q librosa==0.9.2 numpy==1.23.5 opencv-python-headless\n"
                "!pip install -q batch-face"
            ),
            self._code_cell(
                "# Download pre-trained model\n"
                "!mkdir -p checkpoints\n"
                "!gdown 1qBv1fBEpmLBdNDxCQLoRR-fVj_dVb7Nh -O checkpoints/wav2lip_gan.pth\n"
                "# Alternative: !wget 'https://github.com/Rudrabha/Wav2Lip/releases/download/v1.0/wav2lip_gan.pth' -O checkpoints/wav2lip_gan.pth"
            ),
            self._markdown_cell("## 2. Upload Input Files"),
            self._code_cell(
                "import os\n"
                "from google.colab import files\n"
                "\n"
                "# Create input directory\n"
                "os.makedirs('inputs', exist_ok=True)\n"
                "\n"
                f"# Video path (modify if using different source)\n"
                f"VIDEO_PATH = 'inputs/video.mp4'\n"
                f"AUDIO_PATH = 'inputs/audio.mp3'\n"
                f"OUTPUT_PATH = 'results/result_{task_id}.mp4'\n"
                "\n"
                "# Option 1: Upload files manually\n"
                "print('Upload your video file:')\n"
                "uploaded = files.upload()\n"
                "for fn in uploaded:\n"
                "    os.rename(fn, VIDEO_PATH)\n"
                "    break\n"
                "\n"
                "print('Upload your audio file:')\n"
                "uploaded = files.upload()\n"
                "for fn in uploaded:\n"
                "    os.rename(fn, AUDIO_PATH)\n"
                "    break"
            ),
            self._markdown_cell("## 3. Run Wav2Lip"),
            self._code_cell(
                "# Run lip sync inference\n"
                "!python inference.py \\\n"
                "    --checkpoint_path checkpoints/wav2lip_gan.pth \\\n"
                f"    --face $VIDEO_PATH \\\n"
                f"    --audio $AUDIO_PATH \\\n"
                "    --outfile $OUTPUT_PATH \\\n"
                "    --resize_factor 1 \\\n"
                "    --nosmooth\n"
                "\n"
                "print(f'Lip sync complete! Output saved to: {OUTPUT_PATH}')"
            ),
            self._markdown_cell("## 4. Download Result"),
            self._code_cell(
                "# Download the result\n"
                "from google.colab import files\n"
                "import os\n"
                "\n"
                "if os.path.exists(OUTPUT_PATH):\n"
                "    files.download(OUTPUT_PATH)\n"
                "    print('Download started!')\n"
                "else:\n"
                "    print('Error: Output file not found. Check the logs above for errors.')"
            ),
        ]

        return self._create_notebook(cells)

    def _create_enhance_notebook_content(
        self, video_path: str, task_id: str
    ) -> dict:
        """Create the Jupyter notebook JSON for video enhancement."""
        cells = [
            self._markdown_cell(
                "# Video Enhancement (Upscaling)\n\n"
                f"**Task ID:** `{task_id}`\n\n"
                "This notebook upscales and enhances your video using "
                "Real-ESRGAN. Click **Runtime > Run All** to start.\n\n"
                "**Requirements:** Google Colab with GPU runtime."
            ),
            self._markdown_cell("## 1. Setup"),
            self._code_cell(
                "# Install Real-ESRGAN\n"
                "!pip install -q realesrgan basicsr facexlib gfpgan\n"
                "!git clone https://github.com/xinntao/Real-ESRGAN.git\n"
                "%cd Real-ESRGAN\n"
                "!pip install -q -r requirements.txt\n"
                "!python setup.py develop"
            ),
            self._markdown_cell("## 2. Upload Video"),
            self._code_cell(
                "import os\n"
                "from google.colab import files\n"
                "\n"
                "os.makedirs('inputs', exist_ok=True)\n"
                f"INPUT_PATH = 'inputs/video.mp4'\n"
                f"OUTPUT_PATH = 'results/enhanced_{task_id}.mp4'\n"
                "\n"
                "print('Upload your video file:')\n"
                "uploaded = files.upload()\n"
                "for fn in uploaded:\n"
                "    os.rename(fn, INPUT_PATH)\n"
                "    break"
            ),
            self._markdown_cell("## 3. Enhance Video"),
            self._code_cell(
                "# Run enhancement\n"
                "!python inference_realesrgan_video.py \\\n"
                "    -i $INPUT_PATH \\\n"
                "    -o results/ \\\n"
                "    -n RealESRGAN_x4plus \\\n"
                "    --face_enhance\n"
                "\n"
                "print('Enhancement complete!')"
            ),
            self._markdown_cell("## 4. Download Result"),
            self._code_cell(
                "from google.colab import files\n"
                "import glob\n"
                "\n"
                "results = glob.glob('results/*.mp4')\n"
                "if results:\n"
                "    files.download(results[0])\n"
                "else:\n"
                "    print('No output found.')"
            ),
        ]

        return self._create_notebook(cells)

    @staticmethod
    def _create_notebook(cells: list[dict]) -> dict:
        """Create a Jupyter notebook structure."""
        return {
            "nbformat": 4,
            "nbformat_minor": 0,
            "metadata": {
                "colab": {"name": "AI Video Automation - Processing"},
                "kernelspec": {
                    "name": "python3",
                    "display_name": "Python 3",
                },
                "language_info": {"name": "python"},
                "accelerator": "GPU",
                "gpuClass": "standard",
            },
            "cells": cells,
        }

    @staticmethod
    def _markdown_cell(source: str) -> dict:
        """Create a markdown cell."""
        return {
            "cell_type": "markdown",
            "metadata": {},
            "source": [source],
        }

    @staticmethod
    def _code_cell(source: str) -> dict:
        """Create a code cell."""
        return {
            "cell_type": "code",
            "metadata": {},
            "source": [source],
            "execution_count": None,
            "outputs": [],
        }
