#!/usr/bin/env bash
#
# ParaFOMO Büyüme Ajanı — gece DURUM DİGEST'i (TOKEN'SIZ).
#
# Amaç: ajanın ham dosyaları tek tek okuyup token yakmaması için, günün tüm
# durumunu tek compact dosyaya (agent/state/digest.md) toplar. "Beyin=token,
# eller=script" prensibinin veri-toplama ayağı. Hiç LLM çağırmaz.
#
set -uo pipefail
export HOME=/root
REPO=/root/parafomo
VPY=/root/.venvs/parafomo/bin/python
cd "$REPO" || exit 1

OUT_DIR="$REPO/agent/state"
mkdir -p "$OUT_DIR"
OUT="$OUT_DIR/digest.md"
DATE="$(date -u +%Y-%m-%dT%H:%MZ)"

{
  echo "# ParaFOMO Durum Digest'i — $DATE"
  echo "_Bu dosya script'le üretildi (token harcanmadı). Ajan bunu okuyup günü planlar._"
  echo

  echo "## 1) Dürüst pano (dashboard.py — 8 haftalık trend, organik vs direct)"
  timeout 150 "$VPY" scripts/dashboard.py 2>/dev/null | sed -n '1,90p' || echo "(dashboard alınamadı)"
  echo

  echo "## 2) Öğrenme raporu (learn/decide — ne tutuyor: format/ses/saat/retention)"
  sed -n '1,70p' docs/learning-report.md 2>/dev/null || echo "(yok)"
  echo

  echo "## 3) SEO fırsat sorguları (GSC — görünüp sıralaması geride olanlar)"
  sed -n '1,50p' docs/seo-opportunities.md 2>/dev/null || echo "(yok)"
  echo

  echo "## 4) Mevcut sayfalar (yeni-alan boşluğu tespiti için)"
  find src/pages -type f | sort | sed 's#^#- #'
  echo
  echo "### Elde olup sayfası olMAYabilecek veri kaynakları (data/)"
  ls -1 data/*.json 2>/dev/null | sed 's#^#- #'
  echo

  echo "## 5) İçerik envanteri"
  echo "- Blog yazısı sayısı: $(find src/content/blog -name '*.md*' 2>/dev/null | wc -l)"
  echo "- Üretilmiş sosyal/video json: $(ls public/social/*.json 2>/dev/null | wc -l)"
  echo

  echo "## 6) Son 12 commit"
  git log --oneline -12
  echo

  echo "## 7) Çalışma dizini durumu (temiz mi?)"
  git status --short || true
  echo

  echo "## 8) Cron sağlık taraması (son loglarda hata izi)"
  found=0
  for f in logs/*.log; do
    [ -f "$f" ] || continue
    hits="$(grep -iE 'error|hata|traceback|fail|invalid_scope|403|429' "$f" 2>/dev/null | tail -4)"
    if [ -n "$hits" ]; then
      found=1
      echo "### $f"
      echo '```'
      echo "$hits"
      echo '```'
    fi
  done
  [ "$found" = 0 ] && echo "Belirgin hata izi yok."
  echo

  # HAM VERİ EKLERİ (GSC sorguları, öğrenme detayı, YouTube perf, blog envanteri)
  timeout 60 "$VPY" "$REPO/agent/digest-extras.py" 2>/dev/null || echo "_(ham veri ekleri alınamadı)_"
  echo

  echo "## 9) Dünkü ajan görevleri (varsa — devam eden iş)"
  sed -n '1,40p' "$OUT_DIR/tasks-for-user.md" 2>/dev/null || echo "(ilk çalıştırma — önceki görev yok)"
} > "$OUT"

echo "[digest] yazıldı -> $OUT ($(wc -l < "$OUT") satır)"
