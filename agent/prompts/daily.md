# Bu koşu: GÜNLÜK (operatör)

Planı haftalık koşu yazdı; senin işin onu **uygulamak**. Strateji tartışma, yeni bahis açma.

## Sıra
1. **Sağlık (önce bu):** Brief §3'te 🔴 GECİKTİ/HATA bir üretim hattı, yarım rebase, kırık build veya
   Claude durumu sorunu varsa → kök nedeni bul, düzelt, doğrula. Bu, plandaki görevden önce gelir.
   (Duraklatma/kota kaynaklı tek seferlik gecikme hata değildir — bir sonraki çalışmayı bekle.)
   Düzeltemiyorsan `agent/plan/user-tasks.md`'ye Kaan için tek net görev yaz.
2. **Yarım iş:** Brief §14'te `agent-wip` stash'i varsa incele (`git stash show -p stash@{N}`):
   değerliyse `git stash pop` + bitir; değilse `git stash drop`.
3. **Görev:** `agent/plan/week.md` → "Görev kuyruğu"ndaki EN ÜSTTEKİ `- [ ]` görevi al ve UÇTAN UCA bitir:
   kod/içerik → `npm run build` → commit → `bash scripts/deploy-push.sh` → canlıda doğrula (curl).
   - Bitince satırı `- [x] ... → sonuç (link/sayı) · YYYY-MM-DD` yap.
   - Tek gecede bitmeyecek kadar büyükse: ilk anlamlı parçayı bitir + yayınla, kalanını yeni satır olarak
     kuyrukta bırak.
   - Görev artık anlamsızsa (veri değişti, zaten yapılmış): `- [-] ... — iptal: gerekçe` yap, sıradakine geç.
4. **Sonraki görevler:** önceki görev temiz bittiyse ve bütçe varsa sıradakine geç (gecede en fazla 3 görev).
5. **Konu kuyruğu:** `agent/plan/content-queue.md`'de bekleyen (`- [ ]`) konu < 3 ise 3-5 konu ekle
   (kaynak sırası: yaklaşan takvim olayları → GSC fırsat sorguları → aktif bahsin kümesi).
   Her satır: başlık önerisi · hedef sorgu · neden şimdi (1 cümle) · iç-link hedefi.
6. **Rapor + commit:** `agent/state/report.md`'yi yaz; plan/kuyruk değişikliklerini commit'le.

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
