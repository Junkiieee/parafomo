---
title: "Volatilite Nedir? Standart Sapma ve Sharpe Oranıyla Risk Ölçümü"
description: "Volatilite nedir, yatırımda nasıl ölçülür? Standart sapma, Sharpe oranı ve beta katsayısıyla portföy riskini anlamanın eksiksiz rehberi."
pubDate: 2026-09-03
category: "Yatırım"
tags: ["volatilite nedir", "standart sapma", "sharpe oranı", "risk ölçümü", "beta katsayısı", "portföy riski"]
readingTime: 8
featured: false
faq:
  - q: "Volatilite nedir, yatırımda ne anlama gelir?"
    a: "Volatilite, bir yatırım aracının fiyatının belirli bir dönemde ne kadar geniş bir aralıkta dalgalandığını gösterir. Yüksek volatilite hem büyük kazanç hem de büyük kayıp ihtimalini artırır; bu yüzden risk ölçümünün temel göstergesidir."
  - q: "Sharpe oranı nasıl hesaplanır ve ne anlama gelir?"
    a: "Sharpe oranı = (Portföy getirisi − Risksiz faiz oranı) / Standart sapma formülüyle hesaplanır. Oran ne kadar yüksekse, alınan risk başına elde edilen getiri o kadar iyidir. 1'in üzeri iyi, 2'nin üzeri mükemmel kabul edilir."
  - q: "Beta katsayısı 1'den büyük ne anlama gelir?"
    a: "Beta > 1 olan bir hisse, piyasa %1 yükseldiğinde ortalamanın üzerinde yükselir; düştüğünde de daha sert düşer. Yüksek beta = yüksek kaldıraçlı piyasa duyarlılığı anlamına gelir."
  - q: "Volatilite ile risk aynı şey midir?"
    a: "Volatilite riskin önemli bir bileşenidir ancak tamamı değildir. Yüksek volatilite hem yukarı hem aşağı salınım anlamına gelir. Asıl risk, yanlış zamanda satmak zorunda kalmaktır; bu yüzden yatırım ufku da kritik değişkendir."
  - q: "Türkiye'de volatiliteyi takip etmek için hangi araçlar kullanılır?"
    a: "BIST hisse senetleri için KAP üzerinden geçmiş fiyat verilerini indirebilir, volatiliteyi hesaplayabilirsiniz. Küresel ölçekte VIX (ABD korku endeksi) en yaygın volatilite göstergesidir. Türk piyasasına özgü olarak BIST Volatilite Endeksi (VBI) de takip edilebilir."
---

Borsada büyük kazançları fırsatlar getirir; büyük kayıpları ise genellikle fark edilemeyen bir tehlike: **volatilite**. "Bu hisse çok riskli" dediğinizde aslında çoğunlukla yüksek volatiliteden söz ediyorsunuz. Peki volatilite nedir, yatırımda nasıl ölçülür ve portföy kararlarınıza nasıl yansıtırsınız? Bu rehberde adım adım açıklıyoruz.

## Volatilite Nedir?

**Volatilite**, bir varlığın fiyatının belirli bir süre içinde ne kadar geniş bir aralıkta dalgalandığını ifade eder. Matematiksel olarak fiyat değişimlerinin **standart sapması** ile ölçülür.

Basit bir örnekle: İki hisse düşünün.

- **A Hissesi:** Son 12 ayda aylık getirisi +5%, −4%, +6%, −3%, +5% gibi seyretmiş.
- **B Hissesi:** Aynı dönemde +20%, −18%, +25%, −15%, +22% gibi seyretmiş.

Her ikisi de yıl sonunda benzer bir getiri sunmuş olabilir; ancak B hissesinin volatilitesi A'nın dört katı. Bu, B'yi tutan yatırımcının aynı getiri için çok daha geniş iniş-çıkışlara katlanmak zorunda kaldığı anlamına gelir.

Volatilite tek başına ne iyi ne kötüdür — ama risk yönetimi için **vazgeçilmez** bir ölçüttür.

## Standart Sapma: Volatilitenin Matematik Dili

Yatırımda volatilite çoğunlukla **yıllık standart sapma** biçiminde ifade edilir ve genellikle yüzde olarak gösterilir.

**Hesaplama mantığı:**
1. Son N dönemin getirilerini toplayın, ortalamasını bulun.
2. Her getirinin ortalamadan farkını hesaplayın.
3. Bu farkların karesini alın, ortalamasını bulun (varyans).
4. Varyansın karekökü standart sapmadır (günlük).
5. Günlük standart sapmayı yıllıklaştırmak için √252 ile çarpın (borsada yılda yaklaşık 252 işlem günü vardır).

| Varlık Sınıfı | Yıllık Volatilite (yaklaşık) |
|---|---|
| ABD Hazine Bonosu (kısa vade) | %1–3 |
| Altın | %12–18 |
| S&P 500 | %15–20 |
| BIST 100 (TL bazında) | %20–30 |
| Bireysel küçük hisse | %40–80+ |
| Bitcoin | %60–100+ |

Bu tablo size genel bir perspektif sunar; gerçek rakamlar piyasa koşullarına göre önemli ölçüde değişir.

## Beta Katsayısı: Piyasaya Göre Duyarlılık

Standart sapma varlığın kendi içsel dalgalanmasını ölçerken, **beta (β)** bir hissenin piyasanın hareketlerine karşı ne kadar duyarlı olduğunu gösterir.

- **Beta = 1:** Hisse piyasayla aynı hızda hareket eder.
- **Beta > 1:** Piyasa %1 yükselirse hisse daha çok yükselir; piyasa %1 düşerse daha çok düşer (yüksek duyarlılık).
- **Beta < 1:** Piyasadan daha az dalgalanır; defansif hisse özelliği.
- **Beta < 0:** Piyasayla ters yönde hareket eder (altın bazı dönemlerde bu özelliği gösterir).

**BIST'te pratik kullanım:** Portföyünüzde yüksek beta hisseler varsa piyasa rallisinde daha çok kazanırsınız — ancak düzeltme dönemlerinde de ortalamadan daha sert vurulursunuz. Defansif portföy için beta < 1 hisseler veya sabit getirili araçlarla [portföy çeşitlendirmesi](/blog/portfoy-cesitlendirmesi-nasil-yapilir) yapmak mantıklıdır.

## Sharpe Oranı: Risk Başına Gerçek Getiri

İki portföy aynı getiriyi sağlıyorsa hangisi daha iyi? Daha **az riskle** aynı getiriyi sağlayanı. Bunu ölçmek için **Sharpe Oranı** kullanılır.

**Formül:**

> Sharpe Oranı = (Portföy Getirisi − Risksiz Faiz) / Standart Sapma

**Risksiz faiz** olarak genellikle kısa vadeli devlet tahvili faizi kullanılır (Türkiye için TCMB politika faizi yakın bir referans).

| Sharpe Oranı | Yorum |
|---|---|
| < 0 | Risksiz araçtan daha düşük getiri |
| 0 – 0.5 | Zayıf risk-getiri dengesi |
| 0.5 – 1.0 | Kabul edilebilir |
| 1.0 – 2.0 | İyi |
| > 2.0 | Mükemmel (sürdürülmesi zor) |

**Örnek:** A portföyü yıllık %30 getiri sağlarken standart sapması %40. B portföyü %20 getiri sağlarken standart sapması %10. Risksiz faiz %18 olsun.

- A'nın Sharpe'ı: (30 − 18) / 40 = **0.30**
- B'nin Sharpe'ı: (20 − 18) / 10 = **0.20**

Ham getirisi düşük olan A, risk başına daha iyi bir iş çıkarmış. Bu tablo, salt getiriye odaklanmanın neden yanıltıcı olduğunu gösterir.

## Volatilite, Risk ve Yatırım Ufku Üçgeni

Volatilite tehlikeli görünür; ancak tek başına yeterli bir risk göstergesi değildir. Asıl kritik soru şudur: **Ne zaman paraya ihtiyacınız var?**

- **Kısa vade (< 1 yıl):** Yüksek volatiliteli araçlardan kaçının. Düşüş dönemine denk gelirseniz satmak zorunda kalabilirsiniz.
- **Orta vade (1–5 yıl):** Orta volatiliteye katlanılabilir; ancak nakit tampon tutun.
- **Uzun vade (5+ yıl):** Volatilite büyük ölçüde zamana yayılır. Tarihsel olarak BIST ya da S&P 500 gibi endekslerde 10 yıl tutma, negatif getiri riskini önemli ölçüde azaltmıştır.

Bu yüzden yüksek volatiliteli bir hisse, uzun vadeli yatırımcı için katlanılabilir; ancak aynı hisse, birkaç ay içinde paraya ihtiyaç duyacak biri için uygunsuz olabilir.

[Risk ve getiri ilişkisi](/blog/risk-getiri-iliskisi) yazımızda bu dengeyi daha ayrıntılı ele alıyoruz.

## Volatiliteyi Nasıl Yönetirsiniz?

### 1. Pozisyon büyüklüğünü sınırlayın

Yüksek volatiliteli bir varlığa tüm portföyünüzü yatırmak, küçük bir düşüşü bile dayanılmaz hale getirir. Her pozisyonun portföydeki ağırlığını önceden belirleyin.

### 2. Stop-loss emirleri kullanın

Özellikle kısa vadeli pozisyonlarda, zararın belirli bir seviyeyi geçmesini engellemek için [stop-loss emirleri](/blog/stop-loss-nedir-zarar-kesme) kullanın. Bu, "bekleriz, düzelir" tuzağına düşmekten korur.

### 3. Korelasyonu düşük varlıklar karıştırın

Tüm varlıkları aynı anda hareket eden araçlardan oluşturmak, çeşitlendirmenin faydalarını sıfırlar. Altın, tahvil ve hisse senetleri tarihsel olarak düşük veya negatif korelasyon göstermiştir; bu, bir düşerken diğerinin tampon sağlaması anlamına gelir.

### 4. VIX'i bir barometre olarak kullanın

[VIX (Korku Endeksi)](/blog/vix-nedir-korku-endeksi), S&P 500 opsiyonlarından türetilen ve piyasanın gelecek 30 güne dair volatilite beklentisini ölçen bir göstergedir. VIX 30'un üzerine çıktığında piyasalar aşırı korku modundadır; bu tarihsel olarak uzun vadeli alım fırsatlarına daha yakın olduğunuza işaret edebilir — ancak yatırım kararını tek bir göstergeye bağlamayın.

## Varlık Sınıflarının Volatilite Karşılaştırması

| Araç | Kısa Vadeli Volatilite | Uzun Vadeli Stabilite | Türk Yatırımcısı Notu |
|---|---|---|---|
| TL Mevduat | Çok düşük | Yüksek (nominal) | Enflasyon reel getiriyi eritebilir |
| Altın (TL) | Orta | Orta-yüksek | Kur koruması da sağlar |
| BIST 100 | Yüksek | Orta (uzun vadede) | Döviz kuru etkisi hesaba katılmalı |
| Dolar/TL | Orta-yüksek | Kur belirsizliği | Merkez bankası müdahale riski |
| Bireysel hisse | Çok yüksek | Şirkete göre değişken | Tek hisse yoğunlaşmasından kaçının |
| Bitcoin | Çok yüksek | Belirsiz | Spekülatif kısım küçük tutulmalı |

## Özet

- **Volatilite**, fiyat dalgalanmalarının genişliğini ölçer; yatırım riskinin temel göstergesidir.
- **Standart sapma** volatiliteyi sayısallaştırır; yüksek değer daha geniş fiyat salınımı anlamına gelir.
- **Beta katsayısı**, bir hissenin piyasayla kıyasla ne kadar duyarlı olduğunu gösterir.
- **Sharpe oranı**, alınan risk başına elde edilen getiriyi ölçer; iki portföyü karşılaştırmanın en sağlıklı yoludur.
- Volatilite tek başına ne iyi ne kötüdür — **yatırım ufkunuzla** birlikte değerlendirilmelidir.
- Yüksek volatiliteyle başa çıkmanın en etkili yolları: pozisyon sınırlaması, stop-loss ve düşük korelasyonlu varlık karışımıdır.

---

*Bu içerik yalnızca bilgilendirme amaçlıdır; yatırım tavsiyesi değildir. Her yatırım kararı kişisel risk toleransınıza, ufkunuza ve mali durumunuza göre alınmalıdır.*
