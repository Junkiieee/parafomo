# Video yönü — 2026-10-30 (Kaan kararı: "parafomonun kullanım stilini değiştiriyoruz")

**Karar:** ParaFOMO'nun görsel dili artık kodla çizilmiş animasyon (`scripts/anim/`). Eski stok-video / Manim kartı /
statik görsel kart üretimi emekli. Shorts, Reels ve uzun videolar bu dille yapılır. Ajan: video işlerini bu dosyaya
göre seç; eski motora (shorts-build-v4) yalnız yeni motor çökerse yedek olarak düşülür.

## İki görsel dil
1. **Veri animasyonu (izometrik + kaplamalar)** — günlük Shorts/Reels. `scripts/anim/scenes.js` sahneleri (büyük rakam,
   patlatılmış katman, sütun, karşılaştırma, adımlar, ikonlu cümle, kapanış), `skins.js` 8 kaplama, dönüş `skins.json`.
   Sahne planı gece hazırlıkta LLM'le (`anim_from_scenario.py`), sayı kapısı: ekrandaki rakam o an konuşulan cümlede geçer.
2. **"Ekonomi Makinesi" (el çizimi, insanlı — referans: Ray Dalio "How The Economic Machine Works")** — haftalık seri.
   `scripts/anim/kits/dalio.js` (poz verilebilen figür + eşyalar + çizilerek beliren grafik). İlk parça:
   `pieces/dalio-enflasyon` (Short, 36 sn).

## Kanallar
- **YouTube Shorts:** günde 2 güçlü video (3-4 değil). Öncelik: olay günleri (`event-short.py`) > blog konusu > viral format.
- **YouTube uzun:** haftada 1 "Ekonomi Makinesi" bölümü, 8-10 dk (orta reklam), aynı bölümden 2-3 Short kesit.
  Konu sırası: enflasyon → faiz nasıl çalışır → kredi/borç döngüsü → dolar kuru neden yükselir → maaşın anatomisi
  (vergi/SGK) → emekli zammı nasıl hesaplanır (Ocak dalgasından önce) → kira artış oranı → altın neden değerli.
- **Instagram:** eski görsel gönderiler DURDU (altin-daily / bist-daily ×2 / halka-arz-ig cron'ları 2026-10-30 KAPALI).
  Kaan eski gönderileri uygulamadan arşivliyor. Günde en çok 2 Reel (yeni stil).
- **Facebook:** Reels aynı videolar (değişiklik yok).
- **Kanal temizliği:** 2026-10-30'da son 90 günde 0 izlenmeli 23 video gizlendi (liste ve geri alma:
  `/root/parafomo-data/yt-private-plan-20261030.json`). 2026-11-30'da yeniden bak; izlenme alanlar açık kalır.

## Teknik sıra (V = video işi)
- [ ] V1 (Kaan kararı) — kaplama dönüşü seçimi → `scripts/anim/skins.json` (şimdilik yalnız iso).
- [ ] V2 (Kaan kararı) — ses zinciri A/B (EQ + de-esser + kompresör) → evet ise anim_build anlatımına ekle.
- [ ] V3 — Instagram Reels günlük üst sınır 2 (instagram-reel.py; fazlası yalnız YouTube/FB).
- [ ] V4 — Dalio kitini otomatik hatta bağla: LLM sahne planı → karakterli sahne şablonları (alışveriş, para yağmuru,
  kuyruk, fiyat etiketi, grafik, banka, ev, maaş bordrosu). Kabul: bir senaryodan insansız elle müdahalesiz Short.
- [ ] V5 — uzun video 16:9: lf_ hattının görsel katmanı anim + Dalio'ya taşınır; "Ekonomi Makinesi #1: Enflasyon" 8-10 dk.
- [ ] V6 — ölçüm: meta `engine: anim` etiketi; 14 gün sonra yeni/eski kıyas (izlenme, ort. izlenme %, abone/1000 izlenme).
  Hedef: abone/1000 izlenme ≥ 2 (şu an ~0,8).
- [ ] V7 — HyperFrames blok testi (data-chart, milestone-reveal; sunucu boştayken, yük korumasıyla).
- [ ] V8 — SFX katmanı (Kenney CC0 + kodla üretilen efekt), sahne kesmeleri müzik vuruşuna (librosa).

## Sunucu nezaketi (Kaan: aynı sunucuda başka işler de var)
Render hep `nice 19` + Chromium alt süreçleri 30 karede bir renice + 1 dk yük > 2,5 ise 20 dk'ya kadar bekler.
Ağır işler (uzun video render) gece saatlerine konur.
