# ParaFOMO — Kalıcı dersler (düzenlenmiş)

_v1'in 59 deneyi + 2 aylık KPI'ından damıtıldı (2026-10-06). Haftalık koşu bu dosyayı yeniden yazar:
≤40 madde, tekrar yok, kanıtıyla. Ham geçmiş: agent/archive/v1/memory/._

## Kanıtlı çalışan
- **Yeni arama niyeti açan veri/araç sayfaları tek kanıtlı web kaldıracı.** 08-11→08-24 arası 6 araç/takvim
  sayfası + 08-28→09-02 getiri kümesi (altın/dolar/BIST getiri + altın-dolar-borsa hub) sonrası GSC tık
  ~4 → ~40/hafta, gerçek erişim ~3 → ~45-50/hafta. Tekil sayfa etkisi ölçülemez; toplu motor olarak izle.
- **Tarihsel getiri / karar niyeti en temiz yeni yüzeyi açar:** /altin-getiri 28 günde 32 tıkla en çok
  tıklanan sayfa (poz 6,7); /dolar-getiri 10 tık; organik giriş sayfalarının başında bunlar (2026-10-06).
- **Zamanlı makro açıklayıcılar** (olaydan 1-3 gün önce: ABD işsizlik/CPI/NFP/PCE, TCMB kararı) en iyi
  blog sayfaları: abd-issizlik-verisi-altin-dolar-etkisi 28g 12 tık; tcmb-ekim-2026 5 tık/25 gös.
- **Takvim/zamanlama sayfaları** tam eşleşen sorguda ~1 haftada page-1 sınırına gelir (fed-faiz-takvimi
  poz ~10-11, 440 gös/28g) AMA talep mevsimseldir (tcmb/enflasyon/kira takvimleri olay gününe yakın
  canlanır) — olay gününe hizalı ölç, düz pencerede "kaybeden" sanma.
- **AI asistanlar gerçek trafiğin ~%10-12'si** (28g: 20 kullanıcı / 172) — net tablo + kaynak + tarih
  içeren sayfalar alıntılanıyor; büyüyen kanal.

## Kanıtlı çalışmayan (tekrar deneme)
- **Mevcut sayfayı on-page dürtmek** (iç-link, sinonim, FAQ, tazelik, cannibalization düzeltmesi, exact-match
  yeni yazı) 5-7 günde pozisyon oynatmadı — 6+ teyit (NFP, Fed, endeks fonu, Fed-sinonim, Jackson Hole,
  abd-faiz-dolar). Darboğaz dış otorite / arama niyeti.
- **Haber/timing head-term'leri** (ör. "fed faiz kararı") page-1'i haber siteleri tutuyor; açıklayıcıyla girilmez.
- **Canlı değer/fiyat sorguları** (altın fiyatları, dolar endeksi) için ayrı sayfa yeni yüzey açmadı —
  büyük siteler domine ediyor; blog açıklayıcısı zaten sıralanıyorsa yeni sayfa açma.
- **Video mikro-düzenlemeleri** (fade, açılış karesi, micro-cut, bold-claim kanca, seamless-loop,
  contradiction-hook, SFX — 11 deneme) ölçülebilir fark yaratmadı; video başı medyan izlenme Tem→Eyl
  ~100-120 düz. Düşük n'de retention mikro-optimizasyonu çıkmaz sokak.
- **Elle paylaşım gerektiren dağıtım** (Reddit/Ekşi taslakları): 26+ taslak paylaşılmadı, referral 0.
- **IG caption/hashtag/CTA denemeleri** ölçülemedi (insights izni yok, gönderi başı 0-2 beğeni).
- **Shorts→site hunisi** ~0 (59K toplam izlenme → 28 günde 3 "Organic Video" kullanıcısı).
- **Trafiksiz ürün cilası:** portföy ürünü sağlam ama prod'da ~2 kayıt — UX iyileştirmesi kayıt getirmez,
  önce trafik.

## YouTube
- Viral format medyan izlenmesi (son 45g, 2026-10-06): shock_number 250 (n=8) · single_concept 159 (5) ·
  myth 150 (8) · news_reaction 56 (11) · backtest_return 49 (3). Ağu+ geniş pencere: shock 158 · backtest 110
  · myth 99 · single 83 · news 73 · comparison 62. Farklar istatistiksel olarak zayıf (learn/decide "berabere").
- 09-30'da rotasyon "65% AVD kapısı" vekil metriğine göre shock/news'ten backtest/myth'e kaydırıldı; ama
  doğrudan sonuç metriği (izlenme) shock'u öne koyuyor → kararı izlenme@7g + abone kazanımıyla doğrula.
- Kazanan temalar: altın + kayıp korkusu ("paran sessizce eriyor"), otorite delme. Blog→Short medyan ~124;
  tam-Manim varyantı ~87 (Manim tek başına izlenmeyi artırmadı).
- 276 video → 51 abone (izlenme→abone %0,09). YPP için 1000 abone + 10M Shorts izlenmesi/90g gerekir;
  şablon/AI seri üretim "özgün olmayan içerik" incelemesine takılabilir.

## Kısıtlar ve çevre
- **Claude Pro kotası:** haftalık kota Çarşamba 22:00 UTC sıfırlanır + 5 saatlik pencere. v1'de Eylül'ün
  ~16 gecesi limit/OAuth yüzünden boş geçti (14-21 Eyl 8 gece OAuth süresi dolmuş, kimse fark etmedi;
  ~20 IG gönderisi hata metniyle yayınlandı). Kalıcı çözüm: `claude setup-token`.
- Dış veri kaynakları sessizce bozulur (Truncgil v4/v3 boş/bozuk JSON) → her fetch degrade edebilmeli;
  Yahoo yedek. Investing.com 403 → takvim ForexFactory + TÜİK kuralıyla.
- GSC ~2-3 gün gecikmeli; kısmi hafta düşüşü artefakttır (v1 bunu iki kez "çöküş" sandı).
- Deploy: push → Cloudflare otomatik build (yerel build ~15 sn). IG Graph API JPEG + public URL ister
  (GitHub raw / `media` dalı); 9004 geçici hata tekrar denemeyle geçer.
- **Telegram kanalı 2 üye** (2026-10-06): kanala otomatik blog/video paylaşımı şu an dağıtım değeri ~0;
  büyütülmeden kaldıraç sayılmaz. Site bülten formu 2026-10-06'ya kadar `action="#"` idi (kimse abone olamadı).
- Sunucu 2 çekirdek / 3,7 GB RAM / GPU yok: yerel ağır TTS (XTTS) çalışmaz; video render CPU'yu doyurur.
