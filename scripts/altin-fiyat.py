#!/usr/bin/env python3
"""
ParaFOMO — Güncel altın fiyatları veri çekici (data/altin-fiyat.json).

/altin-hesaplama sayfası bu dosyadan build-time'da fiyatları okur. Site günlük
rebuild edildiği için fiyatlar her gün tazelenir. Truncgil v3 today.json'dan
gram/çeyrek/yarım/tam/ata/cumhuriyet/has + ons + ayar fiyatlarını çeker.

Kaynak sessizce bozulabilir (bkz. learnings): fetch başarısızsa MEVCUT
data/altin-fiyat.json korunur (non-fatal), asla boş yazmaz. İlk çalıştırmada
kaynak yoksa güvenli bir varsayılan snapshot yazar.

Kullanım: python3 scripts/altin-fiyat.py   (token harcamaz)
"""
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "altin-fiyat.json")
API = "https://finans.truncgil.com/v3/today.json"

# Truncgil anahtarı -> (etiket, gram-ağırlık, ayar)
TYPES = [
    ("gram-altin",        "Gram Altın",        1.0,      "24 (995)"),
    ("gram-has-altin",    "Has Altın (24 ayar)", 1.0,    "24 (999)"),
    ("ceyrek-altin",      "Çeyrek Altın",      1.75,     "22"),
    ("yarim-altin",       "Yarım Altın",       3.5,      "22"),
    ("tam-altin",         "Tam (Ziynet) Altın", 7.0,     "22"),
    ("ata-altin",         "Ata Altın",         7.2,      "22"),
    ("cumhuriyet-altini", "Cumhuriyet Altını", 7.2,      "22"),
    ("22-ayar-bilezik",   "22 Ayar Bilezik (gr)", 1.0,   "22"),
    ("18-ayar-altin",     "18 Ayar Altın (gr)", 1.0,     "18"),
    ("14-ayar-altin",     "14 Ayar Altın (gr)", 1.0,     "14"),
    ("ons",               "Ons Altın (USD)",   31.1035,  "24"),
]


def parse_tr(s):
    """'6.648,62' -> 6648.62 ; '$4.318,60' -> 4318.60"""
    s = re.sub(r"[^\d.,]", "", str(s))
    s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def fetch():
    req = urllib.request.Request(API, headers={"User-Agent": "Mozilla/5.0 ParaFOMO"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode("utf-8", "ignore"))


def _yahoo_price(symbol):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 ParaFOMO"})
    with urllib.request.urlopen(req, timeout=15) as r:
        d = json.loads(r.read().decode("utf-8", "ignore"))
    return float(d["chart"]["result"][0]["meta"]["regularMarketPrice"])


def yahoo_fallback():
    """Truncgil erişilemezse: son sağlam snapshot'ı canlı gram hareketiyle yeniden
    ölçekle (ons GC=F × USDTRY). Tüm kalem ilişkileri/işçilik primleri korunur,
    sadece board gram hareketi kadar kayar → sayfa asla bayat kalmaz."""
    if not os.path.exists(OUT):
        return None
    try:
        ons_usd = _yahoo_price("GC=F")          # ons altın (USD)
        usdtry = _yahoo_price("USDTRY=X")
    except Exception as e:
        print(f"[altin-fiyat] Yahoo fallback da başarısız ({str(e)[:60]})", file=sys.stderr)
        return None
    new_gram = ons_usd / 31.1035 * usdtry       # 24 ayar gösterge gram (TL)
    old = json.load(open(OUT, encoding="utf-8"))
    kalemler = old.get("kalemler", [])
    old_gram = next((k.get("satis") for k in kalemler if k.get("key") == "gram-altin"), None)
    if not old_gram:
        return None
    factor = new_gram / old_gram
    for k in kalemler:
        for f in ("alis", "satis"):
            if isinstance(k.get(f), (int, float)):
                k[f] = round(k[f] * factor, 2)
    old["kalemler"] = kalemler
    old["_kaynak"] = "Yahoo (GC=F×USDTRY) — Truncgil erişilemedi, son snapshot ölçeklendi"
    return old


def main():
    try:
        data = fetch()
    except Exception as e:
        print(f"[altin-fiyat] Truncgil fetch başarısız ({str(e)[:80]}) → Yahoo fallback deneniyor", file=sys.stderr)
        fb = yahoo_fallback()
        if fb is not None:
            tr_now = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=3)))
            fb["guncellenme"] = tr_now.strftime("%Y-%m-%dT%H:%M:%S+03:00")
            fb["guncellemeEtiket"] = tr_now.strftime("%d %B %Y, %H:%M")
            with open(OUT, "w", encoding="utf-8") as f:
                json.dump(fb, f, ensure_ascii=False, indent=2)
            print(f"[altin-fiyat] Yahoo fallback ile {len(fb.get('kalemler', []))} kalem tazelendi → {OUT}")
            return 0
        print("[altin-fiyat] fallback yok → mevcut dosya korunuyor", file=sys.stderr)
        if os.path.exists(OUT):
            return 0
        data = {}

    items = []
    for key, label, gram, ayar in TYPES:
        node = data.get(key) if isinstance(data, dict) else None
        buy = sell = None
        if isinstance(node, dict):
            buy = parse_tr(node.get("Buying") or node.get("Alış"))
            sell = parse_tr(node.get("Selling") or node.get("Satış"))
        if sell is None and buy is None:
            continue
        items.append({
            "key": key, "label": label, "gram": gram, "ayar": ayar,
            "alis": buy, "satis": sell,
        })

    if not items:
        # Kaynak boş döndü — mevcut dosyayı koru, yoksa yaz-atla.
        print("[altin-fiyat] kaynak boş → yazılmadı", file=sys.stderr)
        return 0 if os.path.exists(OUT) else 1

    tr_now = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=3)))
    out = {
        "_aciklama": "Güncel altın fiyatları (Truncgil v3). Site günlük rebuild'de tazelenir; anlık/kesin işlem fiyatı değildir, göstergedir.",
        "_kaynak": "finans.truncgil.com v3",
        "guncellenme": tr_now.strftime("%Y-%m-%dT%H:%M:%S+03:00"),
        "guncellemeEtiket": tr_now.strftime("%d %B %Y, %H:%M"),
        "kalemler": items,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"[altin-fiyat] {len(items)} kalem yazıldı → {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
