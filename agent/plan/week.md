# Hafta planı — 2026-10-15 → 2026-10-21
_Haftalık koşu: 2026-10-15 · model claude-opus-5-5_
<!-- plan-date: 2026-10-15 -->

## Durum
- Gerçek erişim (Direct hariç) son 7g **57** (28g 183) · son tam hafta 202641: **32** (202640 rekor 51; 4 hafta
  önce 202637: 41) → plato, hedefin ~%0,8'i. GSC 7g 24 tık / 1.092 gös (202641: 17 tık, 202640: 40). Düşüş
  sıralama kaybı değil, olay dalgasının sönmesi: /altin-getiri W38 21 tık → W39-41 3-5 tık, sıra p6-8 sabit.
- **Teşhis (bu koşu, GSC 28g):** hesaplayıcılarımız baş sorgularında p57-100 (kira artış, kıdem, işsizlik, altın
  hesaplama, mevduat), başlıklar sorguyu zaten içeriyor → otorite kilidi. Yeni sayfalar ise **2027 / gelecek yıl**
  sorgularında ilk haftada p4-11 (yeniden değerleme p11, trafik cezaları p9, MTV p8,7, harç p4). Kasım-Ocak zam
  sezonu bu sorguları 5-10x büyütüyor → bu haftanın ağırlığı 2027 kümesi + hacmi ölçülmüş yeni araçlar.
- Kuyruk konuları Trends'le ölçüldü: "bitcoin mi altın mı" 0,1 ve "mevduat mı altın mı" 0 → iptal; yerine
  hacimli 6 konu (asgari ödeme 30↑, para piyasası fonu 35↑, altın hesabı 38, kredi yapılandırma 50, damga vergisi 86).
- YouTube 53 abone (+2/hafta), 300 video; reform sonrası medyan 84 → video bahsi **lost**. Bülten 1 onaylı abone,
  Telegram 2, AdSense kapalı (Kaan kararı). Görev Masası headless'ta HÂLÂ yüklenmiyor (bkz. user-tasks).

## Bahisler
- **B261015-1 — Fırsat motoru: 2027 zam sezonu + hacimli yeni araçlar** · zam/araç kümesi 7g ≥400 gös + ≥10 tık
  (baz 24 gös / 0 tık) · değerlendirme 2026-11-12
- **B261006-1 — Halka arz şirket sayfaları** · /halka-arz/* ≥500 gös + ≥15 tık/hafta (şimdi 100 / 5) · 2026-11-03
- **B261006-2 — Getiri kümesi** · 28g ≥85 tık (şimdi 48, düz) · 2026-11-03 — yeni görev yok, sonucu bekle
- Kapandı: B261006-4 (YouTube kalite reformu) → **lost** (medyan 84 vs hedef 200).

## Görev kuyruğu (günlük koşu en üstteki [ ]'yi alır)
Kural: her veri sayfasında rakamı resmi kaynaktan doğrula (WebSearch ≤6/görev); iki kaynak çelişirse o rakamı
YAZMA. Yeni sayfa = `src/data/tools.ts` kaydı (araç merkezi + blog "Bu konuda hesapla" kutusu + ana sayfa zam bölümü otomatik) + Footer "Hesaplayıcılar" linki + `scripts/og-images.py` CARDS + `image="/og/<slug>.png"` +
FAQPage (WebApplication şeması BaseLayout'tan otomatik) + ilgili 2 sayfadan metin içi link. `npm run build` → `bash scripts/deploy-push.sh`
→ `python3 scripts/wait-live.py https://parafomo.com/<slug>/`.

- [x] T1 (B261015-1) — → canlı https://parafomo.com/konut-kredisi-hesaplama/ (peşinat + kredi/değer, 1/2/3/5M × 60/120 ay tablo, ters hesap "taksitime göre kredi", BDDK 11364 (29.01.2026) metinsel — kaynaklar aralık verdiği için tablo YOK, 6502 md.37 erken ödeme %1/%2, KKDF/BSMV yok; faiz "örnek %2,5" — güncel ortalama bulunamadı, EVDS bekleniyor; footer + /kredi-hesaplama linki + OG) · commit 910ac9d · haftalık koşu 2026-10-15 — **/konut-kredisi-hesaplama yeni araç** · hedef: konut kredisi hesaplama (hacim 170), konut
  kredisi faiz oranları (19,6). İçerik: (a) hesaplayıcı — tutar, vade (ay), aylık faiz → taksit, toplam faiz,
  ödeme planı (mevcut `src/pages/kredi-hesaplama.astro` hesap mantığını yeniden kullan); (b) konut kredisinde
  KKDF/BSMV muafiyeti (resmi kaynakla doğrula); (c) kredi/değer (LTV) oranı sınırları — BDDK'nın GÜNCEL
  düzenlemesi (değişti; doğrulayamazsan bölümü koyma); (d) masraf kalemleri (ekspertiz, ipotek tesis, DASK,
  konut sigortası — tutar yazma, kalem + açıklama); (e) "2 milyon TL konut kredisi taksiti" tipi tablo: 1M/2M/
  3M/5M TL × 60/120 ay, sayfada kullanıcı faiz girer, tablo varsayılan faiz için "örnek faiz %X — TCMB haftalık
  ortalama konut kredisi faizi, <tarih>" (WebSearch ile TCMB/EVDS kaynaklı değer; bulamazsan "örnek faiz" de,
  güncel diye sunma). /kredi-hesaplama ↔ /konut-kredisi-hesaplama karşılıklı link.
  · Kabul: build geçer; canlıda 200, tablo + FAQPage; footer + /kredi-hesaplama'da link; OG kartı.
- [x] T2 (B261015-1) — → canlı https://parafomo.com/kidem-tazminati-hesaplama/#tavan-2027 (tavan tablosu 2025-H2 53.919,68 / 2026-H1 64.948,77 / 2026-H2 73.729,87 — TÜRMOB+2 kaynak; Ocak 2027 tahmini ≈80.621 ₺ = memur zammı %9,35; yeni `src/data/zam2027.ts` ortak modül (emekli sayfası çıktısı birebir aynı doğrulandı); `data/kidem-tavan.json` + health.py Ocak/Temmuz bekçisi; FAQ + başlık; emekli sayfasından link) · commit 081951d · haftalık koşu 2026-10-15 — **/kidem-tazminati-hesaplama: Ocak 2027 tavan tahmini** · hedef: kıdem tazminatı hesaplama
  (86), kıdem tazminatı tavanı (62; "2026" vekil 35, zirve Ocak 207). Sayfada `TAVAN = 73729.87` sabit kodlu →
  önce bu değeri ve Ocak 2026 tavanını resmi kaynaktan (Hazine ve Maliye/ÇSGB tavan genelgesi veya 2 büyük
  kaynak) doğrula; `data/kidem-tavan.json`'a taşı (dönem, tavan, kaynak). Yeni bölüm "Ocak 2027 kıdem tazminatı
  tavanı ne kadar olacak?": tavan memur maaş katsayısıyla güncellenir → tahmin = Temmuz 2026 tavanı × (1 + Ocak
  2027 memur zammı tahmini) — memur zammı tahminini /emekli-zammi-hesaplama'nın kullandığı veri/fonksiyondan al
  (aynı kaynak; elle yazma), açıkça "tahmin" de; geçmiş dönem tavan tablosu (2024-2026, doğrulananlar).
  Başlık: "Kıdem Tazminatı Hesaplama 2026 ve Ocak 2027 Tavan Tahmini". FAQ'ye "2027 kıdem tavanı" sorusu.
  /emekli-zammi-hesaplama'dan bu bölüme metin içi link. · Kabul: canlıda tavan tablosu + 2027 tahmin satırı +
  FAQPage'de yeni soru; build geçer.
- [x] T3 (B261015-1) — → canlı https://parafomo.com/emlak-vergisi-hesaplama/ (oranlar konut 1/2, işyeri 2/4, arsa 3/6, arazi 1/2 binde — 3 kaynak; 7566 s. Kanun geçici 23 "iki kat fazlasını geçemez" metniyle (2x/3x yorumu çelişkili → sayı yazılmadı); 2027-2029 artış = YD oranı (KPMG + hukuk bürosu) → 2027 tahmini data/yeniden-degerleme.json'dan otomatik ≈%27,83; taksit 30 Kasım; emekli/200 m² muafiyeti; DKV eşiği tek kaynak → yazılmadı; footer + OG + YD/MTV sayfalarından link) · commit 3eb40a2 · haftalık koşu 2026-10-15 — **/emlak-vergisi-hesaplama yeni araç** · hedef: emlak vergisi (297), emlak vergisi 2026
  (12), emlak vergisi hesaplama (6,7); 2. taksit son günü Kasım sonu → Kasım ortasına kadar canlı olmalı.
  İçerik: oran tablosu (konut/işyeri/arsa/arazi × büyükşehir/diğer — Emlak Vergisi Kanunu md. 8/18/24 ve 2026
  değişikliği; GİB/RG ile doğrula), 2026 yeniden takdir + artış sınırı kuralları (doğrulanmamışsa yazma),
  emekli/tek konut muafiyeti koşulları, taksit tarihleri, hesaplayıcı (vergi değeri × oran → yıllık + 2 taksit),
  "2027'de emlak vergisi ne kadar artar" — kanuni kural (takdir olmayan yıllarda vergi değeri YD oranının yarısı
  kadar artar mı? DOĞRULA) + `data/yeniden-degerleme.json` ile tahmin. Değerli konut vergisini ayrı satırda
  kısaca an (hacim düşük 1,8). · Kabul: canlıda 200, oran tablosu her satırında kaynak, hesaplayıcı çalışır, FAQPage.
- [ ] T4 (faiz kararı ~160) — **TCMB 22 Ekim: mevcut yazıyı güncelle, yeni yazı AÇMA** · TARİHLİ: 20 Ekim veya
  sonrası (öncesindeyse bir sonraki göreve geç). /blog/tcmb-ekim-2026-faiz-karari-ppk-beklentiler'e "Son durum
  (<tarih>)" bölümü: TCMB Piyasa Katılımcıları Anketi / AA Finans beklenti anketi (kaynaklı) + Eylül TÜFE %29,73
  bağlamı; başlığı "TCMB Faiz Kararı 22 Ekim 2026: Beklenti ve Senaryolar" yap. SONUÇ KUTUSU ARTIK OTOMATİK (RC 10-18): yazıda
  `sonuc: "tcmb:2026-10-22"` + `sonucBaslik` var → karar 22 Ekim 11:25 UTC'de data/tcmb-2026.json'a yazılınca deploy'la
  kutu + "Açıklandı: Politika Faizi %X" başlığı kendiliğinden gelir; ELLE KUTU EKLEME, karar sonrası başlığı
  elle değiştirme (sonucBaslik devreye girer; karar öncesi başlık değişikliği serbest). 23 Ekim sabahı: kutunun canlıda "Karar açıklandı" gösterdiğini + /tcmb-faiz-takvimi'ni
  kontrol et (görünmüyorsa `logs/policy-decisions.log`); SSS'yi geçmiş zamana çevir, `updatedDate`. · Kabul:
  canlı yazıda güncel bölüm; 23 Ekim'den sonra otomatik kutu "açıklandı" durumunda.
- [x] T5 (B261015-1) — → canlı https://parafomo.com/ihtiyac-kredisi-hesaplama/ (KKDF %15 GİB + BSMV %15 7345 CK dahil taksit; BDDK 11152 vade uyarısı; 50/100/200 bin tablo; TCMB ihtiyaç faizi varsayılan) + EVDS: /mevduat-faizi-hesaplama oran tablosu, konut/kredi varsayılan faiz TCMB · commit cd0823e · RC oturumu 10-15 — **/ihtiyac-kredisi-hesaplama yeni araç** · hedef: ihtiyaç kredisi hesaplama (48), ihtiyaç
  kredisi faiz oranları (9,4). T1 bileşenini yeniden kullan; fark: KKDF + BSMV taksite dahil (oranları resmi
  kaynakla doğrula), BDDK tutar bazlı azami vade (doğrula), "50/100/200 bin TL × 12/24/36 ay" tablosu.
  /kredi-hesaplama ↔ /konut-kredisi-hesaplama ↔ /ihtiyac-kredisi-hesaplama linkleri. · Kabul: T1 ile aynı.
- [x] T6 (sistem — konu seçimi doğruluğu) — → OTORITE + BEKLE eylemleri; kira/kıdem/kredi/mevduat → OTORITE doğrulandı; eşitlikte birebir sayfa · commit 3848059 · RC 10-15 — **opportunity_finder "OTORITE" eylemi** · `scripts/learn/opportunity_finder.py`
  `decide()`: sayfa var + GSC'de sorgu yok ya da sıra >40 VE sayfanın `<title>`/H1'i sorgunun köklerini zaten
  içeriyorsa → eylem `OTORITE` (not: "başlık eşleşiyor; sıra otorite kilidinde — on-page görev yapma, uzun
  kuyruk/gelecek yıl açısıyla gir"), skor ×0,3. Başlığı build çıktısından (`dist/<slug>/index.html`) ya da
  .astro'dan oku. `agent/brief.py` §9c açıklamasına eylemi ekle. · Kabul: yeniden çalıştırınca kira artış oranı,
  kıdem tazminatı hesaplama, kredi hesaplama, mevduat faizi hesaplama `OTORITE`; commit.
- [x] K1 (keyword-map) — → canlı https://parafomo.com/memur-zammi-hesaplama/ (zam2027 ortak modül, HMB Temmuz katsayıları, senaryo tablosu) · commit f51291a · RC 10-15 — **/memur-zammi-hesaplama/** · memur zammı 130 + memur maaşı 115 · ayrıntı: agent/plan/keyword-map.md K1 · Kabul: T1 ile aynı
- [x] K2 (keyword-map) — → canlı https://parafomo.com/en-dusuk-emekli-maasi/ (23.552 ₺ taban, memur emeklisi 31.527 ₺, Ocak 2027 hesaplayıcı + ödeme günleri) · commit f51291a · RC 10-15 — **/en-dusuk-emekli-maasi/** · emekli maaşı 447 + en düşük emekli maaşı 62 · ayrıntı: keyword-map.md K2 · Kabul: T1 ile aynı
- [x] K3 (keyword-map) — → canlı https://parafomo.com/bayram-ikramiyesi/ (4.000 ₺, hisse oranı, 2027 tarihleri Diyanet) · commit f51291a · RC 10-15 — **/bayram-ikramiyesi/** · 128 · ayrıntı: keyword-map.md K3 · Kabul: T1 ile aynı
- [x] K5 (keyword-map) — → canlı https://parafomo.com/enflasyon-hesaplama/ (iki tarih arası TÜFE + paranın bugünkü değeri, 1-5 yıl ve yıllık tablolar, TÜİK/TCMB serisinden otomatik; footer + hub + kira/enflasyon-takvimi linkleri + OG) · commit 97717be · 2026-10-16 — **/enflasyon-hesaplama/** · enflasyon oranı 36 + enflasyon hesaplama 21
- [x] K8 (keyword-map) — → canlı https://parafomo.com/gelir-vergisi-hesaplama/ (kira 58.000 ₺ istisna + götürü/gerçek gider, işyeri/serbest meslek %20 stopaj mahsubu, 400.000 ₺ beyan sınırı, 2027 istisna tahmini YD oranıyla otomatik ≈74.000 ₺; footer + hub + vergi-dilimi/kira-artış linkleri + OG) · commit c408ccc · 2026-10-17 — **/gelir-vergisi-hesaplama/** · gelir vergisi hesaplama 50
- [x] K9a (keyword-map) — → canlı https://parafomo.com/ihbar-tazminati-hesaplama/ (İş Kanunu md.17 2/4/6/8 hafta, brüt + gelir vergisi dilimi + binde 7,59 damga → net, ücret×süre tablosu; footer + hub + kıdem/işsizlik linkleri + OG) · commit 3dfff90 · 2026-10-17 — **/ihbar-tazminati-hesaplama/** · ihbar tazminatı 20. Kalan K9b /yillik-izin-hesaplama keyword-map'te
- [ ] T13 (zam sezonu — TARİHLİ, 3 Kasım sonrası) — **YD kesinleşme kontrolü:** 3 Kasım'da release-watch.py
  (10 dk'da bir, 07:00-10:50 UTC) Ekim Yİ-ÜFE gelir gelmez /yeniden-degerleme-orani, /mtv-hesaplama vb. ve CANLI
  yazı /blog/2027-zamlari-yeniden-degerleme-orani-rehberi'yi otomatik "Belli Oldu: %X" yapar (RC 10-18; oran EVDS
  endeksinden TÜİK yöntemiyle — 3 Kasım sabahı TÜİK bülteninin "12 aylık ortalamalara göre" Yİ-ÜFE rakamıyla
  karşılaştır; fark varsa data/yeniden-degerleme.json onikiAyOrt'u bültendeki değere düzelt + `python3 scripts/live-posts.py`
  + deploy). Kasım sonu: VUK tebliğini WebSearch ile doğrula → `tebligOrani` alanına yaz (gecmis'e ELLE satır
  EKLEME; tur Haziran 2027'de kapanınca otomatik arşivlenir). Aralık: MTV/harç/damga için CB kararı çıkarsa →
  `uygulananOrani` (MTV, pasaport-harç sayfaları ve canlı yazı bu oranı kullanır). Her yazımdan sonra
  `python3 scripts/live-posts.py` → commit → `bash scripts/deploy-push.sh`. · Kabul: sayfalar canlıda doğru durumu gösterir.
- [ ] T14 (zam sezonu — TARİHLİ, TÜİK 2027 takvimi yayımlanınca; genelde Ocak'ın ilk günleri) — **TÜİK 2027
  takvimi:** `data/tuik-enflasyon-2027.json` oluştur (2026 dosyasıyla aynı şema; en az "Aralık 2026" → Ocak 2027
  açıklama günü). release-watch.py, emekli/memur sayfaları ve sonuç kutusu takvim dosyalarını glob'la okur; dosya yoksa
  ayın 3-6'sına bakılır (çalışır ama tarih metni eksik kalır). · Kabul: `python3 scripts/release-watch.py --dry --today <gün>` doğru günü söyler.
- [ ] T15 (zam sezonu — 5 Ocak 2027, açıklama günü) — **Ocak 2027 emekli zammı resmî rakam kontrolü:** /emekli-zammi-hesaplama
  ve /memur-zammi-hesaplama birikimli enflasyonu aylık % değişimleri bileşikleyerek hesaplıyor. RC 10-18 araştırması:
  Temmuz 2026 resmî SSK zammı %17,75 = aylık bileşik %17,75 (EVDS 2025=100 endeksiyle %17,76 — endeks 2 ondalık,
  yuvarlama sapması) → yöntem doğru, yine de 0,01 sapma riski var. 5 Ocak'ta Aralık TÜFE açıklanınca (release-watch
  veriyi otomatik çeker, sayfa "Belli Oldu" olur) resmî SSK/Bağ-Kur oranını ÇSGB/SGK açıklamasından doğrula; farklıysa
  `data/tufe-aylik.json`'a `"resmiZam": {"2027-01": {"ssk": <oran>}}` ekle (src/data/zam2027.ts bunu esas alır) →
  build → deploy. · Kabul: canlı sayfadaki oran resmî açıklamayla aynı.
- [ ] T16 (zam sezonu — TARİHLİ, 24 Aralık–10 Ocak) — **Ocak 2027 resmî tarife turu** (RC 10-18 listesi). Aralık sonu
  Resmî Gazete'de çıkan her tebliği WebSearch/RG ile doğrula, sayfayı 2027 resmî rakamına çevir ("tahmin" → "resmî"),
  OG kartını (`scripts/og-images.py` sabit kartlar) yenile, build → deploy. Sıra = arama hacmi:
  1. Asgari ücret: `scripts/asgari-ucret-watch.py` otomatik yazar → doğrula (Kaan'a da mail gider); 1 Ocak'ta yıl devri
     otomatik. Bağlı sabitler: `net-maas-hesaplama` (MIN_BRUT + 2027 tarife), `issizlik-maasi-hesaplama` (MIN_BRUT).
  2. GVK 2027 tarifesi (dilimler, kira istisnası) → `vergi-dilimi-hesaplama`, `gelir-vergisi-hesaplama`, `net-maas-hesaplama`.
  3. MTV 2027 tarifesi + Harçlar Tebliği (CB oranı ≠ YD olabilir → `data/yeniden-degerleme.json` `uygulananOrani`) →
     `mtv-hesaplama` ORNEK tutarları, `pasaport-ehliyet-harci`, `noter-ucretleri` harçları, `tapu-harci-hesaplama` asgari harç.
  4. DVK Tebliği Seri 72 → `damga-vergisi-hesaplama` (BAZ_YIL=2027, tutarlar). VİVK Tebliği Seri 58 → `data/veraset-2026.json`
     2027 değerleri. Noterlik Ücret Tarifesi 2027 (RG ilan) → `noter-ucretleri`. TKGM 2027 fiyat listesi →
     `data/tapu-harci-2026.json` `gosterge2027`. TÜVTÜRK 2027 tarifesi (1 Ocak) → `arac-muayene-ucreti`.
  5. Kıdem tavanı (HMB katsayı genelgesi, Ocak ilk hafta) → `data/kidem-tavan.json`; memur katsayıları → `data/emekli-memur.json`
     (yeni katsayıyla /evde-bakim-maasi ve /engelli-maasi kendiliğinden döner; ASHB'nin Ocak duyurusundaki resmî 65 yaş/engelli
     tutarlarını `data/sosyal-aylik-2026.json` resmi bloğuna yaz — health.py uyarır; 2027 bütçe K cetveli kanunlaşınca butce.2027.durum="kanun");
     doğum yardımı tutarı CB kararıyla artırılırsa `data/dogum-yardimi-2026.json`;
     en düşük emekli aylığı + bayram ikramiyesi; trafik cezaları 2027 (YD uygulandı mı?) → `trafik-cezalari-hesaplama`.
  6. 5 Ocak sonrası: `src/data/zam2027.ts` PERIOD'u 2027-01..06 (Temmuz 2027 zammı) turuna çevir; emekli/memur sayfa metinleri.
  · Kabul: listedeki her sayfa canlıda 2027 resmî rakamını gösterir; health.py temiz.

## Bakım / ürün
- [x] V1 (video kalitesi) — → kök neden: parça sonu +0,12 sn kuyruğu sonraki parçayla aynı konumda çakışıyordu; build_ass parçayı sonrakinden önce bitiriyor · önce/sonra: agent/state/v1-test/compare.png · commit 5d4d98f · RC 10-15 · sonraki 3 günün video-qa'sı izlenecek — **altyazı çakışması hatası** · video-qa son 7g'de 4 videoda "altyazı üst üste binmiş,
  okunamıyor" buldu: sterlin-bir-cumleyle-oynuyor (viral/news), bilezik-aldin (viral/myth), evdeki-altin-calinirsa
  (viral/myth), ceyrek-altinda-gizli-prim (daily-short) → iki hattın ORTAK altyazı kodu. Kök nedeni bul
  (`scripts/shorts-build-v4.py` altyazı/ASS üretimi: kelime zamanları çakışınca iki satır aynı anda mı?
  video-qa günlüğünü `grep -ri altyaz` ile bul). Düzelt; izole test: bu senaryolardan birini `agent/state/`
  altına yeniden render et, çakışan saniyeden ffmpeg ile kare çıkarıp bak. · Kabul: düzeltme commit'i + rapora
  önce/sonra kare yolu; sonraki 3 günün video-qa'sında altyazı çakışması bulgusu yok.
- [x] V2 (video sağlığı) — → teşhis: 3 video public/processed, MFK değil, kısıt yok, yükleme tek+hatasız → teknik kusur YOK; Shorts akışı 0 izlenme verdi (izlenmenin tamamı arama). 2/3'ünde aynı gün aynı konuda kardeş video akışı almış (dolar 5000 ×2 31 dk arayla → 13 vs 554; takı ayar 7 vs bilezik 242 aynı gün) → ÖNERİ (bahis adayı): aynı konu kümesinden günde en çok 1 yükleme. Hijyen: defaultAudioLanguage=tr eklendi · commit f848c10 · RC 10-15 — **0-5 izlenmeli videoların teşhisi** · vadesiz-hesap-parani-sessizce-kucultuyor
  (10-10 viral, 0 izl.), taki-altininda-ayar-tuzagi (10-08, 5), dolar-5000-tl-yi-bir-yilda-ne-yapti (10-07
  viral, 11): YouTube Data API `videos.list part=status,processingDetails,contentDetails` (privacyStatus,
  uploadStatus, rejectionReason, madeForKids, regionRestriction). Sistematik neden (yükleme/işleme/kısıtlama)
  varsa düzelt ya da raporla. · Kabul: rapora 3 videonun durumu + varsa düzeltme.
- [x] P1 (portföy) — → canlı https://app.parafomo.com/portfoy/ Analiz → İlgili veri kartları + hisse detayında halka arz linki (UTM) · backlog [x] + Hesap ayarları düzeltildi · commit 7f6b01f · RC 10-15 — **Panelden içeriğe köprü** (backlog maddesi) · `app/portfoy/` SPA: kullanıcının sahip olduğu
  varlık tipine göre "İlgili veri" kartı (altın → /altin-getiri + /altin-hesaplama; BIST hissesi → /bist-getiri +
  halka arz şirket sayfası varsa /halka-arz/<slug>; gümüş → /gumus-getiri), UTM'li link. YALNIZ frontend (backend/DB
  yok). Önce backlog'daki "Hesap ayarları" maddesini kontrol et (`DELETE /auth/me` zaten var) ve backlog'u düzelt.
  · Kabul: `bash scripts/deploy-app.sh` sonrası app.parafomo.com panelinde kart görünür; backlog [x]; commit.
- [-] P-eski (izleme listesi / watchlist) — park edildi (haftalık koşu 10-15): yeni DB tablosu ister (kırmızı çizgi 6)
  + 5 üyeli üründe değer düşük. Trafik/üye artınca yeniden değerlendir.

## Kullanıcı girdisi gelince (o gün en üste al)
- ✅ YAPILDI 10-15 (commit cd0823e, cron Prş+Cum 12:40) — **TCMB EVDS anahtarı** gelirse (`/root/.config/parafomo/evds.env` → `EVDS_API_KEY`): `scripts/evds-rates.py` yaz
  (haftalık TL mevduat + konut/ihtiyaç kredisi ağırlıklı ortalama faiz) → `data/faiz-oranlari.json` → /mevduat-faizi-hesaplama
  "güncel mevduat faiz oranları" kutusu (hedef: mevduat faiz oranları hacim 57, mevduat faizi hesaplama 57,6 p57)
  + T1/T5 sayfalarında varsayılan faiz otomatik; health.py tazelik satırı; daily-content veri adımına bağla.
- R2 bilgileri → `/root/.config/parafomo/backup.env` (backup.sh otomatik kullanır).

## Notlar (günlük koşu için)
- **RC 2026-10-18 (Kaan: "geliştirmelerin hepsini yap") — yapılanlar, TEKRARLAMA/GERİ ALMA:** açıklama günü motoru
  (live-posts, `sonuc:` kutusu, release-watch, sitemap lastmod) · YD hedef yıl + EVDS endeks (%27,81) · emlak vergisi
  tam oran düzeltmesi · trafik cezası indirimi 1 AY (KK 17/6; 15 gün = itiraz) + sorgulama bölümü (K13) · asgari ücret
  veriden (`data/asgari-ucret.json`, 2027 açıklanınca `yeni`) + Aralık haber bekçisi (`scripts/asgari-ucret-watch.py`,
  cron) · getiri başlıklarında "Son 1 Yılda %X" · TCMB/Fed başlıklarında sıradaki karar günü · ana sayfa "2027 Zam
  Sezonu" bölümü · blog "Bu konuda hesapla" kutusu (`src/data/tools.ts` tek araç listesi) · YouTube açıklama linkleri
  '/' ile + yeni araç eşlemesi · alt-ajanlarla yeni sayfalar: noter-ucretleri, arac-muayene-ucreti,
  damga-vergisi-hesaplama, tapu-harci-hesaplama, tasit-kredisi-hesaplama, veraset-ve-intikal-vergisi-hesaplama
  (keyword-map K10-K12, K16'da işaretli) + 10-19: /engelli-maasi, /evde-bakim-maasi, /dogum-yardimi (K19-K21; sosyal aylıklar
  memur katsayısı × gösterge — asgari ücrete bağlı DEĞİL), /vergi-borcu-sorgulama yolda.
- **Neden bu sıra:** baş sorgularda otorite kilidi var (bkz. learnings); kazanılabilir yer gelecek yıl (2027)
  sorguları ve sitede karşılığı olmayan hacimli araç niyetleri. Sezon zirvesi Kasım-Ocak → T1-T3 Ekim'de canlı olmalı.
- **YAPMA:** halka arz takvimi / kira artış / kredi hesaplama baş sorguları için başlık-H1-FAQ dürtmesi (p57-100,
  başlık zaten eşleşiyor). "X mi Y mi" karşılaştırma yazısı (hacim ≈0). ABD makro (JOLTS/PCE/ISM) yazısı.
- 22 Ekim TCMB ve 28 Ekim Fed sonrası sabah: takvim sayfalarında karar görünüyor mu kontrol et (policy-decisions.sh);
  rakamı elle tahmin ETME.
- Olay sonrası güncelleme bekleyen yazılar (günlük adım 5): abd-eylul-2026-cpi, ecb-eylul-2026,
  ingiltere-eylul-2026-gdp, pce-gdp-agustos/eylul-2026, abd-ekim-2026-cpi (15 Ekim açıklandı).
- Görev Masası okunamazsa koşuyu durdurma; week.md kanonik.
- Headless: döngü/değişken/awk/heredoc yok; çok adımlı iş `agent/state/*.py` ile.

## Biten / iptal (bu hafta)
- [x] (günlük 10-19, keyword-map K16/K22) /bagkur-primi-hesaplama → canlı https://parafomo.com/bagkur-primi-hesaplama/ (%35,75 / indirimli %30,75, en düşük 10.156,73 ₺; 2 kaynakla kuruşu kuruşuna; GSS tutarları kaynaklar çeliştiği için YAZILMADI) · commit c59d0f2
- [x] (haftalık koşu 10-15) Kuyruk konuları Trends ile ölçüldü; 2 hacimsiz konu iptal, 6 hacimli konu eklendi (c9a6540)
- [x] (haftalık koşu 10-15) GSC sayfa×sorgu teşhisi: hesaplayıcılar otorite kilidinde; 2027 sorgularında p4-11
- Geçen hafta biten (10-08 → 10-14): T1 /gumus-getiri · T2 /euro-getiri · T3 /bitcoin-getiri · T4 bülten v1 ·
  T4b bülten formu getiri sayfalarında · T5 Dataset + kaynak satırı · T6 halka arz keşif + ana sayfa kutusu ·
  T7 kanonik/indeks ölçümü · T8 asgari ücret 2027 · T9 emekli zammı iç linkleri · T10 /vergi-dilimi-hesaplama ·
  T11 /trafik-cezalari-hesaplama · T12 /pasaport-ehliyet-harci · V1 shock kanca + rakam doğrulama · V2 YouTube
  kanal kimliği. Bitmeyen: T13 (tarihli), P1 watchlist (park).
