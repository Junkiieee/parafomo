"""Zam alarmı gönderimi — "zam-alarmi:" etiketli ONAYLI abonelere, açıklama günü TEK e-posta.

Söz (src/components/ZamAlarmi.astro, mailer.send_zam_alarm_confirm): resmî rakam açıklandığı gün tek e-posta,
kesin oran + kendi maaşınla hesaplama bağlantısı. Olaylar:
  asgari-<yıl>         yeni asgari ücret (data/asgari-ucret.json: yeni, yıl devrinden sonra guncel)
  memur-emekli-<yıl>   Ocak zammı: önceki yılın Temmuz–Aralık birikimli TÜFE'si (data/tufe-aylik.json;
                       resmiZam["<yıl>-01"].ssk varsa o) + memur toplu sözleşme/enflasyon farkı (src/data/zam2027.ts)

GO-LIVE KAPISI: gerçek abonelere YALNIZ /root/parafomo-data/dash/kontrol.json içinde "zam_alarm_gonder": true
ise gider (anahtar yoksa KAPALI). Kaan e-posta metnini onaylamadan açılmaz: önce --dry-run önizlemesi, sonra
--to <kendi adresi> ile deneme. Kapı kapalıyken bekleyen abone varsa Kaan'a (agent/notify.py, günde 1) haber verilir.

Tekrar yok: olay başına durum /root/parafomo-data/zam-alarm-state.json (DB dizini) — alıcı başına (e-posta
SHA-256 özeti) kayıt tutulur; yarıda kalan gönderim kaldığı yerden sürer, biten olay bir daha gitmez.
SMTP kotası (Brevo ücretsiz 300/gün; onay/sıfırlama mailleri de aynı kotadan): UTC günü başına en çok --max
(varsayılan 250) alıcı; kalan varsa çıkış kodu 3 → ertesi gün aynı komut (ya da bekçinin sonraki koşusu) kalanları
gönderir.

Bekçiler (scripts/asgari-ucret-watch.py, scripts/release-watch.py) --tetik ile çağırır: ilk tetikte kapı kapalıysa
Kaan'a haber verilir ve olay "bekliyor" olarak yazılır; sonraki tetiklerde kapı açılmışsa gönderilir, değilse sessiz.

Kullanım (backend/ içinden, API venv'i ile; ya da bash scripts/zam-alarm-send.sh ...):
  python -m app.zam_alarm_send --olay asgari-2027 --dry-run          # önizleme + alıcı sayısı, gönderme
  python -m app.zam_alarm_send --olay asgari-2027 --to ben@ornek.com # yalnız bu adrese (deneme; kapıdan bağımsız)
  python -m app.zam_alarm_send --olay asgari-2027                    # onaylı zam alarmı abonelerine (kapı açıksa)
  python -m app.zam_alarm_send --olay asgari-2027 --tetik            # bekçi çağrısı (yukarıdaki gibi, tekrar haber yok)
Çıkış: 0 tamam/yapılacak yok/kapı kapalı · 1 gönderim hatası · 2 veri hazır değil/geçersiz olay · 3 kota → devamı var
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import html
import json
import os
import re
import smtplib
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select

from .config import get_settings
from .db import SessionLocal, init_db
from .models import NewsletterSubscriber
from .newsletter_send import _message, _tr_num

REPO = Path(__file__).resolve().parents[2]
DATA = REPO / "data"
SITE = "https://parafomo.com"
_settings = get_settings()
DATA_DIR = Path(_settings.db_path).parent          # canlıda /root/parafomo-data
STATE = DATA_DIR / "zam-alarm-state.json"
KONTROL = DATA_DIR / "dash" / "kontrol.json"
KAPI = "zam_alarm_gonder"
MAX_VARSAYILAN = 250

# Yalnız zam alarmı için kaydolanlar (kaynak etiketi; bülten etiketiyle birleşmiş olabilir: "bulten:/|zam-alarmi:/x")
ZAM = NewsletterSubscriber.source.like("%zam-alarmi:%")
_OLAY_RE = re.compile(r"(asgari|memur-emekli)-(20\d\d)")
AYLAR = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]


class VeriYok(Exception):
    """Olayın resmî rakamı henüz veride yok (ya da olay adı geçersiz)."""


def _pct(x: float) -> str:
    return f"%{_tr_num(x, 2)}"


def _utm(path: str, olay: str) -> str:
    return f"{SITE}{path}?utm_source=zam-alarmi&utm_medium=email&utm_campaign={olay}"


def _load(name: str) -> dict:
    return json.loads((DATA / name).read_text(encoding="utf-8"))


# ---------------------------------------------------------------- olay verisi
def _asgari(yil: int) -> dict:
    d = _load("asgari-ucret.json")
    yeni, g = d.get("yeni"), d.get("guncel") or {}
    if yeni and yeni.get("yil") == yil:
        cur, onceki = yeni, g.get("net")
    elif g.get("yil") == yil:   # yıl devrinden sonra (1 Ocak+): açıklanan rakam guncel'e taşınmış
        cur = g
        onceki = next((x.get("net") for x in d.get("gecmis", []) if x.get("yil") == yil - 1), None)
    else:
        raise VeriYok(f"{yil} asgari ücreti data/asgari-ucret.json'da yok (yeni/guncel)")
    net, brut = cur.get("net"), cur.get("brut")
    if not net or not brut:
        raise VeriYok(f"{yil} asgari ücretinde net/brüt eksik")
    artis = (net / onceki - 1) * 100 if onceki else None
    return {"yil": yil, "net": float(net), "brut": float(brut), "onceki": onceki, "artis": artis}


def _ts_orani(ad: str) -> float:
    """Toplu sözleşme oranı (%) — sitedeki tahmin modülüyle aynı kaynak (src/data/zam2027.ts)."""
    src = (REPO / "src" / "data" / "zam2027.ts").read_text(encoding="utf-8")
    m = re.search(rf"export const {ad}\s*=\s*([0-9]+(?:\.[0-9]+)?)", src)
    if not m:
        raise VeriYok(f"src/data/zam2027.ts içinde {ad} yok (bu yılın toplu sözleşme oranı girilmemiş)")
    return float(m.group(1))


def _memur_emekli(yil: int) -> dict:
    t = _load("tufe-aylik.json")
    aylik = {m["ay"]: m["aylik"] for m in t.get("months", []) if m.get("aylik") is not None}
    donem = [f"{yil - 1}-{a:02d}" for a in range(7, 13)]
    eksik = [k for k in donem if k not in aylik]
    if eksik:
        raise VeriYok(f"Temmuz–Aralık {yil - 1} TÜFE eksik: {', '.join(eksik)} (zam henüz kesinleşmedi)")
    cum = 1.0
    for k in donem:
        cum *= 1 + aylik[k] / 100
    ssk = (cum - 1) * 100
    resmi = ((t.get("resmiZam") or {}).get(f"{yil}-01") or {}).get("ssk")
    if resmi is not None:   # resmî açıklama girildiyse o esas (sitedeki zam2027.ts ile aynı kural)
        ssk = float(resmi)
    ts_h2, ts_h1 = _ts_orani(f"TS_H2_{yil - 1}"), _ts_orani(f"TS_H1_{yil}")
    fark = max(0.0, (1 + ssk / 100) / (1 + ts_h2 / 100) - 1) * 100
    memur = ((1 + fark / 100) * (1 + ts_h1 / 100) - 1) * 100
    return {"yil": yil, "ssk": ssk, "memur": memur, "fark": fark, "ts": ts_h1}


def olay_verisi(olay: str) -> dict:
    m = _OLAY_RE.fullmatch(olay or "")
    if not m:
        raise VeriYok(f"geçersiz olay: {olay!r} (asgari-<yıl> ya da memur-emekli-<yıl>)")
    tur, yil = m.group(1), int(m.group(2))
    return {"tur": tur, **(_asgari(yil) if tur == "asgari" else _memur_emekli(yil))}


# ---------------------------------------------------------------- e-posta
_WRAP = ("<div style='font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;max-width:560px;margin:0 auto;"
         "padding:20px;color:#14201a;line-height:1.55'>")
_BTN = ("style='display:inline-block;background:#0f7a4d;color:#fff;text-decoration:none;padding:11px 18px;"
        "border-radius:8px;font-weight:600'")


def build(olay: str, v: dict) -> tuple[str, str, str]:
    """(konu, html, düz metin). {UNSUB} yer tutucusu _message'da kişiye özel bağlantıyla değişir."""
    e = html.escape
    if v["tur"] == "asgari":
        y = v["yil"]
        subject = f"Asgari ücret {y} belli oldu: net {_tr_num(v['net'])} TL"
        artis = f" (geçen yıla göre {_pct(v['artis'])} artış)" if v.get("artis") is not None else ""
        satirlar = [f"{y} asgari ücreti açıklandı: net {_tr_num(v['net'])} TL, brüt {_tr_num(v['brut'])} TL{artis}."]
        link, link_ad = _utm("/asgari-ucret-hesaplama/", olay), "Net, brüt ve işveren maliyetini hesapla"
        ek = f"Yeni tutar 1 Ocak {y} tarihinden itibaren geçerli."
    else:
        y = v["yil"]
        subject = (f"Ocak {y} zammı kesinleşti: SSK/Bağ-Kur emeklisine {_pct(v['ssk'])}, "
                   f"memura {_pct(v['memur'])}")
        satirlar = [
            f"Aralık {y - 1} enflasyonu açıklandı; Ocak {y} zamları kesinleşti:",
            f"• SSK ve Bağ-Kur emeklisi: {_pct(v['ssk'])} (Temmuz–Aralık {y - 1} birikimli enflasyon)",
            f"• Memur ve memur emeklisi: {_pct(v['memur'])} (%{_tr_num(v['ts'], 0)} toplu sözleşme + "
            f"{_pct(v['fark'])} enflasyon farkı)",
        ]
        link, link_ad = _utm("/emekli-zammi-hesaplama/", olay), "Yeni emekli aylığını hesapla"
        ek = f"Memur maaşını hesaplamak için: {_utm('/memur-zammi-hesaplama/', olay)}"
    alt = ("Zam alarmına kaydolduğun için bu tek e-postayı aldın; haftalık bülten ya da reklam göndermiyoruz. "
           "Bilgi amaçlıdır, yatırım tavsiyesi değildir.")

    parts = [_WRAP, f"<h1 style='font-size:20px;margin:0 0 14px'>{e(subject)}</h1>"]
    parts += [f"<p style='margin:0 0 8px'>{e(s)}</p>" for s in satirlar]
    parts.append(f"<p style='margin:20px 0'><a {_BTN} href='{e(link)}'>{e(link_ad)} →</a></p>")
    if v["tur"] == "memur-emekli":
        parts.append(f"<p style='margin:0 0 8px'><a style='color:#0f7a4d' href='{e(_utm('/memur-zammi-hesaplama/', olay))}'>"
                     "Memur maaşını hesapla →</a></p>")
    else:
        parts.append(f"<p style='margin:0 0 8px;color:#4a564f'>{e(ek)}</p>")
    parts.append(
        "<p style='margin:28px 0 0;padding-top:12px;border-top:1px solid #e6ebe8;font-size:12px;color:#7a847d'>"
        f"{e(alt)}<br><a style='color:#7a847d' href='{{UNSUB}}'>Zam alarmı kaydımı sil</a> · Parafomo · parafomo.com</p></div>")
    text = [subject, "", *satirlar, "", f"{link_ad}: {link}", ek, "", alt, "Kaydını silmek için: {UNSUB}"]
    return subject, "".join(parts), "\n".join(text)


# ---------------------------------------------------------------- durum, kapı
def _hash(email: str) -> str:
    return hashlib.sha256(email.strip().lower().encode("utf-8")).hexdigest()[:24]


def _state_read() -> dict:
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _state_write(state: dict) -> None:
    tmp = STATE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")
    os.chmod(tmp, 0o600)
    tmp.replace(STATE)


def kapi_acik() -> bool:
    """Go-live kapısı: kontrol.json'da açıkça true olmalı (yok/okunamıyor = KAPALI)."""
    try:
        return json.loads(KONTROL.read_text(encoding="utf-8")).get(KAPI) is True
    except (OSError, ValueError, AttributeError):
        return False


def _bildir(olay: str, subject: str, body: str) -> None:
    """Kaan'a uyarı (agent/notify.py — anahtar başına günde 1). Hata gönderimi durdurmaz."""
    try:
        subprocess.run(["python3", str(REPO / "agent" / "notify.py"), "alert", "--key", f"zam-alarm-{olay}",
                        "--subject", subject, "--body", body], timeout=120, check=False)
    except Exception as exc:  # noqa: BLE001
        print(f"UYARI: Kaan'a bildirim gönderilemedi: {exc}", file=sys.stderr)


def _alicilar() -> list[tuple[str, str]]:
    with SessionLocal() as db:
        subs = db.scalars(select(NewsletterSubscriber)
                          .where(NewsletterSubscriber.status == "confirmed", ZAM)
                          .order_by(NewsletterSubscriber.id)).all()
        return [(s.email, s.token) for s in subs]


def _gonder(targets: list[tuple[str, str]], subject: str, html_body: str, text_body: str, on_sent) -> tuple[int, int]:
    sent = failed = 0
    with smtplib.SMTP(_settings.smtp_host, _settings.smtp_port, timeout=30) as server:
        if _settings.smtp_starttls:
            server.starttls()
        if _settings.smtp_user:
            server.login(_settings.smtp_user, _settings.smtp_password)
        for to, token in targets:
            try:
                server.send_message(_message(to, token, subject, html_body, text_body))
                sent += 1
                on_sent(to)
            except smtplib.SMTPException as exc:
                failed += 1
                print(f"HATA {_hash(to)}: {exc}", file=sys.stderr)
            time.sleep(0.3)  # Brevo hız sınırına saygı
    return sent, failed


# ---------------------------------------------------------------- ana akış
def _bugun() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Zam alarmı e-postası (açıklama günü, tek e-posta)")
    ap.add_argument("--olay", required=True, help="asgari-<yıl> | memur-emekli-<yıl>")
    ap.add_argument("--dry-run", action="store_true", help="gönderme; önizlemeyi --out'a yaz, alıcı sayısını yaz")
    ap.add_argument("--out", help="önizleme HTML yolu (varsayılan: DB dizininde zam-alarm-preview-<olay>.html)")
    ap.add_argument("--to", help="yalnız bu adrese gönder (deneme; kapıdan bağımsız, durum güncellenmez)")
    ap.add_argument("--max", type=int, default=MAX_VARSAYILAN,
                    help=f"UTC günü başına en çok kaç alıcı (SMTP günlük kotası; varsayılan {MAX_VARSAYILAN})")
    ap.add_argument("--tetik", action="store_true",
                    help="bekçi çağrısı: olay daha önce tetiklendiyse ve kapı kapalıysa sessizce çık (Kaan'a tekrar haber yok)")
    args = ap.parse_args(argv)
    olay = args.olay.strip().lower()

    try:
        v = olay_verisi(olay)
    except VeriYok as exc:
        print(f"[zam-alarm] {olay}: veri hazır değil — {exc}")
        return 2
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"[zam-alarm] {olay}: veri okunamadı — {exc}", file=sys.stderr)
        return 2
    subject, html_body, text_body = build(olay, v)

    init_db()
    if args.dry_run:
        out = Path(args.out) if args.out else DATA_DIR / f"zam-alarm-preview-{olay}.html"
        out.write_text(html_body.replace("{UNSUB}", "#"), encoding="utf-8")
        alicilar = _alicilar()
        st = _state_read().get(olay, {})
        kalan = [a for a in alicilar if _hash(a[0]) not in set(st.get("gonderilen", []))]
        print(f"[dry-run] konu: {subject}\n[dry-run] önizleme: {out}\n[dry-run] onaylı zam alarmı abonesi: "
              f"{len(alicilar)} (bu olayda gönderilmemiş: {len(kalan)}{', TAMAMLANDI' if st.get('tamam') else ''})\n"
              f"[dry-run] kapı ({KONTROL} → {KAPI}): {'AÇIK' if kapi_acik() else 'KAPALI'}"
              + (f"\n[dry-run] UYARI: alıcı sayısı günlük sınırı ({args.max}) aşıyor; gönderim günlere bölünür"
                 if len(kalan) > args.max else ""))
        print("\n" + text_body.replace("{UNSUB}", "<kişiye özel çıkış bağlantısı>"))
        return 0

    if not _settings.smtp_enabled:
        print("[zam-alarm] SMTP ayarlı değil (backend/.env PORTFOLIO_SMTP_HOST) — gönderilmedi.", file=sys.stderr)
        return 1

    if args.to:
        with SessionLocal() as db:
            sub = db.scalar(select(NewsletterSubscriber).where(NewsletterSubscriber.email == args.to.strip().lower()))
        try:
            sent, failed = _gonder([(args.to.strip(), sub.token if sub else "test")], "[DENEME] " + subject,
                                   html_body, text_body, lambda _to: None)
        except (smtplib.SMTPException, OSError) as exc:
            print(f"[zam-alarm] {olay} deneme: SMTP hatası — {exc}", file=sys.stderr)
            return 1
        print(f"[zam-alarm] {olay} deneme: gönderildi {sent}, hata {failed}")
        return 0 if failed == 0 else 1

    # Aynı anda iki koşu (bekçi + elle) aynı kişiye iki kez göndermesin
    lock = open(DATA_DIR / "zam-alarm.lock", "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print(f"[zam-alarm] {olay}: başka bir gönderim sürüyor — çıkış")
        return 0

    state = _state_read()
    st = state.get(olay, {})
    if st.get("tamam"):
        print(f"[zam-alarm] {olay} zaten gönderildi ({st.get('bitti')}, {len(st.get('gonderilen', []))} kişi) — tekrar yok")
        return 0
    onceden = bool(st)
    gonderilen = set(st.get("gonderilen", []))
    kalan = [a for a in _alicilar() if _hash(a[0]) not in gonderilen]
    st.setdefault("tetiklendi", datetime.now(timezone.utc).isoformat(timespec="seconds"))

    if not kapi_acik():
        state[olay] = st
        _state_write(state)   # bekçi tekrar denemesi bunu görür: kapı açılınca gönderir
        if args.tetik and onceden:
            print(f"[zam-alarm] {olay}: kapı hâlâ kapalı — bekliyor ({len(kalan)} abone)")
            return 0
        print(f"[zam-alarm] {olay}: kapı KAPALI ({KONTROL} → \"{KAPI}\": true değil) — gönderilmedi; "
              f"bekleyen abone {len(kalan)}")
        if kalan:
            _bildir(olay, f"Zam alarmı GÖNDERİLMEDİ: {olay} ({len(kalan)} abone bekliyor)",
                    f"Resmî rakam veride hazır ama go-live kapısı kapalı ({KAPI}).\n\nKonu: {subject}\n\n"
                    f"{text_body.replace('{UNSUB}', '<çıkış bağlantısı>')}\n\nMetni onaylıyorsan zam alarmı "
                    f"gönderimini aç (kontrol.json → \"{KAPI}\": true); bekçi sonraki koşusunda gönderir ya da elle:\n"
                    f"bash scripts/zam-alarm-send.sh --olay {olay}")
        return 0

    st["konu"] = subject
    bugun = _bugun()
    gunluk = {k: n for k, n in st.get("gunluk", {}).items() if k >= bugun[:8]}   # yalnız bu ayın sayaçları
    hak = max(args.max - gunluk.get(bugun, 0), 0)
    parti = kalan[:hak]

    def on_sent(to: str) -> None:   # her başarılı gönderimden sonra diske yaz: çökse de tekrar gitmez
        gonderilen.add(_hash(to))
        gunluk[bugun] = gunluk.get(bugun, 0) + 1
        st["gonderilen"] = sorted(gonderilen)
        st["gunluk"] = gunluk
        state[olay] = st
        _state_write(state)

    sent = failed = 0
    hata = ""
    if parti:
        try:
            sent, failed = _gonder(parti, subject, html_body, text_body, on_sent)
        except (smtplib.SMTPException, OSError) as exc:   # bağlantı/oturum hatası: gönderilenler kayıtlı
            hata = str(exc)
            failed = len(parti) - sum(1 for a in parti if _hash(a[0]) in gonderilen)
    kalan_sayi = sum(1 for a in kalan if _hash(a[0]) not in gonderilen)
    st["gonderilen"] = sorted(gonderilen)
    st["gunluk"] = gunluk
    st["hata"] = st.get("hata", 0) + failed
    if kalan_sayi == 0:
        st["tamam"] = True
        st["bitti"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    state[olay] = st
    _state_write(state)
    print(f"[zam-alarm] {olay}: gönderildi {sent}, hata {failed}, kalan {kalan_sayi}"
          + (f" (günlük sınır {args.max} doldu; yarın devam)" if kalan_sayi and not failed else "")
          + (f" — SMTP: {hata}" if hata else "") + f" — konu: {subject}")
    if failed:
        return 1
    return 3 if kalan_sayi else 0


if __name__ == "__main__":
    sys.exit(main())
