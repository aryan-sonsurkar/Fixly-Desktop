import os

from pydantic_settings import BaseSettings, SettingsConfigDict


def _env_file() -> str:
    return os.environ.get("FIXLY_ENV_FILE", ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_env_file(), env_file_encoding="utf-8", extra="ignore")

    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    supabase_jwt_secret: str = ""
    gemini_api_key: str = ""
    ollama_host: str = "http://localhost:11434"
    google_client_id: str = ""
    google_client_secret: str = ""
    environment: str = "development"
    cors_origins: list[str] = ["*"]


settings = Settings()
