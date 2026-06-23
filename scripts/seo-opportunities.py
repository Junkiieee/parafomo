#!/usr/bin/env python3
"""
ParaFOMO — GSC fırsat sorguları (günlük içerik motoru için).

Google Search Console'dan son 28 günün sorgularını çeker ve "fırsat" olanları
makine-okunur bir dosyaya (docs/seo-opportunities.md) döker. Fırsat = Google
seni o aramada zaten GÖSTERİYOR ama sıra geride / tıklama düşük → o konuda güçlü
bir yazı yazıp sırayı yukarı çekmek, tahmini backlog'dan çok daha isabetli.

Günlük içerik motoru (daily-prompt.md) bu listeyi konu seçiminde KAYNAK (b)
olarak okur: takvimde acil olay yoksa buradaki en üstteki fırsatı seçer; liste
boşsa keywords.md backlog'una düşer.

Servis hesabı anahtarı repo dışıdır (~/.config/parafomo/ga-sa.json).

Kullanım:
  /root/.venvs/parafomo/bin/python scripts/seo-opportunities.py
"""
import os
import sys
from datetime import date, timedelta

from google.oauth2 import service_account
from googleapiclient.discovery import build

KEY = os.path.expanduser("~/.config/parafomo/ga-sa.json")
GSC_SITE = "sc-domain:parafomo.com"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_MD = os.path.join(ROOT, "docs", "seo-opportunities.md")
GSC_SCOPE = ["https://www.googleapis.com/auth/webmasters.readonly"]

# Fırsat eşikleri — yeni/küçük site olduğu için düşük tutuldu.
MIN_IMPRESSIONS = 3      # en az 3 gösterim (Google seni gerçekten gösteriyor)
POS_MIN, POS_MAX = 4.0, 40.0   # 1-3 zaten iyi; 40+ çok uzak
MAX_CTR = 0.10           # %10 altı tıklama oranı → başlık/içerik iyileştir
TOP_N = 12               # listeye en çok kaç fırsat


def gsc_query(sc, start, end, dimensions=None, row_limit=200):
    body = {"startDate": start.isoformat(), "endDate": end.isoformat(), "rowLimit": row_limit}
    if dimensions:
        body["dimensions"] = dimensions
    return sc.searchanalytics().query(siteUrl=GSC_SITE, body=body).execute().get("rows", [])


def main():
    today = date.today()
    start = today - timedelta(days=28)

    header = [
        "# ParaFOMO — GSC Fırsat Sorguları (içerik motoru için)",
        "",
        f"> Üretim: {today.isoformat()} · Dönem: son 28 gün · Kaynak: `scripts/seo-opportunities.py`",
        "> Kullanım: günlük içerik motoru, takvimde acil olay yoksa buradaki **en üstteki** fırsatı",
        "> konu seçer (Yayınlananlar'da zaten varsa atla). Liste boşsa keywords.md backlog'una düşer.",
        "",
    ]

    try:
        creds = service_account.Credentials.from_service_account_file(KEY, scopes=GSC_SCOPE)
        sc = build("searchconsole", "v1", credentials=creds, cache_discovery=False)
        queries = gsc_query(sc, start, today, ["query"], 200)
    except Exception as e:
        body = [f"## Fırsatlar\n\n- [HATA] GSC çekilemedi: {e}\n",
                "- (motor bu turda backlog'a düşmeli)\n"]
        _write(header + body)
        print(f"[!] GSC çekilemedi: {e}")
        return 0

    opp = [q for q in queries
           if q["impressions"] >= MIN_IMPRESSIONS
           and POS_MIN <= q["position"] <= POS_MAX
           and (q["clicks"] / q["impressions"]) < MAX_CTR]
    # Önce yüksek gösterim, sonra daha iyi (düşük) sıra → en kazanılabilir üstte.
    opp.sort(key=lambda x: (-x["impressions"], x["position"]))

    body = ["## Fırsatlar (gösterim var · sıra geride · tıklama düşük)", ""]
    if not opp:
        body.append("- (henüz belirgin fırsat yok — motor backlog'a düşsün)")
    else:
        for q in opp[:TOP_N]:
            body.append(
                f"- [ ] `{q['keys'][0]}` — gösterim {int(q['impressions'])}, "
                f"sıra {q['position']:.1f}, tıklama {int(q['clicks'])}"
            )
    body.append("")

    _write(header + body)
    print(f"[+] {len(opp)} fırsat sorgusu yazıldı -> {OUT_MD}")
    return 0


def _write(lines):
    os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    sys.exit(main())
