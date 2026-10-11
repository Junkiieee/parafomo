"""Veritabanı modelleri: kullanıcı ve portföy varlıkları."""
from __future__ import annotations

import enum
from datetime import date, datetime, timezone

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    String,
    UniqueConstraint,
    func,
)
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
    # Ay sonu portföy özeti e-postası (kullanıcı kapatabilir)
    monthly_email: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
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


class PortfolioSnapshot(Base):
    """Kullanıcı portföyünün günlük toplam değeri (değer grafiği için).

    Gün başına tek satır: /portfolio/summary çağrısı günün satırını tazeler,
    gece cron'u (scripts/portfolio-snapshot.py) girmeyen kullanıcılar için alır.
    """

    __tablename__ = "portfolio_snapshots"
    __table_args__ = (UniqueConstraint("user_id", "day", name="uq_snapshot_user_day"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    day: Mapped[date] = mapped_column(Date, nullable=False)  # UTC günü
    total_value: Mapped[float] = mapped_column(Float, nullable=False)
    total_cost: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class PriceAlert(Base):
    """Tek seferlik fiyat alarmı: eşik aşılınca e-posta gönderilir ve pasifleşir."""

    __tablename__ = "price_alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    asset_type: Mapped[AssetType] = mapped_column(Enum(AssetType), nullable=False)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    # kind: "price" = fiyat eşiği (₺) · "day_pct" = günlük değişim eşiği (%)
    kind: Mapped[str] = mapped_column(String(10), default="price", nullable=False)
    direction: Mapped[str] = mapped_column(String(5), nullable=False)  # "above" | "below"
    threshold: Mapped[float] = mapped_column(Float, nullable=False)
    # repeat: tetiklenince kapanmaz; koşul düzelince yeniden kurulur (armed)
    repeat: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    armed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    triggered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # tetiklendiği andaki fiyat (e-postada ve listede gösterilir)
    triggered_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Transaction(Base):
    """İşlem defteri: lot lot alım/satım kaydı (append-only).

    holdings tablosu POZİSYON özetidir (güncel miktar + ortalama maliyet);
    burası tarihçedir. Satışta realized_pl = (satış fiyatı − o anki ortalama
    maliyet) × miktar olarak hesaplanıp satıra yazılır.
    """

    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    asset_type: Mapped[AssetType] = mapped_column(Enum(AssetType), nullable=False)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    side: Mapped[str] = mapped_column(String(4), nullable=False)  # "buy" | "sell"
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)   # birim ₺
    trade_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    realized_pl: Mapped[float | None] = mapped_column(Float, nullable=True)  # yalnız satışta
    note: Mapped[str | None] = mapped_column(String(280), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Goal(Base):
    """Birikim hedefi: toplam değer TL / USD / gram altın cinsinden eşik."""

    __tablename__ = "goals"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    # "try" = TL değer · "usd" = dolar karşılığı · "gold_g" = gram altın karşılığı
    kind: Mapped[str] = mapped_column(String(12), nullable=False)
    target: Mapped[float] = mapped_column(Float, nullable=False)
    title: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class WatchItem(Base):
    """İzleme listesi: sahip olmadan fiyatı takip edilen varlık."""

    __tablename__ = "watch_items"
    __table_args__ = (
        UniqueConstraint("user_id", "asset_type", "symbol", name="uq_watch_user_symbol"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    asset_type: Mapped[AssetType] = mapped_column(Enum(AssetType), nullable=False)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


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


class NewsletterSubscriber(Base):
    """Bülten abonesi — çift onaylı (pending → confirmed; çıkınca unsubscribed).

    token: onay + çıkış linklerinde kullanılan rastgele, tahmin edilemez anahtar.
    Hesap verisi değil; yalnız e-posta + onay kaydı (KVKK açık rıza zamanı) tutulur.
    """

    __tablename__ = "newsletter_subscribers"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="pending", nullable=False)
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    source: Mapped[str | None] = mapped_column(String(200), nullable=True)
    consent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    confirm_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    unsubscribed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
