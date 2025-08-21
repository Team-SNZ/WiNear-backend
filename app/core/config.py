from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Mongo
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db: str = "winear"
    allowed_origins: list[str] = ["*"]
    

    # MongoDB Server API (Atlas 권장). 예: "1" (기본 활성화)
    mongodb_server_api: str | None = "1"

    # OpenAI / LLM 설정
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o"

    # Redis 설정
    redis_url: str = "redis://localhost:6379/0"

    # 외부 AI 백엔드 설정 (SNZ_RecSys)
    ai_backend_url: str = "http://winear-recsys-agent:8000"  # SNZ_RecSys 서버 (Docker Compose)
    ai_backend_recommendations_path: str = "/agent/recommend"
    ai_backend_timeout_seconds: float = 30.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="WINEAR_",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()

