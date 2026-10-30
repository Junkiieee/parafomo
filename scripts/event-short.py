#!/usr/bin/env python3
"""Olay SONUCU Short'u — resmî rakam açıklanınca o rakamla "açıklandı / belli oldu" videosu.

Olaylar: TÜİK enflasyon günü (TÜFE + o ay geçerliyse kira tavanı, Kasım'da yeniden değerleme oranı, Ocak/Temmuz'da
emekli zammı) · TCMB faiz kararı · Fed faiz kararı · asgari ücret.

Neden (2026-10-28 ölçümü): kanalın en çok izlenen günleri olay günleri (TCMB 22 Ekim: 1.346 izlenme/gün; Fed
önizlemesi 826 izlenme, kanal medyanı ~100). İzlenmenin %21'i YouTube ARAMASINDAN geliyor ve insanlar o gün sonucu
arıyor ("enflasyon açıklandı", "kira artış oranı kasım", "asgari ücret belli oldu"). Gündem videosu (news-daily)
açıklamadan ÖNCE çıktığı için sonucu söyleyemiyordu — 22 Ekim'de yanlış sonuç başlığı bile üretmişti.

Akış: data/*.json'da yeni ve TAZE (≤36 saat) resmî sonuç var mı? Yoksa ağa ve LLM'e hiç çıkmadan biter (ucuz →
sık çağrılabilir). Varsa: olgu metni YALNIZ veri dosyalarındaki rakamlardan kurulur → viral-daily.sh
--format event_result --facts … --must … --link … (senaryo zorunlu rakamları içermezse viral-script reddeder,
yanlış rakamlı video çıkmaz) → başarıda logs/event-shorts.json'a işaretlenir (aynı olay iki kez video olmaz).
Bir çağrıda en fazla BİR video. Gece (≥21:00 UTC) üretmez; olay tazeyse sabahki çağrıya kalır.

Kullanım:  python3 scripts/event-short.py                  # gerekiyorsa üret + yayınla
           python3 scripts/event-short.py --dry            # ne üreteceğini yaz (LLM/yayın yok)
           python3 scripts/event-short.py --dry --now 2026-11-03T08:00 --all   # test: tazelik + yapılmışları yok say
Çağıranlar (arka planda): policy-decisions.sh, kira-artis-update.sh, asgari-ucret-watch.py, learn-daily.sh.
"""
import datetime as dt
import fcntl
import glob
import json
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.environ.get("EVENT_SHORT_DATA") or os.path.join(REPO, "data")       # test: sahte veri klasörü
LOGS = os.path.join(REPO, "logs")
STATE = os.environ.get("EVENT_SHORT_STATE") or os.path.join(LOGS, "event-shorts.json")
LOCK = os.path.join(LOGS, "event-short.lock")
AYLAR = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos",
         "Eylül", "Ekim", "Kasım", "Aralık"]
FRESH_H = 36            # olaydan bu kadar saat sonrasına kadar video anlamlı
WINDOW_UTC = (5, 21)    # 08:00–24:00 TSİ arası üret; dışında sabaha bırak
MAX_ATTEMPTS = 2        # aynı olay için en fazla 2 deneme (LLM/render hatası)
GAP_H = 3               # iki olay videosu arası en az bu kadar saat


def tr(x, nd=2):
    """Türkçe sayı: 2.55 → '2,55' · 36.0 → '36' · 3.5 → '3,50' (nd=2)."""
    x = float(x)
    if abs(x - round(x)) < 1e-9 and nd == 2:
        return str(int(round(x)))
    return f"{x:.{nd}f}".replace(".", ",")


def money(x):
    """28075.5 → '28.075,50'"""
    s = f"{float(x):,.2f}"
    return s.replace(",", "§").replace(".", ",").replace("§", ".")


def thousands(x):
    """28075.5 → '28.075' (rakam kontrolü için tam kısım)"""
    return f"{int(float(x)):,}".replace(",", ".")


def load(name):
    try:
        with open(os.path.join(DATA, name), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def meetings(prefix, extra_key=None):
    out = []
    for p in sorted(glob.glob(os.path.join(DATA, f"{prefix}-20*.json"))):
        try:
            d = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        out += d.get("meetings", [])
        if extra_key:
            out += d.get(extra_key, [])
    seen, uniq = set(), []
    for m in sorted(out, key=lambda m: m.get("decisionDate", "")):
        if m.get("decisionDate") and m["decisionDate"] not in seen:
            seen.add(m["decisionDate"]); uniq.append(m)
    return uniq


def utc(d, hh, mm=0):
    return dt.datetime(d.year, d.month, d.day, hh, mm, tzinfo=dt.timezone.utc)


# ------------------------------------------------------------------ olay dedektörleri
def ev_tuik(now):
    """TÜİK günü → 1-2 olay: her ay 'enflasyon + kira tavanı'; Ekim verisinde ayrıca '<yıl> yeniden değerleme
    oranı', Haziran/Aralık verisinde ayrıca 'emekli zammı' (yılın en büyük iki sorgusu ayrı video hak ediyor)."""
    tufe = load("tufe-aylik.json").get("months") or []
    if len(tufe) < 2:
        return []
    m0, m1 = tufe[0], tufe[1]
    y, mo = map(int, m0["ay"].split("-"))
    covers = f"{AYLAR[mo - 1]} {y}"
    rel = None
    for p in sorted(glob.glob(os.path.join(DATA, "tuik-enflasyon-*.json"))):
        for r in (load(os.path.basename(p)).get("releases") or []):
            if r.get("covers") == covers:
                rel = dt.date.fromisoformat(r["date"])
    if rel is None:
        rel = dt.date(y + (mo == 12), 1 if mo == 12 else mo + 1, 3)
    when = utc(rel, 7)   # 10:00 TSİ
    app = f"{AYLAR[rel.month - 1]} {rel.year}"   # kira tavanı uygulama ayıyla anılır
    tufe_line = (f"TÜİK {covers} enflasyonu ({rel:%d.%m.%Y} açıklandı): TÜFE aylık %{tr(m0['aylik'])}, "
                 f"yıllık %{tr(m0['yillik'])}. Bir önceki ay ({AYLAR[(mo - 2) % 12]}) yıllık enflasyon %{tr(m1['yillik'])} idi.")
    base = {"key": f"tuik:{m0['ay']}", "when": when, "prio": 1, "facts": [tufe_line], "must": [tr(m0["yillik"])],
            "link": "/enflasyon-hesaplama/", "topic": f"{covers} enflasyonu açıklandı", "pending": [], "wait_h": 2}
    kira_ok = False
    for p in sorted(glob.glob(os.path.join(DATA, "kira-artis-*.json")), reverse=True):
        k = load(os.path.basename(p))
        if k.get("guncelAy") == app and k.get("guncelOran") is not None:
            base["facts"].append(f"Kira artış tavanı ({app} döneminde yenilenen sözleşmeler, 12 aylık TÜFE ortalaması): "
                                 f"%{tr(k['guncelOran'])}.")
            base["must"].append(tr(k["guncelOran"]))
            base["link"] = "/kira-artis-orani-hesaplama/"
            base["topic"] += f" — {app} kira artış oranı belli oldu"
            kira_ok = True
            break
    if not kira_ok:
        base["pending"].append("kira tavanı")   # en fazla 2 saat bekle, sonra kirasız çık
    evs = [base]
    if mo == 10:   # Ekim verisi → yeniden değerleme oranı kesinleşir (Kasım'ın en büyük sorgusu)
        yd = load("yeniden-degerleme.json")
        hy = yd.get("hedefYil") or y + 1
        e = {"key": f"yd:{hy}", "when": when, "prio": 0, "link": "/yeniden-degerleme-orani/", "pending": [],
             "wait_h": 6, "topic": f"{hy} yeniden değerleme oranı belli oldu (MTV, harç ve ceza zammı)"}
        if yd.get("sonAy") == m0["ay"] and yd.get("onikiAyOrt") is not None:
            e["facts"] = [f"{hy} yeniden değerleme oranı kesinleşti: %{tr(yd['onikiAyOrt'])} (TÜİK Yİ-ÜFE 12 aylık ortalama, "
                          f"{rel:%d.%m.%Y}). MTV, harçlar ve birçok vergi/ceza tutarı {hy} yılında bu orana göre artar; "
                          f"Cumhurbaşkanı MTV ve harçlarda daha düşük bir oran belirleyebilir.", tufe_line]
            e["must"] = [tr(yd["onikiAyOrt"])]
            evs.append(e)
    if mo in (6, 12):   # Haziran/Aralık verisi → SSK/Bağ-Kur emekli zammı (6 aylık TÜFE farkı)
        want = [f"{y}-{x:02d}" for x in range(mo - 5, mo + 1)]
        by = {r["ay"]: r for r in tufe}
        if all(a in by for a in want):
            cum = 1.0
            for a in want:
                cum *= 1 + float(by[a]["aylik"]) / 100
            zy, zm = (y + 1, "Ocak") if mo == 12 else (y, "Temmuz")
            evs.append({"key": f"emekli:{zy}-{zm}", "when": when, "prio": 0, "link": "/emekli-zammi-hesaplama/",
                        "pending": [], "topic": f"SSK ve Bağ-Kur emekli zammı {zm} {zy} belli oldu",
                        "facts": [f"SSK ve Bağ-Kur emeklilerinin {zm} {zy} zammı (son 6 ayın enflasyon farkı, TÜİK "
                                  f"{rel:%d.%m.%Y}): %{tr((cum - 1) * 100)}.", tufe_line],
                        "must": [tr((cum - 1) * 100)]})
    return evs


def _next_range(ms, after):
    nxt = next((m for m in ms if m["decisionDate"] > after), None)
    return f"{nxt['range']} {nxt['decisionDate'][:4]}" if nxt else ""


def ev_tcmb(now):
    ms = meetings("tcmb")
    done = [m for m in ms if (m.get("result") or {}).get("rate") is not None]
    if not done:
        return None
    m = done[-1]; r = m["result"]
    d = dt.date.fromisoformat(m["decisionDate"])
    prev = r.get("prev")
    if prev is None and len(done) > 1:
        prev = done[-2]["result"].get("rate")
    word = {"cut": "indirim", "hike": "artırım", "hold": "değişiklik yok"}.get(r.get("decision"), "")
    bp = abs(int(r.get("bp") or 0))
    facts = [f"TCMB Para Politikası Kurulu {m['range']} {d.year} kararı: politika faizi (1 hafta vadeli repo) "
             + (f"önceki %{tr(prev)} → yeni %{tr(r['rate'])}" if prev is not None else f"%{tr(r['rate'])}")
             + (f" ({bp} baz puan {word})." if bp else " (değişiklik yok, sabit).")]
    if r.get("lending") is not None and r.get("borrowing") is not None:
        facts.append(f"Gecelik borç verme faizi %{tr(r['lending'])}, gecelik borçlanma faizi %{tr(r['borrowing'])}.")
    nr = _next_range(ms, m["decisionDate"])
    if nr:
        facts.append(f"Sıradaki PPK toplantısı: {nr}.")
    return {"key": f"tcmb:{m['decisionDate']}", "when": utc(d, 11), "topic": f"TCMB faiz kararı açıklandı ({m['range']} {d.year})",
            "facts": facts, "must": [tr(r["rate"])], "link": "/tcmb-faiz-takvimi/", "pending": []}


def ev_fed(now):
    ms = meetings("fomc", "meetings2027")
    done = [m for m in ms if (m.get("result") or {}).get("upper") is not None]
    if not done:
        return None
    m = done[-1]; r = m["result"]
    d = dt.date.fromisoformat(m["decisionDate"])
    hh = int((m.get("tsiTime") or "21:00")[:2]) - 3
    p = done[-2]["result"] if len(done) > 1 else None
    word = {"cut": "indirim", "hike": "artırım", "hold": "değişiklik yok"}.get(r.get("decision"), "")
    bp = abs(int(r.get("bp") or 0))
    facts = [f"Fed (FOMC) {m['range']} {d.year} toplantısı kararı: politika faizi aralığı %{tr(r['lower'])}–%{tr(r['upper'])}"
             + (f" (önceki %{tr(p['lower'])}–%{tr(p['upper'])})" if p else "")
             + (f"; {bp} baz puan {word}." if bp else "; değişiklik yok, sabit tutuldu.")]
    nr = _next_range(ms, m["decisionDate"])
    if nr:
        facts.append(f"Sıradaki Fed toplantısı: {nr}.")
    return {"key": f"fed:{m['decisionDate']}", "when": utc(d, hh), "topic": f"Fed faiz kararı açıklandı ({m['range']} {d.year})",
            "facts": facts, "must": [tr(r["upper"])], "link": "/fed-faiz-takvimi/", "pending": []}


def ev_asgari(now):
    a = load("asgari-ucret.json")
    y = a.get("yeni") or {}
    if not (y.get("aciklanma") and (y.get("net") or y.get("brut"))):
        return None
    if y.get("otomatik") and len(y.get("kaynak") or []) < 3:   # haberden tespit + az kaynak → videoya dayanak değil
        return None
    d = dt.date.fromisoformat(y["aciklanma"])
    net = float(y.get("net") or float(y["brut"]) * 0.85)
    brut = float(y.get("brut") or net / 0.85)
    g = a.get("guncel") or {}
    facts = [f"{y['yil']} asgari ücreti açıklandı ({d:%d.%m.%Y}): net {money(net)} TL, brüt {money(brut)} TL."]
    if g.get("net"):
        facts.append(f"{g.get('yil')} net asgari ücreti {money(g['net'])} TL idi; net artış %{tr((net / float(g['net']) - 1) * 100)}.")
    return {"key": f"asgari:{y['yil']}", "when": utc(d, 12), "topic": f"{y['yil']} asgari ücreti belli oldu",
            "facts": facts, "must": [thousands(net)], "link": "/asgari-ucret-hesaplama/", "pending": []}


DETECTORS = (ev_tuik, ev_tcmb, ev_fed, ev_asgari)


# ------------------------------------------------------------------ durum + çalıştırma
def load_state():
    try:
        return json.load(open(STATE, encoding="utf-8"))
    except Exception:
        return {}


def save_state(st):
    os.makedirs(LOGS, exist_ok=True)
    tmp = STATE + ".tmp"
    json.dump(st, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    os.replace(tmp, STATE)


def candidates(now, st, ignore_state=False):
    found = []
    for det in DETECTORS:
        try:
            r = det(now)
        except Exception as ex:
            print(f"[event-short] {det.__name__} okunamadı: {type(ex).__name__}: {str(ex)[:120]}")
            continue
        found += r if isinstance(r, list) else ([r] if r else [])
    # Tazelik = takvim saati ile verinin İLK görüldüğü anın geç olanı. Neden: TÜİK takviminde tarih yoksa (ör. Aralık
    # verisi Ocak'ta) ayın 3'ü varsayılır; açıklama 5'inde gelirse olay "36 saatten eski" sayılıp en büyük video
    # (Ocak emekli zammı) kaçardı. İlk kurulumda (durum dosyası boş) o an var olan olaylar video OLMAZ (geriye dönük yok).
    seen = st.setdefault("_seen", {})
    boot = not seen and not [k for k in st if not k.startswith("_")]
    out = []
    for e in found:
        first = seen.get(e["key"])
        if first is None:
            first = seen[e["key"]] = now.isoformat(timespec="seconds")
            if boot:
                st[e["key"]] = {"status": "skip", "ts": first, "note": "ilk kurulumda zaten vardı"}
        eff = max(e["when"], dt.datetime.fromisoformat(first))
        age_h = (now - eff).total_seconds() / 3600
        rec = st.get(e["key"], {})
        e["age_h"] = age_h
        if ignore_state:
            out.append(e); continue
        if age_h < 0 or age_h > FRESH_H:
            continue
        if rec.get("status") in ("done", "skip") or rec.get("attempts", 0) >= MAX_ATTEMPTS:
            continue
        if e["pending"] and age_h < e.get("wait_h", 0):
            print(f"[event-short] {e['key']}: bekleniyor ({', '.join(e['pending'])} henüz gelmedi, {age_h:.1f} sa)")
            continue
        out.append(e)
    return sorted(out, key=lambda e: (e["when"], e.get("prio", 1)))


def run(e, st, now):
    facts = " ".join(e["facts"])
    cmd = ["bash", os.path.join(REPO, "scripts", "viral-daily.sh"), "--format", "event_result",
           "--topic", e["topic"], "--facts", facts, "--must", "|".join(e["must"]), "--link", e["link"]]
    rec = st.setdefault(e["key"], {})
    rec["attempts"] = rec.get("attempts", 0) + 1
    rec["ts"] = now.isoformat(timespec="seconds")
    save_state(st)
    print(f"[event-short] {e['key']} → video üretiliyor: {e['topic']} | zorunlu: {e['must']} | link {e['link']}")
    try:
        p = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, timeout=2400)
    except subprocess.TimeoutExpired:
        rec.update({"status": "failed", "error": "viral-daily.sh 40 dk'da bitmedi (zaman aşımı)"})
        save_state(st)
        print(f"[event-short] {e['key']}: ZAMAN AŞIMI (deneme {rec['attempts']}/{MAX_ATTEMPTS})")
        return 2
    tail = (p.stdout or "")[-1500:]
    print(tail)
    if p.returncode != 0:
        print((p.stderr or "")[-800:])
        rec["status"] = "failed"
        rec["error"] = ((p.stderr or "") + tail)[-300:]
        save_state(st)
        print(f"[event-short] {e['key']}: BAŞARISIZ (deneme {rec['attempts']}/{MAX_ATTEMPTS})")
        return 2
    url = ""
    for ln in tail.splitlines():
        if "Tamamlandı:" in ln and "→" in ln:
            url = ln.rsplit("→", 1)[1].strip()
    if not url:   # hat bitti ama YouTube'a yüklenmedi (kota/ağ) → başarı sayma, bir kez daha denensin
        rec.update({"status": "failed", "error": "YouTube URL yok — yükleme başarısız olabilir (logs/event-short.log)"})
        save_state(st)
        print(f"[event-short] {e['key']}: YouTube'a yüklenmedi (deneme {rec['attempts']}/{MAX_ATTEMPTS})")
        return 2
    rec.update({"status": "done", "youtube_url": url, "topic": e["topic"]})
    rec.pop("error", None)
    save_state(st)
    print(f"[event-short] {e['key']}: yayınlandı {url}")
    return 0


def main(argv):
    dry = "--dry" in argv
    now = dt.datetime.now(dt.timezone.utc)
    if "--now" in argv:
        now = dt.datetime.fromisoformat(argv[argv.index("--now") + 1]).replace(tzinfo=dt.timezone.utc)
    os.makedirs(LOGS, exist_ok=True)
    lockf = open(LOCK, "w")
    try:
        fcntl.flock(lockf, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print("[event-short] başka bir event-short çalışıyor — çıkış")
        return 0
    st = load_state()
    before = json.dumps(st, sort_keys=True)
    cands = candidates(now, st, ignore_state="--all" in argv)
    if not dry and json.dumps(st, sort_keys=True) != before:
        save_state(st)
    if dry:
        if not cands:
            print("[event-short] üretilecek taze olay yok")
        for e in cands:
            print(f"- {e['key']} · {e['age_h']:.1f} sa önce · {e['topic']}\n  olgular: {' '.join(e['facts'])}\n"
                  f"  zorunlu: {e['must']} · link {e['link']}" + (f" · eksik: {e['pending']}" if e['pending'] else ""))
        return 0
    if not cands:
        return 0
    if not (WINDOW_UTC[0] <= now.hour < WINDOW_UTC[1]):
        print(f"[event-short] {cands[0]['key']} hazır ama saat {now:%H:%M} UTC — sabaha bırakıldı")
        return 0
    # iki olay videosu arası ≥ GAP_H: aynı gün art arda iki video birbirinin akış dağıtımını yiyor (V2, 10-15)
    last = max((v.get("ts", "") for k, v in st.items() if not k.startswith("_") and v.get("status") == "done"), default="")
    if last:
        gap = (now - dt.datetime.fromisoformat(last)).total_seconds() / 3600
        if gap < GAP_H:
            print(f"[event-short] {cands[0]['key']} hazır ama son olay videosu {gap:.1f} sa önce — {GAP_H} sa aralık bekleniyor")
            return 0
    return run(cands[0], st, now)


if __name__ == "__main__":
    # YAYIN DURDURMA BAYRAĞI (Kaan 2026-10-30): dosya varsa hiçbir şey yayınlanmaz (--dry serbest)
    import os as _os, sys as _sys
    if _os.path.exists("/root/parafomo-data/PUBLISH_PAUSED") and "--dry" not in _sys.argv:
        print("[durduruldu] /root/parafomo-data/PUBLISH_PAUSED var — yayın yapılmadı."); _sys.exit(0)
    sys.exit(main(sys.argv[1:]))
