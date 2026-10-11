"""Pydantic şemaları — istek/yanıt gövdeleri."""
from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from .models import AssetType


# ---- Auth ----
class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str | None = Field(default=None, max_length=120)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class GoogleLogin(BaseModel):
    credential: str  # Google Identity Services ID token (JWT)


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
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
    quantity: float = Field(gt=0)
    cost_price: float = Field(gt=0)
    purchase_date: date | None = None
    note: str | None = Field(default=None, max_length=280)


class HoldingUpdate(BaseModel):
    """Pozisyon düzenleme — yalnız gönderilen alanlar güncellenir."""

    quantity: float | None = Field(default=None, gt=0)
    cost_price: float | None = Field(default=None, gt=0)
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
    threshold: float = Field(gt=0)
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


# ---- Hedefler ----
class GoalCreate(BaseModel):
    kind: Literal["try", "usd", "gold_g"]
    target: float = Field(gt=0)
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
