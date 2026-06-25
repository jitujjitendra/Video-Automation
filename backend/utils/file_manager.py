"""File handling utilities for managing task outputs and temporary files."""

import json
import uuid
from pathlib import Path
from typing import Any, Optional

from .config import get_settings


class FileManager:
    """Manages file operations for video generation tasks."""

    def __init__(self):
        self.settings = get_settings()
        self.output_dir = self.settings.output_dir

    def create_task_directory(self, task_id: Optional[str] = None) -> tuple[str, Path]:
        """Create a new task directory and return (task_id, path)."""
        if task_id is None:
            task_id = str(uuid.uuid4())[:8]

        task_dir = self.output_dir / task_id
        task_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        (task_dir / "scripts").mkdir(exist_ok=True)
        (task_dir / "audio").mkdir(exist_ok=True)
        (task_dir / "video").mkdir(exist_ok=True)
        (task_dir / "final").mkdir(exist_ok=True)

        return task_id, task_dir

    def save_json(self, task_id: str, filename: str, data: Any) -> Path:
        """Save JSON data to a task's directory."""
        task_dir = self.output_dir / task_id
        task_dir.mkdir(parents=True, exist_ok=True)

        filepath = task_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return filepath

    def load_json(self, task_id: str, filename: str) -> Any:
        """Load JSON data from a task's directory."""
        filepath = self.output_dir / task_id / filename
        if not filepath.exists():
            return None

        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_task_dir(self, task_id: str) -> Path:
        """Get the path to a task's directory."""
        return self.output_dir / task_id

    def task_exists(self, task_id: str) -> bool:
        """Check if a task directory exists."""
        return (self.output_dir / task_id).exists()

    def load_template(self, template_name: str) -> dict:
        """Load a template file from the templates directory."""
        template_path = self.settings.templates_dir / template_name
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_name}")

        with open(template_path, "r", encoding="utf-8") as f:
            return json.load(f)
