"""Configuration settings management via Pydantic Settings."""

from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings and environment variable validation."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # API Keys
    rapidapi_key: Optional[str] = Field(default=None, alias="RAPIDAPI_KEY")
    rapidapi_host: str = Field(default="unogsng.p.rapidapi.com", alias="RAPIDAPI_HOST")
    tmdb_api_key: Optional[str] = Field(default=None, alias="TMDB_API_KEY")
    tmdb_read_access_token: Optional[str] = Field(default=None, alias="TMDB_READ_ACCESS_TOKEN")

    # PostgreSQL Database
    db_host: str = Field(default="localhost", alias="DB_HOST")
    db_port: int = Field(default=5432, alias="DB_PORT")
    db_name: str = Field(default="streampulse", alias="DB_NAME")
    db_user: str = Field(default="postgres", alias="DB_USER")
    db_password: str = Field(default="postgres", alias="DB_PASSWORD")
    db_schema_staging: str = Field(default="staging", alias="DB_SCHEMA_STAGING")
    db_schema_reporting: str = Field(default="reporting", alias="DB_SCHEMA_REPORTING")

    # Pipeline Settings
    app_env: str = Field(default="development", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    batch_size: int = Field(default=100, alias="BATCH_SIZE")
    fuzzy_match_threshold: float = Field(default=85.0, alias="FUZZY_MATCH_THRESHOLD")

    @property
    def database_url(self) -> str:
        """Construct SQLAlchemy PostgreSQL connection string."""
        return (
            f"postgresql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


settings = Settings()
