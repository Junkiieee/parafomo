#!/usr/bin/env python3
"""Asgari ücret açıklama bekçisi — Aralık'ta yeni asgari ücret açıklanınca /asgari-ucret-hesaplama'yı dakikalar içinde günceller.

Neden: yeni asgari ücret her yıl ~22-27 Aralık akşamı Çalışma Bakanı'nın basın toplantısıyla açıklanıyor; o gece
"asgari ücret <yıl>" Türkiye'nin en çok aranan finans sorgusu. Resmî veri akışı yok, ajan ertesi sabah 03:00'te
koşuyor → zirve saatler kaçıyordu. Bu bekçi Google News RSS'ini 10 dakikada bir tarar.

Karar kuralı (yanlış rakam yayınlamamak için tutucu):
  - Yalnız son 3 günün, "belirlendi/açıklandı/oldu/duyurdu" içeren ve tahmin/senaryo/soru OLMAYAN başlıklar.
  - Aynı net tutarı (TL) veren kaynaklar sayılır: ÇSGB'nin kendi duyurusu TEK BAŞINA yeter; yoksa Anadolu Ajansı
    + en az 2 farklı kaynak daha; ya da en az 4 farklı kaynak.
  - Kuruş başlıkta yoksa: o net'i veren brütlerden en yuvarlağı (tam TL > ,50) seçilir (bordro yuvarlamasıyla;
    2024-2026 resmî rakamlarıyla doğrulandı).
Onaylanırsa: data/asgari-ucret.json → yeni = {yil, brut, net, aciklanma, kaynak, otomatik: true} → commit →
build kapılı deploy → IndexNow + GSC sitemap → Kaan'a e-posta (doğrulasın; yanlışsa `yeni` = null).
1 Ocak'tan sonra: yeni → guncel, eski guncel → gecmis (yıl devri).

Cron: */10 * * 12,1 *  (pencere dışında ağa çıkmadan biter: 10 Aralık – 10 Ocak)
Kullanım: python3 scripts/asgari-ucret-watch.py [--dry] [--today YYYY-MM-DD] [--feed dosya.xml] [--data test.json]
"""
import datetime as dt
import email.utils
import html
import json
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data", "asgari-ucret.json")
AYLAR = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]

NEG = ("ne kadar olacak", "olacak mı", "kaç tl olacak", "kaç lira olacak", "olabilir",
       # sendika/işveren talepleri, açlık sınırı, emekli/memur haberleri (Türkçe ses değişimi: talep→talebi)
       "talebi", "talebini", "teklifi", "türk-iş", "hak-iş", "disk", "sendika", "işçi tarafı", "işveren tarafı", "tisk",
       "açlık", "yoksulluk", "emekli", "memur", "masaya", "toplantı", "öngörü", "sızdı", "gündemde", "konuşuluyor", "olur mu", "olsun", "tahmin", "senaryo", "beklenti", "beklenen", "uzman", "kulis",
       "iddia", "masada", "teklif", "talep", "hesapla", "anket", "?", "ne kadar olmalı", "öneri", "istedi", "rakam verdi")
POS = ("belirlendi", "açıklandı", "belli oldu", "oldu", "duyurdu", "yürürlüğe")


def tr_lower(s):
    return s.replace("I", "ı").replace("İ", "i").lower()


def kurus(tl):
    return round(tl * 100)


def oranla(tl, bp):
    k = kurus(tl) * bp / 10000
    return (int(k) + (1 if k - int(k) >= 0.5 else 0)) / 100  # yarım yukarı (JS Math.round ile aynı, pozitif sayılar)


def net_of(brut, o):
    sgk, iss = round(o["sgkIsci"] * 100), round(o["issizlikIsci"] * 100)
    return (kurus(brut) - kurus(oranla(brut, sgk)) - kurus(oranla(brut, iss))) / 100


def brut_of(net, o):
    kes = round(o["sgkIsci"] * 100) + round(o["issizlikIsci"] * 100)
    c0 = round(kurus(net) * 10000 / (10000 - kes))
    aday = [k for k in range(c0 - 10, c0 + 11) if abs(net_of(k / 100, o) - net) < 0.001]
    aday.sort(key=lambda k: (0 if k % 100 == 0 else 1 if k % 50 == 0 else 2, abs(k - c0)))
    return (aday[0] if aday else c0) / 100


def tl_from_title(t, lo, hi):
    """Başlıktan net tutar adayları: (lira, kuruş|None). 28.075,50 TL · 28 bin 75 lira · 28075 TL.
    "net" geçiyorsa yalnız ondan SONRAKİ tutar; "net" yok ama "brüt" varsa başlık atlanır (brüt net sanılmasın)."""
    if "net" in t.split():
        t = t[t.index("net"):]
    elif re.search(r"\bnet\b", t):
        t = t[re.search(r"\bnet\b", t).start():]
    elif "brüt" in t:
        return []
    out = []
    for m in re.finditer(r"(\d{1,3}(?:\.\d{3})+|\d{4,6})(?:,(\d{1,2}))?\s*(?:tl|lira|₺)", t):
        lira = int(m.group(1).replace(".", ""))
        kr = int(m.group(2).ljust(2, "0")) if m.group(2) else None
        out.append((lira, kr))
    for m in re.finditer(r"(\d{1,3})\s*bin\s*(\d{1,3})\s*(?:tl|lira|₺)", t):
        out.append((int(m.group(1)) * 1000 + int(m.group(2)), None))
    return [(l, k) for l, k in out if lo <= l <= hi]


def fetch_feed(query):
    url = "https://news.google.com/rss/search?" + urllib.parse.urlencode(
        {"q": query, "hl": "tr", "gl": "TR", "ceid": "TR:tr"})
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (parafomo-asgari-watch/1.0)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def parse_items(xml):
    items = []
    for it in re.findall(r"<item>(.*?)</item>", xml, re.S):
        t = re.search(r"<title>(.*?)</title>", it, re.S)
        d = re.search(r"<pubDate>(.*?)</pubDate>", it)
        src = re.search(r'<source url="([^"]+)">(.*?)</source>', it)
        link = re.search(r"<link>(.*?)</link>", it, re.S)
        if not (t and d):
            continue
        try:
            when = email.utils.parsedate_to_datetime(d.group(1))
        except Exception:
            continue
        host = urllib.parse.urlparse(src.group(1)).netloc.replace("www.", "") if src else "?"
        items.append({"title": html.unescape(t.group(1)), "when": when, "host": host,
                      "src": html.unescape(src.group(2)) if src else "?", "link": link.group(1).strip() if link else ""})
    return items


def save(d):
    with open(DATA, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
        f.write("\n")


def sh(cmd):
    return subprocess.call(cmd, shell=True, cwd=REPO)


def deploy(msg, subject, body, dry):
    if dry:
        print(f"[asgari] (dry) commit+deploy: {msg}")
        return
    subprocess.call(["python3", "scripts/og-images.py", "--only", "asgari-ucret-hesaplama"], cwd=REPO)
    subprocess.call(["bash", "-c", '. scripts/lib/gitsync.sh && git_sync >/dev/null 2>&1; git_add_commit "$1" data/asgari-ucret.json public/og/asgari-ucret-hesaplama.png',
                     "_", msg], cwd=REPO)
    if sh("bash scripts/deploy-push.sh") == 0:
        sh('python3 scripts/wait-live.py "https://parafomo.com/asgari-ucret-hesaplama/" --timeout 600 && '
           'python3 scripts/indexnow.py https://parafomo.com/asgari-ucret-hesaplama/; '
           '/root/.venvs/parafomo/bin/python scripts/gsc-sitemap.py --force')
    subprocess.call(["python3", os.path.join(REPO, "agent", "notify.py"), "alert", "--key", "asgari-ucret",
                     "--subject", subject, "--body", body, "--force"], cwd=REPO)


def main(argv):
    dry = "--dry" in argv
    now = dt.datetime.now(dt.timezone.utc)
    today = (now + dt.timedelta(hours=3)).date()
    if "--today" in argv:
        today = dt.date.fromisoformat(argv[argv.index("--today") + 1])
        now = dt.datetime.combine(today, dt.time(21, 0), dt.timezone.utc)
    global DATA
    if "--data" in argv:  # test
        DATA = argv[argv.index("--data") + 1]
    d = json.load(open(DATA, encoding="utf-8"))
    g, yeni, o = d["guncel"], d.get("yeni"), d["oranlar"]

    # Yıl devri: 1 Ocak'tan itibaren açıklanmış yeni yıl yürürlükte
    if yeni and today >= dt.date(yeni["yil"], 1, 1):
        artis = round((yeni["net"] / g["net"] - 1) * 100, 2)
        acik = dt.date.fromisoformat(yeni["aciklanma"])
        d["gecmis"] = [{"yil": yeni["yil"], "tarih": f"{acik.day} {AYLAR[acik.month - 1]} {acik.year}",
                        "net": yeni["net"], "artis": artis}] + [x for x in d["gecmis"] if x["yil"] != yeni["yil"]]
        d["guncel"] = {k: yeni[k] for k in ("yil", "brut", "net", "aciklanma")}
        d["yeni"] = None
        d["updated"] = today.isoformat()
        print(f"[asgari] yıl devri: {yeni['yil']} yürürlükte (net {yeni['net']})")
        if not dry:
            save(d)
        deploy(f"veri: asgari ücret {yeni['yil']} yürürlüğe girdi (yıl devri, otomatik)",
               f"Asgari ücret {yeni['yil']} yıl devri yapıldı", "guncel ← yeni; sayfa yeni yılı gösteriyor.", dry)
        return 0

    in_window = (today.month == 12 and today.day >= 10) or (today.month == 1 and today.day <= 10)
    hedef = today.year + 1 if today.month == 12 else today.year
    if not in_window or yeni or g["yil"] >= hedef:
        if dry:
            print(f"[asgari] pencere dışı ya da {hedef} zaten var — çıkış")
        return 0

    items = []
    if "--feed" in argv:
        items = parse_items(open(argv[argv.index("--feed") + 1], encoding="utf-8").read())
    else:
        for q in (f"asgari ücret {hedef} net", f"yeni asgari ücret {hedef} belirlendi", "asgari ücret açıklandı net"):
            try:
                items += parse_items(fetch_feed(q))
            except Exception as e:
                print(f"[asgari] UYARI: RSS çekilemedi ({q}): {e}")
    lo, hi = int(g["net"] * 1.03), int(g["net"] * 2.0)
    adaylar = {}  # lira → {hosts, kurus set, titles}
    seen = set()
    for it in items:
        if (now - it["when"]).total_seconds() > 3 * 86400 or it["when"] > now + dt.timedelta(hours=1):
            continue
        t = tr_lower(it["title"])
        if it["link"] in seen:
            continue
        seen.add(it["link"])
        if "asgari ücret" not in t or any(n in t for n in NEG) or not any(p in t for p in POS):
            continue
        if str(hedef) not in t and "yeni asgari ücret" not in t:
            continue
        for lira, kr in tl_from_title(t, lo, hi)[:1]:
            a = adaylar.setdefault(lira, {"hosts": set(), "kurus": set(), "titles": []})
            a["hosts"].add(it["host"])
            if kr is not None:
                a["kurus"].add(kr)
            a["titles"].append(f"{it['src']}: {it['title']} <{it['link']}>")
    if not adaylar:
        print(f"[{now:%Y-%m-%d %H:%M} UTC] [asgari] {hedef} için açıklama başlığı yok")
        return 0
    lira, a = max(adaylar.items(), key=lambda kv: len(kv[1]["hosts"]))
    hosts = a["hosts"]
    resmi = any(h.endswith("csgb.gov.tr") for h in hosts)
    aa = any(h.endswith("aa.com.tr") for h in hosts)
    guclu = resmi or (aa and len(hosts) >= 3) or len(hosts) >= 4
    ozet = f"{lira} TL · {len(hosts)} kaynak ({', '.join(sorted(hosts))})"
    if not guclu:
        print(f"[{now:%Y-%m-%d %H:%M} UTC] [asgari] aday var ama yetersiz: {ozet}")
        return 0
    if len(a["kurus"]) == 1:
        net = lira + next(iter(a["kurus"])) / 100
        brut = brut_of(net, o)
    else:  # kuruş yok/çelişkili → net'in kuruşunu, brütü en yuvarlak yapan değerden bul
        best = None
        for kr in range(0, 100):
            n = lira + kr / 100
            b = brut_of(n, o)
            if abs(net_of(b, o) - n) > 0.001:
                continue
            score = 0 if kurus(b) % 100 == 0 else 1 if kurus(b) % 50 == 0 else 2
            if best is None or score < best[0]:
                best = (score, n, b)
        _, net, brut = best if best else (9, float(lira), brut_of(float(lira), o))
    d["yeni"] = {"yil": hedef, "brut": brut, "net": net, "aciklanma": today.isoformat(),
                 "kaynak": a["titles"][:6], "otomatik": True}
    d["updated"] = today.isoformat()
    print(f"[{now:%Y-%m-%d %H:%M} UTC] [asgari] ONAYLANDI: {hedef} net {net} / brüt {brut} — {ozet}")
    if not dry:
        save(d)
    body = (f"{hedef} asgari ücret haberlerden otomatik algılandı ve sitede yayınlandı:\n"
            f"net {net:,.2f} TL · brüt {brut:,.2f} TL\nKaynaklar:\n- " + "\n- ".join(a["titles"][:6]) +
            "\n\nLütfen resmî açıklamayla doğrula. Yanlışsa data/asgari-ucret.json içinde yeni=null yap ve deploy et "
            "(ya da doğru net/brütü yaz).")
    deploy(f"veri: {hedef} asgari ücret açıklandı — net {net} TL (otomatik, {len(hosts)} kaynak)",
           f"Asgari ücret {hedef}: net {net:,.2f} TL yayınlandı (doğrula)", body, dry)
    if not dry:  # resmî rakamla "asgari ücret belli oldu" Short'u (arka planda; kendi kilidi var)
        subprocess.Popen(["python3", os.path.join(REPO, "scripts", "event-short.py")],
                         stdout=open(os.path.join(REPO, "logs", "event-short.log"), "a"),
                         stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
