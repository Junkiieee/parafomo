#!/usr/bin/env python3
"""
ParaFOMO — ÜRETİM SAĞLIĞI (token'sız).

Her üretim hattının SON BAŞARILI çalışmasını loglardan bulur, beklenen sıklıkla
kıyaslar → OK / GECİKTİ / HATA. Ayrıca: Claude kota/oturum durumu, disk, git
(dal, ileride/geride, yarım rebase), canlı site + portföy API'si, onaylı yayın
kuyruğu (otomatik onay bitişi, onaylı stok) ve bayat veri listesi.

Eski sistemin en pahalı hatası buydu: 8 gece OAuth düşük kaldı, hatlar sessizce
durdu, kimse fark etmedi. 2026-11-18 denetimi: hat listesi emekli işleri izliyordu
(viral/shorts/manim…), hiçbir cron çalıştırmıyordu → disk %88 ve bayat veri sessiz
kaldı. Artık agent/sabah.sh her sabah `--sabah` ile çağırır: rapor istemin sonuna
eklenir, operasyonel sorun varsa Kaan'a tek uyarı (notify.py alert --key saglik).

Kullanım:
  python3 agent/health.py                    # markdown tablo
  python3 agent/health.py --json             # makine-okur özet
  python3 agent/health.py --sabah <dosya>    # raporu dosyaya yaz; stdout'a yalnız UYARI satırları
                                             # (boşsa uyarı yok — sabah.sh bunu notify.py'ye verir)
"""
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request

ROOT = "/root/parafomo"
LOGS = os.path.join(ROOT, "logs")
STATE = os.path.join(ROOT, "agent", "state")
ONAY = "/root/parafomo-data/onay"          # onaylı yayın kuyruğu (scripts/anim/kuyruk.py) — yalnız OKUNUR
TS_RE = re.compile(r"\[(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}):\d{2} UTC\]")
# "(?<!0 )": "… 0 hata" özet satırları (EVDS/OG kartları) hata sayılmasın
ERR_RE = re.compile(r"(?<!0 )HATA|Traceback|hit your|Failed to authenticate|ÜRETİLEMEDİ|başarısız", re.I)
# Disk: kullanılan/(kullanılan+boş) — df'in yüzdesi (shutil'in used/total'ı root ayrılmış bloğu sayıp ~%4 düşük gösterir).
# Eşik boş GB'a göre: build (dist ~0.5 GB) + render + SQLite ~1 GB altında patlar; 4 GB'ta uyarmak 1 haftalık pay bırakır.
DISK_MIN_FREE_GB = 4.0
DISK_MAX_PCT = 90

# ad, log, başarı deseni, beklenen azami yaş (saat; None = olaya bağlı), not
# 2026-11-18: emekli hatlar (viral/shorts/manim/news/altın-IG/BIST — cron'ları 10-30/31'de kapandı) çıkarıldı;
# çalışan işler eklendi. Zaman damgasız loglarda (bots, bülten, portföy) son başarı = dosyanın mtime'ı.
PIPELINES = [
    ("Video yayını (YT+IG+FB)", "kuyruk.log", r"\[yayın\] ✅", 30, "kuyruk.sh yayinla 16:00+18:00 UTC"),
    ("Gece video üretimi", "kuyruk.log", r"\[üret\] ✅|\[hikaye\] ✅ video", 30, "kuyruk.sh uret 00:40 UTC"),
    ("Sabah rutini (Claude)", "sabah.log", r"Sabah rutini bitti \(çıkış 0\)", 26, "agent/sabah.sh 04:37 UTC"),
    ("Blog yazısı", "cron.log", r"\] Tamamlandı$", 80, "Pzt-Cum"),
    ("Fiyat tazeleme", "prices.log", r"push tamam|değişiklik yok", 74, "Pzt-Cmt 08:30-16:30 UTC"),
    ("Halka arz verisi", "halka-arz.log", r"Değişiklik yok|Push başarılı", 14, "6 saatte bir"),
    ("Öğrenme döngüsü", "learn.log", r"Öğrenme döngüsü tamamlandı", 30, "günlük"),
    ("Bakım + yedek", "maintenance.log", r"uzak kopya: portfolio-", 26, "04:30 UTC (portföy DB uzak kopya)"),
    ("Faiz kararı bekçisi", "policy-decisions.log", r"\[policy\]", 14, "4×/gün"),
    ("EVDS faizleri", "evds.log", r"\[evds\] (GÜNCELLENDİ|değişiklik yok)", 200, "Prş+Cum 12:40 UTC"),
    ("Bot arşivi (CF)", "bots.log", r"\[bots\] .+\.jsonl:", 30, "03:20 UTC"),
    ("Portföy fotoğrafı", "portfolio-snapshot.log", r"kullanıcı yazıldı", 30, "20:50 UTC"),
    ("Haftalık bülten", "newsletter.log", r"gönderildi \d+, hata 0", 180, "Pzt 05:30 UTC"),
]


def _now():
    return dt.datetime.now(dt.timezone.utc)


def _parse_ts(m):
    return dt.datetime.strptime(f"{m.group(1)} {m.group(2)}", "%Y-%m-%d %H:%M").replace(tzinfo=dt.timezone.utc)


def scan_log(path, ok_pat, tail_bytes=400_000):
    """Son başarı zamanı + başarıdan SONRAKİ son hata satırı."""
    if not os.path.exists(path):
        return None, None, None
    with open(path, "rb") as f:
        f.seek(0, 2)
        size = f.tell()
        f.seek(max(0, size - tail_bytes))
        text = f.read().decode("utf-8", "ignore")
    ok_re = re.compile(ok_pat)
    cur = last_ok = last_err = last_run = None
    last_line_ok = False
    for line in text.splitlines():
        if not line.strip():
            continue
        m = TS_RE.search(line)
        if m:
            cur = _parse_ts(m)
            last_run = cur
        last_line_ok = bool(ok_re.search(line))
        if last_line_ok:
            last_ok = cur
            last_err = None
        elif ERR_RE.search(line) and "UYARI" not in line[:8]:
            last_err = (cur, line.strip()[:160])
    if last_run is None:
        # Log hiç [YYYY-MM-DD HH:MM:SS UTC] damgası taşımıyor (bots, bülten, portföy): son satır başarıysa
        # son başarı = dosyanın son yazılma anı; son satır başarı değilse (son koşu hata verdi) tarih yok → GECİKTİ.
        last_ok = dt.datetime.fromtimestamp(os.path.getmtime(path), dt.timezone.utc) if last_line_ok else None
        last_run = last_ok
    return last_ok, last_err, last_run


def age_h(t):
    return (_now() - t).total_seconds() / 3600 if t else None


def fmt_age(h):
    if h is None:
        return "hiç"
    return f"{h:.0f} sa önce" if h < 48 else f"{h / 24:.1f} gün önce"


def pipelines():
    rows = []
    for name, log, pat, max_h, note in PIPELINES:
        last_ok, last_err, last_run = scan_log(os.path.join(LOGS, log), pat)
        h = age_h(last_ok)
        if max_h is None:
            status = "OK" if not last_err else "HATA"
        elif last_ok is None or h > max_h:
            status = "GECİKTİ"
        else:
            status = "OK"
        if last_err and status == "OK" and max_h is not None:
            status = "UYARI"
        rows.append({"name": name, "status": status, "last_ok": last_ok.isoformat() if last_ok else None,
                     "age": fmt_age(h), "note": note,
                     "error": last_err[1] if last_err else ""})
    return rows


def kuyruk_status():
    """Onaylı yayın kuyruğu (scripts/anim/kuyruk.py): onaylı stok + otomatik onay (oto.json) bitişi.

    Denetim 2026-11-18 (zamanlama-1): oto.json bitince gece videoları 'bekliyor'a düşer, yayinla yalnız
    'onaylandi' yayınlar → stok ~6 günde biter, yayın sessizce durur. Bitişi uzatmak Kaan'ın kararı
    (panel → 'Onaysız yayın' anahtarı); burada yalnız uyarılır."""
    out = {"onayli": None, "bekliyor": None, "oto_bitis": None, "uyari": []}
    try:
        q = json.load(open(os.path.join(ONAY, "kuyruk.json"), encoding="utf-8"))
    except FileNotFoundError:
        return out
    except Exception as e:
        out["uyari"].append(f"kuyruk.json okunamadı ({type(e).__name__}) → scripts/anim/kuyruk.py liste")
        return out
    items = q.get("items", []) if isinstance(q, dict) else []
    out["onayli"] = sum(1 for i in items if i.get("status") == "onaylandi")
    out["bekliyor"] = sum(1 for i in items if i.get("status") == "bekliyor")
    bugun_tr = (_now() + dt.timedelta(hours=3)).date()          # kuyruk.py ile aynı: TSİ = UTC+3
    try:
        out["oto_bitis"] = json.load(open(os.path.join(ONAY, "oto.json"), encoding="utf-8"))["bitis"]
        kalan = (dt.date.fromisoformat(out["oto_bitis"]) - bugun_tr).days
        if 0 <= kalan <= 7:
            out["uyari"].append(f"otomatik onay {kalan} gün sonra bitiyor ({out['oto_bitis']}): sonra gece videoları "
                                "'bekliyor'a düşer, yayın yalnız onaylıdan sürer → Kaan kararı (panel: 'Onaysız yayın')")
        elif -3 <= kalan < 0:
            out["uyari"].append(f"otomatik onay {out['oto_bitis']}'de bitti: yeni videolar 'bekliyor'da "
                                f"({out['bekliyor']} adet) → Kaan kararı (panel: 'Onaysız yayın') ya da kuyruk.py onayla")
    except FileNotFoundError:
        pass
    except Exception as e:
        out["uyari"].append(f"oto.json okunamadı ({type(e).__name__})")
    if out["onayli"] < 3:
        out["uyari"].append(f"onaylı video stoğu {out['onayli']} (<3; günde 2 yayın yuvası) → kuyruk.py liste + onayla")
    return out


def llm_status():
    try:
        d = json.load(open(os.path.join(LOGS, "llm-status.json"), encoding="utf-8"))
    except Exception:
        d = {"state": "ok"}
    st = d.get("state", "ok")
    until = d.get("until")
    if st in ("session_limit", "weekly_limit") and until:
        try:
            if dt.datetime.fromisoformat(until) <= _now():
                st = "ok"
        except Exception:
            pass
    return {"state": st, "until": until, "message": d.get("message", "")}


def git_status():
    def g(*a):
        # GIT_OPTIONAL_LOCKS=0: izleme `git status` ile index.lock'u kapıp cron'ların commit'iyle yarışmasın
        r = subprocess.run(["git", "-C", ROOT, *a], capture_output=True, text=True, timeout=30,
                           env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"})
        return r.stdout.strip()
    branch = g("rev-parse", "--abbrev-ref", "HEAD")
    rebasing = os.path.isdir(os.path.join(ROOT, ".git", "rebase-merge")) or \
        os.path.isdir(os.path.join(ROOT, ".git", "rebase-apply"))
    ab = g("rev-list", "--left-right", "--count", "origin/main...HEAD").split()
    behind, ahead = (int(ab[0]), int(ab[1])) if len(ab) == 2 else (0, 0)
    dirty = [l for l in g("status", "--porcelain").splitlines() if l.strip()]
    stashes = [l for l in g("stash", "list").splitlines() if "agent-wip" in l]
    return {"branch": branch, "rebasing": rebasing, "ahead": ahead, "behind": behind,
            "dirty": len(dirty), "dirty_sample": dirty[:6], "agent_stashes": stashes[:3]}


def http_ok(url, timeout=12, tries=2):
    # 2 deneme: tek bir anlık ağ hıçkırığı sabah uyarısı göndermesin
    res = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "parafomo-health"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.status
        except Exception as e:
            res = str(e)[:60]
        if i + 1 < tries:
            import time
            time.sleep(5)
    return res


def stale_data():
    """Elle/aylık beslenen veri sayfaları bayatladı mı? (2026-10-10: kira sayfası 2 ay eski kalmıştı.)"""
    out = []
    today = dt.date.today()
    AY = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
    def load(name):
        try:
            return json.load(open(os.path.join(ROOT, "data", name), encoding="utf-8"))
        except Exception:
            return None
    if today.day > 8:  # TÜİK ~3'ü açıklar; 8'inden sonra hâlâ eskiyse sorun
        k = load("kira-artis-2026.json")
        want = f"{AY[today.month - 1]} {today.year}"
        if k and k.get("guncelAy") != want:
            out.append(f"kira oranı bayat ({k.get('guncelAy')} ≠ {want}) → scripts/kira-artis-update.sh")
        t = load("tufe-aylik.json")
        prev = (today.replace(day=1) - dt.timedelta(days=1)).strftime("%Y-%m")
        if t and t["months"][0]["ay"] != prev:
            out.append(f"TÜFE serisi bayat (son {t['months'][0]['ay']} ≠ {prev}) → scripts/tufe-update.py")
        y = load("yeniden-degerleme.json")
        son = (y or {}).get("veriSonAy") or (y or {}).get("sonAy")
        if y and son != prev:
            out.append(f"Yİ-ÜFE/YD serisi bayat (son {son} ≠ {prev}) → scripts/yeniden-degerleme-update.py")
    # Yeniden değerleme sezon bekçisi (Kasım-Aralık): Ekim verisi + tebliğ takibi (week.md T13)
    y = load("yeniden-degerleme.json")
    if y:
        yil = today.year
        if today >= dt.date(yil, 11, 4) and y.get("sonAy", "") < f"{yil}-10":
            out.append(f"YD KRİTİK: Ekim {yil} Yİ-ÜFE hâlâ yok (son {y.get('sonAy')}) — oran kesinleşemedi → scripts/yeniden-degerleme-update.py")
        teblig_ok = (y.get("hedefYil") == yil + 1 and y.get("tebligOrani")) or \
            any(g.get("uygulamaYili") == yil + 1 for g in y.get("gecmis", []))
        if today >= dt.date(yil, 12, 5) and not teblig_ok:
            out.append(f"YD KRİTİK: {yil + 1} tebliğ oranı doğrulanıp yazılmadı → WebSearch ile Resmî Gazete tebliğini bul, data/yeniden-degerleme.json tebligOrani alanına yaz, sonra python3 scripts/live-posts.py")
    # Kıdem tazminatı tavanı Ocak/Temmuz'da değişir; HMB katsayı genelgesi ilk haftada çıkar
    kt = load("kidem-tavan.json")
    if kt and today.day > 10 and today.month in (1, 7):
        want = f"{today.year}-{today.month:02d}-01"
        if kt["donemler"][-1]["baslangic"] != want:
            out.append(f"kıdem tavanı bayat (son dönem {kt['donemler'][-1]['baslangic']} ≠ {want}) → WebSearch ile HMB/TÜRMOB tavanını doğrula, data/kidem-tavan.json'a yeni dönem ekle")
    # Memur katsayıları / en düşük aylıklar Ocak-Temmuz değişir (HMB genelgesi ilk hafta); bayram ikramiyesi yılbaşı
    em = load("emekli-memur.json")
    if em and today.month in (1, 7) and today.day > 15 and em.get("donem") != f"{today.year}-{today.month:02d}":
        out.append(f"memur katsayıları / en düşük emekli aylığı bayat (dönem {em.get('donem')}) → WebSearch ile HMB genelgesi + "
                   "SGK tutarlarını ≥2 kaynakla doğrula, data/emekli-memur.json'u güncelle (/memur-zammi-hesaplama, /en-dusuk-emekli-maasi)")
    # Sosyal aylıklar (/engelli-maasi): memur katsayısı yeni döneme geçtiyse ASHB resmî tutarları da girilmeli
    sa = load("sosyal-aylik-2026.json")
    if em and sa and em.get("donem") and sa.get("resmi", {}).get("donem") and em["donem"] > sa["resmi"]["donem"]:
        out.append(f"sosyal aylıklar bayat: memur katsayısı {em['donem']} ama ASHB resmî tutarlar {sa['resmi']['donem']} → "
                   "ASHB duyurusundan 65 yaş/engelli aylıklarını doğrula, data/sosyal-aylik-2026.json resmi bloğunu güncelle")
    # Emekli promosyonu (/emekli-promosyonu): bankaların kampanyaları ay sonunda biter; resmi sayfadan yeniden kontrol
    ep = load("emekli-promosyon.json")
    if ep:
        biten = [b["banka"] for b in ep["bankalar"] if b.get("bitis") and b["bitis"] < today.isoformat()]
        eski = (today - dt.date.fromisoformat(ep["kontrol"])).days
        if biten or eski > 30:
            out.append(f"emekli promosyonu kontrol bekliyor (son kontrol {ep['kontrol']}, {eski} gün; süresi dolan: "
                       f"{', '.join(biten) or 'yok'}) → bankaların resmi sayfalarını WebFetch ile oku, data/emekli-promosyon.json "
                       "tutar/bitis/kontrol alanlarını güncelle (haber sitesi rakamı YAZMA)")
    # KYK burs/kredi (/kyk-burs-miktari): yeni yıl tutarı Ocak başında açıklanır (Kabine sonrası, GSB duyurusu)
    ky = load("kyk-burs.json")
    if ky and today.month == 1 and today.day > 10 and ky.get("yil") != today.year:
        out.append(f"KYK burs tutarı bayat (yıl {ky.get('yil')}) → gsb.gov.tr duyurusundan {today.year} lisans/YL/doktora "
                   "tutarını al, data/kyk-burs.json tutarlar başına ekle + yil/kontrol (haber sitesi rakamı YAZMA)")
    # app.parafomo.com kendi veri kopyasını okur (deploy-app.sh); repo TÜFE'si ilerideyse app reel getirisi eskide kalır
    try:
        app_t = json.load(open("/srv/parafomo-app/tufe-aylik.json", encoding="utf-8"))
        rt = load("tufe-aylik.json")
        if rt and app_t["months"][0]["ay"] != rt["months"][0]["ay"]:
            out.append(f"app TÜFE kopyası eski ({app_t['months'][0]['ay']} ≠ {rt['months'][0]['ay']}) → bash scripts/deploy-app.sh")
    except Exception:
        pass
    # TCMB haftalık faizleri (EVDS): hafta (Cuma) bir sonraki Cuma ~12:40 UTC cron'unda gelir → Cuma sabahı normal yaş 14 gün;
    # 15 günden eskiyse anahtar/API bozulmuş olabilir
    fz = load("faiz-oranlari.json")
    if fz and (today - dt.date.fromisoformat(fz["hafta"])).days > 15:
        out.append(f"TCMB faiz verisi bayat (son hafta {fz['hafta']}) → bash scripts/evds-update.sh (EVDS anahtarı: ~/.config/parafomo/evds.env)")
    # Günlük/sık güncellenen veri dosyaları: 'updated' alanı eşikten eskiyse alarm
    for name, max_days, fix in (
        ("altin-getiri.json", 4, "scripts/gold-returns.py"), ("dolar-getiri.json", 4, "scripts/dollar-returns.py"),
        ("gumus-getiri.json", 4, "scripts/silver-returns.py"), ("euro-getiri.json", 4, "scripts/euro-returns.py"),
        ("bitcoin-getiri.json", 4, "scripts/bitcoin-returns.py"), ("bist-getiri.json", 4, "scripts/bist-returns.py"),
        # halka-arz.json: 'updated' 2026-11-18'den beri yalnız veri GERÇEKTEN değişince ilerler (halka-arz-update.sh
        # zaman-damgası-yalnız değişikliği geri alır) → hafta sonu Cuma→Pazartesi 3 gün normal; eşik 4.
        ("altin-fiyat.json", 3, "scripts/altin-fiyat.py"), ("halka-arz.json", 4, "scripts/fetch-halka-arz.py"),
        ("economic-calendar.json", 9, "scripts/fetch-economic-calendar.py"),
    ):
        d = load(name)
        upd = (d or {}).get("updated", "")[:10]
        try:
            age = (today - dt.date.fromisoformat(upd)).days
        except Exception:
            continue
        if age > max_days:
            out.append(f"{name} bayat ({age} gün; eşik {max_days}) → {fix}")
    # Talep madencisi + OG kartları üretim kontrolü
    try:
        g = json.load(open(os.path.join(ROOT, "data", "learning", "demand-gaps.json"), encoding="utf-8"))
        age = (today - dt.date.fromisoformat(g["generated_utc"][:10])).days
        if age > 9:
            out.append(f"demand-gaps.json bayat ({age} gün) → scripts/learn/demand_miner.py (learn-daily Çrş+Paz)")
    except Exception:
        out.append("demand-gaps.json yok → scripts/learn/demand_miner.py")
    og = os.path.join(ROOT, "public", "og")
    pngs = [os.path.join(og, f) for f in os.listdir(og)] if os.path.isdir(og) else []
    if len(pngs) < 10:
        out.append(f"OG kartları eksik ({len(pngs)} png) → scripts/og-images.py")
    elif pngs and all((dt.date.today() - dt.date.fromtimestamp(os.path.getmtime(p))).days > 45 for p in pngs):
        out.append("OG kartları 45+ gündür hiç yenilenmemiş → scripts/og-images.py üretimi kontrol et")
    # Canlı blog yazıları (content-templates/blog → scripts/live-posts.py): elle düzenleme veri güncellemesini durdurur
    try:
        import subprocess
        r = subprocess.run(["python3", os.path.join(ROOT, "scripts", "live-posts.py"), "--check"],
                           capture_output=True, text=True, timeout=60)
        for line in r.stdout.splitlines():
            if "UYARI" in line:
                out.append("canlı yazı: " + line.replace("[live-posts] UYARI: ", "")[:400])
            elif "GÜNCELLENECEK" in line:
                out.append("canlı yazı veriden geride: " + line.replace("[live-posts] ", "") + " → python3 scripts/live-posts.py")
    except Exception as e:
        out.append(f"live-posts --check çalışmadı: {e}")
    # Yıl sonu: BÜTÜN yıl dosyalarındaki (+ meetingsYYYY listeleri) son toplantı geçtiyse sonraki yılın takvimi eklenmeli
    # (takvim sayfası "sıradaki karar"ı gösteremez). Sonraki yıl = son toplantının yılı + 1. Eskiden today.year + 1'di:
    # 1 Ocak'tan sonra "data/tcmb-2028.json ekle" diyordu (yıl geçişi denetimi 2026-11-03, af0ec65; ajan uydurma dosya
    # açabilirdi). Not: tcmb-faiz-takvimi.astro yalnız tcmb-2026.json'u, fed-faiz-takvimi.astro meetings + meetings2027'yi okur.
    import glob as _glob
    for prefix, label in (("tcmb", "TCMB"), ("fomc", "Fed")):
        dates = []
        for p in _glob.glob(os.path.join(ROOT, "data", f"{prefix}-[0-9][0-9][0-9][0-9].json")):
            dd = load(os.path.basename(p)) or {}
            for k, v in dd.items():
                if (k == "meetings" or (k.startswith("meetings") and k[8:].isdigit())) and isinstance(v, list):
                    dates += [m["decisionDate"] for m in v if isinstance(m, dict) and m.get("decisionDate")]
        if dates and max(dates) < today.isoformat():
            yil = int(max(dates)[:4]) + 1
            hedef = (f"data/tcmb-{yil}.json ekle ve src/pages/tcmb-faiz-takvimi.astro'yu (şu an yalnız tcmb-2026.json "
                     f"import ediyor) yeni dosyaya bağla" if prefix == "tcmb" else
                     f"data/fomc-2026.json'a meetings{yil} ekle — fed-faiz-takvimi.astro yalnız meetings + meetings2027 "
                     f"okuyor, sayfayı da yeni listeye bağla")
            out.append(f"{label} {yil} toplantı takvimi yok (son toplantı {max(dates)} geçti) → resmî takvimi "
                       f"WebSearch ile doğrula, {hedef}")
    for name, label in (("fomc-2026.json", "Fed"), ("tcmb-2026.json", "TCMB")):
        d = load(name)
        if not d:
            continue
        for m in d["meetings"]:
            # karar günü + 1 gün sonra hâlâ result yoksa
            if (today - dt.date.fromisoformat(m["decisionDate"])).days >= 1 and not m.get("result"):
                out.append(f"{label} {m['decisionDate']} kararı yazılmadı → scripts/policy-decisions.sh")
    return out


def seo_status():
    """scripts/seo-audit.py özeti (panel + sorun listesi)."""
    try:
        d = json.load(open(os.path.join(ROOT, "data", "learning", "seo-audit.json"), encoding="utf-8"))
    except Exception:
        return None
    age = (_now() - dt.datetime.fromisoformat(d["generated"])).total_seconds() / 3600
    return {"counts": d["counts"], "index": d["index"], "pages": d["pages"], "age_h": round(age, 1),
            "by_code": d.get("by_code", {}), "codes": d.get("codes", {}),
            "issues": [i for i in d["issues"] if i["sev"] != "BİLGİ"][:200]}


def distribution_status():
    """Olay sonucu Short'ları (scripts/event-short.py) + Facebook yayın izni (scripts/facebook-*.py)."""
    out = {}
    try:
        st = json.load(open(os.path.join(LOGS, "event-shorts.json"), encoding="utf-8"))
        ev = {k: v for k, v in st.items() if not k.startswith("_") and v.get("status") != "skip"}
        if ev:
            k, v = max(ev.items(), key=lambda kv: kv[1].get("ts", ""))
            out["event"] = {"key": k, **v}
    except Exception:
        pass
    try:
        out["fb"] = json.load(open(os.path.join(LOGS, "fb-status.json"), encoding="utf-8"))
    except Exception:
        pass
    return out


def disk_status():
    du = shutil.disk_usage("/")
    pct = round(du.used / (du.used + du.free) * 100)        # df'in "Use%" değeri
    free_gb = round(du.free / 1e9, 1)
    return pct, free_gb, (free_gb < DISK_MIN_FREE_GB or pct >= DISK_MAX_PCT)


def collect():
    pct, free_gb, low = disk_status()
    return {
        "ts": _now().isoformat(timespec="seconds"),
        "pipelines": pipelines(),
        "llm": llm_status(),
        "git": git_status(),
        "disk_pct": pct,
        "disk_free_gb": free_gb,
        "disk_low": low,
        "site": http_ok("https://parafomo.com/"),
        "api": http_ok("https://api.parafomo.com/health"),
        "kuyruk": kuyruk_status(),
        "stale": stale_data(),
        "seo": seo_status(),
        "dist": distribution_status(),
    }


ICON = {"OK": "✅", "UYARI": "🟡", "GECİKTİ": "🔴", "HATA": "🔴", "BİLİNMİYOR": "⚪"}


def render(h):
    out = ["| Hat | Durum | Son başarı | Not |", "|---|---|---|---|"]
    for r in h["pipelines"]:
        err = f" — `{r['error'][:110]}`" if r.get("error") and r["status"] != "OK" else ""
        out.append(f"| {r['name']} | {ICON.get(r['status'], '')} {r['status']} | {r['age']} | {r['note']}{err} |")
    llm = h["llm"]
    llm_txt = "✅ ok" if llm["state"] == "ok" else f"🔴 {llm['state']}" + (f" (→ {llm['until']})" if llm.get("until") else "")
    g = h["git"]
    git_txt = f"{g['branch']}" + (" · ⚠️ main DEĞİL" if g["branch"] != "main" else "") + \
        (" · ⚠️ YARIM REBASE" if g["rebasing"] else "") + \
        (f" · {g['ahead']} push bekliyor" if g["ahead"] else "") + (f" · {g['behind']} geride" if g["behind"] else "") + \
        (f" · {g['dirty']} kirli dosya" if g["dirty"] else " · temiz")
    if g["agent_stashes"]:
        git_txt += f" · yarım ajan işi stash'te: {g['agent_stashes'][0]}"
    disk = f"%{h['disk_pct']} dolu ({h['disk_free_gb']} GB boş)" + \
        (f" ⚠️ (eşik: <{DISK_MIN_FREE_GB:g} GB boş ya da ≥%{DISK_MAX_PCT}; bakım uyarır)" if h.get("disk_low") else "")
    k = h.get("kuyruk") or {}
    k_txt = "kuyruk.json yok" if k.get("onayli") is None else (
        f"{k['onayli']} onaylı · {k['bekliyor']} bekliyor"
        + (f" · otomatik onay bitişi {k['oto_bitis']}" if k.get("oto_bitis") else ""))
    if k.get("uyari"):
        k_txt += " · 🔴 " + "; ".join(k["uyari"])
    out += ["", f"- **Claude (LLM) durumu:** {llm_txt}",
            f"- **Git:** {git_txt}",
            f"- **Disk:** {disk}",
            f"- **Canlı site:** {h['site']} · **Portföy API:** {h['api']}",
            f"- **Yayın kuyruğu:** {k_txt}",
            "- **Veri tazeliği:** " + ("✅ güncel" if not h.get("stale") else "🔴 " + "; ".join(h["stale"]))]
    d = h.get("dist") or {}
    ev, fb = d.get("event"), d.get("fb")
    ev_txt = "henüz yok" if not ev else (
        f"{ev['key']} → " + ("✅ " + (ev.get("youtube_url") or "yayında") if ev.get("status") == "done"
                             else f"🔴 {ev.get('status')} (deneme {ev.get('attempts')}) — `logs/event-short.log`"))
    fb_txt = "⚪ hiç çalışmadı" if not fb else ("✅ paylaşıyor" if fb.get("ok") else
                                                  f"⏸ {str(fb.get('reason') or '')[:90]}")
    out.append(f"- **Dağıtım:** olay sonucu Short'u: {ev_txt} · Facebook: {fb_txt}")
    return "\n".join(out)


def problems(h, alarm=False):
    """E-posta konusu/özet için kısa sorun listesi.

    alarm=True → yalnız Kaan'a UYARI gerektiren operasyonel sorunlar (agent/sabah.sh → notify.py --key saglik):
    bayat veri ve SEO maddeleri çıkarılır (sabah rutini onları aynı gün kapatır; her gün mail atmasın),
    disk de çıkarılır (scripts/maintenance.sh 04:30'da kendi 'disk' uyarısını du dökümüyle atar)."""
    p = [f"{r['name']}: {r['status']} (son başarı {r['age']}; logs/{spec[1]})"
         for r, spec in zip(h["pipelines"], PIPELINES) if r["status"] in ("GECİKTİ", "HATA")]
    if h["llm"]["state"] != "ok":
        p.append(f"Claude: {h['llm']['state']}")
    if h["git"]["rebasing"]:
        p.append("git: yarım rebase")
    if h["git"]["branch"] != "main":
        p.append(f"git: çalışma dizini '{h['git']['branch']}' dalında (main değil — commit'ler canlıya gitmez)")
    if h.get("disk_low") and not alarm:
        p.append(f"disk %{h['disk_pct']} ({h['disk_free_gb']} GB boş)")
    if h["site"] != 200:
        p.append(f"site: {h['site']}")
    if h["api"] != 200:
        p.append(f"api: {h['api']}")
    p += [f"yayın kuyruğu: {x}" for x in (h.get("kuyruk") or {}).get("uyari", [])]
    ev = (h.get("dist") or {}).get("event")
    if ev and ev.get("status") == "failed":
        try:
            ev_h = age_h(dt.datetime.fromisoformat(ev.get("ts", "")))
        except Exception:
            ev_h = None
        # uyarı yalnız taze başarısızlıkta (≤3 gün); eskisi (ör. 3 Kasım weekly_limit) her sabah mail atmasın
        if not alarm or (ev_h is not None and ev_h <= 72):
            p.append(f"olay Short'u başarısız: {ev['key']} (logs/event-short.log)")
    if alarm:
        return p
    p += [f"veri: {x}" for x in h.get("stale", [])]
    seo = h.get("seo")
    if seo and seo["counts"].get("KRİTİK"):
        p.append(f"SEO: {seo['counts']['KRİTİK']} kritik sorun")
    if seo and seo["age_h"] > 72:
        p.append("SEO denetimi 3 gündür çalışmadı (learn-daily.sh)")
    return p


def sabah_raporu(h):
    """agent/sabah.sh: istemin sonuna eklenen sağlık bölümü (agent/state/saglik.md)."""
    stale = h.get("stale") or []
    tablo = [("- **Veri tazeliği:** " + (f"🔴 {len(stale)} madde (aşağıda)" if stale else "✅ güncel"))
             if l.startswith("- **Veri tazeliği:**") else l for l in render(h).split("\n")]
    out = [f"_Üretildi: {h['ts']} (agent/health.py)_", "", *tablo, ""]
    if stale:
        out.append("**Veri tazeliği — bugün kapatılacaklar** (her biri resmî kaynakla, ≥2 kaynak):")
        out += [f"{i}. {x}" for i, x in enumerate(stale, 1)]
        out.append("")
    pr = [x for x in problems(h) if not x.startswith("veri: ")]
    out.append("**Diğer sorunlar:** " + ("; ".join(pr) if pr else "yok"))
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    h = collect()
    if "--json" in sys.argv:
        print(json.dumps(h, ensure_ascii=False, indent=1))
    elif "--sabah" in sys.argv:
        # agent/sabah.sh: rapor → dosya (istemin sonuna eklenir); stdout'a yalnız uyarı satırları (boş = uyarı yok)
        i = sys.argv.index("--sabah")
        path = sys.argv[i + 1] if i + 1 < len(sys.argv) else os.path.join(STATE, "saglik.md")
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(sabah_raporu(h))
        for x in problems(h, alarm=True):
            print(x)
    else:
        print(render(h))
        pr = problems(h)
        print("\n**Sorunlar:** " + ("; ".join(pr) if pr else "yok"))

