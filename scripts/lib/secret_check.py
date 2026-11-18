#!/usr/bin/env python3
"""Push öncesi SIR BEKÇİSİ — repo HERKESE AÇIK (GitHub). scripts/deploy-push.sh push'tan önce çağırır.

  python3 scripts/lib/secret_check.py [<aralık>]        # varsayılan origin/main..HEAD
  çıkış: 0 temiz · 1 SIR ŞÜPHESİ (push yapılmamalı) · 2 tarama çalışmadı (çağıran karar verir)

Neden (denetim 2026-11-18, repo-7): ~10 cron işi ve başsız sabah rutini bu repoya commit'leyip push'luyor; hiçbir
sır kontrolü yoktu. Yalnız YÜKSEK GÜVENLİ eşleşmede durdurur (yanlış alarm otomatik yayını kilitler):
  1) eklenen satırlarda bilinen token biçimleri (AWS, Google API/OAuth, Anthropic, GitHub, Slack, Meta/IG,
     Brevo, Telegram bot, Stripe canlı anahtar, PEM özel anahtar) — sınır kontrollü; base64 blob içinde tetiklenmez
  2) eklenen satırlarda bu sunucudaki GERÇEK sır değerleri (/root/parafomo/.env, backend/.env,
     ~/.config/parafomo/*.env|*.json içindeki KEY/SECRET/TOKEN/PASSWORD alanları, ≥12 karakter)
  3) eklenen dosya yolları: .env (örnek hariç), *.pem/*.p12/*.pfx/*.key, id_rsa/id_ed25519/id_ecdsa,
     client_secret*.json, *oauth*.json, ga-sa*.json, *.db/*.sqlite*
Sır DEĞERİ hiçbir zaman yazdırılmaz: yalnız commit, dosya, kural adı (ve hangi anahtarın değeri olduğu).
"""
import glob
import json
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SIR_DOSYALARI = ["/root/parafomo/.env", "/root/parafomo/backend/.env"] + \
    sorted(glob.glob("/root/.config/parafomo/*.env*")) + sorted(glob.glob("/root/.config/parafomo/*.json*"))

_S = r"(?<![A-Za-z0-9_+/-])"      # sol sınır: base64/hex akışının ortasında tetiklenmesin ("=" serbest: KEY=değer)
_E = r"(?![A-Za-z0-9_-])"         # sağ sınır
KALIPLAR = [
    ("AWS erişim anahtarı", _S + r"AKIA[0-9A-Z]{16}" + _E),
    ("Google API anahtarı", _S + r"AIza[0-9A-Za-z_-]{35}" + _E),
    ("Google OAuth erişim token'ı", _S + r"ya29\.[0-9A-Za-z_-]{30,}"),
    ("Google OAuth yenileme token'ı", _S + r"1//0[0-9A-Za-z_-]{30,}"),
    ("Google OAuth istemci sırrı", _S + r"GOCSPX-[0-9A-Za-z_-]{20,}"),
    ("Anthropic/Claude anahtarı", _S + r"sk-ant-[0-9A-Za-z_-]{20,}"),
    ("GitHub token'ı", _S + r"(?:gh[pousr]_[0-9A-Za-z]{36,}|github_pat_[0-9A-Za-z_]{22,})"),
    ("Slack token'ı", _S + r"xox[baprs]-[0-9A-Za-z-]{10,}"),
    ("Meta/Facebook erişim token'ı", _S + r"EAA[0-9A-Za-z]{80,}"),
    ("Instagram erişim token'ı", _S + r"IG(?:AA|QV)[0-9A-Za-z_-]{60,}"),
    ("Brevo anahtarı", _S + r"x(?:keysib|smtpsib)-[0-9a-f]{64}-[0-9A-Za-z]{16}"),
    ("Telegram bot token'ı", r"(?<![0-9])[0-9]{8,10}:AA[0-9A-Za-z_-]{33}" + _E),
    ("Stripe canlı anahtarı", _S + r"(?:sk|rk)_live_[0-9A-Za-z]{24,}"),
    ("PEM özel anahtar", r"-----BEGIN (?:[A-Z0-9]+ )*PRIVATE KEY-----"),
]
KALIPLAR = [(ad, re.compile(k)) for ad, k in KALIPLAR]

SIR_ANAHTAR = re.compile(r"KEY|SECRET|TOKEN|PASSWORD|PASSWD|PASS$|PWD|AUTH|CREDENTIAL|PRIVATE", re.I)
# Sır OLMAYAN alan adları (sonek): kimlik/adres/süre — ör. PORTFOLIO_GOOGLE_CLIENT_ID (ön yüzde açık), token_uri
SIR_DEGIL = re.compile(r"(?:^|_)(?:ID|USER|USERNAME|EMAIL|FROM|TO|URL|URI|HOST|PORT|MINUTES|SECONDS|DAYS)$|^PUBLIC_", re.I)
YASAK_YOL = re.compile(
    r"(?:^|/)\.env(?:\.(?!example$|sample$|template$|dist$)[^/]+)?$"
    r"|\.(?:pem|p12|pfx|key)$|(?:^|/)id_(?:rsa|ed25519|ecdsa)$"
    r"|(?:^|/)client_secret[^/]*\.json$|(?:^|/)[^/]*oauth[^/]*\.json$|(?:^|/)ga-sa[^/]*\.json$"
    r"|\.(?:db|sqlite|sqlite3)$", re.I)


def sir_degerleri():
    """(değer, etiket) — etiket yalnız dosya adı + anahtar adı; değer asla yazdırılmaz."""
    out = {}

    def ekle(v, etiket):
        if isinstance(v, str):
            v = v.strip().strip('"').strip("'")
            if len(v) >= 12 and "\n" not in v and not v.lower().startswith(("http://", "https://")):
                out.setdefault(v, etiket)

    def yuru(o, dosya, yol=""):
        if isinstance(o, dict):
            for k, v in o.items():
                if isinstance(v, (dict, list)):
                    yuru(v, dosya, f"{yol}.{k}")
                elif SIR_ANAHTAR.search(str(k)) and not SIR_DEGIL.search(str(k)):
                    ekle(v, f"{os.path.basename(dosya)}:{(yol + '.' + k).lstrip('.')}")
        elif isinstance(o, list):
            for v in o:
                yuru(v, dosya, yol)

    for f in SIR_DOSYALARI:
        try:
            metin = open(f, encoding="utf-8", errors="ignore").read()
        except OSError:
            continue
        if f.endswith(".json") or ".json." in os.path.basename(f):
            try:
                yuru(json.loads(metin), f)
            except Exception:
                pass
            continue
        for line in metin.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.replace("export ", "").strip()
            if SIR_ANAHTAR.search(k) and not SIR_DEGIL.search(k):
                ekle(v, f"{os.path.basename(f)}:{k}")
    return out


def git(*a):
    r = subprocess.run(["git", "-C", REPO, *a], capture_output=True, text=True, errors="replace", timeout=300)
    if r.returncode != 0:
        raise RuntimeError(f"git {' '.join(a[:2])}: {r.stderr.strip()[:200]}")
    return r.stdout


def tara(aralik):
    bulgu = []
    sirlar = sir_degerleri()
    # 3) eklenen dosya yolları
    commit = None
    for line in git("log", "--no-color", "--format=commit %h", "--name-only", "--diff-filter=A", aralik).splitlines():
        if line.startswith("commit "):
            commit = line[7:]
        elif line.strip() and YASAK_YOL.search(line.strip()):
            bulgu.append((commit, line.strip(), 0, "sır/veri dosyası eklenmiş (yol kuralı)"))
    # 1-2) eklenen satırlar
    commit = dosya = None
    satir_no = 0
    for line in git("log", "--no-color", "--no-ext-diff", "--no-textconv", "--format=commit %h", "-p", "-U0",
                    "--no-renames", aralik).splitlines():
        if line.startswith("commit ") and len(line) <= 60:
            commit, dosya = line[7:], None
            continue
        if line.startswith("+++ "):
            dosya = line[6:] if line.startswith("+++ b/") else None
            continue
        if line.startswith("@@"):
            m = re.search(r"\+(\d+)", line)
            satir_no = int(m.group(1)) if m else 0
            continue
        if not line.startswith("+") or dosya is None:
            continue
        icerik = line[1:]
        for ad, rx in KALIPLAR:
            if rx.search(icerik):
                bulgu.append((commit, dosya, satir_no, ad))
        if sirlar and len(icerik) >= 12:
            for v, etiket in sirlar.items():
                if v in icerik:
                    bulgu.append((commit, dosya, satir_no, f"sunucudaki gerçek sır değeri ({etiket})"))
                    break
        satir_no += 1
    return bulgu, len(sirlar)


def main():
    aralik = sys.argv[1] if len(sys.argv) > 1 else "origin/main..HEAD"
    try:
        bulgu, n_sir = tara(aralik)
    except Exception as e:
        print(f"[sır] tarama çalışmadı: {e}")
        return 2
    if not bulgu:
        print(f"[sır] temiz ({aralik}; {len(KALIPLAR)} kalıp + {n_sir} gerçek sır değeri)")
        return 0
    print(f"[sır] ⛔ SIR ŞÜPHESİ — {len(bulgu)} bulgu ({aralik}); değerler yazdırılmaz:")
    for c, d, n, ad in bulgu[:20]:
        print(f"[sır]   {c} {d}" + (f":{n}" if n else "") + f" — {ad}")
    print("[sır] Düzelt: değeri dosyadan çıkar, commit'i düzelt (push'lanmadıysa geçmişte kalmasın), "
          "sızan anahtarı yenile.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
