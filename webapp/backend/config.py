from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Supabase
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str

    # Gemini
    gemini_api_key: str = ""

    # Resend email service
    resend_api_key: str = ""
    app_url: str = "http://localhost:5173"

    # Pipeline defaults (can be overridden per-scan via config payload)
    osint_threshold: float = 0.75
    osint_model: str = "gemini-2.5-flash"
    osint_batch_size: int = 20
    osint_skip_noise: bool = True
    osint_retry_sleep: int = 20

    # Path to the CLI project's src/ directory
    pipeline_src_dir: Path = Path(__file__).resolve().parents[2] / "project" / "src"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
