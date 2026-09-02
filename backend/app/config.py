"""Uygulama ayarları — ortam değişkenlerinden okunur (backend/.env)."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_prefix="PORTFOLIO_",
        extra="ignore",
    )

    jwt_secret: str = "dev-insecure-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 gün

    db_path: str = str(Path.home() / "parafomo-data" / "portfolio.db")

    cors_origins: str = "http://localhost:4321"

    google_client_id: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def database_url(self) -> str:
        return f"sqlite:///{self.db_path}"


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    # DB dizinini garanti et
    Path(settings.db_path).parent.mkdir(parents=True, exist_ok=True)
    return settings
