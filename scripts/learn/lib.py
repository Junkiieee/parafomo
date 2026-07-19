#!/usr/bin/env python3
"""
ParaFOMO — Öğrenme döngüsü ortak kütüphanesi.

Tüm learn/ scriptleri buradan yol, kimlik, jsonl G/Ç, bandit ve skorlama
yardımcılarını alır. Hiçbir yan etki yok — sadece fonksiyonlar.

Veri dosyaları (data/learning/, hepsi .gitignore'lu):
  content-ledger.jsonl  — yayınlanan her içerik + nitelikleri (build_ledger üretir)
  metrics.jsonl         — zaman-serisi metrik anlık görüntüleri (metrics_* üretir)
  winners.json          — karar çıktısı (decide üretir; üreticiler okur)
"""
import os
import re
import json
import hashlib
import datetime as dt

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, "data", "learning")
LOGS = os.path.join(ROOT, "logs")
SOCIAL = os.path.join(ROOT, "public", "social")
BLOG = os.path.join(ROOT, "src", "content", "blog")

LEDGER = os.path.join(DATA, "content-ledger.jsonl")
METRICS = os.path.join(DATA, "metrics.jsonl")
WINNERS = os.path.join(DATA, "winners.json")

CONFIG_DIR = os.path.expanduser("~/.config/parafomo")
GA_SA = os.path.join(CONFIG_DIR, "ga-sa.json")
YT_OAUTH = os.path.join(CONFIG_DIR, "youtube_oauth.json")
IG_ENV = os.path.join(CONFIG_DIR, "instagram.env")

os.makedirs(DATA, exist_ok=True)


# --------------------------- zaman ---------------------------

def now_utc():
    return dt.datetime.now(dt.timezone.utc)


def iso(d=None):
    return (d or now_utc()).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_dt(s):
    """Esnek ISO/tarih ayrıştırıcı → aware UTC datetime (ya da None)."""
    if not s:
        return None
    s = s.strip().replace("Z", "+00:00")
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            d = dt.datetime.strptime(s, fmt)
            if d.tzinfo is None:
                d = d.replace(tzinfo=dt.timezone.utc)
            return d.astimezone(dt.timezone.utc)
        except ValueError:
            continue
    try:
        d = dt.datetime.fromisoformat(s)
        return (d if d.tzinfo else d.replace(tzinfo=dt.timezone.utc)).astimezone(dt.timezone.utc)
    except ValueError:
        return None


# --------------------------- jsonl ---------------------------

def read_jsonl(path):
    if not os.path.exists(path):
        return []
    out = []
    with open(path, encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if ln:
                try:
                    out.append(json.loads(ln))
                except json.JSONDecodeError:
                    pass
    return out


def write_jsonl(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def append_jsonl(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


# --------------------------- env ---------------------------

def load_env(path):
    env = {}
    if not os.path.exists(path):
        return env
    for ln in open(path, encoding="utf-8"):
        ln = ln.strip()
        if "=" in ln and not ln.startswith("#"):
            k, v = ln.split("=", 1)
            env[k.strip()] = v.strip()
    return env


# --------------------------- kimlik ---------------------------

def ga_credentials(scopes):
    """Servis hesabı (GSC + GA4). Yoksa None."""
    if not os.path.exists(GA_SA):
        return None
    from google.oauth2 import service_account
    return service_account.Credentials.from_service_account_file(GA_SA, scopes=scopes)


def youtube_credentials(scopes):
    """OAuth kullanıcı kimliği. İstenen scope verilmemişse refresh sırasında
    invalid_scope patlar; çağıran bunu yakalayıp kanalı atlamalı."""
    if not os.path.exists(YT_OAUTH):
        return None
    from google.oauth2.credentials import Credentials
    cfg = json.load(open(YT_OAUTH))
    return Credentials(
        token=None,
        refresh_token=cfg["refresh_token"],
        client_id=cfg["client_id"],
        client_secret=cfg["client_secret"],
        token_uri="https://oauth2.googleapis.com/token",
        scopes=scopes,
    )


# --------------------------- kimlik/hash ---------------------------

def cid(channel, ref):
    """İçerik kimliği: kanal + doğal referans (video_id / media_id / slug)."""
    return f"{channel}:{ref}"


# --------------------------- bandit ---------------------------

def _seeded_rand(seed_str):
    h = hashlib.sha256(seed_str.encode()).hexdigest()
    return int(h[:8], 16) / 0xFFFFFFFF


def pick_bandit(arms, epsilon=0.2, min_n=5, seed=""):
    """
    Epsilon-greedy kol seçimi.
      arms: {name: {"score": float, "n": int}}
    Kural:
      - Hiç örneklenmemiş / min_n altındaki kol varsa → en az örneklenmiş kolu
        seç (saf keşif). Bu, her seçeneğin veri toplamasını garanti eder.
      - Aksi halde epsilon olasılıkla rastgele kol (keşif), yoksa en yüksek
        ortalama skorlu kol (sömürü).
    Günlük deterministik: aynı gün aynı seed → aynı seçim.
    Dönüş: (secilen_kol, policy)  policy ∈ {"explore-cold","explore","exploit"}
    """
    if not arms:
        return None, "none"
    names = sorted(arms.keys())
    cold = [n for n in names if arms[n]["n"] < min_n]
    if cold:
        # en az örneklenmiş (eşitlikte deterministik ilk)
        cold.sort(key=lambda n: (arms[n]["n"], n))
        return cold[0], "explore-cold"
    r = _seeded_rand(seed + "|eps")
    if r < epsilon:
        idx = int(_seeded_rand(seed + "|pick") * len(names)) % len(names)
        return names[idx], "explore"
    best = max(names, key=lambda n: arms[n]["score"])
    return best, "exploit"


# --------------------------- skorlama ---------------------------

def aggregate(items, key_fn, value_fn):
    """items → {kol: {"score": ortalama, "n": adet, "total": toplam, "var": örnek_varyansı}}
    value_fn None döndüren öğeler o kova için sayılmaz. var, separated() için gerekli."""
    buckets = {}
    for it in items:
        k = key_fn(it)
        v = value_fn(it)
        if k is None or v is None:
            continue
        b = buckets.setdefault(k, {"sum": 0.0, "sumsq": 0.0, "n": 0})
        b["sum"] += v
        b["sumsq"] += v * v
        b["n"] += 1
    out = {}
    for k, b in buckets.items():
        n = b["n"]
        mean = b["sum"] / n if n else 0.0
        # örnek varyansı (n-1); tek örnekte 0 → separated() bunu güvensiz sayar
        var = (b["sumsq"] - b["sum"] ** 2 / n) / (n - 1) if n > 1 else 0.0
        out[k] = {"score": mean, "n": n, "total": b["sum"], "var": max(var, 0.0)}
    return out


def separated(a, b, z=1.0):
    """a'nın ortalaması b'ninkini en az z BİRLEŞİK STANDART HATA kadar aşıyor mu?
    Küçük örnek veya yüksek varyansta std hata büyür → berabere kollar 'ayrık değil'
    sayılır ve sistem kilitlenmez. Örnek büyüdükçe/fark açıldıkça otomatik True olur.
    a,b: aggregate() çıktısı kol sözlükleri (score,n,var)."""
    import math
    na = max(a.get("n", 1), 1)
    nb = max(b.get("n", 1), 1)
    se = math.sqrt(a.get("var", 0.0) / na + b.get("var", 0.0) / nb)
    if se <= 0:  # varyans ölçülemedi (ör. hepsi aynı) → yalın ortalama kıyası
        return a["score"] > b["score"]
    return (a["score"] - b["score"]) / se >= z


def ranking(agg):
    """agg sözlüğünü skora göre azalan listeye çevir."""
    return [
        {"arm": k, "score": round(v["score"], 3), "n": v["n"], "total": round(v["total"], 2)}
        for k, v in sorted(agg.items(), key=lambda kv: -kv[1]["score"])
    ]
