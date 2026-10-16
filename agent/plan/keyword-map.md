# Anahtar kelime haritası — "tüm kelimelerde siteyi güçlendir" (Kaan, 2026-10-15)

Kaynak: `data/learning/opportunities.json` → `tum_firsatlar` (Trends TR 12 ay, "mevduat faizi" = 100).
Her kelime TEK kanonik sayfaya bağlanır (yamyamlaşma yok). Haftalık koşu bu dosyadan görev üretir;
günlük koşu `week.md` kuyruğu bittiğinde buradaki ilk `- [ ]` satırını görev olarak alır (gecede ≤3).
Bitince satırı `- [x] … → canlı URL · tarih` yap. Yeni araç = Footer TOOL_LINKS + `/hesaplama-araclari/`
listesi + FAQPage + ilgili 2 sayfadan metin içi link. Resmî rakamı doğrulayamazsan YAZMA.

**ÖNCELİK (Kaan, 2026-10-15): önce alabileceğimiz kadar ORGANİK TIK.** Sıra = kazanılabilirlik:
uzun kuyruk, mevsimsel ve gelecek yıl (2027) açılı, rakibi zayıf araç/veri sorguları önce; anlık fiyat ve dev baş
terimler (dolar kuru, gümüş fiyatları — Google kendi kutusunda cevaplar, büyük siteler kilitli) EN SONA.
Otorite/dış link işleri şimdilik YAPILMAZ (Kaan: "kalsın"). Fırsat listesinde OTORITE çıkan kelimeye yeni sayfa açma.

## Yapıldı
- [x] altın kaç gram (1100) → /altin-kac-gram/ (HMB resmî tablo) · 2026-10-15
- [x] gram altın (4914), çeyrek altın (2310), cumhuriyet altını (454), 22 ayar bilezik (421), ons altın (426),
  tam/yarım/ata/has/18-14 ayar → /altin-fiyatlari/<tür>/ ×11 · 2026-10-15
- [x] faiz hesaplama (499) → /faiz-hesaplama/ · 2026-10-15
- [x] yüzde hesaplama (234) → /yuzde-hesaplama/ · 2026-10-15
- [x] araç merkezi → /hesaplama-araclari/ (tüm araçlar, iç link) · 2026-10-15
- [x] konut kredisi hesaplama (170) → /konut-kredisi-hesaplama/ · ajan 10-15
- [x] emlak vergisi (297) → /emlak-vergisi-hesaplama/ · ajan 10-15
- [x] kıdem tazminatı tavanı (62) → /kidem-tazminati-hesaplama/#tavan-2027 · ajan 10-15

## Sıradaki (skor sırası — üstteki önce; zam sezonu Kasım-Ocak, sezonluklar öne alındı)
- [x] K1 memur zammı (130) + memur maaşı (115) → **/memur-zammi-hesaplama/** (canlı 2026-10-15) — Ocak 2027 memur zammı =
  toplu sözleşme oranı + 6 aylık enflasyon farkı; emekli zammı sayfasının veri/fonksiyonunu kullan (aynı kaynak);
  Temmuz 2026 resmi oranı + Ocak 2027 tahmini (TÜFE güncellendikçe kendini günceller). Sezon: Ocak.
- [x] K2 emekli maaşı (447) + en düşük emekli maaşı (62) + emekli maaş hesaplama (23) → **/en-dusuk-emekli-maasi/** (canlı 2026-10-15)
  — güncel en düşük tutar (resmî kaynak + tarih), Ocak 2027 tahmini (emekli zammı modülünden), ödeme günleri.
  /emekli-zammi-hesaplama ile karşılıklı link; zam hesabını tekrar etme.
- [x] K3 bayram ikramiyesi (128) → **/bayram-ikramiyesi/** (canlı 2026-10-15) — güncel tutar (resmî), ödeme tarihleri, 2027 Ramazan/
  Kurban tarihleri; tutar değişmediyse "değişmedi" de.
- [x] K4 ihtiyaç kredisi hesaplama (48) → /ihtiyac-kredisi-hesaplama/ · 2026-10-15
- [x] K5 enflasyon oranı (36) + enflasyon hesaplama (21) → **/enflasyon-hesaplama/** (canlı 2026-10-16, commit 97717be) — iki tarih arası TÜFE
  değişimi ile "paranın alım gücü" hesaplayıcı; veri: `scripts/tufe-update.py`'nin TÜİK serisi (veri dosyasını
  genişlet, endeks yoksa önce veri betiği). Güncel yıllık/aylık enflasyon kutusu.
- [ ] K8 gelir vergisi hesaplama (50) → **/gelir-vergisi-hesaplama/** — /vergi-dilimi-hesaplama'nın dilim mantığını
  yeniden kullan (ücret dışı gelir: kira, serbest meslek); 2027 dilimleri YD oranıyla tahmin (tahmin de).
- [ ] K9 ihbar tazminatı (20) + yıllık izin hesaplama (13) → **/ihbar-tazminati-hesaplama/**, **/yillik-izin-hesaplama/**
  — İş Kanunu md. 17 (2/4/6/8 hafta) ve md. 53 (14/20/26 gün, 18 yaş altı/50 yaş üstü ≥20); kanun metninden doğrula.
- [ ] K10 taşıt kredisi hesaplama (26) → **/tasit-kredisi-hesaplama/** — T1 bileşeni; BDDK taşıt kredisi vade/tutar
  sınırları (fatura değerine göre) resmî kaynaktan.
- [ ] K11 noter ücreti (76) → **/noter-ucretleri/** — Noterlik Ücret Tarifesi (Resmî Gazete) — araç satış, vekaletname,
  onay; her Ocak yeni tarife → sezon notu.
- [ ] K12 araç muayene ücreti (46) → **/arac-muayene-ucreti/** — TÜVTÜRK resmî tarife (araç tipine göre), gecikme
  cezası; her Ocak YD oranıyla güncellenir.
- [ ] K13 trafik cezası sorgulama (62) → /trafik-cezalari-hesaplama'ya "sorgulama ve ödeme" bölümü (e-Devlet/
  GİB adımları) — yeni sayfa açma.
- [ ] K14 tefas (160) + fon getirileri (14) → blog "TEFAS nedir, fon nasıl alınır" (kaynak: TEFAS/SPK).
- [ ] K15 beyanname (246) + geçici vergi (46) + kira gelir vergisi (36) → beyanname rehberi + kira geliri beyanı
  yazısı (Mart sezonu: Şubat ortasına kadar canlı).
- [ ] K16 kurumlar vergisi (53), değer artış kazancı (25), bağkur borcu (24), damga vergisi hesaplama (15),
  tapu harcı hesaplama (14), kredi kartı faiz hesaplama (12) → küçük araç/rehberler (önce damga + tapu: zam sezonu).
- [ ] K17 brüt asgari ücret (82) + asgari ücret 2027 net (28) → /asgari-ucret-hesaplama'ya "2027" bölümü — RESMÎ
  karar açıklanınca (Aralık) aynı gün; önceden yalnız senaryo tablosu.
- [x] K18 mevduat faiz oranları (57) + kredi faiz oranları (55) → /mevduat-faizi-hesaplama/#guncel-oranlar + kredi sayfaları (TCMB EVDS haftalık, otomatik) · 2026-10-15
- ⤵ SONA ALINDI (10-15, anlık fiyat / dev baş terim — tık getirmesi zor):
- [ ] K6 dolar kuru (381) + euro kuru (223) + döviz hesaplama (15) → **/doviz-kurlari/** + çevirici — Truncgil
  (altin-fiyat.py ile aynı kaynak) döviz kalemleri; günlük güncelleme altin-daily'ye bağlanır. Fiyat niyeti → tık
  az; uzun-kuyruk ("100 dolar kaç TL") tablo satırlarıyla gir.
- [ ] K7 gümüş fiyatları (212) → **/gumus-fiyatlari/** — gram gümüş/ons gümüş; /gumus-getiri ile link. Kaynak K6 ile aynı.

## Yeniden kur / otorite (sayfa var, sıralanmıyor) — week.md T6 sınıflandırmasına göre
- halka arz takvimi (68, sıra 67) → /halka-arz · mevduat faizi hesaplama (58, sıra 57) · işsizlik maaşı hesaplama
  (24, sıra 83) · enflasyon ne zaman (23, /enflasyon-takvimi sıra 77) · dolar endeksi (15, sıra 76).
  T6 "OTORITE" derse on-page dürtme yapma; yeni araç/küme ve dış linkle güçlenir.

## Yapma
- Dev baş terimlerde (gram altın, altın fiyatları, dolar kuru, borsa) başlık rötuşu — tür/uzun-kuyruk sayfalarıyla gir.
- Hacim < 5 kelimeye sayfa.
