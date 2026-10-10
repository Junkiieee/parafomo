# Hafta planı — 2026-10-08 → 2026-10-14
_Haftalık koşu: 2026-10-08 · model claude-opus-5-5_
<!-- plan-date: 2026-10-08 -->

## Durum
- Gerçek erişim (Direct hariç) son 7g **43** (önceki tam hafta 202640: 51, rekor; 4 hafta önce 202637: 41).
  GSC 7g 36 tık / 1.258 gös · 28g 105 tık / 6.064 gös → **düz platoda** (~40 tık/hafta, ~%0,6 hedef).
  Motor hâlâ getiri+takvim sayfaları: /altin-getiri 31 tık, /dolar-getiri 14, /enflasyon-takvimi 9 (28g).
- **Kök neden bulundu:** Google sitemap'i en son **2026-07-03**'te indirmiş. 10-07'de açılan 40 halka arz
  sayfası "URL is unknown to Google" (0 gös). 10-08'de API ile yeniden gönderildi + `scripts/gsc-sitemap.py`
  artık günlük öğrenme döngüsünde URL kümesi değişince/7 günde bir otomatik gönderiyor.
- YouTube 51 abone (düz), 280 video. Ağu+ veride sonuç metriği net: viral **shock_number medyan 500**
  izlenme (n=11) vs backtest 96 (n=13). 09-30'daki AVD-vekil rebalansı geri alındı (rotasyon aşağıda).
- Gelir/marka: AdSense kapalı (Kaan kararı, trafik bekleniyor) · bülten formu hâlâ bozuk (0 abone) ·
  Telegram 2 üye · IG ölçülemiyor.

## Bahisler
- **B261006-1 — Halka arz şirket sayfaları** · GSC /halka-arz/* ≥500 gös + ≥15 tık/hafta · 2026-11-03
  (sitemap düzeltmesiyle saat 10-08'de yeniden başladı)
- **B261006-2 — Getiri kümesini genişlet** · küme 28g tık 45 → ≥85 · 2026-11-03 (yeni sayfa yok → T1-T3)
- **B261006-4 — YouTube video kalite reformu** · 10-07+ videolarda 7g medyan ≥200 izlenme + ≥8 abone/hafta ·
  2026-10-28 (10-08: viral DOW_FMT shock×3/myth×2/single×2, backtest viralden çıktı)

## Görev kuyruğu (günlük koşu en üstteki [ ]'yi alır)
- [x] T1 (B261006-2) — → canlı https://parafomo.com/gumus-getiri/ (10y TL +%5.215 vs altın +%5.026, altın/gümüş oranı 68,8, Dataset şeması); hub'a gümüş sütunu, /altin-getiri'den link, metodoloji, daily-content veri adımı · haftalık koşu 2026-10-08 — **/gumus-getiri sayfası:** `scripts/silver-returns.py` (gold-returns.py kalıbı; Yahoo
  SI=F × USDTRY=X; gram gümüş TL = ons/31.1035 × kur; YTD + 1/3/5/10 yıl TL/USD getirisi; ağ hatasında mevcut
  veriyi koru) → `data/gumus-getiri.json` (+ gerekiyorsa `public/` kopyası) → `src/pages/gumus-getiri.astro`
  (altin-getiri.astro kalıbı; "gümüş mü altın mı" karar bölümü altın verisiyle yan yana) → /altin-dolar-borsa
  hub'ına gümüş satırı + /altin-getiri'den link → `daily-content.sh` veri adımlarına ekle.
  · Kabul: build geçer; `curl -s https://parafomo.com/gumus-getiri/` 200 ve tabloda 10 yıl satırı; hub'da gümüş.
- [x] T2 (B261006-2) — → canlı https://parafomo.com/euro-getiri/ (euro mu dolar mı tablosu + EUR/USD parite etkisi); hub'a euro, /dolar-getiri'den link · haftalık koşu 2026-10-08 — **/euro-getiri sayfası** (EURTRY=X; T1 kalıbı; "euro mu dolar mı" karar bölümü
  dolar-getiri verisiyle yan yana; /dolar-getiri ↔ /euro-getiri karşılıklı link; hub'a euro satırı; veri
  adımına ekle). · Kabul: canlıda 200 + hub'da euro + /dolar-getiri'de euro linki.
- [x] T3 (B261006-2) — → /bitcoin-getiri (10y $ +%11.002, en büyük düşüş −%75,6 2017-12→2019-01, risk kutusu, bitcoin mi altın mı); hub'a bitcoin, bitcoin-nedir yazısından link · haftalık koşu 2026-10-08 — **/bitcoin-getiri sayfası** (BTC-USD × USDTRY=X; aynı kalıp; volatilite/düşüş
  uyarısı + "yatırım tavsiyesi değildir"; YTD + 1/3/5 yıl (10 yıl veri varsa); en büyük düşüş (max drawdown)
  satırı; hub'a bitcoin satırı; /blog/bitcoin-nedir-nasil-alinir'den link). · Kabul: canlıda 200, hub'da bitcoin.
- [x] T4 (dağıtım/marka) — → RC oturumu 2026-10-08: API (`backend/app/routers/newsletter.py`, çift onay, KVKK onayı, bal küpü, rate-limit, RFC 8058 tek-tık çıkış) + form canlı + https://parafomo.com/bulten/ + haftalık gönderim `bash scripts/newsletter-send.sh` (cron pzt 05:30 UTC, `--dry-run` önizleme). Abone sayısı brief §12'de. Sıradaki bülten işi: formu daha görünür yerlere koy (yazı içi, getiri sayfalarının tablosunun hemen altı) — trafik az, dönüşüm noktası önemli. · eski tanım: **Bülten v1 — kendi altyapımızla (bozuk formu onar).** İzin geldi (10-07). Backend
  (`backend/`, protokol: `/root/.venvs/parafomo-api/bin/python` ile geçici DB'de test → `systemctl restart
  parafomo-api` → `curl -s https://api.parafomo.com/health`): `POST /newsletter/subscribe` (e-posta + KVKK
  onayı, IP rate-limit, Brevo SMTP ile çift onay maili), `GET /newsletter/confirm`, `GET /newsletter/unsubscribe`
  (token); YENİ `newsletter_subscribers` tablosu (mevcut tablolara DOKUNMA). `src/components/Newsletter.astro`
  bu uca bağlansın (başarı/hata mesajı; `action="#"` kalmasın). Gönderim betiği ayrı görev.
  · Kabul: canlıda abone ol → onay maili gelir → linkle DB'de `confirmed`; çık linki çalışır; build geçer.
- [x] T5 (AI asistan görünürlüğü) — → 2026-10-09: Dataset şeması + görünür "Son güncelleme · Kaynak" satırı 6 sayfaya eklendi (/altin-getiri, /dolar-getiri, /bist-getiri, /halka-arz-getiri, /halka-arz, /altin-dolar-borsa; gümüş/euro/bitcoin zaten vardı; takvim sayfalarında kaynak satırı zaten vardı) — canlıda doğrulandı, commit d59d0dd · 2026-10-09 — → 2026-10-08 RC: https://parafomo.com/llms.txt canlı. KALAN: getiri/takvim sayfalarında görünür "Son güncelleme · Kaynak" satırı + eksik `Dataset` şeması kontrolü. · eski tanım: `public/llms.txt` (site özeti + en değerli veri/araç sayfaları: getiri
  kümesi, takvimler, halka arz, hesaplayıcılar + kaynak/güncelleme notu); getiri ve takvim sayfalarında görünür
  "Son güncelleme: <tarih> · Kaynak: ..." satırı + `Dataset` şeması (yoksa). AI asistan trafiği 28g 20 (~%12).
  · Kabul: canlıda /llms.txt 200; 3 sayfada `grep -c '"Dataset"'` ≥1.
- [x] T6 (B261006-1) — → 2026-10-10: sitemap indirme **2026-10-09 08:46** (10-08 sonrası ✓); URL denetimi 6 örnek: 1 indeksli (albayrak, tarama 10-08), 2 "Discovered – not indexed", 3 "unknown". Ana sayfaya "Halka Arz Şirketleri" kutusu canlı (6 şirket sayfasına link; süren/yaklaşan → son 3 tamamlanan + getirisi → tarih bekleyenler günlük döner) commit 3ae1a67. Haftalık koşu indeks sayısını yeniden ölçsün · 2026-10-10 — **Halka arz sayfaları keşif kontrolü (10-12 sonrası):** `python scripts/gsc-sitemap.py
  --status` → indirme tarihi 10-08 sonrası mı? 5 şirket sayfasını brief'teki indeks durumuyla kontrol et. Hâlâ
  "unknown" ise: /halka-arz-getiri tablosundaki her şirket adını da kendi sayfasına linkle (şu an yalnız
  /halka-arz linkli) ve ana sayfaya "Yaklaşan halka arzlar" kutusu (→ 2026-10-08 RC: /halka-arz-getiri tablosundaki 12 şirket artık kendi sayfasına linkli — yalnız ana sayfa kutusu kaldı) (ilk 3, şirket sayfasına link) ekle.
  · Kabul: rapora indirme tarihi + indekslenen sayfa sayısı yazılır; gerekiyorsa linkler canlıda.

- [ ] T7 (SEO ölçüm, RC 10-10 sonrası) — **Kanonik + footer düzeltmesinin etkisini ölç (10-14 sonrası):**
  GSC'de son 7g sayfa listesinde sonda '/' olmayan URL satırı kaldı mı (`searchanalytics` page boyutu)?
  URL denetimi: /emekli-zammi-hesaplama, /bitcoin-getiri, /euro-getiri, /gumus-getiri, /bono-hesaplama
  durumu ("unknown" → indeksli mi?). 10 halka arz sayfası örneği. · Kabul: rapora sayılar yazılır.
- [ ] T8 (yeni niyet) — **Asgari ücret 2027 hazırlığı:** /asgari-ucret-hesaplama'ya "2027 asgari ücret ne zaman
  belli olacak" bölümü (Asgari Ücret Tespit Komisyonu süreci, geçmiş yılların açıklanma tarihleri — YALNIZ
  doğrulanmış kaynakla; tahmini rakam YAZMA) + SSS; başlıkta 2027'yi öne al. Aralık'ta resmi rakam gelince
  aynı gün güncelle (kullanıcı görevi değil, ajan WebSearch ile resmi açıklamayı doğrular).
  · Kabul: build geçer, canlı sayfada 2027 bölümü + FAQPage'de yeni soru.
- [ ] T9 (B261006-1) — **Emekli zammı sayfası iç linkleri:** emeklilik kategorisindeki yazılar
  (bes-bireysel-emeklilik-mantikli-mi, emeklilik-icin-ne-kadar-para) + net-maas/asgari-ucret sayfalarından
  bağlamsal link (footer zaten var; metin içi link ayrıca). · Kabul: ≥4 metin içi link canlıda.

## Bakım / ürün
- [ ] P1 (portföy) — ⏸ 2026-10-09 günlük koşu atladı: watchlist yeni DB tablosu ister (kırmızı çizgi 6 "şemayı değiştirme" — newsletter tablosu Kaan onayıyla açılmıştı) + ders "trafiksiz ürün cilası kayıt getirmez" (2 üye). Haftalık koşu karar versin. — `agent/plan/backlog-portfolio.md`'deki en üstteki açık madde (İzleme listesi / watchlist —
  sahip olmadan takip). Backend değişirse protokoldeki restart + /health. · Kabul: build geçer; canlı panelde
  izleme listesine ekle/sil akışı çalışır; backlog maddesi [x] + commit.
- [x] V1 (video kalitesi) — → 2026-10-09: viral-script.py shock_number istemine kazanan 3 kanca (kira %3 954 izl., 5.000 ton altın 935, çeyrek %10 924) + zorunlu number_source (rakam/hesap/kaynak); kaynaksız/muğlak rakam reddedilip yeniden üretilir, hesap satırı video açıklamasına eklenir; --dry-run modu; 3 dry-run senaryo raporda, birim testte kaynaksız rakam reddedildi · commit cbc4038 · 2026-10-09 — **shock_number kanca kalitesi + rakam doğrulaması** (format artık haftada 3 gün):
  `scripts/viral-script.py` shock_number istemine en çok izlenen 3 shock videonun (ör. kira-geliri-yuzde-2
  500 izl., ledger'dan bul) kanca + ilk 2 cümle kalıbını örnek olarak ekle; senaryo üretiminde shock rakamının
  bir hesap/kaynak satırı taşımasını zorunlu kıl (yanıltıcı başlık = kırmızı çizgi 4). İzole dene:
  `--dry-run`/hazırlık modunda 3 senaryo üret, eskisiyle yan yana rapora koy; rakam kaynaksızsa senaryo reddedilsin.
  · Kabul: 3 örnek senaryo raporda; kaynaksız rakam testi reddediliyor; commit.
- [x] V2 (marka) — → 2026-10-09: token force-ssl kapsamlıymış; channels.update ile kanal açıklaması (brand.md bio + konumlandırma + UTM li parafomo.com linkleri + IG/Telegram + tavsiye-değildir notu) ve anahtar kelimeler yazıldı, API ile doğrulandı · 2026-10-09 — **YouTube kanal kimliği:** kanal açıklaması brand.md konumlandırması + parafomo.com (UTM'li)
  + Telegram/Instagram, kanal anahtar kelimeleri. `channels.update` brandingSettings (OAuth `youtube.force-ssl`
  ise) ile dene; yetki yetmezse Kaan'a 3 adımlık görev yaz. · Kabul: kanal sayfasında yeni açıklama.

## Kullanıcı girdisi gelince (o gün en üste al)
- Müzik klasörü dolarsa (`/root/parafomo-media/music/`) → 1 videoda doğrula, rapora yaz.
- X API ödemesi açılınca → `scripts/post-x.py` (günlük veri kartı + yeni yazı), `deploy/crontab.txt` önerisi.
- R2 bilgileri → `/root/.config/parafomo/backup.env` (backup.sh otomatik kullanır).

## Notlar (günlük koşu için)
- **RC 2026-10-10 eklenen otomasyonlar** (kontrol: `python3 agent/health.py` → "Veri tazeliği"):
  kira-artis-update.sh (ayın 3-8'i; kira + TÜFE serisi), policy-decisions.sh (Fed/TCMB karar gecesi),
  indexnow.py (learn-daily). 22 Ekim TCMB ve 28 Ekim Fed sonrası sabah: sayfada karar görünüyor mu kontrol et;
  görünmüyorsa log'a bak (`logs/policy-decisions.log`) ve kaynağı düzelt — rakamı elle tahmin ETME.
- **Headless izin tuzağı:** 10-07 koşusunda 13 komut reddedildi — `for`/`until` döngüsü, `x=...` değişken
  atama, `awk`, `cd /tmp && ...`, heredoc, `bash -n /mutlak/yol`. Döngü/çok adımlı kontrolü tek
  `python3 -c "..."` ya da repo içi küçük bir `.py` dosyasıyla yap; yolları göreli ver (`bash scripts/...`).
- Konu kuyruğu yayın tarihine göre sıralı (bkz. content-queue.md); bir gün atlanırsa kuyruk kayar — TCMB
  yazısı 19-21 Ekim'den ÖNCE yayınlanacak gibi olursa önüne evergreen bir konu ekle.
- Video rotasyonu 10-08'de değişti; `scripts/learn/winner.py viral.format` bir kazanan döndürürse onu ezer
  (şu an "berabere"). Shock rakamı mutlaka gerçek/hesaplanabilir olmalı.

## Biten / iptal (bu hafta)
- [x] (haftalık koşu) GSC sitemap teşhisi + yeniden gönderim + `scripts/gsc-sitemap.py` günlük otomasyonu · 2026-10-08
- [x] (haftalık koşu) V1-eski (format kanıt tablosu) haftalık koşuda yapıldı → rotasyon kararı uygulandı · 2026-10-08
- Geçen haftadan biten: T1 halka arz sayfaları, M1 güven sayfaları, T2 halka arz SEO (10-07).
