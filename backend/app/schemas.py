"""Pydantic şemaları — istek/yanıt gövdeleri."""
from __future__ import annotations

from datetime import date, datetime

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
    created_at: datetime


# ---- Holdings ----
class HoldingCreate(BaseModel):
    asset_type: AssetType
    symbol: str = Field(min_length=1, max_length=32)
    quantity: float = Field(gt=0)
    cost_price: float = Field(gt=0)
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


class PortfolioSummary(BaseModel):
    total_cost: float
    total_value: float
    total_profit_loss: float
    total_profit_loss_pct: float
    holdings: list[HoldingValued]
    priced_at: datetime
