#!/usr/bin/env python3
"""TÜİK açıklama günü bekçisi — enflasyon/Yİ-ÜFE verisi gelene kadar kira-artis-update.sh'ı sık çalıştırır.

Neden: TÜİK TÜFE ve Yİ-ÜFE'yi ayın ~3'ünde 10:00 TSİ'de (07:00 UTC) açıklar ve aramaların zirvesi o gün
olur (kira artış oranı, emekli zammı, 3 Kasım'da yeniden değerleme oranı → MTV/harç). Eski cron yalnız
08:20 ve 12:20 UTC'de bakıyordu; TCMB tablosu 08:20'den sonra güncellenirse sayfalar 5+ saat gecikiyordu.
Bu bekçi her 10 dakikada bir (cron: */10 7-10 * * *) çalışır, açıklama günü DEĞİLSE ya da veri zaten
geldiyse ağa çıkmadan sessizce biter; açıklama günü veri eksikse kira-artis-update.sh'ı çağırır
(o betik: veri → canlı yazılar → commit → build kapılı deploy → IndexNow + GSC sitemap).

Açıklama günü: data/tuik-enflasyon-*.json takvimindeki tarih (yoksa ayın 3-6'sı) ile sonraki 3 gün.
Ocak'ta Aralık TÜFE'si gelince Ocak emekli/memur zammı kesinleşir → zam alarmı aboneleri (scripts/zam-alarm-send.sh
--olay memur-emekli-<yıl> --tetik; YALNIZ panel kontrol.json "zam_alarm_gonder": true ise gider, olay başına tek
e-posta; kapı sonradan açılırsa pencere içindeki sonraki koşular gönderir).
Kullanım: python3 scripts/release-watch.py [--dry] [--today YYYY-MM-DD]   (--dry: karar ver, çalıştırma)
"""
import datetime as dt
import glob
import json
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AYLAR = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos",
         "Eylül", "Ekim", "Kasım", "Aralık"]


def load(name):
    try:
        with open(os.path.join(REPO, "data", name), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def release_date(covers):
    for p in sorted(glob.glob(os.path.join(REPO, "data", "tuik-enflasyon-*.json"))):
        try:
            for r in json.load(open(p, encoding="utf-8")).get("releases", []):
                if r.get("covers") == covers:
                    return dt.date.fromisoformat(r["date"])
        except Exception:
            continue
    return None


ZAM_STATE = "/root/parafomo-data/zam-alarm-state.json"   # backend/app/zam_alarm_send.py yazar


def zam_alarm(today, dry):
    """Ocak: Aralık TÜFE'si veride → memur/emekli zammı kesin → zam alarmı göndericisini tetikle.
    Go-live kapısı, tekrar kilidi ve kota GÖNDERİCİDE (burada --force yok). Hata bekçiyi durdurmaz."""
    if today.month != 1:
        return
    if not any(r.get("ay") == f"{today.year - 1}-12" for r in load("tufe-aylik.json").get("months", [])):
        return
    olay = f"memur-emekli-{today.year}"
    try:
        with open(ZAM_STATE, encoding="utf-8") as f:
            if (json.load(f).get(olay) or {}).get("tamam"):
                return
    except Exception:
        pass
    if dry:
        print(f"[release-watch] (dry) zam alarmı: scripts/zam-alarm-send.sh --olay {olay} --tetik")
        return
    try:
        r = subprocess.run(["bash", os.path.join(REPO, "scripts", "zam-alarm-send.sh"), "--olay", olay, "--tetik"],
                           cwd=REPO, capture_output=True, text=True, timeout=1800)
        out = ((r.stdout or "") + (r.stderr or "")).strip()
    except Exception as e:  # noqa: BLE001 — bekçi her durumda sürmeli
        out = f"zam alarmı çalıştırılamadı: {e}"
    if out:
        print(f"[release-watch] {out}")


def main(argv):
    dry = "--dry" in argv
    now = dt.datetime.now(dt.timezone.utc)
    today = (now + dt.timedelta(hours=3)).date()  # İstanbul
    if "--today" in argv:  # test için
        today = dt.date.fromisoformat(argv[argv.index("--today") + 1])
    # Bu ay açıklanan veri = geçen ayın verisi
    y, m = (today.year - 1, 12) if today.month == 1 else (today.year, today.month - 1)
    covers_key = f"{y}-{m:02d}"
    covers = f"{AYLAR[m - 1]} {y}"
    kira_label = f"{AYLAR[today.month - 1]} {today.year}"   # kira oranı UYGULAMA ayıyla adlandırılır

    rel = release_date(covers)
    if rel:
        window = rel <= today <= rel + dt.timedelta(days=3)
    else:
        window = 3 <= today.day <= 6
    if not window:
        if dry:
            print(f"[release-watch] açıklama günü değil ({covers} verisi: {rel or 'ayın 3-6’sı'})")
        return 0

    tufe_ok = any(r.get("ay") == covers_key for r in load("tufe-aylik.json").get("months", []))
    yd = load("yeniden-degerleme.json")
    yd_ok = (yd.get("veriSonAy") or yd.get("sonAy") or "") >= covers_key
    kira_ok = load("kira-artis-2026.json").get("guncelAy") == kira_label
    eksik = [ad for ad, ok in (("TÜFE", tufe_ok), ("Yİ-ÜFE", yd_ok), ("kira", kira_ok)) if not ok]
    if not eksik:
        if dry:
            print(f"[release-watch] {covers} verisi zaten güncel")
        zam_alarm(today, dry)   # önceki koşuda yayınlandı; kapı sonradan açıldıysa gönderim burada tamamlanır
        return 0
    print(f"[{now:%Y-%m-%d %H:%M} UTC] [release-watch] {covers} açıklama günü — eksik: {', '.join(eksik)} → kira-artis-update.sh")
    if dry:
        zam_alarm(today, dry)
        return 0
    rc = subprocess.call(["bash", os.path.join(REPO, "scripts", "kira-artis-update.sh")])
    if rc == 0:   # veri → yazılar → build kapılı deploy başarılı: e-postadaki bağlantı güncel sayfaya gider
        zam_alarm(today, dry)
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
