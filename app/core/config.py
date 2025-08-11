from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db: str = "winear"
    allowed_origins: list[str] = ["*"]
    

    # MongoDB Server API (Atlas 권장). 예: "1" (기본 활성화)
    mongodb_server_api: str | None = "1"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="WINEAR_",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()

