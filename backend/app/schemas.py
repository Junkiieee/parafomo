"""Pydantic şemaları — istek/yanıt gövdeleri."""
from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from .models import AssetType

# Sayısal alanlar: NaN/Infinity reddedilir (JSON'a yazılamaz → kullanıcının tüm
# portföy uçları 500 dönüyordu) ve üst sınır konur (çarpım/toplam inf'e taşmasın).
_MAX_AMOUNT = 1e12


def _amount(**kw):
    return Field(gt=0, le=_MAX_AMOUNT, allow_inf_nan=False, **kw)


# ---- Auth ----
class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str | None = Field(default=None, max_length=120)


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(max_length=128)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class GoogleLogin(BaseModel):
    credential: str = Field(max_length=8192)  # Google Identity Services ID token (JWT)


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str = Field(max_length=256)
    new_password: str = Field(min_length=8, max_length=128)


class Message(BaseModel):
    message: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    display_name: str | None
    monthly_email: bool = True
    created_at: datetime


class UserUpdate(BaseModel):
    """Profil güncelleme — yalnız gönderilen alanlar değişir."""

    display_name: str | None = Field(default=None, max_length=120)
    monthly_email: bool | None = None


# ---- Holdings ----
class HoldingCreate(BaseModel):
    asset_type: AssetType
    symbol: str = Field(min_length=1, max_length=32)
    quantity: float = _amount()
    cost_price: float = _amount()
    purchase_date: date | None = None
    note: str | None = Field(default=None, max_length=280)


class HoldingUpdate(BaseModel):
    """Pozisyon düzenleme — yalnız gönderilen alanlar güncellenir."""

    quantity: float | None = _amount(default=None)
    cost_price: float | None = _amount(default=None)
    purchase_date: date | None = None
    note: str | None = Field(default=None, max_length=280)


class HoldingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    asset_type: AssetType
    symbol: str
    quantity: float
    cost_price: float
    purchase_date: date | None
    note: str | None
    created_at: datetime


class HoldingValued(HoldingOut):
    """Canlı fiyatla zenginleştirilmiş pozisyon."""

    current_price: float | None
    cost_value: float
    current_value: float | None
    profit_loss: float | None
    profit_loss_pct: float | None
    change_pct: float | None = None      # gün içi değişim %
    day_change: float | None = None      # gün içi K/Z (TL)


class PortfolioSummary(BaseModel):
    total_cost: float
    total_value: float
    total_profit_loss: float
    total_profit_loss_pct: float
    total_day_change: float | None = None
    total_day_change_pct: float | None = None
    holdings: list[HoldingValued]
    priced_at: datetime
    # Birim çevirileri için güncel kurlar (alınamazsa None)
    usd_try: float | None = None
    gold_gram_try: float | None = None
    # Satışlardan realize edilmiş kâr/zarar (işlem defterinden)
    realized_pl_total: float = 0.0
    realized_pl_year: float = 0.0


class SnapshotOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    day: date
    total_value: float
    total_cost: float


# ---- Fiyat alarmı ----
class AlertCreate(BaseModel):
    asset_type: AssetType
    symbol: str = Field(min_length=1, max_length=32)
    kind: Literal["price", "day_pct"] = "price"
    direction: Literal["above", "below"]
    threshold: float = _amount()
    repeat: bool = False


class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    asset_type: AssetType
    symbol: str
    kind: str
    direction: str
    threshold: float
    repeat: bool
    armed: bool
    active: bool
    triggered_at: datetime | None
    triggered_price: float | None
    created_at: datetime


# ---- İşlemler ----
class TxnCreate(BaseModel):
    asset_type: AssetType
    symbol: str = Field(min_length=1, max_length=32)
    side: Literal["buy", "sell"]
    quantity: float = _amount()
    price: float = _amount()
    trade_date: date | None = None
    note: str | None = Field(default=None, max_length=280)


class TxnOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    asset_type: AssetType
    symbol: str
    side: str
    quantity: float
    price: float
    trade_date: date | None
    realized_pl: float | None
    note: str | None
    created_at: datetime


# ---- Hedefler ----
class GoalCreate(BaseModel):
    kind: Literal["try", "usd", "gold_g"]
    target: float = _amount()
    title: str | None = Field(default=None, max_length=80)


class GoalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    kind: str
    target: float
    title: str | None
    created_at: datetime


# ---- İzleme listesi ----
class WatchCreate(BaseModel):
    asset_type: AssetType
    symbol: str = Field(min_length=1, max_length=32)


class WatchOut(BaseModel):
    id: int
    asset_type: AssetType
    symbol: str
    current_price: float | None
    change_pct: float | None


# ---- Bülten ----
class NewsletterSubscribe(BaseModel):
    email: EmailStr
    consent: bool
    source: str | None = Field(default=None, max_length=200)
    # Bal küpü: insan bunu görmez/doldurmaz; dolu gelirse bot say.
    website: str | None = Field(default=None, max_length=200)
