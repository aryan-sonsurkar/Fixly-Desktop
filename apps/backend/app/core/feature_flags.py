from pydantic_settings import BaseSettings, SettingsConfigDict


class FeatureFlags(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="FEATURE_", env_file=".env", env_file_encoding="utf-8"
    )

    enable_ollama: bool = True
    enable_gemini: bool = True
    enable_email_intelligence: bool = True
    enable_ocr: bool = True
    enable_auto_updater: bool = True
    enable_experimental: bool = False


feature_flags = FeatureFlags()
