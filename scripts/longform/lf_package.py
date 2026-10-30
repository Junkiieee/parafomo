#!/usr/bin/env python3
"""Başlık + kapak birlikte denetimi (Türkçe). Fikir: github.com/Jakeschincariol/youtube-agent-skill
yt-package/title.py — kuralları Türkçeye uyarlandı (ekler: kelimeler 5 harflik kökle karşılaştırılır).

    python3 scripts/longform/lf_package.py --title "…" --top "…" --big "…" --bottom "…"

Engelleyici: başlık >70 krk, kapak başlığı tekrar ediyor, kapakta >5 kelime, >2 BÜYÜK HARF kelime.
Uyarı: >60 krk (masaüstü aramada kesilir), mobilde ilk ~40 krk'da konu görünmüyor, başlıkta sayı yok.
"""
import argparse
import re

STOP = set("ve ile bu bir de da mi mı mu mü ne için kadar neler nasıl hangi gibi daha en çok olan oldu "
           "olacak ya veya ama şu o sen senin ben bizim her hiç".split())


def low(s):
    return s.replace("İ", "i").replace("I", "ı").lower()


def words(s):
    # kesme işaretli ek tek kelime ("ocak'ta"); para/yüzde birimleri kelime sayılmaz
    return [w for w in re.findall(r"[a-zçğıöşü]+(?:['’][a-zçğıöşü]+)?", low(s)) if w not in ("tl", "lira")]


def stems(s):
    return {w[:5] for w in words(s) if w not in STOP and len(w) > 2}


def lint(title, thumb, blocking_only=False):
    t = (title or "").strip()
    th = " ".join(str(thumb.get(k, "")) for k in ("top", "big", "bottom")) if isinstance(thumb, dict) else str(thumb)
    block, warn = [], []
    if len(t) > 70:
        block.append(f"başlık {len(t)} karakter — en fazla 70 (hedef ≤60)")
    elif len(t) > 60:
        warn.append(f"başlık {len(t)} karakter — masaüstü aramada ~60'ta kesilir")
    caps = [w for w in t.split() if len(w) > 2 and w.isupper() and not any(c.isdigit() for c in w)]
    if len(caps) > 2:
        block.append(f"{len(caps)} BÜYÜK HARF kelime — en fazla 2 (spam görünür)")
    shared = stems(t) & stems(th)
    if shared:
        block.append("kapak başlığı tekrar ediyor (" + ", ".join(sorted(shared)) +
                     ") — kapak başlığın söylemediğini söylesin")
    nw = len(words(th)) + len(re.findall(r"\d[\d.,]*", th))
    if nw > 5:
        block.append(f"kapakta {nw} kelime — en fazla 5 (akış boyutunda okunmaz)")
    if not re.search(r"\d", t):
        warn.append("başlıkta sayı/tarih yok — en güvenilir tek iyileştirme")
    head = t[:40]
    if not stems(head):
        warn.append(f"mobilde görünen kısım ('{head}…') konuyu taşımıyor")
    return block if blocking_only else block + warn


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--title", required=True)
    ap.add_argument("--top", default="")
    ap.add_argument("--big", default="")
    ap.add_argument("--bottom", default="")
    a = ap.parse_args()
    issues = lint(a.title, {"top": a.top, "big": a.big, "bottom": a.bottom})
    print("\n".join(f"- {i}" for i in issues) or "temiz")


if __name__ == "__main__":
    main()
