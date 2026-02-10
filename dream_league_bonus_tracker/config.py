"""Configuration management for Dream League Bonus Tracker."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
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
