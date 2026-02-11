"""Configuration management for Dream League Bonus Tracker."""

import sys
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def _get_env_file() -> str:
    """Resolve .env file path (works both in dev and packaged .exe)."""
    if getattr(sys, "frozen", False):
        # Running as PyInstaller .exe - look next to the executable
        return str(Path(sys.executable).parent / ".env")
    return ".env"


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    model_config = SettingsConfigDict(
        env_file=_get_env_file(),
        env_file_encoding="utf-8",
        env_prefix="DREAMTEAM_",
    )

    email: str = ""
    password: str = ""
    season_id: int = 6
    base_url: str = "https://dreamteam.sport5.co.il"


def get_settings() -> Settings:
    """Create and return a Settings instance."""
    return Settings()
