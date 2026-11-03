"""Canlı fiyat servisi — ücretsiz kaynaklar.

BIST hisseleri : Yahoo Finance chart API (<TICKER>.IS)
Altın / Gümüş  : Truncgil v3 today.json (gram-altin / gumus, Selling)

Paralı API KULLANILMAZ (kullanıcı kararı 2026-08-30). Bir eksik çıkarsa
tasks-for-user.md'ye yazılır. Fiyatlar kısa süreli cache'lenir (kaynakları
yormamak + hız). Tüm fiyatlar TL cinsindendir.
"""
from __future__ import annotations

import math
import re
import time

import httpx

from .models import AssetType

_TRUNCGIL_URL = "https://finans.truncgil.com/v3/today.json"
_YAHOO_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}.IS"
_UA = "Mozilla/5.0 (ParaFOMO Portfolio)"
# Kaynak asılırsa istek de asılmasın (özet her pozisyon için sırayla fiyat çeker)
_TIMEOUT = httpx.Timeout(10.0, connect=5.0)

# Basit TTL cache: {cache_key: (timestamp, (price, change_pct))}
_CACHE: dict[str, tuple[float, tuple[float, float | None]]] = {}
_TTL_SECONDS = 120

# Başarısız çekimi kısa süre hatırla: uydurma sembol her özet çağrısında yeniden
# denenmesin (sembol başına _FAIL_TTL). Kaynak ZAMAN AŞIMINA düşerse (asılı) o kaynağı
# _DOWN_TTL boyunca hiç deneme — yoksa özet her pozisyon için sırayla 10 sn bekler.
# Hızlı hatalarda (bağlantı reddi, 5xx) kaynak kapatılmaz: gece cron'ları her sembolü dener.
_FAIL_TTL = 60
_DOWN_TTL = 30
_FAILED: dict[str, float] = {}

# BIST kodu URL yoluna girer: yalnız harf/rakam (../, ?, # ile Yahoo'da başka uç çağrılmasın)
_BIST_RE = re.compile(r"[A-Z0-9]{1,12}")


def is_valid_bist_symbol(symbol: str) -> bool:
    return bool(_BIST_RE.fullmatch(symbol or ""))


def _failed_recently(key: str) -> bool:
    until = _FAILED.get(key)
    if until is None:
        return False
    if until > time.time():
        return True
    _FAILED.pop(key, None)
    return False


def _mark_failed(key: str, ttl: float = _FAIL_TTL) -> None:
    if len(_FAILED) > 10_000:  # uydurma sembollerle şişmesin
        _FAILED.clear()
    _FAILED[key] = time.time() + ttl


def _num(value) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        f = float(value)
    else:
        try:
            f = float(str(value).strip().replace(".", "").replace(",", "."))
        except ValueError:
            return None
    return f if math.isfinite(f) else None


def _pct(value) -> float | None:
    """Truncgil 'Change' alanı ('%0,43' / '%-1,2') → float yüzde."""
    if value is None:
        return None
    s = str(value).strip().replace("%", "").replace(".", "").replace(",", ".")
    try:
        f = float(s)
    except ValueError:
        return None
    return f if math.isfinite(f) else None


def _cache_get(key: str) -> tuple[float, float | None] | None:
    hit = _CACHE.get(key)
    if hit and (time.time() - hit[0]) < _TTL_SECONDS:
        return hit[1]
    return None


def _cache_set(key: str, quote: tuple[float, float | None]) -> None:
    _CACHE[key] = (time.time(), quote)


_TRUNCGIL_DOC: tuple[float, dict] | None = None


def _fetch_truncgil() -> dict:
    """today.json — altın/gümüş/döviz aynı belgeden: TTL boyunca tek çekim.
    Zaman aşımına düştüyse _DOWN_TTL boyunca denemeden ValueError (çağıranlar yakalıyor)."""
    global _TRUNCGIL_DOC
    now = time.time()
    if _TRUNCGIL_DOC is not None and now - _TRUNCGIL_DOC[0] < _TTL_SECONDS:
        return _TRUNCGIL_DOC[1]
    if _failed_recently("src:truncgil"):
        raise ValueError("truncgil geçici olarak erişilemez")
    try:
        with httpx.Client(timeout=_TIMEOUT, headers={"User-Agent": _UA}) as client:
            r = client.get(_TRUNCGIL_URL)
            r.raise_for_status()
            data = r.json()
    except httpx.TimeoutException:
        _mark_failed("src:truncgil", _DOWN_TTL)
        raise
    if not isinstance(data, dict):
        raise ValueError("beklenmeyen truncgil yanıtı")
    _TRUNCGIL_DOC = (now, data)
    return data


def _gold_silver_quote(asset_type: AssetType) -> tuple[float, float | None] | None:
    key = "gram-altin" if asset_type is AssetType.GOLD else "gumus"
    cached = _cache_get(key)
    if cached is not None:
        return cached
    try:
        data = _fetch_truncgil()
    except (httpx.HTTPError, ValueError):
        return None
    entry = data.get(key)
    price = _num(entry.get("Selling")) if isinstance(entry, dict) else None
    if price is None:
        return None
    quote = (price, _pct(entry.get("Change")))
    _cache_set(key, quote)
    return quote


def _fx_quote(asset_type: AssetType) -> tuple[float, float | None] | None:
    """Döviz kuru (USD/EUR satış) — Truncgil, gold ile aynı desen."""
    key = "USD" if asset_type is AssetType.USD else "EUR"
    cached = _cache_get("fx:" + key)
    if cached is not None:
        return cached
    try:
        data = _fetch_truncgil()
    except (httpx.HTTPError, ValueError):
        return None
    entry = data.get(key)
    price = _num(entry.get("Selling")) if isinstance(entry, dict) else None
    if price is None:
        return None
    quote = (price, _pct(entry.get("Change")))
    _cache_set("fx:" + key, quote)
    return quote


_COINGECKO_URL = ("https://api.coingecko.com/api/v3/simple/price"
                  "?ids=bitcoin,ethereum&vs_currencies=try&include_24hr_change=true")


def _crypto_quote(asset_type: AssetType) -> tuple[float, float | None] | None:
    """BTC/ETH TL fiyatı + 24s değişim — CoinGecko (tek çağrı iki koin, cache ortak)."""
    coin = "bitcoin" if asset_type is AssetType.BTC else "ethereum"
    cached = _cache_get("cg:" + coin)
    if cached is not None:
        return cached
    if _failed_recently("src:coingecko"):
        return None
    try:
        with httpx.Client(timeout=_TIMEOUT, headers={"User-Agent": _UA}) as client:
            r = client.get(_COINGECKO_URL)
            r.raise_for_status()
            data = r.json()
        if not isinstance(data, dict):
            raise ValueError("beklenmeyen coingecko yanıtı")
    except httpx.TimeoutException:
        _mark_failed("src:coingecko", _DOWN_TTL)
        return None
    except (httpx.HTTPError, ValueError):
        return None
    for cid in ("bitcoin", "ethereum"):
        entry = data.get(cid)
        if not isinstance(entry, dict):
            continue
        price = _num(entry.get("try"))
        if price is not None:
            chg = _num(entry.get("try_24h_change"))
            _cache_set("cg:" + cid, (price, round(chg, 2) if chg is not None else None))
    return _cache_get("cg:" + coin)


def get_usd_try() -> float | None:
    """Güncel USD/TRY satış kuru (Truncgil); alınamazsa None."""
    cached = _cache_get("usd-try")
    if cached is not None:
        return cached[0]
    try:
        data = _fetch_truncgil()
    except (httpx.HTTPError, ValueError):
        return None
    entry = data.get("USD")
    price = _num(entry.get("Selling")) if isinstance(entry, dict) else None
    if price is None:
        return None
    _cache_set("usd-try", (price, None))
    return price


def _bist_quote(ticker: str) -> tuple[float, float | None] | None:
    ticker = ticker.strip().upper()
    if not is_valid_bist_symbol(ticker):
        return None
    cache_key = f"bist:{ticker}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached
    if _failed_recently(cache_key) or _failed_recently("src:yahoo"):
        return None
    try:
        with httpx.Client(timeout=_TIMEOUT, headers={"User-Agent": _UA}) as client:
            r = client.get(_YAHOO_URL.format(symbol=ticker))
            r.raise_for_status()
            data = r.json()
        result = (data.get("chart") or {}).get("result") or []
        meta = result[0].get("meta") if result else None
        price = _num(meta.get("regularMarketPrice")) if meta else None
    except httpx.TimeoutException:
        # Yahoo asılı → kısa süre hiç deneme (sıradaki semboller 10'ar sn beklemesin)
        _mark_failed("src:yahoo", _DOWN_TTL)
        return None
    except (httpx.HTTPError, ValueError, KeyError, IndexError, AttributeError, TypeError):
        _mark_failed(cache_key)
        return None
    if price is None:
        _mark_failed(cache_key)
        return None
    prev = _num(meta.get("previousClose")) or _num(meta.get("chartPreviousClose"))
    change_pct = ((price - prev) / prev * 100) if prev else None
    quote = (price, change_pct)
    _cache_set(cache_key, quote)
    return quote


def get_quote(asset_type: AssetType, symbol: str) -> tuple[float, float | None] | None:
    """Güncel (birim fiyat TL, gün içi değişim %) döndürür; alınamazsa None."""
    if asset_type is AssetType.BIST:
        return _bist_quote(symbol)
    if asset_type in (AssetType.GOLD, AssetType.SILVER):
        return _gold_silver_quote(asset_type)
    if asset_type in (AssetType.USD, AssetType.EUR):
        return _fx_quote(asset_type)
    if asset_type in (AssetType.BTC, AssetType.ETH):
        return _crypto_quote(asset_type)
    if asset_type is AssetType.CASH:
        return (1.0, 0.0)
    return None


def get_price(asset_type: AssetType, symbol: str) -> float | None:
    """Bir varlığın güncel birim fiyatını (TL) döndürür; alınamazsa None."""
    quote = get_quote(asset_type, symbol)
    return quote[0] if quote else None


# ---- tarihsel seri (varlık detay grafiği) ----
_HIST_TTL = 3600
_HIST_CACHE: dict[str, tuple[float, list[dict]]] = {}
_HIST_RANGES = {"3mo": "1d", "1y": "1d", "5y": "1wk"}


def get_bist_history(ticker: str, rng: str) -> list[dict] | None:
    """BIST kapanış serisi [{t: 'YYYY-MM-DD', p: fiyat}] — Yahoo, 1 saat cache."""
    if rng not in _HIST_RANGES:
        return None
    ticker = ticker.strip().upper()
    if not is_valid_bist_symbol(ticker):
        return None
    key = f"hist:{ticker}:{rng}"
    hit = _HIST_CACHE.get(key)
    if hit and (time.time() - hit[0]) < _HIST_TTL:
        return hit[1]
    if _failed_recently(key) or _failed_recently("src:yahoo"):
        return None
    url = _YAHOO_URL.format(symbol=ticker)
    import datetime as _dt
    try:
        with httpx.Client(timeout=_TIMEOUT, headers={"User-Agent": _UA}) as client:
            r = client.get(url, params={"range": rng, "interval": _HIST_RANGES[rng]})
            r.raise_for_status()
            data = r.json()
        res = data["chart"]["result"][0]
        ts = res["timestamp"]
        closes = res["indicators"]["quote"][0]["close"]
        points = [
            {"t": _dt.datetime.fromtimestamp(t, tz=_dt.timezone.utc).strftime("%Y-%m-%d"),
             "p": round(p, 4)}
            for t, c in zip(ts, closes) if (p := _num(c)) is not None
        ]
    except httpx.TimeoutException:
        _mark_failed("src:yahoo", _DOWN_TTL)
        return None
    except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError, OverflowError, OSError):
        _mark_failed(key)
        return None
    if not points:
        return None
    _HIST_CACHE[key] = (time.time(), points)
    return points
