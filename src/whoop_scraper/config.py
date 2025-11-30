"""Configuration management via environment variables."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def get_default_token_path() -> str:
    """Get the default token path in ~/.config/whoop-scraper/tokens.json."""
    return str(Path.home() / ".config" / "whoop-scraper" / "tokens.json")


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All configuration is done via environment variables.
    Prefix WHOOP_ is used for all settings.
    Loads from .env file if present.
    """

    # Database settings
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "health"
    db_user: str = "health"
    db_password: str = ""

    # Whoop OAuth2 settings
    client_id: str = ""
    client_secret: str = ""
    access_token: str = ""  # Can be set via env var for containerized deployments
    refresh_token: str = ""  # Can be set via env var for containerized deployments
    token_path: str = ""  # Defaults to ~/.config/whoop-scraper/tokens.json

    # Security settings
    encryption_key: str = ""  # Fernet key for encrypting tokens in database

    # Scraping settings
    scrape_days: int = 7  # Number of days to scrape

    model_config = SettingsConfigDict(
        env_prefix="WHOOP_",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    @property
    def database_url(self) -> str:
        """Construct PostgreSQL connection URL."""
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"


def get_settings() -> Settings:
    """Get application settings singleton."""
    return Settings()
