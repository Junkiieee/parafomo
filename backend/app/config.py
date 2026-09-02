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

    # Panelin/sitesinin herkese açık kök adresi — şifre sıfırlama linki bununla kurulur
    frontend_base_url: str = "https://parafomo.com"

    google_client_id: str = ""

    # Şifre sıfırlama token ömrü (dakika)
    reset_token_expire_minutes: int = 60

    # E-posta (SMTP). Boşsa mail GÖNDERİLMEZ; link sunucu loguna yazılır (geliştirme).
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "ParaFOMO <no-reply@parafomo.com>"
    smtp_starttls: bool = True

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def smtp_enabled(self) -> bool:
        return bool(self.smtp_host)

    @property
    def database_url(self) -> str:
        return f"sqlite:///{self.db_path}"


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    # DB dizinini garanti et
    Path(settings.db_path).parent.mkdir(parents=True, exist_ok=True)
    return settings
