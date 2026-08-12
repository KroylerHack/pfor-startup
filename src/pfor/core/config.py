"""
PFOR Platform — Application Configuration
Loads settings from environment variables or .env file.
"""
import secrets
from functools import lru_cache
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide settings loaded from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    POSTGRES_SERVER: str = "100.105.40.29"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "pfor_user"
    POSTGRES_PASSWORD: str = "pfor_password"
    POSTGRES_DB: str = "pfor_db"

    OLLAMA_BASE_URL: str = "http://100.105.40.29:11434"
    OLLAMA_MODEL: str = "llama3.1"

    secret_key: str = secrets.token_urlsafe(32)
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    allowed_origins: list[str] = ["*"]

    @property
    def database_url(self) -> str:
        password = quote_plus(str(self.POSTGRES_PASSWORD))
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{password}@"
            f"{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def postgres_server(self) -> str:
        return self.POSTGRES_SERVER

    @property
    def postgres_port(self) -> int:
        return self.POSTGRES_PORT

    @property
    def postgres_user(self) -> str:
        return self.POSTGRES_USER

    @property
    def postgres_password(self) -> str:
        return self.POSTGRES_PASSWORD

    @property
    def postgres_db(self) -> str:
        return self.POSTGRES_DB

    @property
    def ollama_base_url(self) -> str:
        return self.OLLAMA_BASE_URL

    @property
    def ollama_model(self) -> str:
        return self.OLLAMA_MODEL


@lru_cache()
def get_settings() -> Settings:
    """Return a cached singleton Settings instance."""
    return Settings()
