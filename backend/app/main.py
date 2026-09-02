"""ParaFOMO Portföy Takip API — FastAPI uygulaması."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .db import init_db
from .routers import auth, portfolio, public

_settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="ParaFOMO Portföy API",
    version="0.1.0",
    description="Ücretsiz portföy takip sistemi — BIST hisse + altın + gümüş.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(portfolio.router)
app.include_router(public.router)


@app.get("/health", tags=["meta"])
def health() -> dict:
    return {"status": "ok"}
