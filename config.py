from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # ── Anthropic / Gemini ──────────────────────────────────────────────────────
    anthropic_api_key: str = ""
    gemini_api_key: str = "AIzaSyAJOZe_R4LFIos3N215KSfEy6KqwOPb528"
    claude_model: str = "claude-sonnet-4-20250514"
    claude_max_tokens: int = 1200
    claude_timeout: int = 30          # seconds

    # ── Ollama ─────────────────────────────────────────────────────────────────
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"
    ollama_timeout: int = 60          # seconds (local model is slower)

    # ── App ────────────────────────────────────────────────────────────────────
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = False

    # Max base64 payload size (~50MB audio file)
    max_audio_b64_bytes: int = 70_000_000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
