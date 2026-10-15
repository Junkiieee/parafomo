# Bu koşu: GÜNLÜK (operatör)

Planı haftalık koşu yazdı; senin işin onu **uygulamak**. Strateji tartışma, yeni bahis açma.

## Sıra
1. **Sağlık (önce bu):** Brief §3'te 🔴 GECİKTİ/HATA bir üretim hattı, yarım rebase, kırık build veya
   Claude durumu sorunu varsa → kök nedeni bul, düzelt, doğrula. Bu, plandaki görevden önce gelir.
   (Duraklatma/kota kaynaklı tek seferlik gecikme hata değildir — bir sonraki çalışmayı bekle.)
   Düzeltemiyorsan `agent/plan/user-tasks.md`'ye Kaan için tek net görev yaz.
1b. **SEO denetimi (brief §3b):** KRİTİK varsa (kırık link, yanlış kanonik, noindex+sitemap, Google başka kanonik
   seçmiş, canlıda 200 yok) → görevden ÖNCE düzelt, build + deploy, `python3 scripts/seo-audit.py` ile doğrula.
   KRİTİK yoksa koşu sonunda bütçe kalırsa en fazla BİR UYARI kümesini düzelt (ör. 10 uzun description, ya da bir
   "indekslenmemiş" yazıyı güçlendir/birleştir). Kural: GSC'de gösterim alan sayfanın title'ında baş sorguyu ve
   yılı KORU — yalnız kuyruğu kısalt; 14+ gündür indekslenmeyen genel "nedir" yazısını şişirme → ya özgün veri/tablo
   ekle ya güçlü bir sayfaya birleştir (worker REDIRECTS 301). Ne düzelttiğini rapora yaz.
2. **Yarım iş:** Brief §14'te `agent-wip` stash'i varsa incele (`git stash show -p stash@{N}`):
   değerliyse `git stash pop` + bitir; değilse `git stash drop`.
3. **Görev:** `agent/plan/week.md` → "Görev kuyruğu"ndaki EN ÜSTTEKİ `- [ ]` görevi al ve UÇTAN UCA bitir:
   kod/içerik → `npm run build` → commit → `bash scripts/deploy-push.sh` → canlıda doğrula (curl).
   - Bitince satırı `- [x] ... → sonuç (link/sayı) · YYYY-MM-DD` yap.
   - Tek gecede bitmeyecek kadar büyükse: ilk anlamlı parçayı bitir + yayınla, kalanını yeni satır olarak
     kuyrukta bırak.
   - Görev artık anlamsızsa (veri değişti, zaten yapılmış): `- [-] ... — iptal: gerekçe` yap, sıradakine geç.
4. **Sonraki görevler:** önceki görev temiz bittiyse ve bütçe varsa sıradakine geç (gecede en fazla 3 görev).
   `week.md` görev kuyruğunda yapılabilir `[ ]` kalmadıysa (ya da kalanlar TARİHLİ ve günü gelmediyse)
   `agent/plan/keyword-map.md` "Sıradaki" bölümündeki ilk `- [ ]` satırını görev olarak al (aynı kabul ölçütü:
   canlı + FAQPage + Footer/`/hesaplama-araclari/` linki + resmî kaynak) ve bitince orada `[x]` yap.
5. **Olay sonrası güncelleme (her koşu, 1-2 yazı):** Slug'ında `<ay>-2026` geçen önizleme yazılarından
   olayı GEÇMİŞ ve `updatedDate`'i olmayanları bul (ör. "TCMB Ekim kararı", "Eylül CPI"). Her birine:
   gerçekleşen sonucu RESMİ kaynaktan doğrula (TCMB/BLS/BEA/ECB/TÜİK — veri dosyasında varsa oradan,
   ör. `data/tcmb-2026.json`) → başlığa sonucu yaz ("…Açıklandı: Faiz %37'de Sabit") → gövdenin başına
   `> **Karar/veri açıklandı (tarih):** … ([kaynak](url)) … Sıradaki: [link]` kutusu → ilgili SSS cevabını
   geçmiş zamana çevir → `updatedDate`. Örnek: `tcmb-eylul-2026-faiz-karari-ppk-beklentiler.md` (10-13).
   Neden: geçmiş olay yazısı gelecek zamanla kalınca sıra 5-10'da bile 0 tık alıyor (GSC 2026-10-13).
6. **Konu kuyruğu:** `agent/plan/content-queue.md`'de bekleyen (`- [ ]`) konu < 3 ise 3-5 konu ekle.
   Kaynak: **brief §9c fırsat listesi** (eylemi `YENI_YAZI`/`YENI_ARAC` olan, hacmi ≥ 5 satırlar) →
   hacimli takvim olayı (ailesi §9c'de ≥ 5, örn. TCMB faiz kararı) → aktif bahsin kümesi.
   Hacmi ölçülmemiş ya da < 5 olan sorguya yazı açma (Autocomplete önerisi tek başına talep kanıtı değil).
   Her satır: başlık önerisi · hedef sorgu (hacim N) · neden şimdi (1 cümle) · iç-link hedefi.
7. **Rapor + commit:** `agent/state/report.md`'yi yaz; plan/kuyruk değişikliklerini commit'le.

## Yapma
- Yeni bahis açma, `learnings.md`'yi yeniden yazma (haftalık iş). Kesin yeni bir ders öğrendiysen
  sona TEK madde ekleyebilirsin (tarih + kanıt).
- Plan dışı kozmetik iş (hashtag döndürme, başlık rötuşu, IG caption denemesi) — kanıtlanmış düşük kaldıraç.
- Mikro-deney açma; "ölçeceğim" diye iş bölme.

## report.md biçimi (≤25 satır)
```
## Bugün yaptım
- <görev> → <sonuç, canlı link, sayı>
## Sağlık
- <sorun ve çözüm — yoksa "üretim hatları sağlıklı">
## Sıradaki
- <kuyrukta bir sonraki görev>
## Not (opsiyonel, yalnız önemliyse)
```
