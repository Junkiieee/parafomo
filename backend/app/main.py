"""ParaFOMO Portföy Takip API — FastAPI uygulaması."""
from __future__ import annotations

import math
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import get_settings
from .db import init_db
from .routers import auth, inbox, newsletter, portfolio, public

_settings = get_settings()

# İstek gövdesi üst sınırı: uvicorn/Caddy varsayılanı sınırsız; gövde belleğe okunur.
_MAX_BODY = 64 * 1024
_MAX_BODY_INBOX = 6 * 1024 * 1024  # ham e-posta (worker 5 MB üstünü zaten reddediyor)
_NO_STORE_PREFIXES = ("/auth", "/portfolio", "/inbox")


class _GuardMiddleware:
    """Saf ASGI (BackgroundTasks'ı geciktirmez): gövde boyutu sınırı + güvenlik başlıkları."""

    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        path = scope.get("path", "")
        limit = _MAX_BODY_INBOX if path.startswith("/inbox/") else _MAX_BODY
        for name, value in scope.get("headers", []):
            if name == b"content-length":
                if not value.isdigit() or int(value) > limit:
                    resp = JSONResponse({"detail": "İstek gövdesi çok büyük."}, status_code=413)
                    return await resp(scope, receive, send)
        received = 0

        async def limited_receive():
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > limit:  # chunked gövde: okurken say
                    raise HTTPException(status_code=413, detail="İstek gövdesi çok büyük.")
            return message

        no_store = path.startswith(_NO_STORE_PREFIXES)

        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((b"x-content-type-options", b"nosniff"))
                # kişisel finans verisi ara katmanda/tarayıcıda önbelleğe girmesin
                if no_store and not any(k.lower() == b"cache-control" for k, _ in headers):
                    headers.append((b"cache-control", b"no-store"))
                message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, limited_receive, send_with_headers)


def _json_safe(value):
    """422 gövdesi gelen değeri ('input') yankılar; NaN/Infinity JSON'a yazılamaz → 500 olmasın."""
    if isinstance(value, float) and not math.isfinite(value):
        return str(value)
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    return value


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

# Guard CORS'un İÇİNDE: 413 yanıtı da CORS başlığı alsın (uygulama hatayı okuyabilsin)
app.add_middleware(_GuardMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def _validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": _json_safe(jsonable_encoder(exc.errors()))})


app.include_router(auth.router)
app.include_router(portfolio.router)
app.include_router(public.router)
app.include_router(newsletter.router)
app.include_router(inbox.router)


@app.get("/health", tags=["meta"])
def health() -> dict:
    return {"status": "ok"}
