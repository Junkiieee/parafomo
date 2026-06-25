#!/usr/bin/env python3
"""
ParaFOMO — BIST açılış/kapanış yorumu (Instagram caption ilk cümlesi).

Google News'ten güncel BIST açılış/kapanış başlıkları + Truncgil canlı BIST 100
verisi → Claude tek doğal Türkçe cümle. Yön CANLI VERİDEN (başlıklar bağlam için).
Claude/haber patlarsa veriden türetilmiş yedek.

Kullanım: python3 scripts/bist-yorum.py --type acilis|kapanis
"""
import re
import html
import sys
import subprocess
import urllib.parse
import urllib.request

TG = "https://finans.truncgil.com/v4/today.json"
MODEL = "claude-sonnet-4-6"
QUERY = {
    "acilis": "borsa istanbul açılış bist 100",
    "kapanis": "borsa istanbul kapanış bist 100",
}


def bist():
    t = urllib.request.urlopen(urllib.request.Request(TG, headers={"User-Agent": "Mozilla/5.0"}), timeout=20).read().decode("utf-8", "ignore")
    m = re.search(r'"XU100"\s*:\s*\{[^}]*?"Selling"\s*:\s*(-?[0-9.]+)[^}]*?"Change"\s*:\s*(-?[0-9.]+)', t)
    if not m:
        m2 = re.search(r'"XU100"\s*:\s*\{[^}]*?"Change"\s*:\s*(-?[0-9.]+)[^}]*?"Selling"\s*:\s*(-?[0-9.]+)', t)
        return (float(m2.group(2)), float(m2.group(1))) if m2 else (None, None)
    return float(m.group(1)), float(m.group(2))


def headlines(ptype, n=5):
    q = QUERY.get(ptype, QUERY["acilis"])
    url = "https://news.google.com/rss/search?q=%s&hl=tr&gl=TR&ceid=TR:tr" % urllib.parse.quote(q)
    try:
        t = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=20).read().decode("utf-8", "ignore")
    except Exception:
        return []
    out = []
    for it in re.findall(r"<item>(.*?)</item>", t, re.S):
        m = re.search(r"<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>", it, re.S)
        if m:
            ttl = re.sub(r"\s*-\s*[^-]{2,30}$", "", html.unescape(m.group(1)).strip())
            if ttl and ttl not in out:
                out.append(ttl)
    return out[:n]


def dirword(c):
    if c is None:
        return "yatay"
    return "yükseliş" if c >= 0.05 else ("düşüş" if c <= -0.05 else "yatay")


def fallback(ptype, val, chg):
    dw = dirword(chg)
    ac = ptype == "acilis"
    if dw == "yükseliş":
        return ("Borsa İstanbul güne alıcılı bir başlangıçla, BIST 100 yükselişle açıldı."
                if ac else "Borsa İstanbul günü yükselişle tamamladı; BIST 100 alıcılı kapandı.")
    if dw == "düşüş":
        return ("Borsa İstanbul güne satıcılı başladı; BIST 100 açılışta geriledi."
                if ac else "Borsa İstanbul günü ekside kapattı; BIST 100 satış baskısıyla geriledi.")
    return ("Borsa İstanbul güne yatay bir görünümle başladı."
            if ac else "Borsa İstanbul günü yatay bir seyirle tamamladı.")


def build(ptype, val, chg, hl):
    if not hl:
        return fallback(ptype, val, chg)
    vtxt = f"BIST 100: {val:,.0f}".replace(",", ".") if val else "BIST 100: veri yok"
    vtxt += f" ({dirword(chg)}, %{abs(chg):.2f})" if chg is not None else ""
    when = "açılışı" if ptype == "acilis" else "kapanışı"
    prompt = (
        f"Sen bir Türk finans editörüsün. Aşağıda bugünkü Borsa İstanbul {when} ile ilgili "
        "haber başlıkları ve CANLI BIST 100 verisi var. Tek bir doğal Türkçe cümle yaz: "
        f"günün borsa {when} havasını özetleyen, akıcı, Instagram caption'ının İLK cümlesi "
        "olacak bir yorum.\nKURALLAR: Yön/eğilimi CANLI VERİDEN al (başlıklar eski olabilir). "
        "İsimli uzman/tahmin alıntılama. Rakam uydurma. Abartı/clickbait yapma. Sadece TEK "
        "cümleyi yaz; tırnak, önek, emoji koyma.\n\n"
        f"CANLI VERİ: {vtxt}\n\nBAŞLIKLAR:\n" + "\n".join("- " + h for h in hl)
    )
    try:
        r = subprocess.run(["claude", "-p", prompt, "--model", MODEL],
                           capture_output=True, text=True, timeout=120)
        out = r.stdout.strip().strip('"').split("\n")[0].strip()
        if 15 < len(out) < 240:
            return out
    except Exception:
        pass
    return fallback(ptype, val, chg)


def main():
    args = sys.argv[1:]
    ptype = args[args.index("--type") + 1] if "--type" in args else "acilis"
    try:
        val, chg = bist()
    except Exception:
        val, chg = None, None
    print(build(ptype, val, chg, headlines(ptype)))


if __name__ == "__main__":
    main()
