"""Veritabanı modelleri: kullanıcı ve portföy varlıkları."""
from __future__ import annotations

import enum
from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Enum, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AssetType(str, enum.Enum):
    """Varlık tipi. Fiyat kaynağı buna göre seçilir."""

    BIST = "bist"        # BIST hissesi — symbol = ticker (ör. THYAO), Yahoo <symbol>.IS
    GOLD = "gold"        # Altın (gram, 24 ayar) — Truncgil
    SILVER = "silver"    # Gümüş (gram) — Truncgil


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    # Google-only kullanıcılarda parola olmayabilir (sonraki gece)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    google_sub: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    display_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    holdings: Mapped[list["Holding"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Holding(Base):
    """Kullanıcının portföyündeki tek bir pozisyon (manuel giriş)."""

    __tablename__ = "holdings"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    asset_type: Mapped[AssetType] = mapped_column(Enum(AssetType), nullable=False)
    # BIST için ticker (THYAO); altın/gümüş için "GOLD"/"SILVER" sabiti
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    # adet (hisse) veya gram (altın/gümüş)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    # birim alış fiyatı (TL)
    cost_price: Mapped[float] = mapped_column(Float, nullable=False)
    purchase_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    note: Mapped[str | None] = mapped_column(String(280), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    user: Mapped["User"] = relationship(back_populates="holdings")


class PasswordResetToken(Base):
    """Şifre sıfırlama tek-kullanımlık token'ı (hash'li saklanır)."""

    __tablename__ = "password_reset_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
