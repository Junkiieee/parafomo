---
title: "Opsiyon Nedir? Alım ve Satım Opsiyonu Nasıl Çalışır?"
description: "Opsiyon nedir, call ve put farkı nedir? VİOP'ta opsiyon nasıl işlem yapılır? Alım ve satım opsiyonunu örneklerle anlatan kapsamlı Türkçe rehber."
pubDate: 2026-08-16
category: "Yatırım"
tags: ["opsiyon", "call option", "put option", "türev ürün", "viop", "alım opsiyonu", "satım opsiyonu", "risk yönetimi"]
readingTime: 8
featured: false
faq:
  - q: "Opsiyon nedir kısaca?"
    a: "Opsiyon, belirli bir varlığı (hisse, döviz, emtia) önceden belirlenmiş fiyattan, belirli bir tarihe kadar alma veya satma hakkı tanıyan sözleşmedir. Hak verir, zorunluluk doğurmaz; alıcı isterse hakkını kullanmayabilir."
  - q: "Call ve put opsiyon arasındaki fark nedir?"
    a: "Call (alım) opsiyonu, varlığı belirlenen fiyattan alma hakkı tanır. Put (satım) opsiyonu ise belirlenen fiyattan satma hakkı tanır. Call'da yükselişten, put'ta düşüşten kazanılır."
  - q: "Opsiyon primi nedir, neden ödenir?"
    a: "Opsiyon primi, bu hakkı satın almak için ödenen bedeldir. Prim; varlığın fiyatı, kullanım fiyatı, vadeye kalan süre ve oynaklık (volatilite) gibi faktörlere göre belirlenir. Alıcı prim öder; satıcı prim alır, yükümlülük üstlenir."
  - q: "Türkiye'de opsiyonlar nerede işlem görür?"
    a: "Türkiye'de opsiyonlar VİOP (Vadeli İşlem ve Opsiyon Piyasası) bünyesinde, Borsa İstanbul çatısı altında işlem görür. BIST 30 pay opsiyonları ve döviz opsiyonları bu piyasada aktif olarak işlem görmektedir."
  - q: "Opsiyon alıcısı maksimum ne kadar kaybeder?"
    a: "Opsiyon alıcısının maksimum kaybı ödediği primle sınırlıdır. Hakkı kullanmazsa yalnızca prim tutarını kaybeder. Bu, vadeli işlemlerden (futures) temel farkı oluşturur; futures'ta kayıp sınırsız olabilir."
---

Evin değeri düşmesin diye sigorta yaptırırsın — aylık küçük bir prim öder, büyük bir felaketten korunursun. Finansal piyasalarda opsiyonlar tam olarak bu mantıkla çalışır. **Opsiyon nedir** sorusunun cevabı özünde şudur: Bir varlığı belirlenen fiyattan alma ya da satma **hakkı** veren, ancak bu hakkı kullanmayı **zorunlu kılmayan** bir sözleşme. Bu yazıda alım ve satım opsiyonlarını, nasıl fiyatlandıklarını ve Türkiye'deki VİOP piyasasını örneklerle ele alıyoruz.

## Opsiyon Nedir? Temel Kavramlar

Bir **opsiyon sözleşmesi** dört temel unsurdan oluşur:

- **Dayanak varlık:** Sözleşmenin üzerine yazıldığı varlık (hisse senedi, döviz, altın, endeks).
- **Kullanım fiyatı (Strike Price):** Sözleşmede belirlenen alım veya satım fiyatı.
- **Vade tarihi:** Hakkın en geç kullanılabileceği tarih.
- **Prim:** Opsiyonu satın almak için ödenen bedel.

Opsiyonlar iki taraflı bir anlaşmadır:

- **Alıcı (Buyer/Holder):** Prim öder, hak kazanır. Hakkını kullanıp kullanmamakta serbesttir.
- **Satıcı (Writer/Seller):** Prim alır, yükümlülük üstlenir. Alıcı hakkını kullanırsa yerine getirmek zorundadır.

> Opsiyonlar ile vadeli işlemlerin farkını daha iyi anlamak için [vadeli işlem sözleşmesi (futures) nedir](/blog/vadeli-islem-sozlesmesi-nedir/) yazısını okuyabilirsin.

## Opsiyon Türleri: Call ve Put

### Alım Opsiyonu (Call Option)

**Call opsiyon**, dayanak varlığı belirlenen kullanım fiyatından **satın alma hakkı** tanır. Fiyatın yükseleceğini düşündüğünde tercih edilir.

**Örnek:** XYZ hissesi şu an 100 TL'de. 3 ay vadeli, 110 TL kullanım fiyatlı bir call opsiyon için 5 TL prim ödedin.

- Hisse 130 TL'ye çıkarsa: 110 TL'den alıp 130 TL'den satarsın → 20 TL kâr – 5 TL prim = **15 TL net kâr**
- Hisse 105 TL'de kalırsa: Hakkını kullanmak mantıklı değil → **5 TL prim kaybı**
- Hisse 90 TL'ye düşerse: Hakkını kullanmazsın → **5 TL prim kaybı** (başka zarar yok)

### Satım Opsiyonu (Put Option)

**Put opsiyon**, dayanak varlığı belirlenen kullanım fiyatından **satma hakkı** tanır. Fiyatın düşeceğini düşündüğünde ya da elindeki varlığı korumak istediğinde tercih edilir.

**Örnek:** XYZ hissesi 100 TL, elinde 100 hisse var. 90 TL kullanım fiyatlı bir put opsiyon için 4 TL prim ödedin.

- Hisse 70 TL'ye düşerse: 90 TL'den sat → 90 – 70 = 20 TL koruma – 4 TL prim = **16 TL net korunma**
- Hisse 95 TL'de kalırsa: Hakkı kullanmak anlamsız (piyasada daha pahalıya satarsın) → **4 TL prim kaybı**
- Hisse 110 TL'ye çıkarsa: Hakkı kullanmazsın, hisse değer kazandı → **4 TL prim kaybı** (sigorta masrafı gibi düşün)

## Opsiyon ile Vadeli İşlem (Futures) Farkı

| Özellik | Opsiyon | Vadeli İşlem (Futures) |
|---|---|---|
| Alıcı için zorunluluk | Yok (hak tanır) | Var (yükümlülük doğurur) |
| Satıcı için zorunluluk | Var (alıcı kullanırsa) | Var (her iki taraf için) |
| Alıcının max. kaybı | Ödenen primle sınırlı | Sınırsız olabilir |
| Satıcının max. kaybı | Teorik olarak sınırsız | Sınırsız olabilir |
| Ön maliyet | Prim ödemesi | Teminat yatırma |
| Kullanım esnekliği | Yüksek (hakkı kullanmayabilirsin) | Düşük (sözleşme zorunlu) |
| Türkiye piyasası | VİOP Opsiyon | VİOP Futures |

## Opsiyon Primini Belirleyen Faktörler

Bir opsiyonun fiyatı (prim) çeşitli değişkenlere bağlıdır:

1. **İçsel değer (Intrinsic Value):** Şu anki piyasa fiyatı ile kullanım fiyatı arasındaki olumlu fark. "Para'da" (in-the-money) opsiyonlar içsel değer taşır.
2. **Zaman değeri (Time Value):** Vadesine ne kadar süre kaldığına bağlı. Vade yaklaştıkça erir (time decay / theta).
3. **Oynaklık (Volatilite):** Dayanak varlık ne kadar dalgalanıyorsa prim o kadar yüksek olur; çünkü olumlu senaryo ihtimali artar.
4. **Faiz oranı:** Yüksek faiz ortamında call primleri hafif yükselir.
5. **Temettü:** Hisse temettü ödemesi bekleniyorsa call primleri bunun etkisini içerir.

### "Para'da", "Parada" ve "Para Dışı" Opsiyon

| Durum | Call Opsiyon | Put Opsiyon |
|---|---|---|
| Para'da (In-the-money) | Piyasa fiyatı > kullanım fiyatı | Piyasa fiyatı < kullanım fiyatı |
| Parada (At-the-money) | Piyasa fiyatı ≈ kullanım fiyatı | Piyasa fiyatı ≈ kullanım fiyatı |
| Para Dışı (Out-of-money) | Piyasa fiyatı < kullanım fiyatı | Piyasa fiyatı > kullanım fiyatı |

## VİOP'ta Opsiyon Piyasası

Türkiye'de opsiyonlar **VİOP (Vadeli İşlem ve Opsiyon Piyasası)** aracılığıyla işlem görür. Borsa İstanbul bünyesinde faaliyet gösteren VİOP'ta şu anda aktif olarak işlem gören opsiyon grupları:

- **Pay opsiyonları:** BIST 30 kapsamındaki seçili hisseler üzerine yazılı opsiyon sözleşmeleri.
- **Endeks opsiyonları:** BIST 30 endeks değeri üzerine.
- **Döviz opsiyonları:** USD/TRY ve EUR/TRY paritelerinde.
- **Altın opsiyonları:** Gram altın fiyatı üzerine.

Amerikan tipi opsiyonlar vade sonundan önce her an kullanılabilirken, Avrupa tipi opsiyonlar yalnızca vade tarihinde kullanılabilir. VİOP'ta pay opsiyonlarının büyük bölümü Amerikan tipidir.

## Opsiyonların Avantajları ve Riskleri

| Avantaj | Risk |
|---|---|
| Alıcı için kayıp primle sınırlı | Prim zaman içinde erir (theta riski) |
| Portföy sigortası imkânı (put ile hedge) | Yanlış yön + volatilite düşüşü = hızlı prim kaybı |
| Küçük primle büyük pozisyon kontrolü | Opsiyon sözleşmeleri karmaşık; yanlış anlama riski |
| Fiyat yönüne bağımsız stratejiler | Piyasa beklediğin kadar hareket etmezse zaman değeri sıfırlanır |
| Satıcı için düzenli prim geliri | Opsiyon satıcısının kaybı teorik olarak sınırsız |

> Opsiyon stratejileri portföy riskini yönetmenin güçlü bir yolu olsa da [risk ve getiri ilişkisini](/blog/risk-getiri-iliskisi/) iyi anlamak her şeyden önce gelir.

## Adım Adım: İlk Opsiyon İşlemine Nasıl Başlanır?

1. **Temel kavramları öğren:** Call/put, prim, kullanım fiyatı ve vade kavramlarına tam hâkim ol. Bilmeden opsiyon işlemi yapma.
2. **Aracı kurum seç:** VİOP'a erişim sağlayan herhangi bir BIST üyesi aracı kurumda hesap aç; "vadeli işlem ve opsiyon" hesabı talep et.
3. **Teminat yatır:** VİOP'ta opsiyon satıcıları teminat göstermek zorundadır. Alıcılar için teminat gerekmez; yalnızca prim bedeli yeterlidir.
4. **Sözleşmeyi seç:** Dayanak varlık, vade, kullanım fiyatı ve prim tutarını karşılaştır.
5. **Küçük başla:** İlk deneyimlerde düşük primli, yakın vadeli sözleşmelerle piyasa dinamiklerini gözlemle.
6. **Riski izle:** Pozisyonun değerini her gün takip et; özellikle vade yaklaştıkça zaman erimesini gözlemle.
7. **Vadesinden önce kapat ya da kullan:** Hakkını kullanmak ya da pozisyonu prim gelir/gideriyle kapatmak arasında bilinçli karar ver.

> Zarara karşı kendinizi korumak isteyenler için [stop-loss nedir ve nasıl kullanılır](/blog/stop-loss-nedir-zarar-kesme/) yazısı ek bir perspektif sunuyor.

## Pratik Opsiyon Stratejileri

Opsiyon dünyasında deneyim kazandıkça şu temel stratejileri inceleyebilirsin:

- **Covered Call:** Elinde hisse varken üzerine call satmak → prim geliri elde ederken hisseyi tutmaya devam edersin.
- **Protective Put:** Elindeki hisseyi korumak için put almak → prim maliyeti karşılığında aşağı riski sınırlarsın.
- **Long Straddle:** Büyük hareket bekliyorken hem call hem put almak → yön bilmesen de volatiliteden kazanabilirsin.

Bu stratejiler başlangıç seviyesini aşkın olsa da opsiyonun esnekliğini gösterir: Yalnızca "yükseliş" ya da "düşüş" değil, "sert hareket", "durgunluk" veya "korunma" için de kullanılabilir.

## Özet

- **Opsiyon nedir:** Bir varlığı önceden belirlenen fiyattan alma (call) ya da satma (put) hakkı veren, ancak zorunluluk doğurmayan sözleşmedir.
- **Alıcı prim öder, hak kazanır;** isterse kullanmaz ve yalnızca ödediği primle sınırlı kalır.
- **Satıcı prim alır, yükümlülük üstlenir;** alıcı hakkını kullanırsa yerine getirmek zorundadır.
- Opsiyon primleri; dayanak varlık fiyatı, kullanım fiyatı, vadeye kalan süre ve oynaklık tarafından belirlenir.
- Türkiye'de opsiyonlar **VİOP** aracılığıyla işlem görür; aracı kurum hesabıyla erişilebilir.
- Vadeli işlemlere göre alıcı için **daha sınırlı risk** sunan opsiyonlar, karmaşık yapıları nedeniyle dikkatli bir öğrenme süreci gerektirir.

---

**Yasal Not:** Bu içerik yalnızca bilgilendirme ve eğitim amaçlıdır; yatırım tavsiyesi değildir. Opsiyon işlemleri türev araçlar kapsamında olup tüm yatırımınızı kaybetme riski taşır. Yatırım kararı almadan önce bir finansal danışmana başvurmanız önerilir.
