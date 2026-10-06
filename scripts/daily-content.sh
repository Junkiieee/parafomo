#!/usr/bin/env bash
#
# ParaFOMO — günlük içerik motoru (bu sunucuda cron ile çalışır, Pzt-Cum).
# Akış: veri kaynaklarını tazele → repo'yu senkronla → claude headless ile yeni yazı
#       üret+build+commit → push (Cloudflare otomatik deploy) → Telegram.
#
# v2 (2026-10): konu önce ajanın kuyruğundan (agent/plan/content-queue.md) gelir;
# ajanla aynı anda çalışmaz (ağır-iş kilidi); Claude kotası doluysa sessizce atlar
# ve "Tamamlandı" yalanı söylemez.
#
# Cron: 15 5 * * 1-5 /root/parafomo/scripts/daily-content.sh >> /root/parafomo/logs/cron.log 2>&1

set -uo pipefail

# --- Cron'un sınırlı PATH'ini düzelt (node, npm, claude, git) ---
export PATH="/root/.local/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export HOME="/root"

REPO="/root/parafomo"
. "$REPO/scripts/lib/gitsync.sh"
LOG_DIR="$REPO/logs"
PROMPT_FILE="$REPO/scripts/daily-prompt.md"
VPY="/root/.venvs/parafomo/bin/python"
mkdir -p "$LOG_DIR"
MODEL="${CONTENT_MODEL:-opus}"   # Max 5x (2026-10-06): blog = marka/SEO çekirdeği → en iyi model
EFFORT="${CONTENT_EFFORT:-medium}"
BUDGET="${CONTENT_MAX_BUDGET:-6}"

STAMP="$(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "=================================================="
echo "[$STAMP] ParaFOMO günlük içerik motoru başladı"

cd "$REPO" || { echo "HATA: repo dizinine girilemedi"; exit 1; }

# 0) Ağır-iş kilidi: ajan (agent/run.sh) çalışıyorsa bitmesini bekle (en çok 3 saat).
exec 8>"$REPO/.git/parafomo-heavy.lock"
if ! flock -w 10800 8; then
  echo "[!] Ajan 3 saattir bitmedi — bugünkü içerik atlandı"; exit 0
fi

# 0b) Claude kotası/oturumu durumu: sert limit sürüyorsa hiç başlama.
if ! "$VPY" - <<'PY'
import sys; sys.path.insert(0, "/root/parafomo/scripts/lib")
from llm import blocked_until, read_status
u = blocked_until()
if u:
    print(f"[!] Claude kotası dolu ({read_status().get('state')}) — {u:%H:%M UTC}'e kadar; içerik atlandı")
    sys.exit(1)
PY
then exit 0; fi

# 1) Uzak depo ile senkronla (çakışmayı önle)
echo "[*] git sync"
git_sync || echo "UYARI: pull başarısız, devam ediliyor"

# 1b) Veri kaynaklarını tazele (her biri bağımsız; hata mevcut veriyi korur)
echo "[*] Ekonomik takvim çekiliyor"
python3 "$REPO/scripts/fetch-economic-calendar.py" 2>&1 | sed 's/^/    [takvim] /' || echo "UYARI: takvim güncellenemedi (devam)"
echo "[*] Halka arz takvimi çekiliyor"
python3 "$REPO/scripts/fetch-halka-arz.py" 2>&1 | sed 's/^/    [halka-arz] /' || echo "UYARI: halka arz takvimi güncellenemedi (devam)"
echo "[*] Altın fiyatları çekiliyor"
python3 "$REPO/scripts/altin-fiyat.py" 2>&1 | sed 's/^/    [altin] /' || echo "UYARI: altın fiyatı güncellenemedi (mevcut korunur, devam)"
echo "[*] Dolar endeksi (DXY) çekiliyor"
python3 "$REPO/scripts/dxy.py" 2>&1 | sed 's/^/    [dxy] /' || echo "UYARI: dolar endeksi güncellenemedi (mevcut korunur, devam)"
echo "[*] Altın getiri analizi hesaplanıyor"
python3 "$REPO/scripts/gold-returns.py" 2>&1 | sed 's/^/    [altin-getiri] /' || echo "UYARI: altın getiri güncellenemedi (mevcut korunur, devam)"
echo "[*] Dolar getiri analizi hesaplanıyor"
python3 "$REPO/scripts/dollar-returns.py" 2>&1 | sed 's/^/    [dolar-getiri] /' || echo "UYARI: dolar getiri güncellenemedi (mevcut korunur, devam)"
echo "[*] BIST 100 getiri analizi hesaplanıyor"
python3 "$REPO/scripts/bist-returns.py" 2>&1 | sed 's/^/    [bist-getiri] /' || echo "UYARI: bist getiri güncellenemedi (mevcut korunur, devam)"
echo "[*] ABD tahvil faizleri (getiri eğrisi) çekiliyor"
python3 "$REPO/scripts/us-tahvil.py" 2>&1 | sed 's/^/    [ustahvil] /' || echo "UYARI: ABD tahvil faizleri güncellenemedi (mevcut korunur, devam)"
# GSC fırsat sorguları (konu seçimi kaynağı); venv'de google kütüphaneleri var.
echo "[*] GSC fırsat sorguları çekiliyor"
"$VPY" "$REPO/scripts/seo-opportunities.py" 2>&1 | sed 's/^/    [seo] /' || echo "UYARI: GSC fırsatları güncellenemedi (motor backlog'a düşer)"

# 2) Headless claude ile içerik üret (yazar, build eder, commit'ler).
#    Yalın: MCP/skill yok; model+efor açık (kullanıcı ayarındaki opus/xhigh miras alınmaz).
echo "[*] claude headless çalışıyor (içerik üretimi: $MODEL/$EFFORT, tavan \$$BUDGET)..."
OUT_JSON="$LOG_DIR/content-last.json"
[ -f /root/.config/parafomo/claude.env ] && { set -a; . /root/.config/parafomo/claude.env; set +a; }
claude -p \
  --model "$MODEL" \
  --effort "$EFFORT" \
  --max-budget-usd "$BUDGET" \
  --output-format json \
  --permission-mode acceptEdits \
  --allowedTools Bash Read Write Edit Glob Grep \
  --strict-mcp-config \
  --disable-slash-commands \
  < "$PROMPT_FILE" > "$OUT_JSON" 2>>"$LOG_DIR/content-last.err"

# Sonucu sınıflandır (hata metni "başarı" sayılmasın; kota/auth durumunu ortak dosyaya yaz)
RESULT="$("$VPY" - "$OUT_JSON" <<'PY'
import json, sys
sys.path.insert(0, "/root/parafomo/scripts/lib")
import llm
try:
    raw = open(sys.argv[1], encoding="utf-8").read().strip()
    d = json.loads(raw.splitlines()[-1]) if raw else {}
except Exception:
    d, raw = {}, ""
msg = (d.get("result") or raw or "")[:400]
if d.get("type") == "result" and not d.get("is_error"):
    kind = "ok" if d.get("subtype") == "success" else d.get("subtype", "other")
else:
    kind = llm.classify(msg, d.get("api_error_status"))
    if kind in ("session_limit", "weekly_limit"):
        llm.write_status(kind, msg, llm.parse_reset(msg))
    elif kind == "auth":
        llm.write_status("auth", msg); llm.alert("auth", msg)
cost = d.get("total_cost_usd")
first = msg.splitlines()[0][:200] if msg else ""
print(f"{kind}\tturns={d.get('num_turns')} cost=${cost if cost is not None else '?'}\t{first}")
PY
)"
KIND="${RESULT%%$'\t'*}"
echo "    [claude] sonuç: $RESULT"

# 3) Güvenlik ağı: agent commit'lemediyse kalan içerik/veri değişikliklerini topla
#    (ajanın kodu ayrı commit'lenir; bu iş yalnız içerik + veri yollarını süpürür).
git_add_commit "içerik: otomatik günlük güncelleme ($(date -u '+%Y-%m-%d'))" \
  src/content/blog/ public/covers/ 'public/social/*.png' data/ public/ docs/ src/data/ \
  agent/plan/content-queue.md || true

# 4) Push (Cloudflare deploy'unu tetikler) — SSH deploy key ile şifresiz
if git log origin/main..HEAD --oneline 2>/dev/null | grep -q .; then
  echo "[*] Yerel commit'ler push ediliyor"
  if git_push_retry main; then
    echo "[+] Push başarılı — Cloudflare deploy tetiklendi"
  else
    echo "[!] HATA: push başarısız"
    exit 2
  fi
else
  echo "[i] Push edilecek yeni commit yok"
fi

# 5) Telegram kanalına (@parafomo) yeni yazıyı gönder (dedup'lı — aynı yazıyı 2 kez atmaz)
if [ "$KIND" = "ok" ]; then
  echo "[*] Telegram'a gönderiliyor"
  "$REPO/scripts/post-telegram.sh" || echo "UYARI: Telegram gönderimi başarısız (devam)"
  echo "[$(date -u '+%Y-%m-%d %H:%M:%S UTC')] Tamamlandı"
else
  echo "[$(date -u '+%Y-%m-%d %H:%M:%S UTC')] İçerik ÜRETİLEMEDİ ($KIND) — yarın tekrar"
  exit 3
fi
