# ParaFOMO Ajanı v2

Özerk büyüme ajanı + üretim hatları. Kuruluş: 2026-10-06 (v1: 2026-08-02 → 2026-09-30, `archive/v1/`).

## Neden yeniden kuruldu (v1 otopsisi, Eylül 2026)
| v1 sorunu | v2 çözümü |
|---|---|
| 30 gecenin ~16'sında ajan hiç çalışmadı (Pro kota limiti ×9, OAuth süresi dolması ×8 gece) | Opus haftada 1 (Perşembe, kota sıfırlamasından sonra), günlük koşu Sonnet; oturum limitinde bekle + `--resume`; `claude setup-token` desteği; auth/kota düşünce anında e-posta |
| Script'lerin her `claude -p` çağrısı ~25K token bağlam + kullanıcı ayarındaki opus/xhigh'ı miras alıyordu | `scripts/lib/llm.py` tek kapı: araçsız/ayarsız yalın çağrı (~7K), model+efor açık, kota durum dosyası |
| LLM hata metni ~20 IG gönderisine caption olarak çıktı | kapı hata metnini asla içerik olarak döndürmez (+ eski ikinci emniyet sürüyor) |
| Başarısız gecelerde dünkü rapor yeni tarihle tekrar mail atılıyordu | rapor yalnız bu koşuda yazıldıysa kullanılır; yoksa "ajan çalışamadı + neden" maili |
| 59 deneyin 50'si "sonuçsuz" (düşük trafikte mikro-deney ölçülemez) | ≤3 büyük **bahis**, 2-4 hafta, toplu metrik; günlük mikro-deney yok |
| "Her gece her kanala iş" + "her gece video Ar-Ge" zorunluluğu → kozmetik meşguliyet | haftalık plan + görev kuyruğu; portföy ve video kalitesi haftada ≥1 görev |
| 90 KB digest + 19 KB prompt her gece | ~15-25 KB brief (`brief.py`), kısa promptlar |
| ~12 cron aynı repoda eşzamanlı git → yüzlerce pull/push hatası | `scripts/lib/gitsync.sh` flock kilidi; viral'ın 5 boş slotu git'e dokunmaz |
| `--dangerously-skip-permissions` ile tam yetki | `acceptEdits` + açık izin listesi (`allowed-tools.txt`); dışı otomatik ret, e-postada görünür |
| Disk %83 (2 GB eski video + dist kopyası + 2.8 GB önbellek) | `scripts/maintenance.sh` günlük temizlik |

## Mimari
```
cron ──► agent/run.sh auto (03:00 UTC)
           ├─ runlog.py pick-mode ─► weekly (Perşembe) | daily
           ├─ brief.py ─► state/brief.md   (GA4+GSC+YT KPI, sağlık, plan, bahisler, dersler, fırsatlar)
           ├─ prompts/core.md + prompts/<mod>.md + brief ─► claude -p (izin listesiyle)
           ├─ artık temizliği (commit'lenmemiş ajan işi → git stash "agent-wip-*")
           ├─ build kapısı ─► git push (Cloudflare otomatik deploy)
           └─ notify.py report ─► e-posta (KPI + ajan raporu + sağlık + günün yayın takvimi + görevler)

eller (deterministik cron'lar, ajan olmadan da çalışır) — deploy/crontab.txt
  viral/blog→video/Manim Shorts + IG Reels · blog (content-queue'dan) · IG kartları · veri · öğrenme · bakım
```

| Dosya | Görev |
|---|---|
| `run.sh` | orkestratör (kilit, mod, brief, kota kapısı, claude, resume, stash, build kapısı, push, mail) |
| `prompts/core.md` · `daily.md` · `weekly.md` | ajan talimatları (ortak · operatör · stratejist) |
| `brief.py` | token'sız durum özeti + `memory/kpi-daily.jsonl` KPI serisi |
| `health.py` | üretim hatlarının son başarısı, Claude/git/disk/site/API durumu |
| `pubplan.py` | crontab'dan günün yayın takvimi (e-postada) |
| `bets.py` | bahis defteri (`memory/bets.jsonl`, aktif ≤3) |
| `runlog.py` | mod seçimi, koşu kaydı (`memory/runs.jsonl`), sonuç sınıflandırma |
| `notify.py` | e-posta: `report` (günlük/haftalık) · `alert` (günde 1/tür) |
| `allowed-tools.txt` | ajanın izinli araç/komut listesi |
| `plan/week.md` | haftanın bahisleri + görev kuyruğu (günlük koşu en üstteki `[ ]`'yi yapar) |
| `plan/content-queue.md` | blog konu kuyruğu (`scripts/daily-content.sh` en üsttekini yazar) |
| `plan/user-tasks.md` | Kaan'a bağlı işler (≤3) |
| `plan/backlog-portfolio.md` | portföy ürünü backlog'u |
| `plan/brand.md` | marka kitabı (konumlandırma, ses, görsel kimlik, imza ürünler, gelir ilkeleri) |
| `memory/learnings.md` | düzenlenmiş kalıcı dersler (≤40, haftalık yeniden yazılır) |
| `state/` (git dışı) | brief, prompt, report, run-status, kpi |
| `logs/` (git dışı) | koşu JSON'ları, build logları |

## Komutlar
```bash
agent/run.sh --dry                 # brief + prompt üret, beyni çağırma
agent/run.sh daily                 # elle günlük koşu (weekly ile haftalık)
python3 agent/health.py            # üretim sağlığı
python3 agent/pubplan.py --all     # bugünün takvimi (arka plan işleri dahil)
python3 agent/bets.py list --all   # bahisler
python3 agent/notify.py report --dry
python3 scripts/lib/llm.py --status   # Claude kota/oturum durumu
bash scripts/backup.sh                # portföy DB + ayar yedeği → /root/parafomo-backups (bakım her gün çağırır)
crontab /root/parafomo/deploy/crontab.txt   # cron'u kur/yenile
```

## Knob'lar (cron satırında env olarak)
`AGENT_DAILY_MODEL=sonnet` · `AGENT_DAILY_EFFORT=medium` · `AGENT_DAILY_BUDGET=4` ·
`AGENT_WEEKLY_MODEL=opus` · `AGENT_WEEKLY_EFFORT=high` · `AGENT_WEEKLY_BUDGET=10` · `AGENT_WEEKLY_DOW=4` ·
`CONTENT_MODEL=sonnet` · `CONTENT_EFFORT=medium` · `CONTENT_MAX_BUDGET=2.5`
(Bütçeler API-eşdeğeri dolar; Pro aboneliğinde gerçek ödeme yok, kotayı sınırlar.)

## Kalıcı Claude token'ı (önerilir)
```bash
claude setup-token            # tarayıcıda onayla, token'ı kopyala
printf 'CLAUDE_CODE_OAUTH_TOKEN=%s\n' '<token>' > /root/.config/parafomo/claude.env && chmod 600 /root/.config/parafomo/claude.env
```
`run.sh`, `daily-content.sh` ve `llm.py` dosya varsa otomatik kullanır.

## Duraklatma / sürdürme
```bash
crontab -l > /root/crontab-yedek-$(date +%F).txt && crontab -r     # duraklat
crontab /root/parafomo/deploy/crontab.txt                          # sürdür
```
