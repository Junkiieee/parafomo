#!/usr/bin/env python3
"""Fed ve TCMB faiz kararlarını birincil kaynaktan çekip takvim verisine yazar.

data/fomc-2026.json ve data/tcmb-2026.json'da tarihi geçmiş ama `result` alanı olmayan toplantı
varsa kaynağı okur ve doldurur → /fed-faiz-takvimi ve /tcmb-faiz-takvimi "güncel faiz" kutusu, karar
sütunu ve SSS'si karar gecesi tazelenir. Bekleyen toplantı yoksa ağa hiç çıkmaz.

Kaynaklar (yalnız birincil):
  Fed : federalreserve.gov/newsevents/pressreleases/monetaryYYYYMMDDa.htm (FOMC açıklaması)
  TCMB: tcmb.gov.tr .../Duyurular/Basin/<yıl>/DUY<yıl>-NN (sıra no. bilinmediği için son bilinen
        no.'dan ileri taranır; tarih + "Para Politikası Kurulu (Kurul)" metni eşleşmeli)
Ayıklanamazsa hiçbir şey yazmaz (yanlış rakam yerine boş karar). "GÜNCELLENDİ" basarsa veri değişti.
"""
import datetime as dt
import html
import json
import os
import re
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FOMC = os.path.join(REPO, "data", "fomc-2026.json")
TCMB = os.path.join(REPO, "data", "tcmb-2026.json")
AYLAR = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
         "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
FED_URL = "https://www.federalreserve.gov/newsevents/pressreleases/monetary{d}a.htm"
TCMB_URL = "https://www.tcmb.gov.tr/wps/wcm/connect/TR/TCMB+TR/Main+Menu/Duyurular/Basin/{y}/DUY{y}-{n:02d}"


def text_of(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (parafomo-policy/1.0)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        page = r.read().decode("utf-8", "replace")
    t = re.sub(r"<script.*?</script>|<style.*?</style>", " ", page, flags=re.S | re.I)
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t)))


def frac(s):
    """'3-3/4' / '3‑1/2' / '4' → 3.75 / 3.5 / 4.0"""
    s = s.replace("‑", "-").replace("‐", "-").strip()
    m = re.fullmatch(r"(\d+)(?:-(\d)/(\d))?", s)
    if not m:
        raise ValueError(s)
    v = float(m.group(1))
    if m.group(2):
        v += int(m.group(2)) / int(m.group(3))
    return v


def fed_result(date, prev):
    url = FED_URL.format(d=date.replace("-", ""))
    t = text_of(url)
    m = re.search(r"decided to (maintain|raise|lower) the target range for the federal funds rate"
                  r"(?: by [^ ]+ percentage point)? (?:at|to) ([\d‑‐/-]+) to ([\d‑‐/-]+) percent", t)
    if not m:
        return None
    lo, hi = frac(m.group(2)), frac(m.group(3))
    kind = {"maintain": "hold", "raise": "hike", "lower": "cut"}[m.group(1)]
    bp = round((lo - prev["lower"]) * 100)
    if (kind == "hold") != (bp == 0):
        return None  # metin ile önceki bant tutarsız → yazma
    res = {"decision": kind, "bp": bp, "lower": lo, "upper": hi}
    v = re.search(r"by a (\d+) \W (\d+) vote", t)
    if v:
        res["vote"] = f"{v.group(1)}–{v.group(2)}"
    res["source"] = url
    return res


def tr_num(s):
    return float(s.replace(",", "."))


def tcmb_result(date, year, start_no, prev_rate):
    d = dt.date.fromisoformat(date)
    label = f"{d.day} {AYLAR[d.month - 1]} {d.year}"
    for n in range(start_no, start_no + 20):
        url = TCMB_URL.format(y=year, n=n)
        try:
            t = text_of(url)
        except Exception:
            continue
        if label not in t or "Para Politikası Kurulu (Kurul)" not in t:
            continue
        i = t.find("Para Politikası Kurulu (Kurul)")
        para = t[i:i + 600]
        q = "[’']"
        ch = re.search(rf"yüzde ([\d,]+){q}(?:d|t)en yüzde ([\d,]+){q}(?:y|)e (indirilmesine|yükseltilmesine|artırılmasına)", para)
        hold = re.search(rf"yüzde ([\d,]+){q}(?:d|t)e sabit tutulmasına", para)
        if ch:
            prev, rate = tr_num(ch.group(1)), tr_num(ch.group(2))
            kind = "cut" if ch.group(3) == "indirilmesine" else "hike"
        elif hold:
            prev = rate = tr_num(hold.group(1))
            kind = "hold"
        else:
            return None
        if abs(prev - prev_rate) > 0.01:
            return None  # önceki faizle tutarsız → yazma
        res = {"decision": kind, "bp": round((rate - prev) * 100), "rate": rate}
        if kind != "hold":
            res["prev"] = prev
        res["no"] = f"{year}-{n:02d}"
        # "yüzde 41’den yüzde 40’a" → YENİ değer (40); "yüzde 40’ta sabit" → 40
        corr = rf"yüzde ([\d,]+){q}\w+(?: yüzde ([\d,]+){q})?"
        lend = re.search(r"borç verme faiz oranını " + corr, para)
        borr = re.search(r"borçlanma faiz oranını (?:ise )?" + corr, para)
        if lend and borr:
            res["lending"] = tr_num(lend.group(2) or lend.group(1))
            res["borrowing"] = tr_num(borr.group(2) or borr.group(1))
        res["source"] = url
        return res
    return None


def main():
    today = dt.date.today().isoformat()
    changed = False

    fomc = json.load(open(FOMC, encoding="utf-8"))
    prev = fomc["previous"]
    for m in fomc["meetings"]:
        if m.get("result"):
            prev = m["result"]
            continue
        if m["decisionDate"] > today:
            break
        try:
            res = fed_result(m["decisionDate"], prev)
        except Exception as e:
            print(f"[fed] {m['decisionDate']} çekilemedi: {e}")
            break
        if not res:
            print(f"[fed] {m['decisionDate']} kararı henüz yok/ayıklanamadı")
            break
        m["result"] = res
        prev = res
        changed = True
        print(f"[fed] GÜNCELLENDİ {m['decisionDate']}: {res['decision']} {res['bp']} bp → {res['lower']}–{res['upper']}")

    tcmb = json.load(open(TCMB, encoding="utf-8"))
    prev_rate = tcmb["previous"]["rate"]
    last_no = 0
    for m in tcmb["meetings"]:
        if m.get("result"):
            prev_rate = m["result"]["rate"]
            last_no = int(m["result"]["no"].split("-")[1])
            continue
        if m["decisionDate"] > today:
            break
        res = tcmb_result(m["decisionDate"], tcmb["year"], last_no + 1, prev_rate)
        if not res:
            print(f"[tcmb] {m['decisionDate']} kararı henüz yok/ayıklanamadı")
            break
        m["result"] = res
        prev_rate = res["rate"]
        last_no = int(res["no"].split("-")[1])
        changed = True
        print(f"[tcmb] GÜNCELLENDİ {m['decisionDate']}: {res['decision']} {res['bp']} bp → %{res['rate']}")

    if changed:
        for path, obj in ((FOMC, fomc), (TCMB, tcmb)):
            with open(path, "w", encoding="utf-8") as f:
                json.dump(obj, f, ensure_ascii=False, indent=2)
                f.write("\n")
    else:
        print("[policy] bekleyen karar yok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
