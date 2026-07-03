---
title: "Stablecoin Nedir? USDT, USDC Farkları ve Taşıdığı Riskler"
description: "Stablecoin nedir, nasıl çalışır? USDT ve USDC farkı, algoritmik stablecoin riskleri ve Türkiye'den nasıl kullanılır — kapsamlı başlangıç rehberi."
pubDate: 2026-07-03
category: "Kripto"
tags: ["stablecoin", "USDT", "USDC", "kripto para", "dolar sabitli kripto", "DeFi"]
readingTime: 9
featured: false
faq:
  - q: "Stablecoin nedir, kısaca nasıl tanımlanır?"
    a: "Stablecoin, değeri belirli bir varlığa (genellikle ABD dolarına) sabitlenmiş kripto para birimidir. 1 USDT ya da 1 USDC her zaman yaklaşık 1 dolara eşit olmayı hedefler; bu sayede Bitcoin gibi sert fiyat dalgalanmaları yaşanmaz."
  - q: "USDT ile USDC arasındaki fark nedir?"
    a: "USDT (Tether), en yüksek işlem hacmine sahip stablecoin'dir; ancak rezervlerinin şeffaflığı zaman zaman sorgulanmıştır. USDC (Circle), düzenli bağımsız denetimle desteklendiği ve ABD'li finansal kurumlarla iş birliği yaptığı için şeffaflık açısından daha güçlü kabul edilir. İkisi de 1 dolar sabitini hedefler."
  - q: "Algoritmik stablecoin neden çöker?"
    a: "Algoritmik stablecoin'ler rezerv tutmak yerine arz-talep dengesiyle sabitini korumaya çalışır. Eğer güven sarsılırsa 'ölüm sarmalı' başlayabilir: satış baskısı artar, algoritma sabit tutamaz, daha fazla satış gelir. 2022'de Terra/LUNA ekosisteminin çöküşü bu mekanizmanın nasıl işlediğinin en bilinen örneğidir."
  - q: "Stablecoin'den faiz (getiri) kazanabilir misiniz?"
    a: "Evet. DeFi platformlarında veya bazı kripto borsalarında stablecoin'lerinizi borç verme havuzlarına kilitleyerek yıllık %3-10 arasında değişen getiri elde etmek mümkündür. Ancak bu getiri sabit değildir ve platform riski, akıllı sözleşme açığı gibi ek riskler taşır."
  - q: "Türkiye'de stablecoin tutmak yasal mı?"
    a: "2024 itibarıyla Türkiye'de kripto varlıklara ilişkin yasal çerçeve gelişmektedir; stablecoin dahil kripto varlıklar SPK denetimindeki lisanslı borsalar üzerinden alınıp satılabilir. Yasal durum değişken olduğundan güncel mevzuatı takip etmek önerilir."
---

Kripto para piyasasında Bitcoin veya Ethereum satın aldığınızda yüzde elli değer kaybına hazırlıklı olmanız gerekir. Ama kripto borsasındaki paranızı dolar değerinde sabit tutmak isteseydiniz ne yapardınız? **Stablecoin** tam da bu ihtiyaç için doğdu: blokzincir altyapısını kullanırken fiyat istikrarından ödün vermemenin yolu.

Bu rehberde **stablecoin nedir**, türleri nelerdir, USDT ile USDC arasındaki fark ne, ve en önemlisi bu varlıklar hangi gerçek riskleri taşır — hepsini sade Türkçeyle ele alıyoruz.

## Stablecoin Nedir?

Stablecoin, değeri belirli bir referans varlığa — çoğunlukla ABD dolarına — sabitlenmiş kripto para birimidir. 1 USDT ya da 1 USDC her zaman 1 dolara eşit olmayı hedefler. Ethereum veya Bitcoin gibi serbest dalgalanan varlıklardan farklı olarak stablecoin'ler bu sabitliği çeşitli mekanizmalarla (gerçek dolar rezervi, kripto teminat veya algoritma) sürdürmeye çalışır.

Pratik anlamı şudur: Kripto borsasında işlem yaparken "piyasa çok volatil, bir süre bekleyeyim" dediğinizde birikimlerinizi Bitcoin'de tutmak yerine stablecoin'e çevirirsiniz — değeriniz blokzincirde kalır ama dolar paritesini korumuş olursunuz.

## Stablecoin Türleri: Hangi Mekanizma, Nasıl Çalışır?

Tüm stablecoin'ler aynı şekilde çalışmaz. Sabitliği nasıl koruduklarına göre üç ana kategoriye ayrılırlar.

### 1. Fiat Destekli Stablecoin'ler (En Yaygın)

Arkasında gerçek dolar veya dolar eşdeğeri varlık (devlet tahvili, nakit) bulunan en basit modeldir. Her 1 USDT veya USDC için emanet hesaplarda 1 dolarlık karşılık tutulduğu iddia edilir.

**Örnekler:** USDT (Tether), USDC (Circle), BUSD (Binance/Paxos — artık aktif değil), PYUSD (PayPal)

**Avantaj:** Anlaşılması kolay, en yüksek likidite, geniş borsa desteği.  
**Risk:** Merkezi yapı; rezervleri tutan şirkete güvenmek zorundasınız. Rezervler yeterince şeffaf değilse veya şirket iflas ederse sorun çıkabilir.

### 2. Kripto Teminatlı Stablecoin'ler

Dolara sabitlenmek için gerçek dolar yerine kripto varlıklar (örneğin Ethereum) teminat olarak kilitlenir. Kripto'nun oynaklığına karşı güvence olarak fazla teminat (aşırı teminatlandırma) sağlanır.

**Örnek:** DAI (MakerDAO) — Ethereum ve diğer kripto varlıklar teminat gösterilir, karşılığında DAI üretilir.

**Avantaj:** Merkezi bir şirkete bağımlılık yok; kod ve akıllı sözleşmelerle yönetilir.  
**Risk:** Kripto teminatların değeri hızlı düşerse tasfiye (likidasyona) riski doğar.

### 3. Algoritmik Stablecoin'ler (En Riskli)

Rezerv tutmak yerine arz-talep mekanizmasını algoritmik olarak yönetir; sabitin korunması bir kardeş token ile dengeleme üzerine kurulur.

**Örnek:** TerraUSD (UST) — 2022'de çöken, 40 milyar doların üzerinde değer imha eden kötü şöhretli örnek.

**Avantaj:** Teorik olarak tamamen merkezi olmayan ve ölçeklenebilir model.  
**Risk:** Güven krizi anında "ölüm sarmalı" başlayabilir — piyasa düşer, algoritma basarsa daha fazla satış gelir, sistem çöker. Bu risk teorik değil, gerçekleşmiştir.

## Başlıca Stablecoin'ler Karşılaştırması

| Stablecoin | Tür | Piyasa Değeri (yaklaşık) | Denetim Şeffaflığı | Merkezi mi? |
|---|---|---|---|---|
| **USDT (Tether)** | Fiat destekli | En büyük (~120 Mrd $) | Kısmi (Cayman adaları denetimi) | Evet |
| **USDC (Circle)** | Fiat destekli | İkinci büyük (~45 Mrd $) | Yüksek (BDO denetimi, aylık rapor) | Evet |
| **DAI (MakerDAO)** | Kripto teminatlı | ~5 Mrd $ | Yüksek (zincir üstü verifiable) | Kısmen (DAO yönetimi) |
| **UST (Terra)** | Algoritmik | Çöktü — 2022 | Belirsiz | Hayır |
| **PYUSD (PayPal)** | Fiat destekli | ~1 Mrd $ | Yüksek (Paxos altyapısı) | Evet |

*Piyasa değerleri yaklaşık olup değişkendir.*

## Stablecoin Ne İşe Yarar? Gerçek Kullanım Senaryoları

**1. Volatiliteden korunma:** Bitcoin fiyatı düşeceğini düşünüyorsunuz ama borsadaki paranızı TL'ye çevirmek istemiyorsunuz. Stablecoin'e geçip fırsatı bekliyorsunuz.

**2. Yurt dışı transfer:** Banka havalesi günler alır, maliyetlidir. USDC veya USDT ile saniyeler içinde, düşük ücretle küresel transfer yapılabilir.

**3. DeFi getirisi:** Merkezi olmayan finans (DeFi) platformlarında stablecoin'lerinizi borç vererek yıllık %3-10 arası getiri kazanabilirsiniz. Bu, bankanın dolar mevduatına ödediği faizden çok daha yüksek olabilir; ancak risk yapısı tamamen farklıdır.

**4. Enflasyona karşı dolar tutma:** Türkiye'de TL enflasyonundan korunmak için dolar tutmak isteyenler banka dolar hesabı yerine stablecoin tercih edebilir — kripto borsası hesabı açmak daha hızlıdır ve banka kapanma saati yoktur.

**5. NFT ve kripto ekosistemi işlemleri:** Ethereum ağındaki birçok protokol, NFT pazarı ve DeFi uygulaması ödemeleri stablecoin ile gerçekleştirir.

## USDT mi, USDC mi? Detaylı Fark

Bu iki fiat destekli stablecoin kripto piyasasının en büyük ikilidir. Temel farkları şöyle özetlenebilir:

**USDT (Tether):**
- 2014'ten beri piyasada; en yüksek işlem hacmine sahip.
- Rezervlerinin bileşimi geçmişte birçok kez sorgulandı; 2021'de ABD Emtia İdaresi (CFTC) ile 41 milyon dolarlık uzlaşma yapıldı.
- Büyük Türk borsaları dahil neredeyse her kripto platformunda destekleniyor.
- Volatilite riski düşük ama karşı taraf riski görece yüksek.

**USDC (Circle):**
- 2018'de ABD'li Circle ve Coinbase ortaklığıyla kuruldu.
- ABD finansal düzenleyicileriyle uyumlu; rezervler aylık bağımsız denetimle yayınlanır.
- 2023'te ABD bankacılık krizinde kısa süre sabiti kaybetti (1 dolar = 0,87 USDC'ye indi); ancak rezerv şeffaflığı sayesinde hızla toparlandı.
- Özellikle kurumsal ve DeFi kullanımında tercih ediliyor.

**Hangisini seçmeli?** İşlem kolaylığı öncelikseniz USDT; şeffaflık ve düzenleyici uyum öncelikseniz USDC daha güçlü bir tercih.

## Stablecoin'lerin Gerçek Riskleri

"Sabitlenmiş" ifadesi stablecoin'lerin risksiz olduğu anlamına gelmez. Tam tersi — kendine özgü risk türleri taşırlar.

### Karşı Taraf Riski (Merkezi Stablecoin'lerde)
USDT veya USDC tuttuğunuzda Tether veya Circle şirketine güveniyorsunuz. Bu şirket iflas ederse, yetersiz rezervi ortaya çıkarsa ya da devlet tarafından bloke edilirse varlıklarınıza erişemeyebilirsiniz. Kripto'nun "merkezi otorite yok" söylemi burada geçerli değildir.

### Rezerv Şeffaflığı Sorunu
Özellikle USDT için uzun süre "1 USDT = 1 dolar rezerv" iddiasının tam kanıtı sunulamadı. Piyasada güven krizi yaşanırsa sabit bozulabilir ("de-peg"). 2022'de USDT kısa süreli olarak 0,95 dolara geriledi.

### Algoritmik Çöküş (Terra/LUNA Dersi)
2022 Mayıs'ında TerraUSD (UST) algoritması çalışmayı bıraktı, birkaç günde sıfıra yakın değere düştü. On milyarlarca dolar yatırımcı kaybı yaşandı. Algoritmik stablecoin, tasarımı gereği "güven oyunu" oynuyor; güven sarsıldığında sistem hızla dağılabiliyor.

### Regülasyon Riski
ABD, AB ve Türkiye stablecoin düzenlemesi üzerinde aktif olarak çalışıyor. Regülasyon değişikliği belirli stablecoin'lerin kullanımını kısıtlayabilir ya da ihraççı şirketi operasyonel baskıyla karşılaştırabilir.

### Akıllı Sözleşme Riski (DeFi'da Kullanımlarda)
Stablecoin'lerinizi DeFi protokollerine yatırdığınızda o protokolün akıllı sözleşme kodundaki hatalar sizi doğrudan etkiler. Geçmişte pek çok DeFi hack'i stablecoin havuzlarını hedef almıştır.

## Türkiye'den Stablecoin Nasıl Kullanılır?

### Adım 1: Lisanslı kripto borsasında hesap açın
Türkiye'de SPK lisanslı borsalar üzerinden işlem yapmanız hem yasal koruma hem de güvenlik açısından önemlidir. Hesap açarken kimlik doğrulaması (KYC) gerekir.

### Adım 2: TL ile USDT veya USDC alın
TL/USDT veya TL/USDC çifti arama çubuğunda bulun, almak istediğiniz tutarı girin, onaylayın.

### Adım 3: Saklama yöntemini belirleyin
- **Borsa cüzdanı:** Küçük tutarlar için yeterli; borsanın güvenliğine bağımlısınız.
- **Yazılım cüzdanı (MetaMask, Trust Wallet):** Kendi anahtarınızda; daha fazla kontrol ama sorumluluk da size ait.
- **Donanım cüzdanı (Ledger):** Büyük tutarlar için en güvenli seçenek.

Cüzdan güvenliği hakkında detaylı bilgi için [Bitcoin başlangıç rehberimize](/blog/bitcoin-nedir-nasil-alinir) bakabilirsiniz — orada anlatılan seed phrase kuralları tüm kripto varlıklar için geçerlidir.

### Adım 4: Kullanım amacınızı netleştirin
Stablecoin'i ne için kullanacağınızı baştan belirlemek, gereksiz risk almaktan korur:
- Borsa içi bekletme → borsa cüzdanı yeterli
- Uzun vadeli tasarruf → kişisel cüzdan
- DeFi getirisi → akıllı sözleşme riskini kabul etmek şart

## Stablecoin Portföyde Nasıl Konumlanır?

Stablecoin Bitcoin veya Ethereum gibi büyüme potansiyeli taşıyan bir varlık değildir — değeri sabit kalmayı amaçlar. Portföyde üstlendiği roller şunlardır:

1. **Nakit eşdeğeri:** Kripto varlık alımı öncesi bekleme mevkii.
2. **Risk tampon bölgesi:** Piyasa düşüşlerinde volatil varlıkları stablecoin'e çevirme.
3. **DeFi getiri aracı:** Agresif kripto riski almadan blokzincir ekosistemine katılım.

Dikkat: Stablecoin'i "dolar hesabı" gibi düşünmek büyük yanılgıya yol açabilir. Dolar mevduatı TMSF güvencesindedir; stablecoin bu güvence kapsamında değildir.

[Enflasyona karşı korunma yöntemlerini](/blog/enflasyondan-nasil-korunur) araştırıyorsanız: stablecoin gerçek bir araç olmakla birlikte TL enflasyonuna karşı tek savunma hattı yapılmamalıdır; altın, döviz mevduatı ve [endeks fonları](/blog/endeks-fonu-nedir) ile çeşitlendirme daha sağlam bir strateji sunar.

Kripto yatırımına ilk kez adım atıyorsanız [Ethereum nedir rehberimiz](/blog/ethereum-nedir) size blokzincir ekosistemini daha geniş bir perspektiften anlatacaktır.

## Özet

- **Stablecoin**, değeri 1 dolara (veya başka bir referansa) sabitlenmiş kripto paradır; fiyat dalgalanmasından korunmak için kullanılır.
- Üç tür vardır: **fiat destekli** (USDT, USDC — en yaygın), **kripto teminatlı** (DAI) ve **algoritmik** (en riskli — Terra/LUNA çöküşü bunun kanıtıdır).
- USDT hacim lideridir; USDC şeffaflıkta öne çıkar. Hangisini seçeceğiniz kullanım amacınıza göre değişir.
- Stablecoin "risksiz" değildir: karşı taraf riski, rezerv şeffaflığı sorunu, düzenleyici değişiklik ve algoritmik çöküş riskleri gerçektir.
- Türkiye'den SPK lisanslı borsalar aracılığıyla kolayca alınabilir; saklama yöntemini tutara ve kullanım amacına göre belirleyin.

---

*Bu içerik yatırım tavsiyesi değildir; genel bilgilendirme amaçlıdır. Kripto varlıklar ve stablecoin'ler yüksek risk içerebilir. Yatırım kararı almadan önce kendi mali durumunuzu ve risk toleransınızı değerlendirin; gerekirse lisanslı bir finansal danışmandan destek alın.*
