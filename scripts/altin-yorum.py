#!/usr/bin/env python3
"""
ParaFOMO — Günlük altın yorumu (Instagram caption ilk cümlesi).

Google News'ten güncel altın başlıklarını (birkaç kaynak) + Truncgil canlı
fiyatlarını alır, Claude'a verip TEK doğal Türkçe cümle yazdırır.
Yön/eğilim CANLI VERİDEN gelir (başlıklar bağlam/tema için). İsimli uzman
tahmini alıntılanmaz, rakam uydurulmaz.

Claude veya haber çekimi başarısız olursa: veriden türetilmiş yedek cümle.

Çıktı: stdout'a TEK cümle (caption'ın ilk satırı). Sadece bu betik
`claude -p` çağırır (küçük, ~1 cümle). Diğer her şey ücretsiz.
"""
import re
import html
import sys
import json
import subprocess
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))
from llm import call as llm_call  # tek LLM kapısı (hata metni asla caption olmaz)
import urllib.parse
import urllib.request

API = "https://finans.truncgil.com/v4/today.json"
MODEL = "haiku"  # tek cümle: en ucuz model yeter


def fetch_prices():
    req = urllib.request.Request(API, headers={"User-Agent": "Mozilla/5.0 (ParaFOMO)"})
    t = urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "ignore")

    def pick(k, p):
        m = re.search(r'"' + re.escape(k) + r'"\s*:\s*\{[^}]*?"' + p + r'"\s*:\s*(-?[0-9.]+)', t)
        return float(m.group(1)) if m else None

    gra, has, usd = pick("GRA", "Selling"), pick("HAS", "Selling"), pick("USD", "Selling")
    ons = (has * 31.1035 / usd) if (has and usd) else None
    return {
        "gram": (gra, pick("GRA", "Change")),
        "ons": (ons, pick("HAS", "Change")),
        "ceyrek": (pick("CEYREKALTIN", "Selling"), pick("CEYREKALTIN", "Change")),
        "cumhuriyet": (pick("CUMHURIYETALTINI", "Selling"), pick("CUMHURIYETALTINI", "Change")),
    }


def fetch_headlines(n=5):
    titles = []
    for q in ("gram altın", "altın fiyatları yorum"):
        url = "https://news.google.com/rss/search?q=%s&hl=tr&gl=TR&ceid=TR:tr" % urllib.parse.quote(q)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            t = urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "ignore")
        except Exception:
            continue
        for it in re.findall(r"<item>(.*?)</item>", t, re.S):
            m = re.search(r"<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>", it, re.S)
            if m:
                ttl = html.unescape(m.group(1)).strip()
                # kaynak adını başlık sonundan ayıkla ("... - Kaynak")
                ttl = re.sub(r"\s*-\s*[^-]{2,30}$", "", ttl).strip()
                if ttl and ttl not in titles:
                    titles.append(ttl)
    return titles[:n]


def dirword(chg):
    if chg is None:
        return "yatay"
    if chg >= 0.05:
        return "yükseliş"
    if chg <= -0.05:
        return "düşüş"
    return "yatay"


def fallback(prices):
    g = dirword(prices["gram"][1])
    c = dirword(prices["ceyrek"][1])
    if g == c == "yükseliş":
        return "Altın cephesinde alıcılar güne hâkim; gram ve ziynet altınlarında yukarı yönlü seyir öne çıkıyor."
    if g == c == "düşüş":
        return "Altında satıcılı bir açılış var; gram ve ziynet altınları güne geri çekilerek başladı."
    if g == "yükseliş":
        return "Gram altın güne yükselişle başlarken ziynet altınlarında ayrışma dikkat çekiyor."
    if g == "düşüş":
        return "Gram altın güne geri çekilerek başlarken piyasa karışık sinyaller veriyor."
    return "Altın piyasası güne nispeten yatay bir görünümle başlıyor."


def fmt(v):
    if v is None:
        return "veri yok"
    return f"{v:,.0f}".replace(",", ".")


def build_comment(prices, headlines):
    if not headlines:
        return fallback(prices)
    pv = (f"Gram altın {fmt(prices['gram'][0])} TL ({dirword(prices['gram'][1])}), "
          f"Ons {fmt(prices['ons'][0])} USD ({dirword(prices['ons'][1])}), "
          f"Çeyrek {fmt(prices['ceyrek'][0])} TL ({dirword(prices['ceyrek'][1])}), "
          f"Cumhuriyet {fmt(prices['cumhuriyet'][0])} TL ({dirword(prices['cumhuriyet'][1])}).")
    hl = "\n".join("- " + h for h in headlines)
    prompt = (
        "Sen bir Türk finans editörüsün. Aşağıda bugünkü altın haber başlıkları ve "
        "CANLI fiyat verisi var. Tek bir doğal Türkçe cümle yaz: günün altın piyasası "
        "havasını özetleyen, akıcı, bir Instagram caption'ının İLK cümlesi olacak bir yorum.\n"
        "KURALLAR: Yön/eğilimi CANLI VERİDEN al (başlıklar eski olabilir). İsimli "
        "uzman/tahmin alıntılama. Rakam uydurma. Abartı/clickbait yapma. Sadece TEK "
        "cümleyi yaz; tırnak, önek, emoji koyma.\n\n"
        f"CANLI VERİ: {pv}\n\nBAŞLIKLAR:\n{hl}"
    )
    try:
        ok, out, _kind = llm_call(prompt, model=MODEL, effort="low", timeout=120, tries=1, tag="altin-yorum",
                                  think=False)
        if ok:
            # tek cümleye indir, tırnak temizle
            out = out.strip().strip('"').strip()
            out = out.split("\n")[0].strip()
            # ikinci emniyet: hata/limit metni yine de sızarsa caption YAPMA
            low = out.lower()
            _bad = ("api error", "authenticate", "oauth", "access token",
                    "invalid api", "usage limit", "rate limit", "credit balance",
                    "please run", "not logged in", "weekly limit", "you've hit",
                    "hit your", "resets", "quota")
            if 15 < len(out) < 240 and not any(b in low for b in _bad):
                return out
    except Exception:
        pass
    return fallback(prices)


def main():
    try:
        prices = fetch_prices()
    except Exception:
        print("Altın piyasası güne hareketli bir görünümle başlıyor.")
        return
    headlines = fetch_headlines()
    print(build_comment(prices, headlines))


if __name__ == "__main__":
    main()
