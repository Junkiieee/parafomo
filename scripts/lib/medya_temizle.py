#!/usr/bin/env python3
"""Bakım: yayınlanmış video render'ları + render önbelleği temizliği (scripts/maintenance.sh her gün çağırır).

  python3 scripts/lib/medya_temizle.py [--dry-run] [--gun 14] [--repo /root/parafomo]

Neden (denetim 2026-11-18, repo-3/zamanlama-4): disk 11-11'de 7.3 GB boştan 11-18'de 4.0 GB'a indi. Bakım yalnız
public/social'ın üst düzeyini (-maxdepth 1) siliyordu; public/social/longform (154 MB) ve anim (59 MB) hiç
silinmiyor, her build dist/'e bir kopya daha alıyordu; /root/.cache/parafomo/anim (~1.2 GB) iş klasörleri birikiyordu.

Siler (eşik --gun, varsayılan 14 — `find -mtime +14` ile aynı: ≥15 tam gün):
  1) public/social/*.mp4 ve public/social/anim/*.mp4 — yayın kuyruğunda 'bekliyor'/'onaylandi' olanlar HARİÇ
  2) public/social/longform/*.mp4 — yalnız yanındaki <ad>.meta.json'da video_id VAR ve (privacy=public ya da
     tamamlandi=true) ise; zamanlanmış özel uzun video (ör. lf-ekonomi-defteri-3) yayına kadar korunur
  3) /root/.cache/parafomo/{anim,longform}/<girdi> — içindeki EN YENİ dosya eşikten eskiyse; tts/ (TTS önbelleği,
     yeniden üretmek ücretli) ve kuyrukta bekleyen / yayımlanmamış uzun video slug'ları HARİÇ
Silinenler yeniden üretilebilir: videolar YouTube/IG'de, senaryoları git'te.
"""
import argparse
import json
import os
import shutil
import sys
import time

KUYRUK = "/root/parafomo-data/onay/kuyruk.json"
CACHE = "/root/.cache/parafomo"
CACHE_HARIC = {"tts"}


def gun_yasi(mtime, now):
    return int((now - mtime) // 86400)


def boyut(p):
    if os.path.isfile(p):
        return os.path.getsize(p)
    t = 0
    for d, _, fs in os.walk(p):
        for f in fs:
            try:
                t += os.path.getsize(os.path.join(d, f))
            except OSError:
                pass
    return t


def en_yeni_mtime(p):
    m = os.path.getmtime(p)
    if os.path.isdir(p):
        for d, ds, fs in os.walk(p):
            for x in ds + fs:
                try:
                    m = max(m, os.path.getmtime(os.path.join(d, x)))
                except OSError:
                    pass
    return m


def korunanlar():
    """Kuyrukta bekleyen/onaylı videoların mp4 yolları + slug'ları. Kuyruk okunamazsa None (hiçbir şey silinmez)."""
    yollar, sluglar = set(), set()
    if not os.path.exists(KUYRUK):
        return yollar, sluglar
    try:
        q = json.load(open(KUYRUK, encoding="utf-8"))
    except Exception as e:
        print(f"[!] kuyruk.json okunamadı ({type(e).__name__}) — video render'ları bugün SİLİNMEDİ")
        return None
    for it in q.get("items", []):
        if it.get("status") in ("bekliyor", "onaylandi"):
            if it.get("mp4"):
                yollar.add(os.path.realpath(it["mp4"]))
                sluglar.add(os.path.splitext(os.path.basename(it["mp4"]))[0].removeprefix("short-"))
            if it.get("slug"):
                sluglar.add(it["slug"])
    return yollar, sluglar


def longform_yayinda(mp4):
    meta = mp4[:-4] + ".meta.json"
    try:
        m = json.load(open(meta, encoding="utf-8"))
    except Exception:
        return False
    return bool(m.get("video_id")) and (m.get("privacy") == "public" or m.get("tamamlandi") is True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--gun", type=int, default=14)
    ap.add_argument("--repo", default=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    a = ap.parse_args()
    now = time.time()
    social = os.path.join(a.repo, "public", "social")
    k = korunanlar()
    sil, korunan, sayac = [], 0, {"üst": 0, "anim": 0, "longform": 0, "önbellek": 0}

    # 1-2) public/social render'ları
    for alt, etiket in (("", "üst"), ("anim", "anim"), ("longform", "longform")):
        d = os.path.join(social, alt)
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            p = os.path.join(d, f)
            if not f.endswith(".mp4") or not os.path.isfile(p) or gun_yasi(os.path.getmtime(p), now) <= a.gun:
                continue
            if etiket == "longform":
                if not longform_yayinda(p):
                    korunan += 1
                    continue
            else:
                if k is None:
                    korunan += 1
                    continue
                stem = os.path.splitext(f)[0].removeprefix("short-")
                if os.path.realpath(p) in k[0] or stem in k[1]:
                    korunan += 1
                    continue
            sil.append((etiket, p))

    # 3) render önbelleği iş klasörleri
    yayimlanmamis_lf = set()
    lf_dir = os.path.join(social, "longform")
    if os.path.isdir(lf_dir):
        for f in os.listdir(lf_dir):
            if f.endswith(".meta.json") and not longform_yayinda(os.path.join(lf_dir, f[:-10] + ".mp4")):
                yayimlanmamis_lf.add(f[:-10])
    koru_slug = (k[1] if k else set()) | yayimlanmamis_lf
    for alt in ("anim", "longform"):
        d = os.path.join(CACHE, alt)
        if not os.path.isdir(d) or k is None:
            continue
        for f in sorted(os.listdir(d)):
            p = os.path.join(d, f)
            if f in CACHE_HARIC or f in koru_slug or os.path.islink(p):
                continue
            if gun_yasi(en_yeni_mtime(p), now) > a.gun:
                sil.append(("önbellek", p))

    toplam = {"video": 0, "önbellek": 0}
    for etiket, p in sil:
        b = boyut(p)
        toplam["önbellek" if etiket == "önbellek" else "video"] += b
        sayac[etiket] += 1
        if a.dry_run:
            print(f"    [dry] {p} ({b / 1e6:.1f} MB)")
            continue
        try:
            shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
        except OSError as e:
            print(f"[!] silinemedi: {p} ({e})")
    on = "[dry] silinecek" if a.dry_run else "silindi"
    print(f"[*] eski video render'ı {on}: {sayac['üst'] + sayac['anim'] + sayac['longform']} "
          f"(üst {sayac['üst']}, anim {sayac['anim']}, longform {sayac['longform']}; korunan {korunan}) "
          f"— {toplam['video'] / 1e6:.0f} MB")
    print(f"[*] render önbelleği {on}: {sayac['önbellek']} girdi — {toplam['önbellek'] / 1e6:.0f} MB")


if __name__ == "__main__":
    sys.exit(main())
