from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    supabase_url: str = ""
    supabase_anon_key: str = ""
    gemini_api_key: str = ""
    ollama_host: str = "http://localhost:11434"
    environment: str = "development"
    cors_origins: list[str] = ["*"]


settings = Settings()
