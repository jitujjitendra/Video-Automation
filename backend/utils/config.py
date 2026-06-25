"""Settings and configuration management for the AI Video Automation Agent."""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent


class Settings:
    """Application settings loaded from environment variables."""

    def __init__(self):
        self.gemini_api_key: Optional[str] = os.getenv("GEMINI_API_KEY")
        self.host: str = os.getenv("HOST", "0.0.0.0")
        self.port: int = int(os.getenv("PORT", "8000"))
        self.output_dir: Path = PROJECT_ROOT / os.getenv("OUTPUT_DIR", "outputs")
        self.templates_dir: Path = PROJECT_ROOT / "templates"

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @property
    def has_api_key(self) -> bool:
        """Check if a valid API key is configured."""
        return bool(self.gemini_api_key and self.gemini_api_key != "your_key_here")

    def update_api_key(self, key: str) -> None:
        """Update the API key at runtime."""
        self.gemini_api_key = key


# Singleton settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get the global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
