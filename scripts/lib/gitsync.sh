#!/usr/bin/env bash
# Ortak git yardımcıları — eşzamanlı cron'ların non-fast-forward push yarışını çözer.
#
# Önceki desen `git push ... | sed ... || echo "UYARI"` sed'in çıkış kodunu (daima 0)
# kontrol ettiği için push hatası SESSİZCE yutuluyordu. git_push_retry gerçek push
# çıkış kodunu (PIPESTATUS) kontrol eder; başarısızsa pull --rebase --autostash ile
# uzağı alıp bir kez daha dener.
#
# Kullanım: . "$REPO/scripts/lib/gitsync.sh"  → sonra `git_push_retry` çağır.

git_push_retry() {
  local branch="${1:-main}"
  git push origin "$branch" 2>&1 | sed 's/^/    [push] /'; [ "${PIPESTATUS[0]}" -eq 0 ] && return 0
  echo "    [push] başarısız (muhtemelen non-fast-forward) → pull --rebase deneniyor"
  git pull --rebase --autostash origin "$branch" 2>&1 | sed 's/^/    [pull] /'
  git push origin "$branch" 2>&1 | sed 's/^/    [push] /'; [ "${PIPESTATUS[0]}" -eq 0 ] && return 0
  echo "UYARI: push yine başarısız ($branch)"
  return 1
}
