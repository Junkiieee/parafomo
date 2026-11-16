#!/usr/bin/env python3
"""Telegram kanalına paylaşım ("Parafomo · Zam ve Para Alarmı") — Bot API, harici paket yok.

Kimlik repo DIŞINDA: ~/.config/parafomo/telegram.env  → TELEGRAM_BOT_TOKEN=…  TELEGRAM_CHANNEL=@parafomo
(Kaan panelden token'ı gönderince bu dosyaya yazılır; bot kanala yönetici eklenmiş olmalı.)

  python3 scripts/telegram-post.py --metin "…" [--foto https://parafomo.com/…jpg] [--dry]
Kural: kanal resmî rakam alarmıdır, asla al-sat tavsiyesi değildir (SPK/TSPB uyarıları); siyaset yok.
Yayın kilidi: /root/parafomo-data/PUBLISH_PAUSED varsa yalnız ONAYLI_YAYIN=1 ile.
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

ENV = os.path.expanduser("~/.config/parafomo/telegram.env")


def env():
    e = {}
    if os.path.exists(ENV):
        for line in open(ENV, encoding="utf-8"):
            if "=" in line and not line.startswith("#"):
                k, v = line.strip().split("=", 1)
                e[k] = v
    return e


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--metin", required=True)
    ap.add_argument("--foto", default="")
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    if len(a.metin) > (1000 if a.foto else 4000):
        sys.exit("metin çok uzun (fotoğraflı 1.000, düz 4.000 karakter)")
    print(a.metin if not a.foto else f"[foto] {a.foto}\n{a.metin}")
    if a.dry:
        print("[telegram] --dry: gönderilmedi"); return
    e = env()
    tok, kanal = e.get("TELEGRAM_BOT_TOKEN"), e.get("TELEGRAM_CHANNEL")
    if not tok or not kanal:
        sys.exit("[telegram] HATA: ~/.config/parafomo/telegram.env içinde TELEGRAM_BOT_TOKEN ve TELEGRAM_CHANNEL yok")
    yol, veri = ("sendPhoto", {"chat_id": kanal, "photo": a.foto, "caption": a.metin}) if a.foto else \
        ("sendMessage", {"chat_id": kanal, "text": a.metin, "disable_web_page_preview": "false"})
    try:
        with urllib.request.urlopen(f"https://api.telegram.org/bot{tok}/{yol}", data=urllib.parse.urlencode(veri).encode(), timeout=30) as r:
            j = json.load(r)
    except urllib.error.HTTPError as ex:
        j = json.loads(ex.read().decode() or "{}")
    if not j.get("ok"):
        sys.exit(f"[telegram] HATA: {j.get('description', j)}")   # token asla basılmaz
    print(f"[telegram] ✅ gönderildi (mesaj {j['result']['message_id']})")


if __name__ == "__main__":
    if os.path.exists("/root/parafomo-data/PUBLISH_PAUSED") and "--dry" not in sys.argv and os.environ.get("ONAYLI_YAYIN") != "1":
        print("[durduruldu] PUBLISH_PAUSED var — yalnız ONAYLI_YAYIN=1 ile."); sys.exit(0)
    main()
