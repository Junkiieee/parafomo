#!/usr/bin/env python3
"""Video QA kare sayfası: TEK ffmpeg çağrısıyla videodan N kareyi zaman damgalı tek PNG'ye dizer.

Neden (denetim 2026-11-18, panel-ajan-4): sabah rutini kareleri for-döngüsü/değişkenle tek tek çıkarıyordu;
başsız koşuda izin listesi döngüyü reddetti, turlar yandı, ajan /tmp'ye geçici script yazmaya düştü.
Bu araç tek komuttur ve çıktısı Read ile bakılacak tek bir PNG'dir.

  /root/.venvs/parafomo/bin/python scripts/anim/kare_sayfasi.py public/social/short-<slug>.mp4 [--n 8]
      → agent/tmp/kare-<ad>.png  (agent/tmp/ git dışı; bakım 7 günden eskisini siler)
  seçenekler: --out <png> · --genislik 360 (kare başına px) · --sutun 4 · --bas <sn> --son <sn> (aralık)

Kareler aralıkların ORTASINDAN alınır (ilk/son siyah kare atlanır); her karenin sol üstünde zamanı yazar.
"""
import argparse
import json
import math
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def sure(mp4):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", mp4],
                       capture_output=True, text=True, timeout=60)
    try:
        return float(json.loads(r.stdout)["format"]["duration"])
    except Exception:
        sys.exit(f"[kare] süre okunamadı: {mp4} ({(r.stderr or '').strip()[:200]})")


def komut(mp4, out, bas, aralik, n, gen, sutun, satir, etiket):
    # select: ilk kare + her `adim` saniyede bir kare (fps filtresi EOF'ta son kareyi düşürüyordu).
    # Giriş bas'tan (n - 0.5) adım sürer → tam n kare (k = 0..n-1), fazlası tile'a sızmaz.
    adim = aralik / n
    vf = ["select='isnan(prev_selected_t)+gte(t-prev_selected_t\\," + f"{max(adim - 0.02, 0.01):.4f}" + ")'",
          f"scale={gen}:-2"]
    if etiket:
        # %{pts:hms:<ofset>} → videodaki gerçek zaman (giriş -ss ile kaydırıldığı için ofset eklenir)
        vf.append("drawtext=text='%{pts\\:hms\\:" + f"{bas:.3f}" + "}':x=6:y=6:fontsize=" + str(max(12, gen // 18))
                  + ":fontcolor=yellow:box=1:boxcolor=black@0.6:boxborderw=4")
    vf.append(f"tile={sutun}x{satir}:padding=4:margin=4:color=gray")
    return ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
            "-ss", f"{bas:.3f}", "-t", f"{(n - 0.5) * adim:.3f}", "-i", mp4,
            "-vf", ",".join(vf), "-frames:v", "1", "-update", "1", out]


def main():
    p = argparse.ArgumentParser(description="Videodan tek PNG kare sayfası (QA)")
    p.add_argument("mp4")
    p.add_argument("--n", type=int, default=8, help="kare sayısı (1-48, varsayılan 8)")
    p.add_argument("--out", help="çıktı PNG (varsayılan agent/tmp/kare-<ad>.png)")
    p.add_argument("--genislik", type=int, default=360, help="kare genişliği px (varsayılan 360)")
    p.add_argument("--sutun", type=int, default=0, help="sütun sayısı (varsayılan: en çok 4)")
    p.add_argument("--bas", type=float, default=0.0, help="aralık başı (sn)")
    p.add_argument("--son", type=float, default=0.0, help="aralık sonu (sn; 0 = video sonu)")
    a = p.parse_args()
    if not os.path.isfile(a.mp4):
        sys.exit(f"[kare] dosya yok: {a.mp4}")
    try:
        os.nice(19)   # kural: render/ffmpeg nice 19
    except Exception:
        pass
    d = sure(a.mp4)
    bas = max(0.0, min(a.bas, d))
    son = d if a.son <= 0 else min(a.son, d)
    aralik = son - bas
    if aralik <= 0.05:
        sys.exit(f"[kare] geçersiz aralık: {bas}-{son} sn (video {d:.2f} sn)")
    n = max(1, min(a.n, 48))
    sutun = a.sutun if a.sutun > 0 else min(n, 4)
    satir = math.ceil(n / sutun)
    gen = max(80, min(a.genislik, 1080))
    ad = os.path.splitext(os.path.basename(a.mp4))[0]
    out = a.out or os.path.join(ROOT, "agent", "tmp", f"kare-{ad}.png")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    # k. kare ≈ bas + (k + 0.5) * aralik / n — giriş yarım adım kaydırılır
    ofset = bas + aralik / (2 * n)
    zamanlar = [bas + aralik * (i + 0.5) / n for i in range(n)]
    for etiket in (True, False):   # drawtext (freetype/font) yoksa etiketsiz dene
        r = subprocess.run(komut(a.mp4, out, ofset, aralik, n, gen, sutun, satir, etiket),
                           capture_output=True, text=True, timeout=600)
        if r.returncode == 0 and os.path.exists(out) and os.path.getsize(out) > 0:
            break
    else:
        sys.exit(f"[kare] ffmpeg başarısız: {(r.stderr or '').strip()[-400:]}")
    print(f"[kare] {out}  ({n} kare, {sutun}x{satir}, video {d:.1f} sn"
          + ("" if etiket else ", zaman etiketi YOK") + ")")
    print("[kare] zamanlar (sn): " + ", ".join(f"{t:.1f}" for t in zamanlar))


if __name__ == "__main__":
    main()
