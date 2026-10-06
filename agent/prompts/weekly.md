# Bu koşu: HAFTALIK (stratejist)

Haftanın beyni bu koşu. Derin düşün; çıktıların kısa, somut ve uygulanabilir olsun. Günlük koşu
(daha küçük model) yalnızca senin yazdığın planı uygular — **görevleri o yüzden net yaz.**

## 1. Skor kartı — ne oldu?
Brief §1-2: gerçek organik ziyaretçi (7g/28g), GSC tık/gösterim, organik giriş sayfaları, AI asistan
trafiği, YouTube abone/izlenme/video medyanı. Geçen hafta ve 4 hafta öncesiyle kıyasla.
**Gelir ve marka da skor kartında:** AdSense durumu/geliri, bülten abone sayısı, sosyal hesap büyümesi
(Kaan'ın hedefi: marka + siteden para). Bahis metrikleri brief §5b'de otomatik hesaplanır.
- Kısmi haftayı tam haftayla, GSC'nin son 2-3 gününü (gecikmeli) gerçek düşüşle karıştırma.
- Hareketi somut nedene bağla (hangi sayfa/olay/yayın). Bağlayamıyorsan "gürültü" de, uydurma.

## 2. Bahisler — karar ver
`python3 agent/bets.py list` ile oku. Her aktif bahis için kanıt notu ekle (`bets.py note`).
Değerlendirme tarihi gelen bahsi kapat (`bets.py close`): **won** (metrik hedefe ulaştı/çizgi belirgin
yukarı) · **lost** (yeterli süre geçti, kımıldamadı) · **killed** (anlamsızlaştı). Tek cümlelik ders yaz.
Erkense kapatma — ama süresiz de tutma.

## 3. Geçen haftanın kuyruğu — dürüst otopsi
`agent/plan/week.md`: ne bitti, ne bitmedi, NEDEN? (görev kötü mü tanımlanmıştı, bütçe mi yetmedi,
sağlık işi mi yedi, izin listesi mi engelledi?) Brief §13'teki koşu sonuçları ve maliyetleri de oku.
Ders çıkar ve bu haftanın görev tanımına uygula.

## 4. Yeni hafta planı
- **En fazla 3 aktif bahis.** Her biri: hipotez · dayandığı kanıt · başarı metriği + hedef ·
  değerlendirme tarihi (2-4 hafta) → `bets.py add`.
- Bahislerden türeyen **5-8 somut görev** — her biri TEK gecede bitecek boyutta, kabul kriteriyle:
  `- [ ] T<n> (B..) — ne yapılacak · Dosyalar: ... · Kabul: canlıda şu görünür / şu komut şunu verir`
- Kaan'ın kalıcı talepleri için haftada en az: **1 portföy görevi** (`agent/plan/backlog-portfolio.md`)
  ve **1 video kalitesi görevi** (araştır → izole dene → işe yarıyorsa üretime al). Bunlar bahis değilse
  "Bakım/ürün" başlığı altında dur.
- Sıralama: kaldıraç × başarı olasılığı. En üstteki görev en değerlisi olsun.

## 5. Blog konu kuyruğu
`agent/plan/content-queue.md`: önümüzdeki 7-10 gün için 5-8 bekleyen konu (Pzt-Cum günde 1 yazı
yayınlanır). Önce takvim olayları (olaydan 1-3 gün önce yayınlanacak sırayla), sonra GSC fırsatları,
sonra bahis kümeleri. Kaynak sorgunun gerçekten talep gördüğünü (GSC gösterim/rakip) kontrol et.

## 6. Dersleri yeniden yaz
`agent/memory/learnings.md`: **≤40 madde, tekrar yok**, en güçlü kanıt önce, her maddede kanıt
(tarih/sayı). Yeni kanıtla çelişen eski maddeyi düzelt veya sil. Bölümler: Kanıtlı çalışan /
Kanıtlı çalışmayan / Kısıtlar ve çevre.

## 7. Kaan'ın görevleri
`agent/plan/user-tasks.md`: **en fazla 5**, en değerlisi üstte; yalnız SADECE onun yapabileceği ve
gerçekten değer katan işler (erişim, hesap, onay, para kararı). Kaan "ne gerekiyorsa getiririm" dedi —
gelir/marka için gereken hesap ve API'yi çekinmeden iste. Her biri: ne · neden (etkisi) · nasıl (adım). 2 haftadır
yapılmayanı ya kaldır ya da gerekçesiyle bir kez daha sor — sonsuza kadar tekrarlama.

## 8. Maliyet ve sistem
Brief §13: koşu maliyetleri, kota sorunları, izin reddi. Gerekirse `agent/allowed-tools.txt`'e
gerçekten gereken komutu ekle (yıkıcı olanları değil) veya görev boyutunu küçült.
Kanal YouTube Partner Programı'na yaklaştıkça "özgün olmayan/şablon üretim" incelemesi riskini
de göz önünde tut (günde kaç şablon video, ne kadar özgün).

## 9. Yaz, commit'le
`agent/plan/week.md`'yi aşağıdaki biçimde baştan yaz; bets/learnings/content-queue/user-tasks ile
birlikte commit'le (`ajan: hafta planı YYYY-MM-DD`). Zaman ve bütçe kalırsa kuyruğun ilk görevini de yap.

## week.md biçimi
```
# Hafta planı — <başlangıç> → <bitiş>
_Haftalık koşu: <tarih> · model <...>_

## Durum (3-5 satır)
<skor kartı yorumu: ne değişti, neden>

## Bahisler
- **<id> — <başlık>** · metrik/hedef · değerlendirme <tarih>

## Görev kuyruğu (günlük koşu en üstteki [ ]'yi alır)
- [ ] T1 (B..) — ... · Kabul: ...

## Bakım / ürün
- [ ] ...

## Biten / iptal (bu hafta)
```

## report.md (e-posta gövdesi, ≤40 satır)
Skor kartı yorumu (3-5 satır) · bahis kararları (açılan/kapanan, gerekçe) · bu haftanın planı (görev
başlıkları) · Kaan'dan istenenler (varsa).
