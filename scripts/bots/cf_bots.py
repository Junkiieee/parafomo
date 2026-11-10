#!/usr/bin/env python3
"""ParaFOMO — Cloudflare bot arşivi + rapor (2026-11-09, Kaan: "botlarla ne yapabiliriz").

Cloudflare her isteği görür ve bot IP'lerini doğrular (verifiedBotCategory: sahte "GPTBot" yazan biri buraya düşmez).
Ama veriyi yalnız 30 gün tutar → bu betik her gün son 24 saati kopyalar, repo DIŞINA arşivler, haftalık rapor çıkarır.
Yöntem DuvInc/cloudflare-ai-crawl-history (MIT) ile aynı sorgu (httpRequestsAdaptiveGroups + verifiedBotCategory_neq "");
onların Worker+R2 kurulumu yerine sunucuda Python + yerel dosya.

Token: ~/.config/parafomo/cloudflare.env (CLOUDFLARE_API_TOKEN, CLOUDFLARE_ZONE_ID). Gereken izin: Zone·Analytics·Read.

  pull [--days N]   son N günü (varsayılan 1) 6 saatlik pencerelerle çek → /root/parafomo-data/bots/<gün>.jsonl
  report [--days 7] bot bazında istek, en çok okunan sayfalar, kullanıcı-tetikli (ChatGPT-User vb.) sayfalar
"""
import argparse, collections, datetime as dt, json, os, sys, urllib.request, urllib.error

ENV = os.path.expanduser("~/.config/parafomo/cloudflare.env")
OUT = "/root/parafomo-data/bots"
GQL = "https://api.cloudflare.com/client/v4/graphql"
LIMIT = 10000

# UA parçası → (bot adı, sağlayıcı, amaç). Amaç: egitim | arama | kullanici (bir kişi o an soruyor) | klasik
BOTS = [
    ("ChatGPT-User", "OpenAI", "kullanici"), ("OAI-SearchBot", "OpenAI", "arama"), ("GPTBot", "OpenAI", "egitim"),
    ("Claude-User", "Anthropic", "kullanici"), ("Claude-SearchBot", "Anthropic", "arama"), ("ClaudeBot", "Anthropic", "egitim"),
    ("Perplexity-User", "Perplexity", "kullanici"), ("PerplexityBot", "Perplexity", "arama"),
    ("MistralAI-User", "Mistral", "kullanici"), ("DuckAssistBot", "DuckDuckGo", "arama"),
    ("meta-externalagent", "Meta", "egitim"), ("meta-externalfetcher", "Meta", "kullanici"),
    ("Amazonbot", "Amazon", "egitim"), ("Applebot", "Apple", "klasik"), ("Bytespider", "ByteDance", "egitim"),
    ("CCBot", "Common Crawl", "egitim"), ("Google-CloudVertexBot", "Google", "egitim"),
    ("Googlebot", "Google", "klasik"), ("Google-InspectionTool", "Google", "klasik"), ("GoogleOther", "Google", "klasik"),
    ("bingbot", "Microsoft", "klasik"), ("YandexBot", "Yandex", "klasik"), ("DuckDuckBot", "DuckDuckGo", "klasik"),
    ("facebookexternalhit", "Meta", "onizleme"), ("Twitterbot", "X", "onizleme"), ("TelegramBot", "Telegram", "onizleme"),
    ("WhatsApp", "Meta", "onizleme"), ("Slackbot", "Slack", "onizleme"),
    # 2026-11-10 ilk 30 günlük arşivde tanınmayanlar
    ("PetalBot", "Huawei", "arama"), ("ShapBot", "Shap", "arama"), ("KeenableBot", "Keenable", "arama"),
    ("Reflectionbot", "Reflection AI", "egitim"),
    ("AhrefsBot", "Ahrefs", "seo"), ("SemrushBot", "Semrush", "seo"), ("MJ12bot", "Majestic", "seo"), ("DotBot", "Moz", "seo"),
    ("trendictionbot", "Talkwalker", "izleme"),
]
AI_SAGLAYICI = {"OpenAI", "Anthropic", "Perplexity", "Mistral", "Meta", "Amazon", "ByteDance", "Common Crawl", "Reflection AI", "Shap"}


def env():
    e = dict(l.strip().split("=", 1) for l in open(ENV) if "=" in l and not l.startswith("#"))
    return e["CLOUDFLARE_API_TOKEN"], e["CLOUDFLARE_ZONE_ID"]


def classify(ua, category):
    u = (ua or "").lower()
    for tok, prov, amac in BOTS:
        if tok.lower() in u:
            return tok, prov, amac
    return (category or "diğer"), "?", "diğer"


def gql(token, query, variables):
    req = urllib.request.Request(GQL, data=json.dumps({"query": query, "variables": variables}).encode(),
                                 headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        d = json.load(r)
    if d.get("errors"):
        msg = d["errors"][0].get("message", "")
        if "permission" in msg or "authz" in json.dumps(d["errors"]):
            sys.exit("HATA: Cloudflare token'ında Zone·Analytics·Read izni yok (agent/plan/user-tasks.md 5. madde). Çıkılıyor.")
        sys.exit(f"HATA: GraphQL: {msg[:300]}")
    return d["data"]


Q = """query($z:String!,$s:Time!,$e:Time!,$l:Int!){viewer{zones(filter:{zoneTag:$z}){
  httpRequestsAdaptiveGroups(limit:$l,filter:{datetime_geq:$s,datetime_lt:$e,verifiedBotCategory_neq:""},orderBy:[count_DESC]){
    count dimensions{clientRequestPath userAgent verifiedBotCategory edgeResponseStatus}}}}}"""


def pull(days):
    token, zone = env()
    os.makedirs(OUT, exist_ok=True)
    now = dt.datetime.now(dt.timezone.utc).replace(minute=0, second=0, microsecond=0)
    for d in range(days, 0, -1):
        day_end = now - dt.timedelta(days=d - 1)
        rows = []
        for h in range(4):   # 6 saatlik pencereler: grup sınırı (10k) güvenli kalsın
            s = day_end - dt.timedelta(hours=24 - 6 * h)
            e = s + dt.timedelta(hours=6)
            data = gql(token, Q, {"z": zone, "s": s.isoformat().replace("+00:00", "Z"),
                                  "e": e.isoformat().replace("+00:00", "Z"), "l": LIMIT})
            grp = data["viewer"]["zones"][0]["httpRequestsAdaptiveGroups"]
            if len(grp) >= LIMIT:
                print(f"UYARI: {s:%m-%d %H}h penceresi sınırda ({LIMIT}) — eksik olabilir")
            for g in grp:
                dm = g["dimensions"]
                bot, prov, amac = classify(dm["userAgent"], dm["verifiedBotCategory"])
                rows.append({"ts": s.isoformat(), "path": dm["clientRequestPath"], "bot": bot, "saglayici": prov,
                             "amac": amac, "cf_kategori": dm["verifiedBotCategory"], "status": dm["edgeResponseStatus"],
                             "n": g["count"], **({"ua": (dm["userAgent"] or "")[:160]} if prov == "?" else {})})
        fn = os.path.join(OUT, f"{(day_end - dt.timedelta(hours=1)):%Y-%m-%d}.jsonl")
        with open(fn, "w") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"[bots] {fn}: {len(rows)} grup, {sum(r['n'] for r in rows)} istek")


def report(days):
    files = sorted(f for f in os.listdir(OUT) if f.endswith(".jsonl"))[-days:] if os.path.isdir(OUT) else []
    if not files:
        sys.exit("Arşiv boş — önce `pull`.")
    rows = [json.loads(l) for f in files for l in open(os.path.join(OUT, f))]
    print(f"BOT RAPORU {files[0][:10]} → {files[-1][:10]} ({len(files)} gün, Cloudflare doğrulamalı)")
    by = collections.Counter(); prov = {}
    for r in rows:
        by[r["bot"]] += r["n"]; prov[r["bot"]] = (r["saglayici"], r["amac"])
    print("\nBOT BAZINDA (istek · sağlayıcı · amaç)")
    for b, n in by.most_common(20):
        print(f"  {n:6d}  {b:<22} {prov[b][0]:<12} {prov[b][1]}")
    ai = sum(n for b, n in by.items() if prov[b][0] in AI_SAGLAYICI)
    print(f"\nYapay zekâ botları toplam: {ai} / {sum(by.values())} bot isteği")
    for baslik, filt in (("YAPAY ZEKÂNIN EN ÇOK OKUDUĞU SAYFALAR", lambda r: r["saglayici"] in AI_SAGLAYICI),
                         ("KULLANICI SORUSUYLA AÇILAN SAYFALAR (ChatGPT-User, Perplexity-User, Claude-User…) = insanlar AI'a şu an bunu soruyor",
                          lambda r: r["amac"] == "kullanici"),
                         ("GOOGLEBOT'UN EN ÇOK TARADIĞI SAYFALAR", lambda r: r["bot"] == "Googlebot")):
        c = collections.Counter()
        for r in rows:
            if filt(r):
                c[r["path"]] += r["n"]
        print(f"\n{baslik}")
        for p, n in c.most_common(15):
            print(f"  {n:5d}  {p}")
    unk = collections.Counter()
    for r in rows:
        if r["saglayici"] == "?" and r.get("ua"):
            unk[(r["bot"], r["ua"][:110])] += r["n"]
    if unk:
        print("\nTANINMAYAN BOTLAR (Cloudflare kategorisi · user-agent) → BOTS listesine eklenecek adaylar")
        for (cat, ua), n in unk.most_common(12):
            print(f"  {n:5d}  {cat:<24} {ua}")
    err = collections.Counter((r["bot"], r["status"]) for r in rows if r["status"] >= 400 and r["saglayici"] in AI_SAGLAYICI | {"Google"})
    if err:
        print("\nHATA ALAN BOT İSTEKLERİ (bot, durum)")
        for (b, st), n in err.most_common(10):
            print(f"  {n:5d}  {b} {st}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["pull", "report"])
    ap.add_argument("--days", type=int, default=None)
    a = ap.parse_args()
    pull(a.days or 1) if a.cmd == "pull" else report(a.days or 7)
