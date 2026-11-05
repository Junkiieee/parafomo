#!/usr/bin/env bash
# Ortak git yardımcıları — TÜM cron'lar ve ajan git'e YALNIZ bu fonksiyonlarla dokunur.
#
# Neden (Eylül 2026 otopsisi): ~12 iş aynı repoda eşzamanlı fetch/rebase/commit/push
# yapıyordu → logs'ta yüzlerce "pull başarısız / push başarısız" (index.lock yarışı,
# rebase ortasında commit). Artık her git işlemi tek bir kilit (flock) altında sıralanır.
#
# Kullanım: . "$REPO/scripts/lib/gitsync.sh"
#   git_sync                         → uzağı al (fetch + rebase --autostash)
#   git_add_commit "mesaj" yol...    → yalnız verilen yolları ekle + commit (değişiklik yoksa sessiz)
#   git_push_retry [dal]             → push; non-fast-forward ise rebase + bir kez daha
#   git_locked komut...              → herhangi bir git komutunu kilit altında çalıştır

GIT_LOCK="${GIT_LOCK:-/root/parafomo/.git/parafomo-git.lock}"

_git_lock_take() {
  flock -w "${GIT_LOCK_WAIT:-600}" 9 || { echo "UYARI: git kilidi ${GIT_LOCK_WAIT:-600}sn içinde alınamadı" >&2; return 1; }
}

git_locked() {
  ( _git_lock_take || exit 1; "$@" ) 9>"$GIT_LOCK"
}

_git_rebase_cleanup() {
  # Yarım kalmış rebase repoyu kilitli bırakmasın (sonraki tüm işler patlar).
  # Önce --abort (HEAD'i ve autostash'i geri koyar); o da olmazsa --quit (çalışma
  # dizinine DOKUNMAZ, autostash'i stash listesine kaydeder).
  if [ -d .git/rebase-merge ] || [ -d .git/rebase-apply ]; then
    git rebase --abort >/dev/null 2>&1 || git rebase --quit >/dev/null 2>&1
  fi
}

git_sync() {
  (
    _git_lock_take || exit 1
    git fetch -q origin main 2>&1 | sed 's/^/    [fetch] /'
    [ "${PIPESTATUS[0]}" -eq 0 ] || exit 1
    # Uzakta yeni bir şey yoksa rebase (ve autostash) hiç yapılmaz.
    git merge-base --is-ancestor origin/main HEAD 2>/dev/null && exit 0
    git rebase -q --autostash origin/main 2>&1 | sed 's/^/    [rebase] /'
    if [ "${PIPESTATUS[0]}" -ne 0 ]; then
      _git_rebase_cleanup
      exit 1
    fi
  ) 9>"$GIT_LOCK"
}

git_add_commit() {
  local msg="$1"; shift
  (
    _git_lock_take || exit 1
    # Her yol ayrı eklenir: biri yoksa (boş glob vb.) diğerleri yine eklenir.
    for p in "$@"; do git add -- "$p" >/dev/null 2>&1; done
    git diff --cached --quiet && exit 0
    git commit -q -m "$msg"
  ) 9>"$GIT_LOCK"
}

# PUSH ÖNCESİ BUILD KAPISI (2026-11-02). Neden: getiri verisinden 10 yıl satırı düşünce /altin-dolar-borsa sayfası
# build'i çökertti; veri commit'i yine de push'landı → Cloudflare derlemesi sessizce başarısız oldu, canlı site sabahki
# sürümde kaldı, SEO denetimi yarım dist'i tarayıp "87 kırık link" maili attı. Artık bu sunucudan hiçbir push
# `npm run build` geçmeden gitmez; kırıksa Kaan'a mail (günde bir). Atlama: SKIP_BUILD_GATE=1 (deploy-push.sh zaten build alır).
_build_gate() {
  [ "${SKIP_BUILD_GATE:-}" = "1" ] && return 0
  local repo log
  repo="$(git rev-parse --show-toplevel 2>/dev/null)" || return 0
  [ -f "$repo/package.json" ] || return 0
  log="$repo/logs/deploy-build.log"
  # log kilit alındıktan sonra açılır; kilit zaman aşımı (75) build hatası sayılmaz (sahte "KIRIK" maili yok)
  ( cd "$repo" && PATH="/root/.local/bin:/usr/local/bin:/usr/bin:/bin:$PATH" \
       flock -E 75 -w 600 /tmp/parafomo-build.lock sh -c 'nice -n 10 npm run build > "$1" 2>&1' _ "$log" )
  local rc=$?
  [ "$rc" -eq 0 ] && return 0
  if [ "$rc" -eq 75 ]; then
    echo "    [build-kapısı] build kilidi 600 sn'de boşalmadı (başka build sürüyor) — push sonraki çalışmaya kaldı" >&2
    return 1
  fi
  echo "    [build-kapısı] npm run build KIRIK — push ENGELLENDİ (canlı site eski sürümde kalır). Son satırlar:" >&2
  tail -12 "$log" | sed 's/^/    [build] /' >&2
  python3 "$repo/agent/notify.py" alert --key build-kirik --subject "parafomo: site build KIRIK — push engellendi" \
    --body "$(printf 'Push, build geçmediği için engellendi (scripts/lib/gitsync.sh build kapısı).\n\n%s\n\nDüzelt: npm run build hatasını gider, sonra: bash scripts/deploy-push.sh' "$(tail -25 "$log")")" >/dev/null 2>&1 || true
  return 1
}

git_push_retry() {
  local branch="${1:-main}"
  # push edilecek yerel commit varsa önce build kapısı (git kilidi DIŞINDA: build 15 sn, diğer işler commit'ine devam etsin)
  if [ -n "$(git log "origin/$branch..HEAD" --oneline 2>/dev/null)" ]; then
    _build_gate || return 1
  fi
  (
    _git_lock_take || exit 1
    git push -q origin "$branch" 2>&1 | sed 's/^/    [push] /'; [ "${PIPESTATUS[0]}" -eq 0 ] && exit 0
    echo "    [push] reddedildi (muhtemelen non-fast-forward) → rebase + tekrar"
    git fetch -q origin "$branch" && git rebase -q --autostash "origin/$branch" 2>&1 | sed 's/^/    [rebase] /'
    if [ "${PIPESTATUS[0]}" -ne 0 ]; then _git_rebase_cleanup; fi
    git push -q origin "$branch" 2>&1 | sed 's/^/    [push] /'; [ "${PIPESTATUS[0]}" -eq 0 ] && exit 0
    echo "UYARI: push yine başarısız ($branch)"
    exit 1
  ) 9>"$GIT_LOCK"
}
