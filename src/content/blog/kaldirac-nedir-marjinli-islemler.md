---
title: "Kaldıraç Nedir? Marjinli İşlemlerde Risk ve Getiri Hesabı"
description: "Kaldıraç nedir, marjinli işlem nasıl çalışır? Kaldıraç oranı, margin call ve gerçek örneklerle avantaj ve riskleri anlatan kapsamlı Türkçe rehber."
pubDate: 2026-08-18
category: "Yatırım"
tags: ["kaldıraç nedir", "marjinli işlem", "margin call", "leverage", "viop", "risk yönetimi", "türev ürün"]
readingTime: 8
featured: false
faq:
  - q: "Kaldıraç nedir kısaca?"
    a: "Kaldıraç (leverage), elindeki sermayenin katı büyüklüğünde pozisyon açmana olanak tanıyan finansal mekanizmadır. Örneğin 1:10 kaldıraçla 10.000 TL'lik teminatla 100.000 TL'lik işlem yapabilirsin. Kazancını büyütür ama kaybını da aynı oranda artırır."
  - q: "Margin call nedir, ne zaman gelir?"
    a: "Margin call, pozisyondaki kayıp büyüdüğünde teminat (marjin) tutarının minimum eşiğin altına düşmesiyle gelen zorunlu ek teminat uyarısıdır. Para yatırmazsan aracı kurum pozisyonu otomatik kapatır ve bu kapatma yüksek zararla sonuçlanabilir."
  - q: "Kaldıraç oranı nasıl seçilir?"
    a: "Kaldıraç oranı ne kadar yüksekse risk o kadar büyük olur. Deneyimsiz yatırımcılar için 1:2 veya 1:5 gibi düşük oranlar önerilir. Deneyim arttıkça ve pozisyon yönetimi iyileştikçe oran artırılabilir; ancak 1:50 veya üstü kaldıraçlar ancak profesyonel yatırımcılar için uygundur."
  - q: "Kaldıraç hangi ürünlerde kullanılır?"
    a: "Vadeli işlem sözleşmeleri (futures), opsiyonlar, CFD (Fark Sözleşmeleri), forex işlemleri ve kripto türev ürünleri kaldıraçlı enstrümanlardır. Türkiye'de bireysel yatırımcılar VİOP üzerinden kaldıraçlı işlem yapabilir."
  - q: "Kaldıraçlı işlemde ne kadar kaybedebilirim?"
    a: "Teorik olarak tüm teminatını kaybedebilirsin; bazı ürünlerde teminatını aşan kayıplar da oluşabilir (negatif bakiye riski). Bu yüzden stop-loss emirleri ve pozisyon boyutlandırması kaldıraçlı işlemlerde hayati önem taşır."
---

Az parayla büyük pozisyon açmak kulağa çekici gelir — ve tam olarak bu yüzden kaldıraç hem heyecan verici hem de tehlikelidir. **Kaldıraç nedir**, nasıl hesaplanır ve yatırımcıyı nasıl etkileyebilir? Bu rehberde gerçek rakamlar ve somut senaryolarla konuyu baştan sona açıklıyoruz.

## Kaldıraç (Leverage) Nedir?

**Kaldıraç**, elindeki sermayeyi teminat göstererek çok daha büyük bir pozisyon değerini kontrol etmeni sağlayan finansal mekanizmadır. Adını fizik biliminden alır: küçük bir kuvvetle büyük bir ağırlığı kaldıran kaldıraç prensibi, finansta küçük bir sermayeyle büyük bir işlem hacmini kontrol etme anlamına gelir.

Pratik anlamda: 1.000 TL nakit ile 10.000 TL değerinde bir pozisyon açabiliyorsan, **1:10 kaldıraç** kullanıyorsun demektir.

## Kaldıraç Nasıl Çalışır? Temel Mekanik

Kaldıraçlı işlemlerde iki temel kavram vardır:

- **Teminat (Marjin):** Pozisyonu açmak için aracı kuruma yatırman gereken minimum tutar.
- **Pozisyon büyüklüğü:** Gerçekte kontrol ettiğin toplam değer (teminat × kaldıraç oranı).

### Kaldıraç Formülü

```
Kaldıraç Oranı = Pozisyon Büyüklüğü ÷ Teminat
Marjin (%) = 1 ÷ Kaldıraç Oranı × 100
```

**Örnek:**
- Teminat: 5.000 TL
- Kaldıraç oranı: 1:20
- Kontrol edilen pozisyon: 5.000 × 20 = 100.000 TL

## Kazanç ve Kayıp: Kaldıraçlı Senaryo Analizi

Kaldıraç getiriyi de kaybı da eşit oranda büyütür. Aynı başlangıç sermayesiyle kaldıraçlı ve kaldıraçsız senaryoyu karşılaştıralım:

**Senaryo:** 5.000 TL sermaye, döviz kuru %3 yükseldi.

| Özellik | Kaldıraçsız İşlem | 1:10 Kaldıraçlı |
|---------|-------------------|-----------------|
| Kullanılan teminat | 5.000 TL | 5.000 TL |
| Kontrol edilen pozisyon | 5.000 TL | 50.000 TL |
| %3 yükselişte kazanç | 150 TL | 1.500 TL |
| %3 düşüşte kayıp | 150 TL | 1.500 TL |
| Teminata göre getiri/kayıp | %3 | %30 |

Görüldüğü gibi kaldıraç, hem olası kazancı hem de olası kaybı aynı oranda büyütür. %3'lük bir hareket, 1:10 kaldıraçla teminat üzerinde %30'luk etki yaratır.

## Margin Call Nedir? En Kritik Risk

Kaldıraçlı işlemlerde yatırımcının en çok duyduğu uyarı **margin call** (teminat tamamlama çağrısı) dur.

### Nasıl Tetiklenir?

1. Pozisyon aleyhine döner; hesabın teminat tutarı erir.
2. Hesaptaki bakiye **sürdürme marjini (maintenance margin)** seviyesinin altına düşer.
3. Aracı kurum sana bildirim gönderir: "Hesabına ek teminat yatır."
4. Belirlenen süre içinde ek teminat yatırmazsan aracı kurum pozisyonu **piyasa fiyatından zorla kapatır.**

### Margin Call Örneği

- Başlangıç teminatı: 10.000 TL
- Sürdürme marjini seviyesi: %30 → 3.000 TL
- Pozisyon 7.000 TL zarar ederse margin call gelir.
- O anda pozisyon kapatılırsa kalan teminat: 3.000 TL (7.000 TL kayıp gerçekleşmiş olur).

> Bazı piyasalarda hızlı fiyat hareketlerinde hesabın eksi bakiyeye de düşebilir — buna **negatif bakiye riski** denir. Türkiye'de VİOP bu riski takas güvencesiyle sınırlar ama kripto türev borsaları ve bazı forex platformlarında bu risk mevcuttur.

## Hangi Ürünlerde Kaldıraç Kullanılır?

| Ürün | Kaldıraç Oranı (Tipik) | Türkiye'de Erişim |
|------|------------------------|-------------------|
| VİOP Futures (endeks, döviz) | 1:5 – 1:20 | Borsa İstanbul VİOP |
| VİOP Opsiyonları | Prim odaklı (doğal kaldıraç) | Borsa İstanbul VİOP |
| Forex (Avrupa düzenlemeli) | 1:30 (perakende), 1:500 (profesyonel) | Lisanslı forex firmaları |
| CFD (Fark Sözleşmesi) | 1:5 – 1:20 (AB düzenlemesi) | Yurt dışı SPK lisanslı |
| Kripto Türevleri | 1:2 – 1:125 | Merkezi kripto borsaları |

Türkiye'de bireysel yatırımcılar için en düzenlenmiş ve şeffaf kaldıraçlı piyasa **VİOP**'tur. SPK denetimi altında çalışır, takas güvencesi sunar.

## Kaldıraçlı İşlemde Pozisyon Boyutlandırması

Kaldıraçlı işlemde en kritik karar, ne kadar büyük pozisyon açacağın değil — **bir işlemde ne kadar kayıp göze alacağın**dır. Profesyonel yatırımcılar genellikle şu kuralı uygular:

### %1-%2 Riski Kuralı

> Her işlemde hesabının en fazla **%1–2'sini** riske atıyorsun.

**Uygulama:**
1. Hesap büyüklüğü: 50.000 TL
2. İşlem başına maksimum risk: 50.000 × %2 = 1.000 TL
3. Stop-loss mesafesi: 500 pip (veya fiyat birimi)
4. Uygun pozisyon büyüklüğü: Risk ÷ Stop-loss mesafesi formülüyle hesaplanır.

Bu kural sayesinde arka arkaya 10 kaybetsen bile hesabın %20 erir, biter gitmez.

## Kaldıraç Kullanmanın Adımları

1. **Kaldıraçlı piyasayı ve ürünü seç:** VİOP futures, opsiyon veya başka bir araç.
2. **Hesap ve teminat gereklilikleri:** Aracı kurumun başlangıç teminatı ve sürdürme marjini koşullarını öğren.
3. **Pozisyon boyutunu belirle:** Risklenebileceğin maksimum tutara göre lot/kontrat sayısını hesapla.
4. **Stop-loss emri gir:** Pozisyona girerken aynı anda stop-loss sev seviyesini belirle ve emrini sisteme işle.
5. **Teminat takibi yap:** Pozisyon açıkken hesabı düzenli izle; marjin seviyesi kritik eşiğe yaklaşırsa pozisyonu küçült.
6. **Çıkış planını önceden belirle:** Hem kâr hedefini (take profit) hem de zararı durdur (stop-loss) önceden tanımla; duygusal kararlardan kaçın.

> Kaldıraçlı pozisyonlarda risk sınırlamanın en pratik aracı stop-loss emirleridir. [Stop-loss nedir ve nasıl kullanılır](/blog/stop-loss-nedir-zarar-kesme/) yazısında bu konuyu ayrıntılı bulabilirsin.

## Kaldıracın Avantajları ve Riskleri

| Avantaj | Risk |
|---------|------|
| Küçük sermayeyle büyük pozisyon | Kayıplar teminatı aşabilir |
| Hızlı getiri potansiyeli | Margin call ile zorunlu kapanış |
| Portföy hedge imkânı (futures ile) | Psikolojik baskı ve hatalı karar riski |
| Çift yönlü işlem (düşüşten kazanma) | Kaldıraç maliyeti (gece pozisyon taşıma faizi) |
| Likid piyasalara düşük sermayeyle erişim | Hızlı piyasa hareketlerinde ani kayıp |

## Kaldıraç ve Türkiye Yatırımcısı

Türkiye'de bireysel yatırımcıların kaldıraçlı işlem yapabileceği en organize piyasa VİOP'tur. VİOP'ta işlem gören başlıca kaldıraçlı ürünler şunlardır:

- **BIST 30 Endeks Futures:** Türk borsasının düşüşüne veya yükselişine toplu pozisyon.
- **Döviz Futures (USDTRY, EURTRY):** Kur hareketlerine karşı hem spekülasyon hem korunma.
- **Altın Futures:** Gram altın fiyatına kaldıraçlı erişim.
- **Pay (Hisse) Opsiyonları:** Belirli hisse senetleri için hak sözleşmeleri.

VİOP'ta Takasbank takas güvencesi sunduğundan karşı taraf riski minimum seviyededir; bu da bireysel yatırımcı için forex veya kripto türev platformlarına göre önemli bir avantajdır.

> Vadeli işlem sözleşmelerinin detaylı mekaniklerini anlamak için [vadeli işlem sözleşmesi (futures) nedir](/blog/vadeli-islem-sozlesmesi-nedir/) rehberimize göz at.

## Kaldıraç Kimler İçin Uygun Değil?

Kaldıraçlı işlemler aşağıdaki profiller için yüksek tehlike taşır:

- **Yeni başlayanlar:** Spot piyasa deneyimi olmadan kaldıraç hızla tüm sermayeyi bitirebilir.
- **Uzun vadeli yatırımcılar:** Bileşik getiri stratejisi, kaldıraçla değil düzenli yatırımla inşa edilir.
- **Acil fon kullanıcıları:** Kaldıraçlı pozisyon için asla harcanabilir olmayan para kullanılmamalıdır.
- **Yüksek stres yaşayanlar:** Psikolojik baskı hatalı kararlara yol açar; karar verirken soğukkanlılık şarttır.

## Özet

- **Kaldıraç**, küçük teminatla büyük pozisyon kontrolü sağlayan mekanizmadır; kazancı ve kaybı eşit oranda büyütür.
- **Margin call**, teminat belirli eşiğin altına düştüğünde gelen zorunlu ek teminat uyarısıdır; karşılanamazsa pozisyon zorla kapatılır.
- Türkiye'de bireysel yatırımcılar için en güvenli kaldıraçlı piyasa **VİOP**'tur; Takasbank güvencesiyle çalışır.
- Her işlemde hesabın en fazla **%1–2'sini** riske atmak uzun vadeli hayatta kalma şansını artırır.
- Kaldıraçlı işlem, [risk ve getiri dengesini](/blog/risk-getiri-iliskisi/) çok iyi anlayan, deneyimli yatırımcılar için anlamlıdır; yeni başlayanlar için önerilmez.

---

**Yasal Not:** Bu içerik yalnızca bilgilendirme amaçlıdır; yatırım tavsiyesi değildir. Kaldıraçlı işlemler yüksek risk içerir ve tüm yatırımını kaybetmene yol açabilir. Türev ürün işlemleri yapmadan önce SPK lisanslı bir finansal danışmana başvurmanı öneririz.
