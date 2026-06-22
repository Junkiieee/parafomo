# ParaFOMO — X (Twitter) Yerel Paylaşım Botu (Windows)

Local makinende çalışır. Senin **gerçek tarayıcı oturumunla** X'e girer ve siteden
(RSS) gelen **en yeni yazıyı** günde bir kez, insan temposunda paylaşır. Bu sunucuya
veya repo'ya bağımlı değildir; en yeni yazıyı `parafomo.com/rss.xml`'den okur ve
`posted.json` ile aynı yazıyı iki kez atmaz.

> ⚠️ **Uyarı:** Tarayıcı otomasyonu X kullanım şartlarına aykırıdır. Düşük hacim
> (günde 1) + gerçek oturum riski **azaltır** ama **sıfırlamaz**. Hesap askıya
> alınabilir. Sorumluluk sana aittir. Daha güvenli yol resmi API'dir (`.env`'deki
> anahtarlar) ama linkli post ücretlidir.

---

## Kurulum (tek seferlik)

### 1. Node.js kur
https://nodejs.org → **LTS** sürümünü indir, kur. Kurulum sonrası kontrol:
```
node --version
```

### 2. Google Chrome kurulu olsun
Bot, daha az "bot sinyali" için kurulu **gerçek Chrome**'u kullanır. Chrome yoksa
bundled Chromium'a düşer ama Chrome önerilir: https://www.google.com/chrome/

### 3. Bot dosyalarını al
Bu `x-bot` klasörünü local makinene kopyala (repo'yu `git clone` ettiysen zaten içinde).
Klasörde bir komut istemi (cmd) aç:
```
cd C:\...\parafomo\x-bot
npm install
npx playwright install chrome
```
> `npm install` Playwright'i kurar. `npx playwright install chrome` Chrome'u
> Playwright'e tanıtır (Chrome zaten kuruluysa bunu atlayabilirsin).

### 4. X'e bir kez elle giriş yap
```
node post-x.mjs --login
```
Açılan tarayıcıda X hesabına normal şekilde giriş yap (gerekirse 2FA). Giriş
bitince **pencereyi kapat**. Oturum `x-bot\.profile` klasörüne kaydedilir; bir daha
giriş istemez.

### 5. Test et (paylaşmadan)
```
node post-x.mjs --dry
```
Hazırlanan tweet'i ekrana yazar, paylaşmaz. Metin iyiyse gerçek paylaşımı dene:
```
node post-x.mjs
```
(İlk çalıştırmada 5-40 dk rastgele bekleme yapar — bu kasıtlı, bot sinyalini azaltır.
Test için beklemeyi görmek istemezsen `--dry` kullan.)

---

## Otomatik günlük çalıştırma (Task Scheduler)

1. Başlat → **Task Scheduler** (Görev Zamanlayıcı) aç
2. Sağda **Create Task** (Görev Oluştur) — *Basic Task değil, normal Task*
3. **General** sekmesi: ad ver (ör. `ParaFOMO X bot`). "Run only when user is logged on"
   seçili kalsın (tarayıcı görünür çalışacak).
4. **Triggers** → New → Daily → saat **12:30** (makinen genelde açık olduğu saat).
   *(Bot kendi içinde ayrıca 5-40 dk rastgele gecikme ekler; sabit saat sorun değil.)*
5. **Actions** → New → Program/script: `run-x-bot.bat` dosyasının tam yolu:
   ```
   C:\...\parafomo\x-bot\run-x-bot.bat
   ```
   "Start in" alanına da `x-bot` klasör yolunu yaz.
6. **Conditions**: "Start the task only if the computer is on AC power" işaretini
   kaldırabilirsin (laptop'ta pille de çalışsın).
7. OK → bitti.

Artık makinen açıkken her gün, en yeni yazı paylaşılmamışsa, otomatik paylaşılır.
Yeni yazı yoksa hiçbir şey yapmaz (zaten paylaşılmışı tekrar atmaz).

---

## Komutlar

| Komut | Ne yapar |
|-------|----------|
| `node post-x.mjs --login` | Tarayıcıyı aç, X'e elle giriş yap (tek seferlik) |
| `node post-x.mjs --dry`   | Tweet'i derle ve yazdır (paylaşmaz) |
| `node post-x.mjs`         | En yeni yazıyı paylaş (paylaşılmadıysa) |

## Sorun giderme
- **"GİRİŞ YOK" yazıyor:** Oturum düşmüş. Tekrar `node post-x.mjs --login` yap.
- **Buton bulunamadı / selector hatası:** X arayüzünü değiştirmiş olabilir; bana
  haber ver, seçicileri güncellerim.
- **Log:** Otomatik çalıştırmalar `x-bot.log` dosyasına yazar.
- **Aynı yazı tekrar atılmaz:** `posted.json` paylaşılan linkleri tutar. Sıfırlamak
  için bu dosyayı silebilirsin.
