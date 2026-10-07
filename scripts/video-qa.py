#!/usr/bin/env python3
"""
ParaFOMO — VİDEO KALİTE KAPISI (yükleme öncesi; shorts-build-v4.py render sonrası otomatik çağırır).

Neden (2026-10-06/07): yayındaki videolarda Türk finans içeriğine Filipin pesosu etiketi, zloti,
Hollanda bayrağı, "Federal Reserve logo" yerine uydu fotoğrafı, 4. saniyede simsiyah kare çıktı —
kimse kareye bakmıyordu. Bu kapı her sahneden bir kare alır:
  1) deterministik: neredeyse siyah/boş kare → sorunlu
  2) Claude (görsel okuma): kare, o sahnenin konuşmasıyla ve Türk izleyiciyle uyumlu mu?
Sorunlu sahne indeksleri döner; oluşturucu o sahneleri marka kartıyla yeniden render eder.
LLM yoksa/kota doluysa yalnız deterministik kontrol uygulanır (yayın durmaz).

Kullanım: python3 scripts/video-qa.py <slug>   → stdout: sorunlu indeksler (virgüllü) veya boş
Sonuç meta JSON'a (public/social/short-<slug>.json → "qa") ve logs/video-qa.jsonl'a yazılır.
"""
import datetime as dt
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "public", "social")
WORK = "/root/.cache/parafomo/qa"
LOG = os.path.join(ROOT, "logs", "video-qa.jsonl")
sys.path.insert(0, os.path.join(ROOT, "scripts", "lib"))


def _frame(mp4, t, out):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", mp4, "-frames:v", "1",
                    "-vf", "scale=360:-1", out], check=True, capture_output=True)
    return out


def _mean_luma(path):
    from PIL import Image, ImageStat
    im = Image.open(path).convert("L")
    w, h = im.size
    # üst marka bandı ve alt logo şeridini dışarıda bırak
    im = im.crop((0, int(h * 0.06), w, int(h * 0.90)))
    st = ImageStat.Stat(im)
    return st.mean[0], st.stddev[0]


def _sheet(paths, out):
    from PIL import Image, ImageDraw, ImageFont
    ims = [Image.open(p).convert("RGB") for p in paths]
    w, h = ims[0].size
    sheet = Image.new("RGB", (w * len(ims), h + 70), (255, 255, 255))
    d = ImageDraw.Draw(sheet)
    try:
        f = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 44)
    except Exception:
        f = ImageFont.load_default()
    for k, im in enumerate(ims):
        sheet.paste(im, (k * w, 70))
        d.text((k * w + 16, 12), f"SAHNE {k}", font=f, fill=(200, 0, 0))
    sheet.save(out, quality=85)
    return out


PROMPT = """Bir Türk finans markasının (ParaFOMO) YouTube Shorts videosunun yayın öncesi kalite kontrolünü yapıyorsun.
`{sheet}` dosyasını Read aracıyla aç: soldan sağa her sahneden bir kare var (üstte "SAHNE n" etiketi).

Sahneler (konuşma metni + istenen görsel):
{scenes}

Her sahne için karar ver. YALNIZ şu AÇIK hatalarda işaretle:
- görsel, o sahnenin konuşmasıyla belirgin şekilde ilgisiz (ör. faiz anlatılırken uydu haritası, antika saat)
- Türk izleyiciyi yanıltan yabancı unsur: yabancı banknot/para destesi, yabancı market fiyat etiketi,
  Türkiye anlatılırken başka ülkenin bayrağı/binası
- yanlış kişi/logo (istenen kişi/kurum değil)
- kare boş, simsiyah ya da yazı okunamayacak şekilde üst üste binmiş
SORUN DEĞİL (işaretleme): koyu zeminli marka kartı (büyük rakam/kelime), konuyla genel olarak uyumlu stok
görüntü (borsa ekranı, altın, hesap makinesi, çalışan insanlar), siyah-beyaz arşiv fotoğrafı, ParaFOMO
logolu kapanış kartı. Emin değilsen işaretleme.

SADECE şu JSON'u döndür: {{"bad": [{{"i": <sahne no>, "reason": "<kısa Türkçe gerekçe>"}}]}}"""


def check(slug, use_llm=True):
    meta_p = os.path.join(OUT_DIR, f"short-{slug}.json")
    meta = json.load(open(meta_p, encoding="utf-8"))
    mp4 = meta.get("file") or os.path.join(OUT_DIR, f"short-{slug}.mp4")
    tl = meta.get("timeline") or []
    if not tl or not os.path.exists(mp4):
        return []
    os.makedirs(WORK, exist_ok=True)
    frames, bad, notes = [], {}, []
    for seg in tl:
        t = seg["start"] + 0.6 * (seg["end"] - seg["start"])
        fp = _frame(mp4, t, os.path.join(WORK, f"{slug}-{seg['i']}.jpg"))
        frames.append(fp)
        mean, sd = _mean_luma(fp)
        if mean < 14 and sd < 10:
            bad[seg["i"]] = f"neredeyse boş/siyah kare (parlaklık {mean:.0f})"
    llm_used = False
    if use_llm:
        import llm
        sheet = _sheet(frames, os.path.join(WORK, f"qa-{slug}.jpg"))
        scenes = "\n".join(f"- SAHNE {s['i']} ({s['kind']}): \"{s['spoken'][:160]}\" · istenen görsel: {s['visual']}"
                           for s in tl)
        ok, out, kind = llm.call(PROMPT.format(sheet=os.path.basename(sheet), scenes=scenes),
                                 model="sonnet", effort="low", timeout=240, tries=1,
                                 tag="video-qa", files=[sheet])
        if ok:
            llm_used = True
            m = re.search(r"\{.*\}", out, re.S)
            try:
                for b in (json.loads(m.group(0)).get("bad") or []) if m else []:
                    i = int(b.get("i"))
                    if 0 <= i < len(tl) and tl[i].get("visual") != "marka kartı":
                        bad.setdefault(i, str(b.get("reason", ""))[:160])
            except Exception as e:
                notes.append(f"QA yanıtı ayrıştırılamadı: {str(e)[:60]}")
        else:
            notes.append(f"LLM kontrolü yapılamadı ({kind}) — yalnız deterministik kontrol")
    rec = {"ts": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "slug": slug,
           "llm": llm_used, "bad": {str(k): v for k, v in sorted(bad.items())}, "notes": notes}
    meta["qa"] = rec
    json.dump(meta, open(meta_p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    for k, v in sorted(bad.items()):
        print(f"[qa] sahne {k}: {v}")
    if not bad:
        print(f"[qa] {len(tl)} sahne temiz" + ("" if llm_used else " (yalnız deterministik)"))
    return sorted(bad)


if __name__ == "__main__":
    res = check(sys.argv[1], use_llm="--no-llm" not in sys.argv)
    print(",".join(str(i) for i in res))
