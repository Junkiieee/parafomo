#!/usr/bin/env python3
"""
ParaFOMO Büyüme Ajanı — KPI TAKİP (trafik/tıklama/gösterim/izlenme zaman serisi).

dashboard.py --json çıktısını okur, günlük compact KPI snapshot'ını
agent/memory/kpi-history.jsonl'a EKLER (tarihe göre dedup → gün içi tekrar
çalışırsa günceller). Böylece ajan hareketi zaman içinde TAKİP eder:
hangi hafta ne oldu, hangi hamleden sonra hangi metrik kımıldadı.

Kullanım: python3 agent/kpi-track.py [dashboard-json-yolu]
"""
import os, sys, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "agent", "state", "kpi-today.json")
HIST = os.path.join(ROOT, "agent", "memory", "kpi-history.jsonl")


def main():
    if not os.path.exists(SRC):
        print(f"[kpi] kaynak yok: {SRC}"); return
    d = json.load(open(SRC, encoding="utf-8"))
    ga, gsc, yt = d.get("ga", {}), d.get("gsc", {}), d.get("yt", {})
    snap = {
        "date": d.get("date"),
        "organic_week": ga.get("organic_last", 0),          # haftalık gerçek erişim (Direct hariç)
        "direct_share": round(ga.get("direct_share", 0), 1),
        "gsc_clicks_week": gsc.get("clicks_last", 0),
        "gsc_impr_week": gsc.get("impressions_last", 0),
        "gsc_ctr": gsc.get("ctr_last", 0),
        "gsc_best_pos": gsc.get("best_pos", 0),
        "gsc_opportunities": gsc.get("opportunities", 0),
        "yt_subs": yt.get("subs", 0),
        "yt_views": yt.get("views", 0),
        "yt_videos": yt.get("videos", 0),
    }
    # geçmişi oku, aynı tarihi değiştir (dedup)
    rows = []
    if os.path.exists(HIST):
        for line in open(HIST, encoding="utf-8"):
            line = line.strip()
            if line:
                try:
                    r = json.loads(line)
                    if r.get("date") != snap["date"]:
                        rows.append(r)
                except Exception:
                    pass
    rows.append(snap)
    os.makedirs(os.path.dirname(HIST), exist_ok=True)
    with open(HIST, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"[kpi] snapshot eklendi ({snap['date']}): organik={snap['organic_week']}/hf "
          f"gsc_tık={snap['gsc_clicks_week']} gsc_gös={snap['gsc_impr_week']} yt_izl={snap['yt_views']}")


if __name__ == "__main__":
    main()
