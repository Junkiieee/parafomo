#!/usr/bin/env python3
"""
ParaFOMO — Karar motoru (öğrenme döngüsünün beyni).

Girdi : content-ledger.jsonl (nitelikler) ⋈ metrics.jsonl (performans) + web-queries.json
Çıktı : data/learning/winners.json  (üreticiler okur)
        docs/learning-report.md      (insan okur)
        Telegram özeti (--telegram)

İLKE — güven yoksa müdahale etme:
Bir boyut (format/ses/motor/slot) için yeterli örnek (min_n) yoksa policy='explore'
ve next_pick=None döner; üreticiler o zaman MEVCUT rotasyonlarını sürdürür (ki bu
zaten keşiftir). Ancak bir seçenek istatistiksel olarak öne çıkınca policy='exploit'
olur ve üretici o seçeneğe geçer. Böylece sistem az veriyle asla gürültüye kilitlenmez.

Kalite sinyali önceliği (YouTube): averageViewPercentage (RETENTION) > views.
Retention abone sayısından bağımsız olduğu için "içerik iyi mi" sorusunun en dürüst
yanıtıdır.
"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib  # noqa: E402

WINDOW_DAYS = 45
MIN_N = 4          # bir kolun "karara hazır" sayılması için asgari örnek
EPSILON = 0.2
Z_SEP = 1.0        # kazanan kolun ikinciyi geçmesi gereken asgari birleşik std hata
                   # (etki-büyüklüğü kapısı: yeterli örnek olsa bile BERABERE kollara
                   #  kilitlenme — MIN_N örnek sayısını, Z_SEP fark anlamlılığını korur)


# --------------------------- skor fonksiyonları ---------------------------

def yt_score(m):
    """RETENTION öncelikli. Yoksa views. İkisi de yoksa None."""
    if m.get("avg_view_pct") is not None:
        return float(m["avg_view_pct"])
    if m.get("views") is not None:
        return float(m["views"])
    return None


def yt_reach(m):
    return float(m["views"]) if m.get("views") is not None else None


def web_score(m):
    # tıklama en değerli sinyal; görüntüleme + etkileşim süresi ikincil
    return (m.get("clicks", 0) * 5) + m.get("pageviews", 0) + (m.get("eng_sec", 0) / 60.0)


def ig_score(m):
    s = m.get("likes", 0) + 2 * m.get("comments", 0)
    s += 3 * m.get("saved", 0) + 5 * m.get("shares", 0)  # insights varsa
    return s


# --------------------------- veri birleştirme ---------------------------

def latest_metrics():
    """id -> en güncel metrik sözlüğü."""
    out = {}
    for r in lib.read_jsonl(lib.METRICS):
        cur = out.get(r["id"])
        if cur is None or r["fetched_utc"] >= cur["fetched_utc"]:
            out[r["id"]] = r
    return {k: v["metrics"] for k, v in out.items()}


def join():
    """ledger + metrik + skor → zenginleştirilmiş öğe listesi."""
    metrics = latest_metrics()
    cutoff = lib.now_utc().timestamp() - WINDOW_DAYS * 86400
    items = []
    for r in lib.read_jsonl(lib.LEDGER):
        pub = lib.parse_dt(r.get("published_utc"))
        if pub and pub.timestamp() < cutoff:
            continue
        m = metrics.get(r["id"], {})
        it = dict(r)
        it["metrics"] = m
        if r["channel"] == "youtube":
            it["score"] = yt_score(m)
        elif r["channel"] == "web":
            it["score"] = web_score(m) if m else None
        elif r["channel"] == "instagram":
            it["score"] = ig_score(m) if m else None
        else:
            it["score"] = None
        items.append(it)
    return items


# --------------------------- boyut kararı ---------------------------

def decide_dim(items, key_fn, seed):
    """Bir boyut için bandit kararı. Dönüş: dict(policy,next_pick,ranking,eligible)."""
    scored = [it for it in items if it.get("score") is not None]
    agg = lib.aggregate(scored, key_fn, lambda it: it["score"])
    rank = lib.ranking(agg)
    eligible = {k: v for k, v in agg.items() if v["n"] >= MIN_N}
    if len(eligible) >= 2:
        pick, policy = lib.pick_bandit(eligible, EPSILON, MIN_N, seed)
        if policy == "exploit":
            # Etki-büyüklüğü kapısı: kazanan, ikinciyi Z_SEP birleşik std hata kadar
            # geçmiyorsa kollar fiilen BERABERE → kilitleme, keşfe devam et.
            ordered = sorted(eligible.values(), key=lambda v: -v["score"])
            if not lib.separated(ordered[0], ordered[1], Z_SEP):
                return {"policy": "explore", "next_pick": None, "ranking": rank,
                        "decided": False, "tied": True}
        return {"policy": policy if policy != "explore-cold" else "explore",
                "next_pick": pick if policy == "exploit" else None,
                "ranking": rank, "decided": policy == "exploit"}
    return {"policy": "explore", "next_pick": None, "ranking": rank, "decided": False}


def top_slugs(items, channel, n=8):
    scored = [it for it in items if it["channel"] == channel and it.get("score")]
    scored.sort(key=lambda it: -it["score"])
    return [{"slug": it.get("slug") or it["id"], "score": round(it["score"], 2)} for it in scored[:n]]


# --------------------------- ana ---------------------------

def main():
    items = join()
    yt = [it for it in items if it["channel"] == "youtube"]
    viral = [it for it in yt if it["subtype"] == "viral"]
    day = lib.now_utc().date().isoformat()

    metrics_all = latest_metrics()
    sig_ret = any("avg_view_pct" in m and m["avg_view_pct"] is not None for m in metrics_all.values())
    sig_views = any("views" in m for m in metrics_all.values())
    sig_ig_ins = any("reach" in m for m in metrics_all.values())
    sig_web = any(it["channel"] == "web" and it.get("score") for it in items)

    fmt = lambda it: it["attrs"].get("format")
    voice = lambda it: it["attrs"].get("voice")
    engine = lambda it: it["attrs"].get("engine")
    slot = lambda it: it["attrs"].get("slot_idx")

    winners = {
        "generated_utc": lib.iso(),
        "window_days": WINDOW_DAYS,
        "min_samples": MIN_N,
        "signals": {"youtube_retention": sig_ret, "youtube_views": sig_views,
                    "instagram_insights": sig_ig_ins, "web": sig_web},
        "shorts": {
            "voice": decide_dim(yt, voice, f"{day}|voice"),
            "engine": decide_dim(yt, engine, f"{day}|engine"),
        },
        "viral": {
            "format": decide_dim(viral, fmt, f"{day}|format"),
            "slot": decide_dim(viral, slot, f"{day}|slot"),
        },
        "topics": {
            "top_blog": top_slugs(items, "web"),
            "top_youtube": top_slugs(items, "youtube"),
        },
        "notes": [],
    }

    # slot: exploit değilse bile bilgilendirici öneri (en iyi 3 slot)
    slot_rank = winners["viral"]["slot"]["ranking"]
    winners["viral"]["slot"]["recommended_slots"] = [r["arm"] for r in slot_rank[:3] if r["arm"]]

    # fırsat sorguları (web-queries.json'dan)
    wq_path = os.path.join(lib.DATA, "web-queries.json")
    if os.path.exists(wq_path):
        wq = json.load(open(wq_path))
        winners["topics"]["opportunity_queries"] = wq.get("opportunity", [])

    # notlar (insan + üretici için)
    if not (sig_ret or sig_views):
        winners["notes"].append(
            "YouTube metriği YOK → shorts/viral kararları keşif modunda. "
            "Re-auth yapılınca (youtube.readonly + yt-analytics.readonly) otomatik devreye girer.")
    if not sig_ig_ins:
        winners["notes"].append(
            "Instagram insights izni yok → sadece beğeni/yorum. reach/kaydetme için "
            "instagram_manage_insights izni gerekli (opsiyonel).")

    json.dump(winners, open(lib.WINNERS, "w"), ensure_ascii=False, indent=2)
    print(f"[+] winners.json yazıldı -> {lib.WINNERS}")

    write_report(winners, items)
    if "--telegram" in sys.argv:
        telegram(winners)
    return 0


def write_report(w, items):
    L = ["# ParaFOMO — Öğrenme Raporu", "",
         f"> {w['generated_utc']} · pencere: son {w['window_days']} gün · "
         f"asgari örnek: {w['min_samples']}", ""]
    s = w["signals"]
    L += ["## Sinyal durumu", "",
          f"- YouTube retention: {'✅' if s['youtube_retention'] else '❌ (re-auth gerekli)'}",
          f"- YouTube izlenme: {'✅' if s['youtube_views'] else '❌ (re-auth gerekli)'}",
          f"- Instagram insights: {'✅' if s['instagram_insights'] else '❌ (izin gerekli)'}",
          f"- Web (GA4+GSC): {'✅' if s['web'] else '❌'}", ""]

    def dim(title, d):
        if d.get("next_pick"):
            tail = f" → seçim: `{d['next_pick']}`"
        elif d.get("tied"):
            tail = " (kollar berabere — fark anlamlı değil, rotasyon sürüyor)"
        else:
            tail = " (yeterli veri yok, rotasyon sürüyor)"
        out = [f"### {title} — **{d['policy']}**" + tail, ""]
        for r in d["ranking"][:8]:
            if r["arm"]:
                out.append(f"- `{r['arm']}` — skor {r['score']}, örnek {r['n']}")
        out.append("")
        return out

    L += ["## Kararlar", ""]
    L += dim("Shorts sesi", w["shorts"]["voice"])
    L += dim("Shorts motoru (google/edge)", w["shorts"]["engine"])
    L += dim("Viral format", w["viral"]["format"])
    L += dim("Viral yayın slotu", w["viral"]["slot"])

    L += ["## Konu sinyalleri", "", "**En iyi blog sayfaları:**"]
    for t in w["topics"]["top_blog"][:6]:
        L.append(f"- {t['slug']} — skor {t['score']}")
    L += ["", "**🎯 Fırsat sorguları** (içerik/başlık iyileştir):"]
    for q in w["topics"].get("opportunity_queries", [])[:8]:
        L.append(f"- `{q['query']}` — gös {q['impressions']}, sıra {q['position']}")
    L += [""]
    if w["notes"]:
        L += ["## Notlar", ""] + [f"- {n}" for n in w["notes"]] + [""]

    out = os.path.join(lib.ROOT, "docs", "learning-report.md")
    open(out, "w", encoding="utf-8").write("\n".join(L))
    print(f"[+] rapor -> {out}")


def telegram(w):
    env = lib.load_env(os.path.join(lib.ROOT, ".env"))
    token, chat = env.get("TELEGRAM_BOT_TOKEN"), env.get("TELEGRAM_CHAT_ID")
    if not (token and chat):
        print("[!] Telegram token/chat yok"); return
    import urllib.request
    import urllib.parse
    dec = []
    for name, path in [("format", w["viral"]["format"]), ("ses", w["shorts"]["voice"]),
                       ("motor", w["shorts"]["engine"])]:
        if path.get("next_pick"):
            dec.append(f"{name}={path['next_pick']}")
    line = "🧠 Kararlar: " + (", ".join(dec) if dec else "hâlâ keşifte (yeterli veri yok)")
    opp = w["topics"].get("opportunity_queries", [])
    txt = (f"<b>🧠 ParaFOMO öğrenme özeti</b>\n{line}\n\n"
           f"🎯 Fırsat sorgusu: {opp[0]['query'] if opp else '—'}\n"
           f"Tam rapor: docs/learning-report.md")
    data = urllib.parse.urlencode({"chat_id": chat, "text": txt, "parse_mode": "HTML",
                                   "disable_web_page_preview": "true"}).encode()
    try:
        urllib.request.urlopen(urllib.request.Request(
            f"https://api.telegram.org/bot{token}/sendMessage", data=data), timeout=15)
        print("[+] Telegram gönderildi")
    except Exception as e:
        print(f"[!] Telegram hata: {e}")


if __name__ == "__main__":
    sys.exit(main())
