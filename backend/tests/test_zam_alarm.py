"""Zam alarmı gönderici: kapı, alıcı seçimi, olay başına tekrar yok, kota bölme. Gerçek SMTP yok."""
from __future__ import annotations

import json
import secrets
from email.message import EmailMessage

import pytest

from app import zam_alarm_send as z
from app.db import SessionLocal
from app.models import NewsletterSubscriber


class FakeSMTP:
    """smtplib.SMTP yerine: gönderilenleri toplar, istenen adreste hata verir."""
    sent: list[EmailMessage] = []
    fail_to: set[str] = set()

    def __init__(self, *a, **kw):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def starttls(self):
        pass

    def login(self, *a):
        pass

    def send_message(self, msg):
        if msg["To"] in self.fail_to:
            raise z.smtplib.SMTPRecipientsRefused({msg["To"]: (550, b"no")})
        FakeSMTP.sent.append(msg)


@pytest.fixture
def env(tmp_path, monkeypatch):
    data = tmp_path / "data"
    data.mkdir()
    (data / "asgari-ucret.json").write_text(json.dumps({
        "guncel": {"yil": 2026, "brut": 33030.0, "net": 28075.5, "aciklanma": "2025-12-23"},
        "yeni": {"yil": 2027, "brut": 40000.0, "net": 34000.0, "aciklanma": "2026-12-24", "otomatik": True},
        "gecmis": [{"yil": 2026, "net": 28075.5}],
    }), encoding="utf-8")
    months = [{"ay": f"2026-{m:02d}", "aylik": 1.0, "yillik": 30} for m in range(7, 13)]
    (data / "tufe-aylik.json").write_text(json.dumps({"months": months}), encoding="utf-8")
    dash = tmp_path / "dash"
    dash.mkdir()
    monkeypatch.setattr(z, "DATA", data)
    monkeypatch.setattr(z, "DATA_DIR", tmp_path)
    monkeypatch.setattr(z, "STATE", tmp_path / "zam-alarm-state.json")
    monkeypatch.setattr(z, "KONTROL", dash / "kontrol.json")
    monkeypatch.setattr(z._settings, "smtp_host", "smtp.test.invalid")
    monkeypatch.setattr(z.smtplib, "SMTP", FakeSMTP)
    monkeypatch.setattr(z.time, "sleep", lambda s: None)
    bildirim: list[str] = []
    monkeypatch.setattr(z, "_bildir", lambda olay, subject, body: bildirim.append(subject))
    FakeSMTP.sent = []
    FakeSMTP.fail_to = set()
    return {"tmp": tmp_path, "data": data, "bildirim": bildirim}


def _kapi(env, acik):
    (env["tmp"] / "dash" / "kontrol.json").write_text(json.dumps({"zam_alarm_gonder": acik}), encoding="utf-8")


def _abone(email, status="confirmed", source="zam-alarmi:/asgari-ucret-hesaplama/"):
    with SessionLocal() as db:
        db.add(NewsletterSubscriber(email=email, status=status, source=source, token=secrets.token_urlsafe(16)))
        db.commit()


def _alicilar():
    return sorted(m["To"] for m in FakeSMTP.sent)


def test_selects_only_confirmed_zam_subscribers(env):
    _kapi(env, True)
    _abone("a@example.com")
    _abone("b@example.com", source="bulten:/|zam-alarmi:/emekli-zammi/")
    _abone("c@example.com", source="bulten:/")                 # yalnız bülten
    _abone("d@example.com", status="pending")                  # onaysız
    _abone("e@example.com", status="unsubscribed")             # ayrılmış
    _abone("f@example.com", source=None)
    assert z.main(["--olay", "asgari-2027"]) == 0
    assert _alicilar() == ["a@example.com", "b@example.com"]
    msg = FakeSMTP.sent[0]
    assert "34.000 TL" in msg["Subject"] and msg["List-Unsubscribe"].startswith("<https://api.parafomo.com/newsletter/unsubscribe?token=")
    body = msg.get_body(("plain",)).get_content()
    assert "utm_source=zam-alarmi" in body and "{UNSUB}" not in body


def test_gate_closed_by_default_sends_nothing_and_notifies(env):
    _abone("a@example.com")
    assert z.main(["--olay", "asgari-2027"]) == 0              # kontrol.json yok → KAPALI
    _kapi(env, False)
    assert z.main(["--olay", "asgari-2027"]) == 0
    (env["tmp"] / "dash" / "kontrol.json").write_text('{"zam_alarm_gonder": "true"}', encoding="utf-8")
    assert z.main(["--olay", "asgari-2027"]) == 0              # yalnız JSON true açar
    assert FakeSMTP.sent == []
    assert env["bildirim"] and "GÖNDERİLMEDİ" in env["bildirim"][0]
    state = json.loads((env["tmp"] / "zam-alarm-state.json").read_text())
    assert not state["asgari-2027"].get("tamam") and not state["asgari-2027"].get("gonderilen")


def test_idempotent_per_event(env):
    _kapi(env, True)
    _abone("a@example.com")
    assert z.main(["--olay", "asgari-2027"]) == 0
    assert z.main(["--olay", "asgari-2027"]) == 0
    assert len(FakeSMTP.sent) == 1
    state = json.loads((env["tmp"] / "zam-alarm-state.json").read_text())
    assert state["asgari-2027"]["tamam"] is True
    assert "a@example.com" not in json.dumps(state)            # durum dosyasında adres değil özet


def test_daily_quota_split_and_resume(env, monkeypatch):
    _kapi(env, True)
    for i in range(5):
        _abone(f"s{i}@example.com")
    gun = {"d": "2026-12-24"}
    monkeypatch.setattr(z, "_bugun", lambda: gun["d"])
    assert z.main(["--olay", "asgari-2027", "--max", "2"]) == 3
    assert z.main(["--olay", "asgari-2027", "--max", "2"]) == 3     # aynı gün: kota dolu, gönderim yok
    assert len(FakeSMTP.sent) == 2
    gun["d"] = "2026-12-25"
    assert z.main(["--olay", "asgari-2027", "--max", "2"]) == 3
    gun["d"] = "2026-12-26"
    assert z.main(["--olay", "asgari-2027", "--max", "2"]) == 0
    assert _alicilar() == [f"s{i}@example.com" for i in range(5)]
    assert z.main(["--olay", "asgari-2027"]) == 0 and len(FakeSMTP.sent) == 5


def test_trigger_mode_notifies_once_then_sends_when_gate_opens(env):
    _abone("a@example.com")
    assert z.main(["--olay", "asgari-2027", "--tetik"]) == 0     # ilk tetik: kapı kapalı → Kaan'a haber
    assert z.main(["--olay", "asgari-2027", "--tetik"]) == 0     # tekrar: sessiz
    assert len(env["bildirim"]) == 1 and FakeSMTP.sent == []
    _kapi(env, True)                                              # Kaan metni onayladı, kapıyı açtı
    assert z.main(["--olay", "asgari-2027", "--tetik"]) == 0
    assert _alicilar() == ["a@example.com"]


def test_smtp_connection_error_keeps_progress(env, monkeypatch):
    _kapi(env, True)
    _abone("a@example.com")

    class Down(FakeSMTP):
        def __init__(self, *a, **kw):
            raise OSError("bağlantı reddedildi")

    monkeypatch.setattr(z.smtplib, "SMTP", Down)
    assert z.main(["--olay", "asgari-2027"]) == 1
    monkeypatch.setattr(z.smtplib, "SMTP", FakeSMTP)
    assert z.main(["--olay", "asgari-2027"]) == 0 and _alicilar() == ["a@example.com"]


def test_failed_recipient_retried_next_run_without_duplicates(env):
    _kapi(env, True)
    _abone("ok@example.com")
    _abone("bad@example.com")
    FakeSMTP.fail_to = {"bad@example.com"}
    assert z.main(["--olay", "asgari-2027"]) == 1
    FakeSMTP.fail_to = set()
    assert z.main(["--olay", "asgari-2027"]) == 0
    assert _alicilar() == ["bad@example.com", "ok@example.com"]


def test_to_sends_single_test_mail_regardless_of_gate(env):
    _abone("a@example.com")
    assert z.main(["--olay", "asgari-2027", "--to", "kaan@example.com"]) == 0
    assert _alicilar() == ["kaan@example.com"] and FakeSMTP.sent[0]["Subject"].startswith("[DENEME]")
    assert not (env["tmp"] / "zam-alarm-state.json").exists()


def test_dry_run_writes_preview_and_sends_nothing(env, capsys):
    _kapi(env, True)
    _abone("a@example.com")
    out = env["tmp"] / "onizleme.html"
    assert z.main(["--olay", "asgari-2027", "--dry-run", "--out", str(out)]) == 0
    assert FakeSMTP.sent == [] and "34.000 TL" in out.read_text(encoding="utf-8")
    assert "abonesi: 1" in capsys.readouterr().out


def test_data_not_ready(env):
    _kapi(env, True)
    _abone("a@example.com")
    assert z.main(["--olay", "asgari-2028"]) == 2              # 2028 açıklanmadı
    months = [{"ay": f"2026-{m:02d}", "aylik": 1.0} for m in range(7, 12)]   # Aralık yok
    (env["data"] / "tufe-aylik.json").write_text(json.dumps({"months": months}), encoding="utf-8")
    assert z.main(["--olay", "memur-emekli-2027"]) == 2
    assert z.main(["--olay", "ne-olur-2027"]) == 2
    assert FakeSMTP.sent == []


def test_memur_emekli_figures_match_site_formula(env):
    v = z.olay_verisi("memur-emekli-2027")
    ssk = (1.01 ** 6 - 1) * 100                                 # 6 ay × %1
    assert v["ssk"] == pytest.approx(ssk)
    fark = max(0.0, (1 + ssk / 100) / 1.07 - 1) * 100          # zam2027.ts: TS_H2_2026 = 7, TS_H1_2027 = 5
    assert v["fark"] == pytest.approx(fark)
    assert v["memur"] == pytest.approx(((1 + fark / 100) * 1.05 - 1) * 100)


def test_asgari_after_year_rollover_uses_guncel(env):
    (env["data"] / "asgari-ucret.json").write_text(json.dumps({
        "guncel": {"yil": 2027, "brut": 40000.0, "net": 34000.0},
        "yeni": None,
        "gecmis": [{"yil": 2027, "net": 34000.0}, {"yil": 2026, "net": 28075.5}],
    }), encoding="utf-8")
    v = z.olay_verisi("asgari-2027")
    assert v["net"] == 34000.0 and v["artis"] == pytest.approx((34000 / 28075.5 - 1) * 100)
