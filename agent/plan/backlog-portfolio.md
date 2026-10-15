# 💼 Portföy Takip — ürün backlog'u

> **2026-10-11 — ÜRÜNÜN YENİ EVİ: app.parafomo.com/portfoy/ (lobi mimarisi).** Kaan uygulamaları
> SATMAK istiyor; app.parafomo.com/ lobi (uygulama rafı), her uygulama `app/<slug>/` klasöründe.
> Portföy: `app/portfoy/` → `bash scripts/deploy-app.sh` → Caddy `/srv/parafomo-app`
> (backend aynı api.parafomo.com). Ortak stil `app/theme.css`. Eski /portfoy/panel duruyor (yönlendirme notlu).
> Bu backlog'daki UX maddeleri bundan sonra `app/portfoy/` içinde yapılır (Astro panel'e DEĞİL).
> **2026-10-11 AKŞAM — v3 "satılabilir ürün" paketi CANLI (commit 5119aae + cila):** değer grafiği
> (snapshot upsert + gece cron) · reel getiri (TÜFE zinciri) · "Ne olsaydı" kıyası (data/benchmarks.json,
> 15y boşluksuz, scripts/build-benchmarks.py GÜNLÜK veriden ay kapanışı türetir — aylık mumlar bozuk) ·
> hedefler · alarm v2 (day_pct + tekrarlayan; cron armed/rearm) · varlık detay grafiği (/public/history) ·
> hesap ayarları + KVKK silme + /kvkk sayfası · aylık özet maili (users.monthly_email, cron ay başı) ·
> /birikim DCA simülatörü + paylaşım kartı · GA4 (G-4KNGH3574V) · AppCTA köprüsü (8 veri sayfası + blog).
>
> **ARAÇ:** sunucuda headless Chromium var → tasarım değişikliğini EKRAN GÖRÜNTÜSÜYLE denetle:
> playwright-core + executablePath ~/.cache/ms-playwright/chromium_headless_shell-1148/chrome-linux/headless_shell
> (--no-sandbox). Örnek betikler RC scratch'ındaydı; desen: newContext({viewport,colorScheme}) → goto →
> screenshot. Demo moduna #demo-btn ile girilir (giriş gerektirmez).
>
> **Sıradaki adaylar (öncelik sırası):**
> 1. TÜFE serisini (data/tufe-aylik.json) 2021-01'e kadar RESMÎ kaynaktan WebSearch-doğrulamalı genişlet
>    → 5y+ dönemlerde reel getiri ve simülatör enflasyon satırı açılır (şu an dürüst notla gizli).
> 2. Birikim paylaşım kartını IG hattına bağla: haftada 1 otomatik "ayda X TL'yi Y'ye koysaydın" kartı
>    (scripts/ ile canvas yerine PIL'de aynı tasarım) — uygulamaya trafik hunisi.
> 3. Varlık detayına haber/temettü satırı (kaynak araştır) · grafikte 1A/3A chip'leri veri birikince zenginleşir.
> 4. ✅ İşlem defteri YAPILDI (2026-10-11 v4): transactions tablosu + satış + realize K/Z + birim görünümü
>    (₺/$/g). Kalan türevler: yıllık realize raporu, satışta FIFO seçeneği (şimdilik ort. maliyet).
> 5. ✅ v5 YAPILDI (2026-10-11): çok-varlık (USD/EUR/BTC/ETH/nakit, CoinGecko+Truncgil), sınıf bazlı
>    dağılım (fx yeşil #177245/#2F9E6A, kripto magenta #A23B8F/#C95CB0 — validator onaylı), XIRR +
>    öne çıkanlar satırı, /public/news varlık haberleri (detay kipinde).
> 6. SIRADAKİLER: çoklu portföy (cüzdanlar; premium bel kemiği — portfolios tablosu + FK migrasyonu,
>    DİKKATLİ planla) · TEFAS fon desteği (veri kaynağı araştır: tefas.gov.tr) · temettü takvimi
>    (kaynak araştır) · CSV içe aktarma · onboarding sihirbazı · ETH tarihsel grafik kaynağı.
> 7. Premium paket adayları (Kaan ödeme kararı verince): çoklu portföy, sınırsız alarm, aylık PDF rapor.
> Kaan 2026-10-11: "uygulama çok basit olmuş" → satılabilir derinlik öncelik: aday işler sırayla —
> pozisyon geçmişi/değer grafiği (günlük snapshot tablosu gerekir, şema onayı Kaan'dan), izleme listesi,
> fiyat alarmı (e-posta), çoklu portföy, hedef/oran analizi. Yeni eklenenler (yapıldı): gizlilik gözü,
> pay %, CSV dışa aktarma.



> **Durum: CANLI** — `https://api.parafomo.com` (systemd `parafomo-api`) + `/portfoy-takip` (halka açık
> SEO + üyeliksiz hesaplayıcı) + `/portfoy/panel` (üye paneli) + `/portfoy/sifre-sifirla`.
> Kaan'ın talebi (2026-09-02): ürün sürekli gelişsin (UX + portföy yönetimi). v2'de haftalık plana
> haftada en az 1 madde buradan girer (v1'de her gece zorunluydu; trafik ~50/hafta iken kayıt ~2 —
> önce trafik, ürün cilası sürer ama öncelik değil).

## Protokol (bir madde işlerken)
1. En üstteki `[ ]` maddeyi al (Kaan geri bildirimi her zaman en üste).
2. Uygula; güvenliği koru (localhost bind, CORS yalnız parafomo.com, parola hash, rate-limit, panel noindex).
3. Test: `npm run build` geçmeli; `backend/` değiştiyse geçici DB ile uvicorn + curl.
4. Deploy: frontend → commit + `bash scripts/deploy-push.sh`; backend → commit + deploy-push +
   `systemctl restart parafomo-api` + `curl -s https://api.parafomo.com/health`. Sırlar (`backend/.env`) commit'lenmez.
5. Canlıda doğrula; maddeyi `[x]` yap + `— YYYY-MM-DD: ne yapıldı, commit` satırı.

Kod: `backend/` + `src/pages/portfoy*` + `public/portfoy-*.js`. Dağıtım: `deploy/DEPLOY.md`. Venv: `/root/.venvs/parafomo-api`.

---

## BACKLOG (öncelikli — üstten işle)

### 🔴 Kullanıcı geri bildirimi (en yüksek öncelik)
- [x] **BIST hisse arama / otomatik tamamlama.** Kök sorun: kullanıcı "TÜPRAŞ"/"TUPRAS" yazdı, doğru
  kod **TUPRS** olduğu için canlı veri gelmedi. Kullanıcı **şirket adı VEYA kod** yazınca listeden
  doğru sembolü seçsin (ör. "tüpraş" → `TUPRS · Tüpraş`). Hem panelde (`a-symbol`) hem hesaplayıcıda
  (`.r-sym`). BIST sembol listesi bir `data/bist-symbols.json` (kod+isim) olarak paketlenir; istemci
  tarafı anlık arama. Liste kapsamıyorsa serbest metin + doğrulama (aşağıdaki madde) devrede kalsın.
  — 2026-09-04: `public/bist-symbols.json` (129 sembol) + `public/portfoy-autocomplete.js` (paylaşılan
  widget, Türkçe-aksan duyarsız, kod+isim arama) panel `a-symbol` + hesaplayıcı `.r-sym`'e bağlandı.
  Doğrulama testi: tüpraş/TUPRAS/tupras/Tüpraş→TUPRS, "türk hava"→THYAO, koç→KCHOL. build ✓ 163 sayfa.
  commit 42bfc26, push→Cloudflare.
- [x] **Ekleme anında sembol doğrulama + net hata.** BIST pozisyonu eklerken `/public/price` ile
  kontrol et; fiyat `null` ise KAYDETME ve net mesaj ver: "TUPRAS için canlı veri bulunamadı —
  Tüpraş'ın kodu TUPRS. Hisse arama kutusunu kullan." Aynı kontrolü hesaplayıcıda da iyileştir.
  — 2026-09-04: panel `add-form` submit'i önce girdiyi doğru ticker'a çözer, sonra `/public/price`
  ile kontrol eder; null ise KAYDETMEZ + net Türkçe hata. Hesaplayıcı calc-loop'u da ad/kodu çözer.
  commit 42bfc26.
- [x] **Tabloda "canlı veri yok" göstergesi + fiyat yenile + son güncelleme saati.** current_price
  null olan satırı görsel uyar (ikon+tooltip), "Fiyatları yenile" butonu, "son güncelleme HH:MM".
  — 2026-09-05: panel `pf-toolbar` (Fiyatları yenile butonu + spin anim + "Son güncelleme HH:MM"),
  null current_value satırı "⚠ veri yok" (help-tooltip: kod yanlış/kaynak yanıt vermiyor), toolbar'da
  stale varlık sayısı uyarısı. build ✓ 164. commit push→Cloudflare.

### 🟠 Portföy yönetimi (çekirdek işlevsellik)
- [x] **Pozisyon DÜZENLEME** (adet/maliyet/tarih güncelle). Şu an sadece ekle/sil. Backend `PATCH
  /portfolio/holdings/{id}` + panelde satır içi düzenleme.
  — 2026-09-06: Backend `PATCH /portfolio/holdings/{id}` (HoldingUpdate şeması, exclude_unset kısmi
  güncelleme, sahiplik kontrolü→404, gt=0 doğrulama→422). Test edildi: uvicorn+curl (update/422/404/
  summary yansıması ✓). Panelde satır-içi ✎ düzenleme: satırı adet/gram + birim maliyet + alış tarihi
  input'larına çevirir, Kaydet(PATCH)/Vazgeç. build ✓ 165; JS syntax node --check ✓. commit 6f41f15,
  push→Cloudflare + `systemctl restart parafomo-api`; PATCH route canlı doğrulandı (403=auth gerekli).
- [x] **Aynı sembolde birden çok alım → ortalama maliyet / birleştirme** (veya işlem geçmişi modeli).
  — 2026-09-07: Backend `add_holding` aynı (user,asset_type,symbol) pozisyonu bulunca ayrı satır
  açmaz → adet-ağırlıklı ortalama maliyete birleştirir + en erken alış tarihini korur (merge=200,
  yeni=201). Panel: birleşme olunca yeşil bilgi notu. Test: uvicorn+curl (10@100+5@130→15@110 tek
  satır, distinct sembol ayrı, 200/201 ✓); build ✓ 166. commit fc3b20a, push→Cloudflare + restart
  parafomo-api + health ✓ + POST route canlı (403=auth). Sıradaki 🟠: varlık ağırlık % + dağılım donut.
- [x] **Varlık başına ağırlık %** + **portföy dağılım grafiği** (donut: varlık türü/hisse). Hafif,
  bağımlılıksız SVG/canvas.
  — 2026-09-10: Panelde özet kartının altına **varlık dağılımı donut'u + legend** eklendi. Her varlığın
  ağırlığı güncel değere (yoksa maliyete) göre hesaplanıp bağımlılıksız SVG (r=15.9155/çevre≈100,
  stroke-dasharray) + %'li legend olarak gösterilir; tek pozisyonda gizli (<2 varlık). 10 renkli palet,
  değere göre azalan sıra. build ✓ 167. Frontend-only push→Cloudflare. Sıradaki 🟠: gün-içi değişim %
  sütunu (Yahoo regularMarketChangePercent).
- [x] **Gün içi değişim (%)** sütunu (Yahoo `regularMarketChangePercent`), toplamda günlük K/Z.
  — 2026-09-11: `prices.get_quote()` (price, change_pct) döner — BIST Yahoo `previousClose`, altın/gümüş
  Truncgil `Change` ("%0,43") parse. Panel tablosuna **"Bugün"** sütunu (%'li + TL K/Z small), özet
  kartına **günlük K/Z** (TL + %) satırı; canlı gün-içi veri yoksa gizli. Backend testi: TUPRS 10@400
  +0,60%→+₺25, altın 5gr +0,43%→+₺144,84, toplam +₺169,84 (+0,45%) ✓. build ✓ 168. commit 6c00197,
  push→Cloudflare + restart parafomo-api; openapi.json'da yeni alanlar canlı doğrulandı.
- [ ] **İzleme listesi (watchlist)** — sahip olmadan takip; ileride hedef-fiyat uyarısı (e-posta).

### 🟡 UX / cila
- [ ] **Yükleme/skeleton durumları** (özet + fiyat çekilirken), **hata toast'ları**, boş-durum rehberi.
- [x] **Mobil**: dokunuş hedefleri, tablo yatay kaydırma/iyi kart görünümü, form ergonomisi.
  — 2026-09-29: mobilde (≤560px) edit/sil butonları 28→40px, refresh büyütüldü, satır-içi edit
  input'ları 16px (iOS odak-zoom önleme), tabloya -webkit-overflow-scrolling:touch. build ✓, push→Cloudflare.
- [~] **Erişilebilirlik**: aria etiketleri, klavye navigasyonu, kontrast, focus halkaları.
  — 2026-09-30 (KISMİ): tab'lara `aria-selected` (aktif tab ekran-okuyucuya duyurulur, setMode'da güncellenir)
  + TÜM etkileşimli öğelere global `:focus-visible` halkası (klavye kullanıcısı odağı GÖRÜR; fare tıklamasında
  çıkmaz). build ✓ 177, commit 4e975e9, push→Cloudflare. Kalan: ok-tuşu tab-nav, kontrast denetimi.
- [ ] **Sayı/biçim**: TL/kuruş tutarlılığı, büyük sayılar (Mn/Mr), negatiflerde renk/işaret.
- [~] **Hesap ayarları**: ✅ ad + aylık özet (PATCH /auth/me) · ✅ hesabı sil KVKK (DELETE /auth/me + UI onaylı) · şifre değiştirme yalnız e-postalı sıfırlama akışıyla (ayrı uç YOK) · e-posta doğrulama YOK (opsiyonel). (10-15 kontrol edildi)

### 🟢 Büyüme / SEO (retention → trafik)
- [ ] **"Portföyümü paylaş"** — anonim snapshot linki/görseli (büyüme kancası, IG/Telegram'a uygun).
- [ ] **Tanıtım sayfasını derinleştir** (`/portfoy-takip`): örnek portföyler, daha çok SEO içerik,
  iç link (altın/bist/halka-arz sayfalarından ve blog'dan), FAQ genişlet.
- [x] **Panelden içeriğe köprü**: Analiz'de "İlgili veri" kartları (varlık türüne göre parafomo.com getiri/hesaplama sayfaları, UTM utm_source=app&utm_medium=portfoy) + hisse detayında halka arz şirket sayfası (deploy-app.sh halka-arz-map.json üretir) · 2026-10-15

### 🔵 Sağlamlık / altyapı
- [ ] **Fiyat kaynağı dayanıklılığı**: Yahoo 429/boş için yedek kaynak + cache süresini akıllı uzat;
  toplu fiyat çekiminde tek tek yerine paralel/batch.
- [ ] **Basit kullanım metriği**: kayıt/giriş/pozisyon-ekleme sayaçları (gizlilik dostu) → haftalık öğren.
- [ ] **Testler**: backend için küçük pytest, kritik akışlar için jsdom smoke — regresyon önle.

---

## GÜNLÜK KAYIT (her gece buraya EKLE — üzerine yazma)
- 2026-09-02: Sistem kuruldu ve TAMAMEN CANLI (backend+panel+SEO araç+Google+şifre sıfırlama).
  Yol haritası oluşturuldu; günlük geliştirme bu geceden itibaren buradan işlenecek.
- 2026-09-04: BIST hisse arama/autocomplete + ekleme anında canlı-fiyat doğrulaması (🔴 ilk 2 madde).
- 2026-09-05: Tabloda "canlı veri yok" göstergesi + "Fiyatları yenile" butonu + "Son güncelleme HH:MM"
  (🔴 3. madde tamam). Böylece kullanıcı sessiz-veri-yok durumunu artık GÖRÜR ve elle tazeleyebilir —
  09-04'teki doğrulama zincirini kapatan UX parçası (ekleme engellenirse de mevcut satırda kaynak
  geçici düşerse görünür). Sıradaki: 🟠 pozisyon DÜZENLEME (PATCH backend + satır-içi).
- 2026-09-06: Pozisyon DÜZENLEME (🟠 ilk madde) — PATCH backend + satır-içi ✎ düzenleme UI.
  Kullanıcı yanlış girdiği pozisyonu artık silip-yeniden-eklemek yerine düzeltiyor (friction ↓ =
  retention ↑). Sıradaki 🟠: aynı sembolde çoklu alım → ortalama maliyet / işlem geçmişi.
- 2026-09-10: Varlık dağılımı donut + ağırlık % (🟠 madde tamam). Özet kartının altında bağımlılıksız SVG
  donut + %'li legend; güncel değere (yoksa maliyete) göre ağırlık, tek pozisyonda gizli. build ✓ 167,
  frontend-only push→Cloudflare. Kullanıcı portföy dağılımını tek bakışta görüyor = retention. Sıradaki:
  gün-içi değişim % sütunu (Yahoo regularMarketChangePercent).
- 2026-09-24: 🟡 UX — hata toast'ları (KISMI). `loadPortfolio` non-401 hatalarda (ağ/500/api erişilemez)
  artık sessiz kalmıyor: kırmızı banner + "Yeniden dene" butonu. Önceden catch bloğu tüm hataları
  yutuyordu → kullanıcı boş/eski panelle kalıyordu. build ✓ 171, commit 8606213 push→Cloudflare.
  Not: 2 kayıt gerçeği ışığında ürün-derinleştirme minimum tutuldu; watchlist (🟠) ertelendi, enerji
  düşük-risk UX cilası + IG hijyeni + SFX (YouTube) + iç-link (SEO) hamlelerine dağıtıldı. Sıradaki 🟡:
  yükleme/skeleton durumları (özet+fiyat çekilirken).
- 2026-09-26: 🟡 boş-durum onboarding rehberi. Yeni kayıt olan kullanıcının gördüğü ilk ekran tek satırlık
  "henüz pozisyonun yok" idi → 3-adımlı onboarding kartına çevrildi (ikon + başlık + "nasıl çalışır" 3 adım +
  "+ İlk pozisyonu ekle" CTA butonu → ekleme formunu açar, a-type'a odaklanır, forma smooth-scroll). 2 kayıt
  gerçeği ışığında onboarding friction'ı = en yüksek kaldıraçlı retention noktası. build ✓ 174, frontend-only
  push→Cloudflare. Sıradaki 🟡: yükleme/skeleton (özet+fiyat çekilirken — kısmen var, refresh sırasına genişlet).
- 2026-09-28: 🟡 yükleme/skeleton — refresh sırasına genişletildi. Önceden "Fiyatları yenile"de yalnız
  buton dönüyordu; özet değerleri eski rakamla duruyordu (güncelleniyor cue'su yok). loadPortfolio(refreshing)
  parametresi eklendi: elle yenilemede özet-kartına mevcut `.summary-card.loading` shimmer'ı uygulanır
  (ilk-yükleme skeleton'ıyla aynı CSS, ek bağımlılık yok), render bitince kalkar. Kullanıcı fiyatların
  gerçekten çekildiğini GÖRÜR. build ✓ 175, frontend-only push→Cloudflare. Sıradaki 🟡: mobil dokunuş hedefleri.
- 2026-09-29: 🟡 mobil ergonomi — dokunuş hedefleri (edit/sil 40px), iOS zoom önleme (edit input 16px),
  tablo touch-scroll. build ✓, frontend-only push→Cloudflare. Sıradaki 🟡: erişilebilirlik (aria/klavye/kontrast).
- 2026-09-30: 🟡 erişilebilirlik (KISMİ) — tab'lara aria-selected + tüm etkileşimli öğelere global
  :focus-visible halkası (klavye kullanıcısı odağı görür). 2 kayıt gerçeği → min ürün-derinleştirme, düşük-risk
  a11y cilası. build ✓ 177, commit 4e975e9, push→Cloudflare. Sıradaki 🟡: sayı/biçim (TL/kuruş, Mn/Mr, negatif renk).
