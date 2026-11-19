"""Bellek içi kayan pencere hız sınırlayıcı + gerçek istemci IP'si.

Servis tek uvicorn süreciyle çalışır (deploy/parafomo-api.service) — sayaçlar
süreç içinde tutulur, yeniden başlatınca sıfırlanır. Uçların sınırları
kendi router dosyalarında tanımlıdır.
"""
from __future__ import annotations

import ipaddress
import threading
import time
from collections import deque

from fastapi import HTTPException, Request, status

from .config import get_settings


def client_ip(request: Request) -> str:
    """Hız sınırı anahtarı olarak istemci IP'si.

    Caddy → uvicorn: uvicorn proxy-headers (127.0.0.1 güvenilir) X-Forwarded-For'dan
    gerçek IP'yi request.client'a yazar. CF-Connecting-IP'ye yalnız ayar açıksa güvenilir
    (DNS-only kurulumda istemci bu başlığı istediği gibi yazar).
    """
    ip = ""
    if get_settings().trust_cf_connecting_ip:
        ip = (request.headers.get("cf-connecting-ip") or "").strip()
    if not ip:
        ip = request.client.host if request.client else "?"
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return ip[:64]
    if addr.version == 6:
        if addr.ipv4_mapped:
            return str(addr.ipv4_mapped)
        # IPv6'da tek abone /64 içinde sınırsız adres döndürebilir → ağı anahtar yap
        return str(ipaddress.ip_network(f"{addr}/64", strict=False))
    return str(addr)


class RateLimiter:
    """Anahtar başına `window` saniyede en fazla `limit` olay.

    Bellek sınırlı: süresi geçen anahtarlar pencere başına bir kez süpürülür,
    anahtar sayısı max_keys'i aşarsa en eskiler atılır (çok IP'li saldırıda şişmesin).
    """

    def __init__(self, limit: int, window: float, max_keys: int = 50_000) -> None:
        self.limit = limit
        self.window = window
        self.max_keys = max_keys
        self._hits: dict[str, deque] = {}
        self._lock = threading.Lock()
        self._last_sweep = time.monotonic()

    def _sweep(self, now: float) -> None:
        if now - self._last_sweep >= self.window:
            self._last_sweep = now
            for key in [k for k, q in self._hits.items() if not q or now - q[-1] > self.window]:
                del self._hits[key]
        while len(self._hits) > self.max_keys:
            del self._hits[next(iter(self._hits))]

    def _queue(self, key: str, now: float) -> deque:
        q = self._hits.get(key)
        if q is None:
            q = self._hits[key] = deque()
        while q and now - q[0] > self.window:
            q.popleft()
        return q

    def allowed(self, key: str) -> bool:
        """Kaydetmeden: bu anahtar şu an sınırın altında mı?"""
        now = time.monotonic()
        with self._lock:
            q = self._hits.get(key)
            if q is None:
                return self.limit > 0
            return len(self._queue(key, now)) < self.limit

    def hit(self, key: str) -> bool:
        """Olayı kaydet; sınır aşılmışsa kaydetmeden False döner."""
        now = time.monotonic()
        with self._lock:
            self._sweep(now)
            q = self._queue(key, now)
            if len(q) >= self.limit:
                return False
            q.append(now)
            return True

    def reset(self, key: str) -> None:
        with self._lock:
            self._hits.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._hits.clear()


def enforce(limiter: RateLimiter, key: str, detail: str | None = None) -> None:
    """Sınır aşıldıysa 429 fırlat."""
    if not limiter.hit(key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail or "Çok fazla deneme. Lütfen birkaç dakika sonra tekrar dene.",
        )


class MailBudget:
    """Üyeliksiz uçlardan (sıfırlama, bülten onayı) çıkan TÜM e-postalar için ortak bütçe.

    Saatlik sınır patlamayı keser (özellik bir saat içinde toparlanır); günlük sınır SMTP
    kotasını (Brevo ücretsiz: 300/gün) alarm/aylık özet/bülten için korur.
    """

    def __init__(self, per_hour: int, per_day: int) -> None:
        self.hour = RateLimiter(limit=max(per_hour, 0), window=3600, max_keys=10)
        self.day = RateLimiter(limit=max(per_day, 0), window=86400, max_keys=10)
        self._lock = threading.Lock()

    def hit(self, key: str = "mail") -> bool:
        with self._lock:
            if not (self.hour.allowed(key) and self.day.allowed(key)):
                return False
            self.hour.hit(key)
            self.day.hit(key)
            return True

    def clear(self) -> None:
        self.hour.clear()
        self.day.clear()


public_mail_budget = MailBudget(get_settings().public_mail_per_hour, get_settings().public_mail_per_day)
