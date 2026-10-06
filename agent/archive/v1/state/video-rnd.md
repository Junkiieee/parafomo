# Video Kalitesi Ar-Ge Günlüğü (birikmeli — her gece EKLE)

Amaç: WebSearch ile internetten yeni video araçları/teknikleri araştır → dene →
retention'ı artıranı üretim hattına entegre et. Her gece buraya ekle, tekrar etme.

## 2026-09-02 — SEAMLESS-LOOP ENTEGRE EDİLDİ (araştır→dene→entegre döngüsünün "entegre" adımı)

**Bu gece = ENTEGRASYON gecesi (araştırma 08-28'de yapılmıştı; disiplin: bulguyu kuyrukta
tut, slot açılınca uygula).** 08-27-1 hook deneyi bu gece kapandı → retention slotu boşaldı →
kuyruğun #2'si SEAMLESS-LOOP uygulandı.

**Ne yaptım:** `viral-script.py` validation sonrası, `cta` beat'inin görselini `hook` beat'inin
görseliyle özdeşleştirdim (deterministik, tek-değişken). Hook chart değilse `segs[4].visual =
segs[0].visual`. Böylece Short loop'landığında kapanış→açılış görsel süreklilik ipucu vermez,
kanca 2. kez izlenir. Kanıtlı outlier: `stagflasyon-nedir %162`, `bankandaki-250-bin %95` zaten
tesadüfen loop'a yakın biten videolardı — sistematikleştirdim. Exp `2026-09-02-1` (retention,
TEK açık — eşzamanlılık tavanı). Kohort ~09-07 olgun.

**NEDEN sadece görsel-katman (audio değil):** format sabit 5-beat + cta'da "abone ol" sözü var
→ audio loop'lanamaz (abone ol → hook akışsız). Ama GÖRSEL katman loop'lanabilir: izleyici
kaydırmadan önce aynı sahneyi görünce döngü "kesintisiz" algılanır. Audio-callback (kapanış
cümlesi = kancaya callback) sıradaki iterasyon (kuyruk #2b) — ama o cta-spoken'ı değiştirir,
bu retention deneyi olgunlaşınca izole test edilecek (confound etmemek için ŞİMDİ değil).

**Sıradaki gece kuyruğu (GÜNCEL):** (1) 2026-09-02-1 seamless-loop OLGUNLAŞMASINI bekle (~09-07).
(2) audio-callback kapanış cümlesi (cta-spoken = hook callback; retention, loop kapanınca izole).
(3) series-labeling "X/N" (abone). (4) cut-synced SFX. (5) caption inactive-word DIM + MarginV (düşük).

## 2026-08-31 — TTS PROSODY / DELIBERATE PAUSE (grounded audit: bizde SSML yok, kaldıraç script-punctuation)

**Araştırdım (WebSearch):** "faceless finance Shorts retention 2026 TTS voice pacing prosody pause emphasis."
Kaynaklar: fluxnote.io/guides/best-text-to-speech-youtube-2026, fluxnote.io/guides/faceless-channel-retention-strategies-2026,
vidrush.ai/blog/why-your-ai-voiceover-sounds-robotic, virvid.ai/blog/best-ai-voice-models-faceless-ugc-scary-story.
**2026 best-practice özeti (retention için TTS pacing):**
1. **Deliberate pause placement:** sürpriz iddiadan SONRA, reveal/payoff'tan ÖNCE, bölümler arası **1-2sn boşluk** bırak
   → vurgu yaratır + izleyiciye işleme süresi verir + görsel geçişe zaman.
2. **Doğal nefes ritmi:** gerçek anlatıcı her 10-20 kelimede durur; AI SADECE noktalama olduğu yerde durur →
   nefes alacağın yere **virgül/nokta/üç nokta** koy.
3. **Cümle uzunluğu <15 kelime** (bizde zaten viral-script hook ≤7 kelime kuralı var, gövde kontrol edilmeli).
4. Finans = **otoriter, ölçülü ses** (yüksek-enerji değil) — bizde Chirp3-HD Orus/Schedar beğenildi, uyumlu.

**AUDIT — bizim TTS hattımız (`shorts-build-v4.py:161-170`):** Google TTS'e **`{"input":{"text": ...}}` = DÜZ METİN**
gönderiyoruz (SSML değil). Chirp3-HD zaten SSML `<break>` DESTEKLEMEZ (özel model, markup'ı yok sayar). Tek prosody
kaldıracımız: **(a) global `speakingRate`** ve **(b) metindeki noktalama.** Yani "pause placement" bizde SADECE
senaryo metnindeki noktalama ile yapılabilir — bu bir **viral-script.py üretim-metni** işi, ffmpeg/ses-motoru işi değil.

**TEK somut delta (grounded, izole):** `viral-script.py` beat metinlerine **kasıtlı duraklama noktalama**sı üretsin:
kancadaki iddiadan sonra **"…"** (üç nokta), beat1 payoff-köprüsünden/reveal'dan önce **kısa cümle + nokta**. Örn:
"Çeyrek altının %10'u senin değil… Peki nereye gidiyor?" → üç nokta Chirp3-HD'de belirgin nefes/gerilim duraklaması verir.
Bu, 08-27-1'in payoff-köprüsü ekseniyle AYNI aileden (hook→payoff ritmi) — yeni bir görsel değil, konuşma ritmi.

**NEDEN ENTEGRE ETMEDİM (eşzamanlılık tavanı — 8-retention-confound kök kuralı):** TTS-pause = ort retention %
metriğine roll-up. Açık `08-27-1` (hook bold-claim + payoff-köprü, ~09-01 olgun) ZATEN o metriği izliyor + kuyrukta
SEAMLESS-LOOP (#2) var. 3. retention deneyi açmak confound olur. **Karar:** 08-27-1 kapanınca, TTS-pause noktalamasını
hook/payoff ailesindendir diye **SEAMLESS-LOOP ile aynı batch'te** entegre et (ikisi de hook-ritmi/kapanış-akışı;
loop için "loop noktasında sessizlik boşluğu olmasın" kuralıyla da örtüşür — TTS son kelime→ilk kelime akışı).

**Sıradaki gece kuyruğu (GÜNCEL):** (1) 08-27-1 kapat (~09-01). (2) SEAMLESS-LOOP + **TTS-pause noktalama (aynı batch,
hook/kapanış-akışı ailesi)** — retention, tek-izole-batch. (3) series-labeling X/N (abone). (4) cut-synced SFX.
(5) Manim tek-odak/dim. (6) caption inactive-word DIM + MarginV (düşük öncelik). (7) dedike kapak. (8) bed.mp3.

Mevcut hat: senaryo=Claude · ses=Google Chirp3 TTS · görsel=Wikimedia+Pexels · montaj=ffmpeg/PIL · font=Anton/Oswald.

---
## 2026-08-30 — Zoom punch-in / pattern-interrupt cadence AUDIT: bizde ZATEN var, öneriyi AŞIYORUZ + veri-şoku Short girdisi entegre edildi

**Araştırdım (WebSearch):** "YouTube Shorts retention 2026 faceless finance pattern interrupt b-roll cut
frequency zoom punch-in". Kaynaklar: johnisaacson.co.uk/how-youtube-algorithm-works-2026,
virvid.ai/blog/faceless-youtube-algorithm-retention-2026, virvid.ai/blog/average-view-duration-vs-retention-youtube-2026,
joyspace.ai/pattern-interrupt-reset-attention-span, fluxnote.io/guides/faceless-channel-retention-strategies-2026.
**2026 best-practice özeti:** (1) ilk 5sn'de pattern-interrupt → static açılışa göre +%23 retention; (2) zoom
punch-in (%10-15 aynı açıda içeri dalma) = ekipmansız görsel reset; (3) görsel değişim her **3-5sn** (statik =
retention katili); (4) algoritma AVD'yi (average view duration) retention%'den daha çok umursuyor → uzunluk×tutma.

**AUDIT — bizim `shorts-build-v4.py` (satır 527-704):** ZATEN uyguluyoruz ve öneriyi AŞIYORUZ:
- hook beat = güçlü zoom-in punch (satır 640-647, ilk ~0.55sn tam→sıkı kadraj) ✓ (ilk-5sn interrupt)
- micro-cut faz bölme ~1.8-2.7sn + her faz taze wide→tight zoom + faz-parite yatay-yön alternasyonu (651-680) ✓
  → **1.8-2.7sn < önerilen 3-5sn = daha AGRESİF, öneriyi aşıyoruz** (bkz learning 08-27: 1.8sn micro-cut iyi-pratik korundu)
- orta beat mid-video punch-in + tease kartı (734, 828) ✓
→ Caption (08-29) ve seamless-loop (08-28) gibi: genel-geçer "pattern-interrupt ekle" tavsiyesi bizde YENİ İŞ DEĞİL.
Yeni tek kavramsal nokta: **AVD > retention%** — algoritma toplam izlenme-süresini ödüllendiriyor → daha uzun
tam-izlenen video daha iyi. Bu tam da **SEAMLESS-LOOP**'un (kuyruk #2) neden en yüksek kaldıraç olduğunu doğruluyor
(loop → hook 2. kez izlenir → AVD artar). 3. bağımsız teyit; loop kararı pekişti.

**BUGÜN ENTEGRE ETTİĞİM (retention-metriğini confound ETMEYEN üretim girdisi):** web↔YT köprüsü — yeni
`/dolar-getiri` + `/altin-getiri` veri varlıklarındaki çarpıcı kıyası `viral-script.py` WINNING_THEMES'e (d)
GERÇEK-VERİ ŞOKU ekseni olarak ekledim: "son 10 yılda altın TL bazında dolardan ~3.6 KAT fazla kazandırdı;
10.000 TL dolara → ~160 bin, altına → ~550 bin". Kazanan shock_number formatının (skor 317) + kazanan konu
ekseninin (altın/kayıp-korkusu) birebir yakıtı; #1 YT videomuzun ('10.000 TL altına koysaydın', 962 izlenme,
%55 ret) veri-güncel versiyonu. Tema-girdisi = topic seçimi; hook-mekaniği (08-27-1) DEĞİL → confound yok, exp açmadım.

**NEDEN retention edit ENTEGRE ETMEDİM (disiplin):** retention slotu `08-27-1` (hook bold-claim, ~09-01 olgun) +
kuyrukta SEAMLESS-LOOP (#2) ile dolu. Eşzamanlılık tavanı: 2. retention edit = 8-retention-confound kök hatası.

**Sıradaki gece kuyruğu (GÜNCEL):** (1) 08-27-1 kapat (~09-01). (2) SEAMLESS-LOOP (retention, tek-izole; artık
3x teyitli: loop→AVD↑). (3) series-labeling X/N (abone). (4) cut-synced SFX. (5) Manim tek-odak/dim.
(6) caption inactive-word DIM + MarginV (birleşik, düşük öncelik). (7) dedike kapak. (8) bed.mp3.
Açık yön: kinetik motion-graphics, arşiv/kolaj estetiği, daha güçlü ilk-3sn kanca.

---
## 2026-08-05 — İlk 3sn kanca + kelime-düzeyi altyazı araştırması → **v4 build motoru keşfi**

**Araştırdım (WebSearch):**
1. **İlk 3sn kanca / pattern-interrupt** (opus.pro, virvid.ai, conbersa.ai — 2026 kılavuzları):
   İzleyicilerin %50-60'ı ilk 3sn'de kayıyor. Kazanan: (a) görsel pattern-interrupt = açılışta hızlı **punch-in/zoom**, (b) 0:01'de görünür vaat, (c) **zaman dilimi içeren** kanca "%18 daha yüksek retention", (d) cesur iddia + merak boşluğu. → Bizim kanıtlı `backtest_return` formatımız (skor 175.7) zaten "bu yıl %21", "5 yılda" gibi zaman+şok-sayı kullanıyor; araştırma bunu DOĞRULUYOR.
2. **Kelime-düzeyi karaoke altyazı** (github: nicolaigaina/ai-video-captions, ffmpeg-ai, VidNo — Whisper+FFmpeg+ASS `\k`): Hormozi/MrBeast/karaoke stilleri, aktif kelime highlight. → **Bizde ZATEN VAR** (shorts-build ASS `\k` + whisper hizalama). Yeniden keşfetmeye gerek yok.

**Kritik keşif (dene aşamasında):** Üretim hattı `scripts/shorts-build.py` kullanıyor AMA repoda **`scripts/shorts-build-v4.py`** var ve tam da araştırmanın önerdiği retention özelliklerini içeriyor, canlıya bağlı DEĞİL:
- Açılışta **"hook" punch-in zoom** (`_kenburns` motion="hook") = pattern-interrupt.
- Sahne başına değişen Ken Burns (zoom-in/out/pan) → "her klip aynı" hissini kırar.
- Sinematik grading `eq=saturation=1.12:contrast=1.06` + `vignette` → düz stok hissini azaltır (hafıza: jenerik stok sevilmiyor).
- Aktif kelime rengi **canlı sarı #FFE14D** (canlıda YEŞİL; hafıza: sarı-highlight tercih ediliyor).
- Altyazı fontu 98 → **112px** (mobil okunurluk).
- Diff sadece 63 satır, TAMAMI görsel/motion katmanında; ses/senaryo/karaoke mantığı AYNI. CLI iki caller'la da uyumlu.

**Karar:** v4'ü izole test et (throwaway slug) → geçerli MP4 üretiyorsa canlı hattı (viral-daily.sh + shorts-daily.sh) v4'e çevir. Sonuç aşağıda.
**Build testi (izole, throwaway slug `zz-test-v4-motion`):** ✅ Geçti. 5 segment (hook+3 point+cta), Pexels B-roll fallback çalıştı, çıktı **1080×1920 h264/aac, 34sn, 7.7MB** geçerli MP4. Exit 0. Test dosyaları silindi.

**ENTEGRE EDİLDİ:** `viral-daily.sh` + `shorts-daily.sh` artık `shorts-build-v4.py` çağırıyor (deney 2026-08-05-4). Bundan sonraki TÜM Shorts açılış punch-in + hareketli kadraj + sinematik grading + sarı 112px altyazı ile üretilecek. Retention'ı Adım 0'da (birkaç video yayınlanınca) ölçüp deneyi kapat.

**Yan fayda (infra):** Eski `git push ... | sed ... || echo` deseni sed'in çıkış kodunu kontrol ettiği için push hataları SESSİZ yutuluyordu. `scripts/lib/gitsync.sh` → `git_push_retry` eklendi (gerçek PIPESTATUS + pull --rebase --autostash retry); video hattına bağlandı. Diğer ~8 cron scriptine yarın yayılacak.

**Sıradaki gece adayları (tekrar araştırma, buradan devam):** (1) Google TTS SSML `<mark>` timepointing ile whisper'sız kelime-zamanlaması (CPU'da whisper yavaş — hız kazancı). (2) Açılış 0-1sn'de tam-ekran metin "cold open" kartı (mevcut hook overlay'i güçlendir). (3) B-roll yerine kinetik motion-graphics sahne kütüphanesi (anim-demo.py mevcut — sahne şablonlarına bağla).


---
## 2026-08-06 — Animasyonlu sayı sayacı (count-up) → #1 formata (backtest_return) payoff motoru

**Araştırdım (WebSearch):**
1. **Animasyonlu count-up sayaç** (videocaptions.ai, krumzi, infogram "2026 data-viz trends"): ease-out ile hızlanıp HEDEFE yavaşlayarak inen sayaç, statik sayıya göre dikkat+hatırlamayı belirgin artırıyor — "motion earns the pause": göz hareketi yakalar, sayının "inişini" bekler, iniş = ödül. Binlik ayraç + ön/son ek (₺, %, x) + easing "landing" standart.
2. **Finansta animasyonlu zaman-serisi** (justanimations, infogram): Vanguard "paran yıl yıl büyüyor" animasyonu → uzun-vade abonelikte **+%32**. "Paran büyüyor" animasyonu finansal içerikte kanıtlı dönüşüm kaldıracı.

**Neden bizim için kritik:** En yüksek skorlu formatımız **backtest_return** (skor 129.9) tam olarak "10.000 TL koysaydın bugün X TL" = start→end sayı. Count-up bu formatın payoff anına birebir oturuyor. Kanıtlı kazananı görsel olarak güçlendirmek = düşük risk, yüksek kaldıraç.

**Denedim + inşa ettim:** `scripts/countup-overlay.py` — start→end, Türkçe biçimli (21.400 TL), ₺/%/x son ekli, ease-out cubic, marka sarısı #FFE14D + Anton font, üstte Oswald alt-etiket ("5 YILDA BIST 100"), okunur gölge. ŞEFFAF PNG kare dizisi + alfa'lı .mov üretir (ffmpeg overlay uyumlu). **Test:** start=10000 end=21400 dur=2.2 hold=0.6 → 84 kare + 17MB prores 4444 mov, exit 0. Landing karesi görsel QA'dan geçti (marka sarısı, net, B-roll üstünde okunur).

**Durum:** Araç HAZIR ve test edildi; henüz canlı hatta DEĞİL. Sıradaki gece: `shorts-build-v4.py`'de backtest_return manifestine `countup:{start,end,label}` alanı ekle → payoff sahnesinde static overlay yerine PNG-dizisi overlay (make_clip'e image-sequence overlay yolu). viral-script.py backtest_return üretirken start/end sayılarını manifeste yazsın. Entegre olunca retention deneyi aç (baseline: mevcut backtest_return ort. retention).

**Sıradaki gece adayları (buradan devam):** (1) count-up'ı v4 payoff sahnesine bağla (yukarıda). (2) Google TTS SSML `<mark>` timepointing → whisper'sız kelime zamanlaması (CPU hız). (3) Açılış 0-1sn cold-open tam-ekran metin kartı.

---
## 2026-08-07 — count-up sayaç CANLI hatta bağlandı + micro-payoff kesim araştırması

**Entegre ettim (dün inşa edilen count-up → canlı):** `shorts-build-v4.py` artık
`backtest_return` senaryolarının payoff (chart) beat'inde animasyonlu count-up
sayacı gösteriyor. Yeni: `make_countup()` (chart payload `amount`→`end_value`,
pct'den de türetir) + `make_clip(countup_dir=...)` image-sequence overlay yolu
(setpts ile konuşma başında girer, `eof_action=repeat` son değerde donar).
`countup-overlay.py`'ye `--cy` (dikey konum) eklendi → sayı üst-üçlüğe (y=600)
oturuyor, altyazılarla (y=1450) çakışmıyor. **SAVUNMACI:** count-up üretimi VEYA
count-up'lı ffmpeg klibi kırılırsa otomatik SAYAÇSIZ yeniden kurulur — canlı hat
asla düşmez (try/except fallback). İzole test: color-base + gerçek make_clip
countup yolu → geçerli MP4, payoff karesi görsel QA'dan geçti ("BUGÜN 21.395 TL",
net/okunur, marka sarısı landing). Deney `2026-08-07-1` açıldı (retention).

**Araştırdım (WebSearch — YENİ, bugün):** 2026 Shorts retention kılavuzları
(virvid.ai, opus.pro, faceless.so):
1. **Hook > her şey:** "1sn retention'da %10 iyileşme, görsel faktörlerde %100
   iyileşmeden değerli." İlk-3sn'de izleyicilerin %50-60'ı kayıyor.
2. **Ekranda-metin hook = +%18 izlenme**; ilk 5sn'de pattern-interrupt = +%23
   retention (statik açılışa göre). → Bizde punch-in zoom + büyük hook altyazısı
   ZATEN var; araştırma doğruluyor.
3. **YENİ eylem adayı — micro-payoff / shot-type kesimi:** başta her 10-15sn'de
   FARKLI çekim tipine kes; her 2-3sn'de bir "pattern break". Bizim segmentler
   ~8sn tek B-roll → segment İÇİNDE 2-3sn'de bir B-roll/hareket değişimi retention'ı
   artırabilir. Düşük riskli deneme: `make_clip`'te uzun segmentleri 2 alt-klibe
   bölüp farklı Ken Burns yönü ver (kesim hissi). Sıradaki gece adayı.
4. **A/B hook testi:** aynı Short'un 3 farklı hook'u, farklı saatlerde, Studio'da
   3sn retention kıyası. Üretim çoklu-varyant desteklemiyor; ileride.

**Sıradaki gece adayları (buradan devam):** (1) micro-payoff intra-segment kesim
(yukarıda #3). (2) Google TTS SSML `<mark>` timepointing → whisper'sız kelime
zamanlaması (CPU hız). (3) Açılış 0-1sn cold-open tam-ekran metin kartı.

---
## 2026-08-08 — Intra-segment MICRO-CUT (5-saniye kuralı) → CANLI hatta bağlandı

**Araştırdım (WebSearch — yeni, bugün):** 2026 Shorts retention editing kılavuzları
(opus.pro ideal-length, joyspace pattern-interrupt, air.io, pixflow):
1. **"5-Saniye Kuralı" (2026):** timeline'da görsel olarak 5sn hiçbir şey değişmeyen
   blok VARSA retention orada düşüyor. Kural: hiçbir segment görsel değişim olmadan
   ~5sn geçmesin.
2. **Top Shorts ~2-4sn'de bir keser** (cut/zoom/grafik/SFX) = her değişim izleyicinin
   dikkat saatini sıfırlar (novelty craving). "Aggressive editing" retention'ın
   temel motoru.
3. Bizim durum: v4 segmentleri ~8sn ve **tek sürekli Ken Burns** → tam da kuralın
   yasakladığı >5sn statik-hissi blok. Kanca (punch-in) + sarı altyazı zaten var
   ama segment GÖVDESİ durağan.

**Denedim + entegre ettim (savunmacı):** `shorts-build-v4.py` `_kenburns()`:
uzun segmentlerde (`dur>5.0`) sahne ~2.7sn'lik `n=max(2,round(dur/2.7))` alt-faza
bölünüyor; her faz taze **wide→tight zoom** (`1296-316*pw`, sawtooth `pw=mod(t,seg)/seg`),
faz sınırında kadraj wide'a **SNAP** eder = görsel "kesim" hissi (pattern-interrupt),
tek broll input'la (ekstra kaynak yok). Hook + kısa segmentler (≤5sn) DEĞİŞMEDİ.
`float(D)` try/except guard → ifade bozulursa eski davranışa düşmez, sadece uzun-segment
yolu; render asla crash etmez. **İzole test:** tam v4 filtre zinciri (2x crop+scale+fps)
8sn color/testsrc üstünde → geçerli **1080×1920, 8.00sn, h264 MP4, exit 0**. ffmpeg
sawtooth `mod` ifadesini kabul etti. Deney `2026-08-08-1` (retention).
**Yan fayda:** aynı build IG Reels'i de besliyor → IG Reels de micro-cut kazanır.

**Sıradaki gece adayları (buradan devam):** (1) faz sınırında Ken Burns YÖNÜNÜ de
değiştir (zoom + pan alternate) → kesim daha belirgin. (2) Google TTS SSML `<mark>`
timepointing → whisper'sız kelime zamanlaması (CPU hız). (3) Açılış 0-1sn cold-open
tam-ekran metin kartı. (4) count-up'ı comparison formatına da genişlet.

---
## 2026-08-09 — Micro-cut v4.2: faz-yönü alternasyonu (görsel değişimin TÜRÜNÜ çeşitlendir)

**Araştırdım (WebSearch — yeni, bugün):** 2026 Shorts retention/hook kılavuzları
(miraflow, prapermedia, thefluxcanvas, aibrify retention-curve, virvid "first-3s"):
1. **2026 pacing hedefi: ~1.5-2sn'de bir GÖRSEL DEĞİŞİM** — ve değişimin TÜRÜNÜ
   çeşitlendir: cut / kamera hareketi / metin değişimi / zoom / renk. Sadece aynı
   zoom'u tekrarlamak "değişim" saymıyor (novelty craving sönüyor).
2. **İkincil hook ~14-15sn** (30sn Short'ta 3 "act" checkpoint'i); **son kareyi
   loop'a göre tasarla** (döngü retention'ı katlar).
3. **Hook > her şey:** tamamlanma oranı birincil sıralama sinyali; güçlü açılış
   3-5x daha çok gösterim. Bold-claim / curiosity-gap açılışları öne çıkıyor.
   Araçlar: CapCut auto-caption, ContHunt hook-analizi (opsiyonel, ücretli değil).

**Denedim + entegre ettim (savunmacı):** `shorts-build-v4.py` `_kenburns` micro-cut
yolu v4.1→**v4.2**: faz başına taze wide→tight zoom KORUNDU, ÜSTÜNE faz-parite ile
**yatay kadraj yönü alternasyonu** eklendi. `s=(2*mod(floor(t/seg),2)-1)` → çift faz
soldan→merkeze, tek faz sağdan→merkeze pan; `x=(in_w-out_w)*(0.5-s*0.3*(1-pw))`
(frac ∈ [0.2,0.8], sınırlarda kırpma yok). Sonuç: her faz FARKLI çekim gibi durur,
faz-sınırı snapi karşı tarafa atlar = daha belirgin "kesim" hissi (araştırma #1:
sadece zoom değil, değişimin TÜRÜNÜ çeşitlendir). Bu, video-rnd'deki sıradaki-aday
(a)'yı uygular. **İzole test:** tam crop→scale:1080:1920→fps30 zinciri, testsrc2
1620x2880 8sn üstünde → geçerli **1080×1920, 8.00sn, h264 MP4, exit 0**. ffmpeg
`floor`+`mod` ifadesini kabul etti. `float(D)` guard mevcut → bozulursa yalnız
uzun-segment yolu etkilenir. Ayrı deney AÇILMADI: 08-08-1 (micro-cut retention) hâlâ
ölçülmedi; üstüne ikinci confound eklemektense v4.2 micro-cut'ı 08-08-1'in GÜNCEL
üretim durumu say — retention ölçülünce birleşik micro-cut etkisi okunur.

**Sıradaki gece adayları (buradan devam):** (1) **loop-friendly son kare** — son
beat'in son karesini açılış karesine görsel yakınlaştır (araştırma #2, döngü). (2)
**ikincil hook ~14-15sn** — orta beat'e mini pattern-interrupt/metin-kartı. (3)
Google TTS SSML `<mark>` timepointing (whisper'sız hız). (4) count-up'ı comparison
formatına genişlet. (5) cold-open 0-1sn tam-ekran metin kartı.

---
## 2026-08-10 — Loop-friendly kapanış (Retention-Loop) → CANLI hatta bağlandı

**Araştırdım (WebSearch — yeni, bugün):** 2026 Shorts retention/loop kılavuzları
(shortimize retention-rate, upmyviews looping, aibrify retention-curve, conthunt,
joinbrands):
1. **Retention-Loop = 3 tartışılmaz öğeden biri** (0.5sn görsel hook · Retention-Loop
   yapısı · Interest-Node hizası). "Loopable ending drives rewatches" — tekrar-izlenme
   tamamlanma oranını ve dolayısıyla sıralamayı katlıyor.
2. **Son kare ilk kareye bağlanmalı** (illa birebir değil, kavramsal): döngü noktası
   sorunsuz olunca YouTube auto-loop'u "bir sonraki mantıklı kare" gibi hissettiriyor.
3. **İkincil hook ~14-15sn** + her 10-15sn açık-döngü (open loop) yeniden-kancası;
   **20-35sn** runtime tamamlanma için ideal.

**Denedim + entegre ettim (savunmacı):** `shorts-build-v4.py` `make_loop_tail()` +
concat öncesi ekleme. İlk klibin (hook) açılış karesi `-frames:v 1` ile PNG'ye alınır,
~0.4sn'lik SESSİZ (anullsrc) bir dilime dönüştürülür (scale 1080x1920, fps30, yuv420p,
aac) ve klip listesinin SONUNA eklenir. Böylece YouTube/IG videoyu loop'a aldığında
son kare ≈ ilk kare = kesintisiz döngü (rewatch tetikler). Tamamen additive; `len(clips)>=2
and not no_broll` koşulu + try/except → düşerse hiç eklenmez, hat asla kırılmaz. **IG Reels
de aynı build'den miras alır** (Reels daha agresif loop'lar → kazanç muhtemelen daha büyük).
**İzole test:** synth clip00 (2sn A/V) → frame çıkar → 0.4sn still+silent → concat →
geçerli **1080×1920, süre 2.0→2.44sn, video+audio stream, exit 0**. Framing/micro-cut'tan
AYRI mekanizma (döngü noktası) → deney `2026-08-10-2` (08-08-1'i confound etmez).

**Sıradaki gece adayları (buradan devam):** (1) **ikincil hook ~14-15sn** — orta beat'e
mini pattern-interrupt/metin-kartı (araştırma #3, henüz yok). (2) **runtime denetimi 20-35sn**
— mevcut süre dağılımını ölç; >35sn ise senaryo satır sayısı/uzunluğu kıs (tamamlanma
kaldıracı). (3) Google TTS SSML `<mark>` timepointing (whisper'sız hız). (4) count-up'ı
comparison formatına genişlet. (5) cold-open 0-1sn tam-ekran metin kartı.

---
## 2026-08-11 — Mid-video ikincil-hook (v4.3 rehook) → CANLI hatta bağlandı

**Araştırdım (WebSearch — yeni, bugün):** 2026 Shorts secondary-hook / mid-video
retention (joyspace pattern-interrupt, shortzly retention-strategies, aibrify
retention-curve, rivereditor, opus.pro hook-formulas):
1. **Rehook = mid-video'ya ekilen kısa dikkat-yeniden-yakalama aracı.** 3 tip: soru-
   rehook, tease-rehook, **pattern-interrupt rehook** (beklenen ritmi kır — yeni açı /
   ani zoom / sahne değişimi, izleyici yapıya yerleştiği anda).
2. **Her 10-15sn'de bir pattern-interrupt** (b-roll cut / jump cut / grafik) "boredom
   clock"u sıfırlar, drop-off eğrisini düzleştirir; **%50 noktasında mid-point retention
   hook** standart retention yapısının parçası (Hook→Value→Interrupt→Value→CTA).
3. Tamamlanma oranı birincil sıralama sinyali olmaya devam ediyor; orta-video terk =
   en büyük sızıntı noktası.

**Denedim + entegre ettim (savunmacı):** `shorts-build-v4.py` v4.2→**v4.3**. `_kenburns`'e
**`rehook`** dalı: ilk ~0.55sn'de tam kadrajdan (1296) sıkı kadraja (900, 9:16 kilitli)
HIZLI punch-in, sonra sabit → sürekli Ken Burns yerine ani zoom = belirgin pattern-
interrupt. main()'de `rehook_idx = len(segs)//2` (yalnız >=4 beat; hook/son-CTA doğal
olarak dışta; **Manim ve count-up beat'i hariç** — kendi animasyonları var, `not countup_dir`
guard). Sadece TEK orta beat etkilenir; diğer beat'ler v4.2 micro-cut/Ken Burns aynen kalır.
**İzole ffmpeg testi:** rehook crop→scale:1080:1920→eq/vignette zinciri, testsrc2
1296x2304 6sn üstünde → geçerli **1080×1920, 6.00sn, exit 0**. `ast.parse` OK. Framing/
loop-tail'den AYRI mekanizma (mid-video dikkat) → deney `2026-08-11-2` (08-08-1/08-10-2'yi
confound etmez; farklı beat + farklı zaman penceresi 40-60%).

**Sıradaki gece adayları (buradan devam):** (1) **soru/tease rehook** — mid-beat'e görsel
punch YANINDA kısa metin-kartı ("peki ya şu?") ile sözel rehook (araştırma #1 tip 1-2;
henüz yalnız görsel punch var). (2) **runtime 20-35sn denetimi** — süre dağılımını ölç,
>35sn ise senaryo kısalt (tamamlanma kaldıracı; hâlâ ölçülmedi). (3) Google TTS SSML
`<mark>` timepointing (whisper'sız hız). (4) count-up'ı comparison formatına genişlet.
(5) cold-open 0-1sn tam-ekran metin kartı.

---
## 2026-08-12 — Süre denetimi: 40-45sn → 28-33sn (Completion-Rate) → CANLI hatta bağlandı

**Araştırdım (WebSearch — yeni, bugün):** 2026 Shorts optimal length / completion
(piktochart length-guide, shortimize retention-rate, opus.pro ideal-length, virvid,
retensis stats):
1. **Completion + retention algoritmanın en ağır tarttığı iki sinyal.** 20-35sn
   videolar en yüksek tamamlanmayı alır; **≤30sn %80+ retention** aşabiliyor. 20-28sn
   "setup + payoff'u dar çerçevede" tutarak güçlü retention üretiyor.
2. Kısa Short'un doğal avantajı: 20sn'lik videoyu sonuna kadar izlemek 45sn'likten
   çok daha kolay → daha yüksek completion → daha çok öneri hızı.
3. (Uyarı) 50-60sn de RETAIN ederse 22x izlenme alabiliyor (opus 5400-Short analizi),
   ama bu confound: retention'ı zaten iyi olan uzun içerik. Bizim retention ~%35-45
   (orta) → önce completion'ı yükselt, uzun-forma sonra.

**ÖLÇTÜM (data-driven, kendi çıktımız):** `ffprobe` ile son 30 Short süresi →
**33-45sn, 20/30'u >35sn, tepe 45.1sn, medyan ~37sn.** Yani sistematik olarak
completion sweet spot'unun (20-35sn) ÜSTÜNDE üretiyoruz. Retention ~%35-45 ile
tutarlı (40sn video / ~15sn ort = ~%37).

**Kök neden + entegre ettim:** `viral-script.py` ve `shorts-script.py` PROMPT'u
senaryoya açıkça **"40-45 saniyelik"** üret diyordu (overshoot'un kaynağı). Her ikisinde:
süre hedefi **28-33sn**'e çekildi + "tamamlanma #1 sinyal, 20-35sn en yüksek, dolgu YOK,
hedefin üstüne taşma" talimatı eklendi; **beat başı 12-20 kelime → 11-15 kelime**
(toplam ~52-64 kelime → ~28-32sn TTS). `ast.parse` ✓ her iki dosya. Deney `2026-08-12-2`.
**Yarın Adım 0'da ölç:** yeni Short'ların ffprobe süre dağılımı medyan 28-33'e indi mi
(deterministik, hemen görülür) + retention%. NOT: 08-11-2 rehook'u kısmen confound eder
(ikisi de retention%'i oynatır) ama süre etkisi ffprobe ile ayrı ölçülebilir; mekanizma
farklı (payda vs mid-video eğri).

**Sıradaki gece adayları (buradan devam):** (1) **soru/tease rehook** — mid-beat görsel
punch YANINDA kısa metin-kartı ("peki ya şu?") sözel rehook (henüz yalnız görsel punch).
(2) süre değişiminin retention'a etkisini 3-5 yeni videoda doğrula, tutmuşsa learnings'e
yaz. (3) Google TTS SSML `<mark>` timepointing (whisper'sız hız). (4) count-up→comparison.
(5) cold-open 0-1sn tam-ekran metin kartı.

---
## 2026-08-13 — Sözel/görsel tease-rehook kartı (v4.3→v4.4) → CANLI hatta bağlandı

**Araştırdım (WebSearch — yeni, bugün):** 2026 Shorts mid-video text-card rehook / pattern-
interrupt (aibrify retention-curve-playbook, shortzly retention-strategies, joinbrands
best-practices, thefluxcanvas):
1. **Rehook = drift başlayınca dikkati yeniden yakalayan kısa araç; her 10-15sn'de bir
   "açık döngü" (open loop) commitment-clock'u sıfırlar.** 3 tip: **question** ("bunu sen de
   yaşadın mı?"), **tease** (spesifik vaatle merak), **pattern-interrupt** (ritmi kır).
2. **25-35sn'de pattern-interrupt** (kesim/zoom/grafik/ses) yeni izleyicinin drift ettiği anda
   attention'ı resetler; ~12-15sn statik kadraj sonrası bir yüzde izleyici kaymaya başlar.
3. On-screen graphic/text bir pattern-interrupt biçimidir — "boredom clock"u kırar.

**Kök neden + entegre ettim:** v4.3 orta beat'e YALNIZ görsel punch-in (zoom) koyuyordu; sözel/
metin rehook yoktu (araştırma #1 tip 1-2 eksik). `shorts-build-v4.py` v4.3→**v4.4**:
`make_rehook_card()` marka-renkli küçük merak kartı üretir (REHOOK_CARDS rotasyonu: "PEKİ YA
ŞU?"/"AMA DUR—"/"İŞTE ASIL MESELE"/"BİR DE ŞUNU DÜŞÜN"/"DİKKAT—", slug'a göre `sum(ord)`
**stabil** seçim — `hash()` PYTHONHASHSEED randomize eder, kullanılmadı). `make_clip`'e
`rehook_card` param: format=rgba, fade-in st=0.15 d=0.22, fade-out st=1.32 d=0.30, overlay
merkez-üst `y=960-24*(yukarı-kayma micro-motion)`, `enable=between(0.15,1.65)`. Yalnız
`i==rehook_idx and not countup_dir and not is_manim`; **kart hattı kırılırsa kartsız yeniden
kur** (fail-safe, canlı hat kırılmaz). Görsel zoom (v4.3) + metin kartı (v4.4) = birleşik
pattern-interrupt, orta-video (40-60%) hedefli.

**Doğrulama:** `ast.parse` ✓. Kart render (PIL) → 790×176 png ✓. **İzole ffmpeg testi:**
fade-in/out + `y=960-24*max(0,1-(t-0.15)/0.28)` yukarı-kayma + `enable=between(0.15,1.65)`
overlay, color 1080×1920 5sn üstünde → **1080×1920, 5.00sn, exit 0**. Deney `2026-08-13-2`
(mekanizma 08-11-2 rehook-zoom'dan AYRI: aynı beat ama görsel yerine metin ekseni; ikisi de
orta-video eğriyi oynatır — attribution için orta-video retention deltasına bak).

**Sıradaki gece adayları (buradan devam):** (1) rehook kartı metnini beat İÇERİĞİNE göre
dinamikleştir (jenerik yerine spesifik tease vaadi — araştırma #1 "spesifik promise" daha güçlü;
şimdilik sabit rotasyon). (2) süre değişiminin (08-12-2) retention'a etkisini 3-5 yeni videoda
doğrula → tutmuşsa learnings'e "kısa Short 28-33sn > uzun". (3) Google TTS SSML `<mark>`
timepointing (whisper'sız hız). (4) count-up→comparison. (5) cold-open 0-1sn tam-ekran metin kartı.

---
## 2026-08-14 — Açılış from-black fade KESİLDİ (v5→v5.1, frame-0 hook) → CANLI hatta bağlandı

**Araştırdım (WebSearch — yeni, bugün):** 2026 Shorts first-3s cold-open hook / cliff
(socialync algorithm-2026, aibrify retention-curve-playbook, thefluxcanvas, opus.pro hooks,
prapermedia):
1. **Cliff = saniye 1-3 arasında %30-50 düşüş, 2026'nın #1 başarısızlık modu.** Açılış 2-3sn
   swipe'ı hak etmeli; **intro kartı / logo animasyonu / from-black fade / wide establishing
   shot = cliff tetikleyici** (kancayı geciktirir).
2. **%85 Shorts sessiz izleniyor** → kanca metni opsiyonel değil; ilk KAREDE okunur olmalı
   (sözle değil metinle teslim).
3. En iyi içerik 2.5-3sn'de ilk geçidi geçmeli; ~14-15sn'de ikincil hook. Görsel değişim her
   1.5-2sn (kesim/zoom/metin değişimi).
4. (Elenen) jenerik POV hook 2024'te tutuyordu, 2026'da retention kaybettiriyor.

**Kök neden + entegre ettim:** Kod denetimi → v5 `draw_hook_card` kanca metnini overlay PNG'ye
gömüp frame-0'dan tam opaklıkla basıyordu (İYİ). AMA `make_clip` her klibin bg'sine
`fade=t=in:st=0:d=0.20` (siyahtan açılış) uyguluyordu → hook klibinde ilk ~6 kare sahne+kanca
KARARMIŞ, tam da 1-3sn cliff'inde (araştırma #1+#2 ihlali). `make_clip`'e `opening` param:
yalnız `i==0` (hook) beat'inde from-black fade KALDIRILDI (`fdin=""`+`null`); sonraki sahneler
yumuşak 0.20s geçişi korur (araştırma #3 sahne-arası pacing). **Ayrı yüzey** → açık
rehook(08-11-2/08-13-2)/süre(08-12-2)/count-up(08-07-1)/micro-cut(08-08-1)/loop(08-10-2)
deneylerini confound ETMEZ.

**Doğrulama:** `ast.parse` ✓. İzole ffmpeg: opening frame0 piksel **253** (parlak) vs faded
frame0 **0** (siyah) → fade kaldırma çalışıyor. **Tam render** (gram-altin senaryosu, correct
venv /root/.venvs/parafomo): **exit 0, 34.5sn geçerli mp4**; frame-0 hook bölgesi (y700-1000)
**44.652 parlak piksel / max lum 255** = kanca ilk karede tam okunur. Deney `2026-08-14-2`.
**Yarın Adım 0'da ölç:** yeni Shorts açılış (ilk-3sn) retention + toplam retention%.

**Sıradaki gece adayları (buradan devam):** (1) rehook kart metnini beat İÇERİĞİNE göre
dinamikleştir (spesifik tease > sabit rotasyon; ama 08-13-2 açıkken confound riski — 08-13-2
kapanınca yap). (2) süre değişimini (08-12-2) 3-5 yeni videoda retention'la doğrula →
tutmuşsa learnings'e "kısa 28-33sn > uzun". (3) Google TTS SSML `<mark>` timepointing
(whisper'sız hız). (4) count-up→comparison. (5) 2.5-3sn ilk-geçit için hook beat'ini min
süreye sabitleme (kanca çok uzun sürmesin).

---
## 2026-08-15 — Shorts custom KAPAK (frame-0) → CANLI upload hattına bağlandı + caption doğrulaması

**Araştırdım (WebSearch — yeni, bugün):**
1. **Word-level / karaoke altyazı (opus.pro, vocallab.ai, bytecap, shortzly, reelwords):** 2026'da
   kelime-seviyesi zaman damgalı + aktif-kelime highlight altyazı retention'ı artıran STANDART;
   ilk saniyelerde ekran hareketi izleyiciye "kalma" nedeni verir; SRT'yi seslendirmeyle birlikte
   kelime-zamanlı üretip highlight stili gömmek en temiz yol.
   → **BULGU: Bizim hattımız BUNU ZATEN YAPIYOR.** `shorts-build-v4.py`: `transcribe_words`
   (faster-whisper `word_timestamps=True`) → `align_words` (difflib ile script'e hizala) →
   aktif kelime sarı `C_SUNG=#FFE14D` karaoke highlight. Yani caption tarafı 2026 best-practice'te;
   SSML `<mark>` timepointing (önceki aday #3) GEREKSIZ — whisper zaten kelime-seviyesi veriyor.
   **Aksiyon: caption'ı yeniden icat etmeye zaman harcama; teyit edildi, bırak.**
2. **Shorts custom thumbnail — 2026-07 YENİ özelliği (blog.youtube, tubefilter, vidiq, miraflow):**
   YouTube artık Shorts'a custom kapak yüklemeye izin veriyor (frame seç / desktop Studio'dan
   yükle / videoya tasarlı kare göm). Kapak swipe-player'da GÖRÜNMEZ ama **kanal grid'i, Shorts
   rafı, ARAMA sonuçları, abonelik feed'i ve ana sayfada** görünür → keşfedilebilirliği (dolayısıyla
   izlenmeyi) etkiler. Varsayılan kapak çoğu zaman **rastgele/bulanık bir orta kare** olur.
3. **İlk kare = hook (adshortsai, opus.pro, shortimize):** ilk 3sn'de %50-60 drop; "her Short'un
   içinde en az bir güçlü, thumbnail'e değer kare bulundur ki rastgele bulanık kare yerine onu
   seçebilesin". v5.1 frame-0 (fade'siz, kalın kanca + wordmark) tam da bu.

**Kök neden + entegre ettim (CANLI hat):** `youtube-upload.py` yüklemeden sonra kapağı AÇIKÇA
ayarlamıyordu → YouTube otomatik (çoğu zaman orta, zayıf) kare seçiyordu; keşif yüzeyleri
(grid/arama/abonelik) bundan zarar görüyordu. Darboğaz analizi: **yüksek retention + düşük izlenme
= dağıtım/keşif sorunu** (learnings). Bu doğrudan keşif yüzeyini iyileştirir.
→ `set_shorts_thumbnail(yt, vid, video_path)` eklendi: yükleme sonrası ffmpeg ile **t=0.35sn**
(hook metni tam çizili, hâlâ ilk saniye) frame çıkarır, `yt.thumbnails().set(videoId, media_body)`
ile custom kapak yapar. **Non-fatal**: kanal custom-thumbnail'a uygun değilse (doğrulanmamış) ya
da kare çıkmazsa `try/except` → yükleme AKIŞI KIRILMAZ, sadece uyarı basar (kırmızı çizgi: sosyal
hattı bozma). Scope `youtube.upload` thumbnails.set için yeterli.

**Doğrulama:** `ast.parse` ✓. İzole ffmpeg test (canlı bir short üstünde): `-ss 0.35 -frames:v 1`
→ 1080×1920, ort. parlaklık ~90 (siyah değil), max lum 255. Görsel inceleme: kare = kalın kanca
metni ("Uzmanlar borsayı önerdi, altın hepsini geçti") + Parafomo wordmark + @parafomo = temiz,
grid'e değer kapak. Deney `2026-08-15-1`. **ÖLÇÜM NOTU:** retention'ı ETKİLEMEZ (swipe-player
kapağı göstermez) — saf KEŞİF/izlenme metriği; Adım 0'da yeni Shorts izlenme + grid/arama trafik
payına bak, retention eğrisine DEĞİL. Açık retention deneylerini (hook-fade/rehook/süre) confound
etmez (ayrı yüzey: keşif vs izleme).

**Sıradaki gece adayları (buradan devam):** (1) frame-0 yerine DEDIKE tasarlı kapak (grid'de daha
büyük punch: kısa 3-4 kelime + kontrast) — frame-0 iyi ama grid küçük gösterimde metin uzun
olabilir; kapak-özel kısa başlık üret. (2) rehook kart metnini beat içeriğine göre dinamikleştir —
AMA 08-13-2 KAPANANA kadar bekle (confound). (3) süre değişimini (08-12-2) 3-5 yeni videoda
retention'la doğrula → tutmuşsa learnings'e "kısa 28-33sn > uzun". (4) count-up→comparison
(comparison elendi, düşük öncelik). (5) hook beat'ini min süreye sabitle (2.5-3sn ilk-geçit).

---
## 2026-08-16 — Shorts açıklama SEO (konu-hashtag) entegre + retention deney over-subscription teşhisi

**Araştırdım (WebSearch — yeni, bugün):**
1. **2026 pacing hedefi = görsel değişim her 1,5–2 sn** (opus.pro, aibrify, upmyviews, virvid.ai):
   kesim / kamera hareketi / metin overlay değişimi / zoom / renk kayması — herhangi biri sayılır.
   Drop'un %50-60'ı ilk 3 sn'de. Bizim v5.1 micro-cut (>5sn segmenti ~2.7sn alt-fazlara böler)
   bu hedefin ALTINDA kalıyor (2.7sn > 2sn); AMA Ken Burns sürekli hareket = kısmen "kamera
   hareketi" sayılıyor, net bug değil. → **video-rnd adayı:** micro-cut fazını 2.7→~1.8sn'ye
   çekmeyi DENE (08-08-1 kapanınca; şimdi confound eder).
2. **Progress bar / kinetik mute-değer öğeleri** (schedulala, joinbrands): sessiz izleme için
   ilerleme çubuğu + kinetik metin retention'ı destekleyen 2026 öğesi. AMA "ne kadar kaldı"
   sinyali drop'a da yol açabilir (karışık kanıt) → kör ekleme RİSKLİ, ölçülü test adayı, logla.
3. **Shorts SEO — arama/keşif** (hollyland, shortimize): Shorts YouTube ARAMASINDA da yüzeyleşiyor;
   açıklama ilk satırı + KONUYA-DUYARLI hashtag arama sıralamasını besler. Jenerik geniş etiket zayıf.

**Kök neden + ENTEGRE ETTİM (arama-keşif yüzeyi — retention'ı ETKİLEMEZ):** `youtube-upload.py`
`with_funnel()` her videoya AYNI statik `#finans #para #yatırım #ekonomi #borsa #altın #dolar`
bloğunu basıyordu. Bu tam da IG'de KANITLI KAYBEDEN desen (08-06-2/08-08-2: konu-hashtag > jenerik
blok). Aynı dersi YouTube'a taşıdım: `topic_hashtags(slug, title)` slug+başlıktan niş etiket üretir
(#kıdemtazminatı/#gramaltın/#bist100/#tüfe...) + #parafomo/#finans core, konu az sinyalse birkaç
geniş etiketle tamamlar, max 9. Test: abd-faiz→#altın #gramaltın #dolar #döviz #faiz; kıdem→
#kıdemtazminatı #tazminat; bist→#borsa #bist100. `ast.parse` ✓. Deney `2026-08-16-3`.
**Neden bu gece BUNU seçtim (retention edit DEĞİL):** aşağıdaki teşhis.

**TEŞHİS (kök neden — kendi süreç hatam):** Şu an **8 açık retention deneyi** (08-05-4 v4, 08-07-1
count-up, 08-08-1 micro-cut, 08-10-2 loop, 08-11-2 rehook-görsel, 08-12-2 süre, 08-13-2 rehook-kart,
08-14-2 hook-fade) HEPSİ AYNI havuz metriğini ("yeni Shorts ort. retention%") ölçüyor. 9. bir
retention değişikliği eklemek hepsini confound eder → HİÇBİRİ tekil doğrulanamaz. Bu, deney
tasarımının aşırı-abone olması. **Düzeltme planı:** retention edit'lerini DONDUR; v5.1 hattıyla
≥8-10 yeni video biriksin; Adım 0'da v5.1 BATCH'ini eski baseline'a karşı TEK verdict olarak
doğrula (bilesik micro-atıflar yerine). Bu yüzden bu gece retention'a DOKUNMADIM; ayrı yüzeye
(arama-keşif hashtag) yatırım yaptım.

**Sıradaki gece adayları (buradan devam):** (1) retention edit DONDUR — v5.1 batch birikince topluca
doğrula. (2) micro-cut fazı 2.7→1.8sn (08-08-1 kapanınca). (3) progress-bar ölçülü test (drop riski
— tek videoda izole dene). (4) dedike kısa-metin kapak (08-15-1 doğrulanınca). (5) açıklama ilk
satırını hedef-anahtar-kelimeyle güçlendir (arama SEO, hashtag ile aynı yüzey).

---
## 2026-08-17 — Pacing 1.5-2sn (3. teyit) → micro-cut gap ÖLÇÜLDÜ + kuyruğa alındı (retention DONDURULDU)

**Araştırdım (WebSearch — bugün, yeni kaynaklar):**
1. **2026 pacing = görsel değişim her 1.5–2sn** (aibrify retention-curve-playbook, upmyviews 2026 strategy, opus.pro): "ekranda her 2.5sn'de en az bir hareket/kesim/yeni metin", ideali **1.5–2sn/görsel değişim**; drop'un %50-60'ı ilk 3sn. 3. kez çıkıyor (08-13, 08-16, bugün) = güçlü, tekrarlı sinyal.
2. **Loop-friendly bitiş + %85 mute-caption** (opus.pro ideal-length, virvid.ai): sonu ilk kareye bağlayan bitiş + izlemelerin %85'i sessiz → altyazı zorunlu. Bizde VAR (loop-tail 08-10-2, sarı ASS altyazı). Yeniden keşif yok.
3. **Araçlar:** CapCut (auto-caption), **ContHunt** (hook-yapısı analizi), InShot. ContHunt not edildi — hook-skorlama için ileride değerlendir (ücretsiz kısım var mı bak).

**DENEDİM/ÖLÇTÜM (izole, entegrasyon YOK):** `shorts-build-v4.py:660` — micro-cut faz süresi `n = round(durf/2.7)` = **~2.7sn/faz**. 2026 hedefi 1.5-2sn → bizimki **~%35 yavaş**. Düzeltme tek satır: `2.7 → 1.8` (8sn segmentte 3 yerine ~4-5 kesim). Ölçüm netleşti, düzeltme hazır.

**NEDEN ENTEGRE ETMEDİM (bilinçli):** Bu bir retention edit. Bu gece 7 confound retention deneyini kapatıp SADECE 08-14-2'yi v5.1 batch'inin tek tracker'ı olarak bıraktım (temiz verdict için ≥8-10 v5.1 videosu biriksin). Şimdi pacing edit'i eklersem batch'i yeniden confound eder. **Kural: aynı metriğe tek izole açık deney.** Bu yüzden DONDURDUM.

**Sıradaki gece (net kuyruk):** (1) **08-14-2 (v5.1 batch) kapanınca İLK retention edit = micro-cut 2.7→1.8sn** (pacing 1.5-2sn; 3x teyitli, en yüksek öncelikli, tek-değişken temiz deney olarak aç). (2) sonra dedike kısa-metin kapak (08-15-1 kapanınca). (3) ContHunt hook-skorlama değerlendir. (4) açıklama ilk satırı hedef-anahtar (08-16-3 hashtag kapanınca — aynı arama yüzeyi, confound etme).

---
## 2026-08-18 — Shorts BAŞLIK optimizasyonu (yeni, UNBLOCKED yüzey) → front-load entegre edildi

**Araştırdım (WebSearch — bugün, yeni):**
1. **Shorts feed başlığı ~40 karakterde KESİLİR** (joinbrands 2026 best-practices, ytzolo title-length,
   humbleandbrag CTR rules): watch-page 100 char sınırı olsa da AKIŞTA ~40 char sonrası truncate.
   Kural: konu-anahtarı + kanca İLK 40 char'a; declarative (soru değil) cümle; videonun açılış
   kancasını yansıt. Link: joinbrands.com/blog/youtube-shorts-best-practices, ytzolo.com/blog/youtube-video-title-length-best-practices-2026
2. **İlk 3 hashtag başlık ÜSTÜNDE tıklanabilir görünür** (hashtagtools.io): title char yakmadan
   görünürlük → hashtag description'da kalsın (bizde zaten öyle, 08-16-3). Yeniden keşif yok.
3. **A/B: tek değişken, min 48 saat** (humbleandbrag). Title'ı izole test etmek doğru — retention
   edit değil, ayrı yüzey.

**ENTEGRE ETTİM (retention'ı ETKİLEMEZ — ayrı yüzey, confound YOK):** `viral-script.py:144` başlık
prompt'u yalnız "<70 karakter, kancadan farklı" diyordu; feed-truncation kuralı yoktu. Ekledim:
"Shorts akışı ~40 char'da keser → en çarpıcı konu-anahtarını (altın/dolar/faiz…) İLK 40 char'a
front-load et; soru değil iddialı cümle." `ast.parse` ✓. Deney `2026-08-18-2`. Neden bu gece BU:
retention/hashtag/thumbnail yüzeyleri açık deneylerle dolu (confound olurdu); TITLE hiç deneyi
olmayan temiz-izole yüzeydi.

**Sıradaki gece adayları (buradan devam):** (1) 08-14-2 v5.1 batch kapanınca İLK retention edit =
micro-cut 2.7→1.8sn (pacing 1.5-2sn, 3x teyitli, hazır). (2) dedike kısa-metin kapak (08-15-1
kapanınca). (3) başlık front-load'ı 5-8 videoda gözle doğrula (feed'de ilk-40 anahtar görünüyor mu).
(4) ContHunt hook-skorlama ücretsiz kısmını değerlendir. (5) açıklama ilk-satır anahtar (08-16-3 hashtag kapanınca).

---
## 2026-08-20 — Word-by-word karaoke altyazı DOĞRULANDI (zaten current) + funnel araç-linki entegre

**Araştırdım (WebSearch — bugün, yeni kaynaklar):**
1. **Word-by-word / karaoke highlight altyazı = 2026'nın en yüksek-kanıtlı retention kaldıracı**
   (opus.pro caption-best-practices, blitzcutai, vocallab.ai word-highlighting): burned-in altyazı
   +%12-15 completion; **word-by-word senkron highlight +%15-25 retention** (statik satır bloğuna
   karşı). Kural: kalın beyaz + ince siyah stroke, 2-5 kelime öbeği, aktif kelime highlight,
   center-lower third. Araçlar: CapCut/Descript/Submagic/Vocallab (otomatik).
2. **DURUM (re-discovery — GAP DEĞİL):** `shorts-build-v4.py:243-287` ZATEN gerçek Whisper-hizalı
   `{\k}` ASS karaoke kullanıyor: aktif kelime SARI highlight, okunmamış beyaz (satır 66) — tam da
   2026 best-practice. En büyük caption kaldıracı elimizde; bir daha araştırma. Not: kanca segmentinde
   alt-karaoke yok (metin üstte büyük statik kartta, satır 919) — bilinçli, çift-metin önleme.
3. **caption pozisyonu = center-lower third** (search): bizim MarginV'yi bir sonraki retention
   penceresinde doğrula (RETENTION yüzeyi → 08-14-2 batch açıkken DOKUNMA, confound eder).

**ENTEGRE ETTİM (CLEAN yüzey — retention'ı ve hashtag arama bloğunu ETKİLEMEZ):**
`youtube-upload.py` → `tool_url_for()` eklendi + `with_funnel()` güncellendi. Önce blog-olmayan viral
Short'un funnel linki JENERİK ana sayfaya gidiyordu; artık konuya uygun **interaktif araç sayfasına**
gider (altın→/altin-hesaplama, kdv→/kdv-hesaplama, maaş→/net-maas-hesaplama, faiz→/fed-faiz-takvimi…;
eşleşme yoksa /ekonomik-takvim). Lead satırı da "🧮 İlgili ücretsiz hesaplama/veri aracı:" oluyor.
Bu FUNNEL/UTM yüzeyi (YT→site huni, BÜYÜME-D) — retention/hashtag-arama'dan ayrı. `ast.parse` ✓ +
mapper test ✓ (altın/kdv doğru, fallback ekonomik-takvim). Exp AÇMADIM: YT→site referral yapısal
zayıf (kanıtlı ~0), dağıtım-C gibi exp olarak izlemek inconclusive üretir — değişikliği yap, izleme.

**NEDEN retention edit YAPMADIM (bilinçli, disiplin):** 08-14-2 (v5.1 hook-fade) retention batch hâlâ
açık; temiz verdict için ≥8-10 v5.1 videosu birikmeli (manim/news cron'ları haftalık API limitine
takıldığından son 2 gün üretim düştü → batch hâlâ ince, retention verisi 3-7g gecikmeli). 9. retention
ed'i eklemek confound eder (8-retention-üst-üste hatasının kök dersi). DONDURULDU.

**Sıradaki gece (net kuyruk):** (1) 08-14-2 v5.1 batch OLGUNLAŞINCA (≥8-10 video) TEK verdict kapat →
İLK retention edit = **micro-cut 2.7→1.8sn** (pacing 1.5-2sn, 3x teyitli, hazır). (2) sonra caption
MarginV'yi center-lower-third'e göre doğrula (retention penceresi). (3) dedike kısa-metin kapak
(08-15-1 kapanınca). (4) ContHunt hook-skorlama ücretsiz kısmı.

---
## 2026-08-21 — Pacing 4. TEYİT + hook-yazım kuralı (present-tense/declarative) + funnel mevduat map

**Araştırdım (WebSearch — bugün):** "YouTube Shorts hook retention first 3s 2026 techniques" →
kaynaklar: opus.pro (hook-formulas + ideal-length), upmyviews 2026-strategy, aibrify retention-curve-
playbook, virvid.ai first-3-seconds, teleprompter.works best-practices, schedulala editing-tips.
1. **Pacing 1.5–2sn/görsel değişim = 4. BAĞIMSIZ TEYİT** (08-13, 08-16, 08-20, bugün). "her 1.5-2sn'de
   kesim/kamera-hareketi/metin-değişimi/zoom/renk"; drop'un %50-60'ı ilk 3sn. → bizim micro-cut
   ~2.7sn/faz hâlâ %35 yavaş; **micro-cut 2.7→1.8 edit'i artık 4x-kanıtlı, en yüksek öncelikli kuyruk
   başı.** Yeni bilgi yok, sadece güçlenen sinyal.
2. **YENİ — hook yazım kalıbı** (opus hook-formulas, virvid): kanca = "TEK net vaat, PRESENT tense,
   aktif fiil, SORU DEĞİL iddialı cümle" + hook↔payoff köprüsü (ilk 3sn vaat ↔ son 3sn ödeme).
   "This is why…" > "Today we'll discuss…". → viral-script.py hook prompt'una eklenebilir AMA bu bir
   RETENTION yüzeyi (hook kalitesi retention'ı oynatır) → **08-14-2 batch açıkken DOKUNMA (confound).**
   Batch kapanınca micro-cut'tan SONRA sıradaki izole retention edit adayı olarak KUYRUĞA alındı.
3. **ContHunt (hook-skorlama)** ücretsiz-tier kontrolü kuyrukta — bu gece token web'e (mevduat sayfası)
   ayrıldı; sıradaki geceye taşındı.

**ENTEGRE ETTİM (CLEAN funnel yüzeyi — retention/search'i ETKİLEMEZ):** `youtube-upload.py` _TOOL_MAP'e
`("mevduat","/mevduat-faizi-hesaplama")` eklendi → mevduat-konulu blog-olmayan Short'un funnel linki
bugün yayınlanan yeni araç sayfasına iner (ör. "banka-mevduati-seni-degil-bankayi-korur"). Test: slug
eşleşme ✓; "vadeli işlem" (futures) yanlış eşleşmesin diye bare "vadeli" anahtarı EKLENMEDİ (test'te
yakalandı, kaldırıldı). `ast.parse` ✓. Funnel yüzeyi = exp açılmadı (YT→site yapısal zayıf, dağıtım-C
dersi: değişikliği yap, izleme).

**ÜRETİM DURUMU:** claude CLI haftalık limiti reset oldu (manim-daily 08-20 16:07 başarıyla yayınladı;
08-14 sonrası ~15+ short json birikti). v5.1 batch DOLUYOR ama retention 3-7g gecikmeli → en taze v5.1
kohortun retention'ı ~08-24'te olgunlaşır. **08-14-2 bir cycle daha DONDURULDU** (erken verdict =
premature-confound riski). Sıradaki cycle büyük ihtimalle kapatılabilir → micro-cut açılır.

**Sıradaki gece (net kuyruk, güncel):** (1) 08-14-2 v5.1 batch OLGUN (≥8-10 video + retention) → TEK
verdict kapat → **micro-cut 2.7→1.8sn** (4x teyitli). (2) SONRA hook-yazım kuralı (present-tense/
declarative/payoff-köprü) izole retention edit olarak aç. (3) caption MarginV center-lower-third.
(4) dedike kısa-metin kapak (08-15-1 kapanınca). (5) ContHunt ücretsiz-tier.

---
## 2026-08-22 — ContHunt ücretsiz-tier DEĞERLENDİRİLDİ (pipeline'a uymaz) + ücretsiz auto-B-roll taraması (yok) + funnel işsizlik map

**Araştırdım (WebSearch — bugün):** (1) "ContHunt hook analyzer free tier 2026", (2) "free YouTube
Shorts retention B-roll AI tools 2026".

1. **ContHunt ücretsiz-tier = kuyruktaki iş TAMAMLANDI, ama beklenen şey DEĞİL.** Kaynak: conthunt.app/blog.
   ContHunt bir **rakip-keşif/analitik** aracı (Node Velocity Alerts: ücretsiz-tier'de 1 alert, hangi
   kanal/konu node'u hızlanıyor). "Neden viral oldu → retention hook" analizi RAKİP videolar için, kendi
   senaryomuzu skorlayan bir API DEĞİL. → **Sonuç: üretim hattına ENTEGRE EDİLECEK bir şey yok**; ücretsiz
   tier'i yalnız 1 rakip TR-finans node'unu elle izlemek için kullanılabilir (opsiyonel manuel iş, düşük
   öncelik). Kuyruktan DÜŞÜRÜLDÜ — bir daha "ContHunt entegre et" diye araştırma.
2. **Ücretsiz auto-B-roll (AI) taraması:** Fliki / VEED / OpusClip / HeyGen — hepsinde iyi B-roll özelliği
   ÜCRETLİ (OpusClip AI B-roll $29/ay, HeyGen Sora2/Veo3.1). API-anahtarsız/ücretsiz, pipeline'a takılacak
   auto-broll YOK. Bizim **Manim** hattı zaten özgün+ücretsiz B-roll yerine geçen yol (kullanıcı jenerik
   stok istemiyor — Manim doğru yön). → task-list adayı: kullanıcı ödemeli B-roll isterse OpusClip $29/ay.
3. **Word-by-word karaoke altyazı = retention'ın en yüksek kaldıracı olarak YİNE teyit** (nemovideo, 3.
   bağımsız kaynak). Bizde ZATEN var (shorts-build-v4 ASS {\k}). Yeni bilgi yok, sinyal güçlendi.

**ENTEGRE ETTİM (CLEAN funnel yüzeyi — retention/hashtag/search ETKİLEMEZ):** `youtube-upload.py`
_TOOL_MAP'e `("işsizlik"/"issizlik" → /issizlik-maasi-hesaplama)` eklendi, **"maaş" jenerik anahtarından
ÖNCE** (first-match; test: issizlik-slug→işsizlik sayfası, net-maas-slug→net-maaş bozulmadan). Bugün canlıya
alınan işsizlik aracının funnel karşılığı. Funnel yüzeyi = exp AÇILMADI (YT→site yapısal zayıf, dağıtım-C
dersi: değişikliği yap, izleme).

**NEDEN retention edit YAPMADIM (disiplin, değişmedi):** 08-14-2 (v5.1 hook-fade) retention batch HÂLÂ açık;
en taze v5.1 kohortu ~08-24'te olgunlaşır. 9. retention edit'i eklemek confound (8-retention-üst-üste kök
hatası). DONMUŞ. Sıradaki gece Adım 0'da olgunsa kapat → micro-cut 2.7→1.8sn (4x teyitli) AÇILIR.

**Sıradaki gece kuyruğu (güncel):** (1) 08-14-2 v5.1 batch OLGUN → TEK verdict kapat → micro-cut 2.7→1.8sn.
(2) hook-yazım kuralı (present-tense/declarative/payoff-köprü) izole retention edit. (3) caption MarginV
center-lower-third. (4) dedike kısa-metin kapak (08-15-1 kapanınca). ContHunt kuyruktan düştü.

---
## 2026-08-23 — micro-cut 2.7→1.8sn UYGULANDI (5. teyit) + B-roll pattern-interrupt kuralı doğrulandı

**Araştırdım (WebSearch — bugün):** "YouTube Shorts retention 2026 optimal shot pacing cut frequency
b-roll first frames" → kaynaklar: opus.pro/blog/ideal-youtube-shorts-length, hailuoai.video shorts-pacing,
increditors.com video-pacing-science, shortzly.com short-form-pacing-guide-2026, prepublish.ai retention.

1. **Pacing 1-2sn/görsel değişim = 5. BAĞIMSIZ TEYİT** (08-13, 08-16, 08-20, 08-21, bugün). increditors:
   "sık sahne değişimi statik-çekime göre **+%32 retention**". opus/shortzly: high-performing Shorts 2-4sn'de
   bir kesim, ama görsel-değişim (shot alternasyonu) 1-2sn. Bizim micro-cut 2.7sn/faz = banda göre %35 yavaştı.
   → **UYGULADIM:** shorts-build-v4.py line 660 `round(durf/2.7)` → `round(durf/1.8)` (v5.2). 8sn segmentte
   3→4 kesim. Tek-değişkenli edit (08-14-2 hook-fade inconclusive kapandıktan sonra açılan TEK retention deneyi
   = **08-23-2**). ast.parse ✓. v5.2 kohortu ~08-27'de olgunlaşır → Adım 0'da ölç.
2. **B-roll = retention aracı, dekor değil** (increditors, opus): "her 10-15sn'de bir pattern-interrupt
   (b-roll kesimi/jump-cut/grafik) sıkılma saatini sıfırlar, drop-off eğrisini düzleştirir." Bizde Manim
   sahneleri + micro-cut faz-snap zaten pattern-interrupt sağlıyor; 1.8sn faz bunu sıklaştırır. Yeni araç yok,
   mevcut hat doğrulandı.
3. **İlk 1-2sn görsel-hook + bold text + hızlı VO başlangıcı** (prepublish, hailuoai) — bizde v5.1 hook-frame0
   (fade kesildi) + kalın kanca metni + Google TTS zaten var. Teyit, yeni iş yok.

**Sıradaki gece kuyruğu (güncel):** (1) 08-23-2 v5.2 micro-cut OLGUN (~08-27, ≥8 video+retention) → TEK verdict
kapat. (2) SONRA hook-yazım kuralı (present-tense/declarative/payoff-köprü) izole retention edit olarak aç.
(3) caption MarginV center-lower-third. (4) dedike kısa-metin kapak (08-15-1 kapanınca). ContHunt düştü (rakip-analitik).

---
## 2026-08-24 — BOLD-CLAIM > curiosity-question ilk-frame kuralı (faceless kanal) — queue'ya pekişti, retention slotu FROZEN

**Araştırdım (WebSearch — bugün):** "YouTube Shorts opening text hook first frame retention 2026 curiosity gap".
Kaynaklar: virvid.ai/blog/first-3-seconds-hook-faceless-shorts-2026, tubeanalytics.net/blog/youtube-shorts-retention-guide,
aibrify.com/blog/youtube-shorts-retention-curve-playbook, reelforgeai.io youtube-shorts-algorithm-2026, opus.pro.

1. **YENİ+eyleme-dönük bulgu: faceless kanallarda BOLD CLAIM > curiosity-gap SORU** (virvid, aibrify). "Bold claims
   signal immediate value; curiosity gaps create an itch — ama kişisel-marka olmayan faceless kanalda bold claim
   ERKEN retention'ı DAHA HIZLI sürüyor." Biz faceless'iz (marka=ParaFOMO, yüz yok). → viral-script hook satırı BAZEN
   soru kuruyor ("Altınını neden hiç zenginleştirmez?" tipi). Kural: ilk-frame = **iddialı/net cümle** (soru değil).
   Bu TAM kuyruktaki "hook-yazım kuralı (declarative)" ile örtüşüyor → sinyal 2. bağımsız kaynakla güçlendi.
2. **İlk-frame text spec teyit:** 4-7 kelime, yüksek kontrast, top/bottom safe-zone (virvid, opus). Bizde v5.1 kalın
   kanca-frame var; bazı hook'lar 7+ kelime → declarative kuralına "≤7 kelime" ekle.
3. **1-sn swipe-away = Stage-1 gate** (reelforge, tubeanalytics): ilk 1sn ayrı ölçülüyor ama AYNI 'ort retention %'
   metriğine roll-up ediyor (08-23-2 orta-bölge 3-15sn ile aynı metrik).

**NEDEN entegre ETMEDİM (disiplin — kök-hata tekrarını önle):** hook-text ilk-1-3sn retention'ı etkiler = 08-23-2
(açık, ~08-27 olgun) ile AYNI 'ort retention %' metriğine roll-up. İkinci retention deneyi = 8-retention-confound kök
hatasının tekrarı. EŞZAMANLILIK TAVANI: aynı metriğe TEK açık deney. → Araştırma LOG'landı, entegrasyon 08-27'ye
(08-23-2 kapanınca) KUYRUKLANDI. "Zaman yoktu" değil — bilinçli confound-önleme.

**Sıradaki gece kuyruğu (güncel):** (1) 08-23-2 v5.2 micro-cut OLGUN (~08-27) → TEK verdict kapat. (2) SONRA hook-yazım
kuralı = **present-tense + declarative BOLD-CLAIM (soru değil) + ≤7 kelime + payoff-köprü** izole retention edit aç
(bugünkü araştırma 2. kaynakla pekiştirdi). (3) caption MarginV center-lower-third. (4) dedike kısa-metin kapak.

---
## 2026-08-25 — AUDIO katmanı denetimi: ducking ZATEN var + cut-synced SFX yeni kaldıraç (QUEUED, retention-confound)

**Araştırdım (WebSearch — bugün):** "YouTube Shorts 2026 background music sound design retention audio hook faceless".
Kaynaklar: joinbrands.com/blog/youtube-shorts-best-practices, reelforgeai.io/blog/youtube-shorts-algorithm-2026-complete-guide,
myinstantplay.com/blog/transition-sound-effects-and-video-hooks-complete-guide, virvid.ai/blog/first-3-seconds-hook-faceless-shorts-2026,
miraflow.ai/blog/youtube-shorts-best-practices-2026-complete-guide.

1. **Audio ducking = search'ün #1 retention ipucu → BİZDE ZATEN VAR (denetlendi).** shorts-build-v4.py L966: müzik bed
   volume=0.13 + `sidechaincompress=threshold=0.03:ratio=10:attack=15:release=350` → VO gelince bed otomatik kısılıyor.
   Yeni iş YOK, mevcut hat doğrulandı. NOT: `public/social/assets/bed.mp3` YOK → her Short generated `pad.mp3`'e düşüyor
   (telifsiz, ban-güvenli). Trending-müzik telif/ban riski (kırmızı çizgi) — kullanmıyoruz, doğru.
2. **NEGATİF-TEYİT (önemli): AI-avatar YÜZ throttle'lanıyor** (reelforge/miraflow): "Shorts leading with AI avatar face
   → distribution few-hundred–~1000 impression cap, retention'a bakmaksızın." Biz faceless text/B-roll/Manim = throttle'ın
   DOĞRU tarafındayız. Ders: gelecekte 'konuşan AI-avatar' EKLEME — mevcut faceless yön kanıtlı doğru.
3. **YENİ KALDIRAÇ (myinstantplay): cut-synced transition SFX** — "ses tam kesim-frame'inde patlarsa (bass/whoosh cut'ta)
   beyin dopamin salgılar, pattern-interrupt tamamlanır." Bizde micro-cut faz-snap (v5.2, 08-23-2) VAR ama faz sınırında
   SES yok — sadece görsel snap. Faz-boundary'lerine hafif whoosh/impact SFX = görsel+işitsel pattern-interrupt birlikte.
   → **ENTEGRE ETMEDİM (disiplin):** SFX retention'ı etkiler = 08-23-2 (v5.2 micro-cut, AÇIK, ~08-27 olgun) ile AYNI
   'ort retention %' metriğine roll-up. 2. retention deneyi = 8-retention-confound kök hatası. EŞZAMANLILIK TAVANI.
   → 08-27'ye (08-23-2 kapanınca) KUYRUKLANDI.

**Sıradaki gece kuyruğu (güncel, retention slotu 08-27'de açılınca TEK-değişken sırayla):**
(1) 08-23-2 v5.2 micro-cut OLGUN (~08-27) → TEK verdict kapat.
(2) hook-yazım BOLD-CLAIM kuralı (present-tense + declarative, soru değil + ≤7 kelime + payoff-köprü) — izole retention edit.
(3) **cut-synced transition SFX** (bugünkü yeni bulgu — faz-boundary whoosh/impact) — izole retention edit.
(4) caption MarginV center-lower-third. (5) dedike kısa-metin kapak.
_Not: bed.mp3 (gerçek telifsiz bed) kurmak da retention'ı etkiler → aynı kuyruğa, tekil-izole ölç._

---
## 2026-08-26 — DATA-VİZ "tek-odak" ilkesi (Manim sahne tasarımı) — QUEUED (retention-confound)

**Araştırdım (WebSearch + WebFetch — bugün):** "faceless finance Shorts 2026 animated data visualization caption retention".
Kaynaklar: overseeros.com/blog/successful-faceless-finance-youtube-channels (YENİ kaynak), vozo.ai faceless-niches,
reelforgeai.io youtube-shorts-algorithm-2026, virvid.ai ai-faceless-automation-stack-2026.

1. **YENİ eyleme-dönük ilke: her grafik TEK odak noktası** (overseeros): finans görselinde "simple upward/downward
   line with one focal point" — birden çok seri/veriyle ekranı boğma, TEK finansal gerilimi izole et. Bu bizim
   Manim sahnelerine DOĞRUDAN uygular: **backtest** (büyüyen eğri) zaten tek-odak (iyi); ama **compare** (karşılaştırma
   barları) ve **concept** kartlarında bazen 3+ öğe yarışıyor. Kural: sahnede bir count-up/rakam VURGULU, gerisi
   soluk (dim). Bu bizim EN YÜKSEK skorlu formatımız **shock_number** (skor 349.7) ile aynı prensip → bağımsız teyit.
2. **Teyit (yeni iş yok):** "documentary retention ilk 15sn'de kazanılır, görsel karmaşıklıkla değil" (overseeros) →
   kanca-öncelikli hattımızı (v5.1/v5.2 hook-frame) doğruluyor. "Specific numbers = tangible" → shock_number DNA'sı.
3. **NEGATİF (kırmızı-çizgi teyidi):** virvid otomasyon-stack'i tam-AI-avatar öneriyor → biz faceless text/Manim
   kalıyoruz (08-25 throttle dersi). Avatar EKLEME kararı pekişti.

**NEDEN entegre ETMEDİM (disiplin):** Manim sahne-tasarımı (tek-odak/dim) retention'ı etkiler = açık `08-23-2`
(v5.2 micro-cut, ~08-27 olgun) ile AYNI 'ort retention %' metriğine roll-up. 2. retention deneyi = 8-retention-confound
kök hatası. EŞZAMANLILIK TAVANI → 08-27'ye (08-23-2 kapanınca) KUYRUKLANDI.

**Sıradaki gece kuyruğu (güncel, retention slotu 08-27'de açılınca TEK-değişken sırayla):**
(1) 08-23-2 v5.2 micro-cut OLGUN (~08-27) → TEK verdict kapat.
(2) hook-yazım BOLD-CLAIM kuralı (present-tense + declarative, soru değil + ≤7 kelime + payoff-köprü).
(3) cut-synced transition SFX (faz-boundary whoosh/impact).
(4) **Manim tek-odak/dim sahne tasarımı (bugünkü yeni bulgu — compare/concept sahnelerinde tek rakam vurgulu).**
(5) caption MarginV center-lower-third. (6) dedike kısa-metin kapak. (7) bed.mp3 telifsiz bed.

---
## 2026-08-27 — Retention slotu AÇILDI: hook BOLD-CLAIM entegre + series-labeling (non-retention) QUEUED

**Adım 0'da kapandı:** `08-23-2` (v5.2 micro-cut faz 2.7→1.8sn) → **inconclusive** (10. teyit: sub-saniye
pacing edit'i düşük-n retention'da çözünmüyor). 1.8sn micro-cut İYİ PRATİK olarak korundu, exp izlenmiyor.
Retention slotu boşaldı.

**ENTEGRE ETTİM (queue #2 — izole retention edit, yeni exp `08-27-1`):** viral-script.py hook kuralı:
EN FAZLA 9→**7 kelime** + **ŞİMDİKİ ZAMAN İDDİALI DÜZ CÜMLE (bold-claim)** tercih (soru kancası caydırıldı)
+ beat1'e **PAYOFF-KÖPRÜ** (kancanın açtığı döngüye 1. saniyede somut ödül-kırıntısı; açıklamayı sona saklama).
Kaynak: virvid/opus/reelforge (first-3s, ≤7 kelime, 1sn swipe-gate) + kendi DNA (shock_number 311 + myth 307 =
kazanan formatlar zaten düz-iddia; comparison=soru elendi 74). Kohort ~09-01 olgun → Adım 0'da kapat.

**Araştırdım (WebSearch — bugün, NON-retention lever, çünkü retention slotu artık dolu):**
"YouTube Shorts 2026 subscriber growth discoverability series playlist". Kaynaklar: joinbrands.com,
posteverywhere.ai/blog/how-to-get-more-youtube-subscribers, influenceflow.io shorts+long-form 2026,
shortsync.app/guides/grow-youtube-shorts.
1. **YENİ non-retention lever: "Part 1 of X" seri-etiketleme** — episode 1 açıkça episode 2'yi kurar;
   "1/4" etiketi seri-tamamlama + ABONE taahhüdünü yükseltiyor. Bizim YT hedefimiz ABONE (retention değil) →
   bu farklı, confound-etmeyen bir metrik (subscriber/views). Konu-kümesi Shorts serileri (ör. "Altın serisi 1/4",
   "Fed serisi") kurulabilir.
2. **Teyit (yeni iş yok):** Shorts = YT'nin ana discovery motoru, izlenmelerin çoğu abone-olmayandan; evergreen
   (aylar sonra arama trafiği). İlk-2-3sn kanca kritik → bugünkü hook-rule'u doğruluyor.
3. **Comment-depth signal** (ilk 50 yoruma 2 saatte yanıt) → bizde yorum hacmi 0-2/video, düşük kaldıraç, atlandı.

**NEDEN series-labeling'i ENTEGRE ETMEDİM (disiplin):** başlık/hook üreticisini bu gece ZATEN değiştirdim
(08-27-1). Series-labeling de başlığa/kancaya dokunur → iki eşzamanlı başlık-değişikliği = confound. Series
farklı metrik (abone) olsa da başlık-yüzeyinde 08-27-1 ile karışır. → **08-27-1 olgunlaşınca (~09-01) sıraya.**

**Sıradaki gece kuyruğu (güncel):**
(1) 08-27-1 hook BOLD-CLAIM OLGUN (~09-01) → kapat.
(2) **series-labeling "konu serisi X/N" (bugünkü yeni bulgu — abone metriği, retention-confound DEĞİL ama
    başlık-yüzeyi 08-27-1 ile confound → 08-27-1 sonrası).**
(3) cut-synced transition SFX (faz-boundary whoosh/impact) — retention slotu 08-27-1 sonrası açılınca.
(4) Manim tek-odak/dim sahne tasarımı — retention, aynı slot.
(5) caption MarginV center-lower-third. (6) dedike kısa-metin kapak. (7) bed.mp3 telifsiz bed.

---
## 2026-08-28 — SEAMLESS-LOOP yapısı (yüksek-kaldıraç yeni bulgu, kuyruğa) + veri-getiri Short fikri

**Araştırdım (WebSearch + WebFetch — bugün):** "YouTube Shorts retention 2026 open loop hook first frame
faceless finance" + virvid.ai/blog/looping-structure-shorts-retention-2026.
Kaynaklar: blitzcutai.com/blog/best-youtube-shorts-hooks-2026, virvid.ai/blog/looping-structure-shorts-retention-2026,
aibrify.com/blog/youtube-shorts-retention-curve-playbook, virvid.ai/blog/first-3-seconds-hook-faceless-shorts-2026.

1. **YENİ EYLEME-DÖNÜK LEVER — SEAMLESS LOOP (faceless yapısal avantaj):** Yüz/beden yok → izleyiciye
   "video bitti/yeniden başladı" diyen fiziksel süreklilik ipucu YOK. Son 3-5sn'yi ilk 3sn'ye **dikişsiz
   bağlarsan** Short loop'ladığında kanca 2. kez izleniyor → retention >%100'e çıkabiliyor. **Bizde zaten
   kanıt var:** `stagflasyon-nedir` %162 retention + `bankandaki-250-bin` %95 = tesadüfen loop'a yakın biten
   videolar. Bunu SİSTEMATİK yaparsak en yüksek-kaldıraçlı retention hamlesi olabilir.
   **Somut kurallar (shorts-build/viral-script'e uygulanacak):**
   - Son beat'in görseli = ilk beat'in görseline yakın-özdeş (aynı arka plan/tema/layout). Manim'de: kapanış
     sahnesi = açılış sahnesiyle aynı tema/tip (ör. ikisi de bigstat/slate).
   - Kapanışta CTA'yı görselden çıkar (follow-for-more loop'u kırar); "follow" ekran-metni loop noktasına KOYMA.
   - Loop noktasında sessizlik boşluğu olmasın (TTS son kelime → ilk kelimeye akışlı); freeze-frame yok, son
     karede hareket kalsın.
   - Süre ≤22-25sn (tam-tamamlama + loop için).
   - Kapanış cümlesi = kancaya "callback" (döngüyü kapatıp yeniden açan), mid-momentum biter (mid-sentence değil).
2. **NEDEN ENTEGRE ETMEDİM (disiplin — eşzamanlılık tavanı):** Seamless-loop = ort retention % metriğine
   roll-up. Açık `08-27-1` (hook bold-claim, ~09-01 olgun) ZATEN o metriği izliyor → 2. retention deneyi =
   8-retention-confound kök hatası. **08-27-1 kapanınca sıraya** (queue #2 önüne, en yüksek kaldıraç).
3. **Fikir (web↔YT köprüsü):** Bugün ürettiğim /halka-arz-getiri veri varlığı (ort +%51.5, KARCL +%275)
   doğrudan bir **shock_number Short** senaryosu (kazanan format, skor 317): "2026'da halka arza girenler
   ortalama %51 kazandı — ama biri %275 patladı, biri %12 batırdı." Veri→Short→veri-sayfası hunisi. viral
   konu havuzuna eklenebilir.

**Sıradaki gece kuyruğu (GÜNCEL — en yüksek kaldıraç öne):**
(1) 08-27-1 hook BOLD-CLAIM OLGUN (~09-01) → kapat.
(2) **SEAMLESS-LOOP (bugünkü bulgu — kanıtlı outlier stagflasyon %162; sistematikleştir) — retention, 08-27-1 sonrası TEK-izole.**
(3) series-labeling "konu serisi X/N" (abone metriği; başlık-yüzeyi 08-27-1 ile confound → sonrası).
(4) cut-synced transition SFX. (5) Manim tek-odak/dim. (6) caption MarginV. (7) dedike kapak. (8) bed.mp3.

---
## 2026-08-29 — Karaoke caption best-practice AUDIT: bizde ZATEN var; tek delta = inactive-word DIM (kuyruğa)

**Araştırdım (WebSearch + WebFetch):** "YouTube Shorts caption/subtitle style retention 2026 faceless finance
word-highlight karaoke". Kaynaklar: opus.pro/blog/youtube-shorts-caption-subtitle-best-practices,
blitzcutai.com/blog/best-caption-style-youtube-shorts-2026, vocallab.ai/blog/word-highlighting-subtitles,
voicecreator.pro/blog/word-by-word-animated-captions.
**2026 best-practice özeti:** kalın beyaz + ince siyah stroke, kelime-kelime (2-5 kelime öbek), center-lower
third, **word-level karaoke highlight** (aktif kelime kontrast renk + hafif büyür, çevre kelimeler DIMMER) →
altyazılı Shorts'ta +%12-15 tamamlama.

**AUDIT — bizim sistemimiz (`shorts-build-v4.py` satır 280-291):** ZATEN uyguluyoruz:
- `\k` karaoke timing (aktif kelime = C_SUNG sarı, okunmamış = C_UNSUNG beyaz) ✓
- pop-scale overshoot 84→106→100 (aktif kelime "hafif büyür") ✓
- yüksek kontrast (Outline 8, ScaledBorderAndShadow), font 94, \an5 center ✓
→ 2026 best-practice'i büyük ölçüde KARŞILIYORUZ. Genel-geçer "karaoke caption ekle" tavsiyesi bizde yeni iş değil.

**TEK somut delta (kuyruğa):** araştırma "çevre kelimeler DIMMER" diyor; bizde okunmamış kelime TAM BEYAZ
(C_UNSUNG). Bunu **dimli gri** (ör. ~%55-65 beyaz) yaparsak aktif sarı kelime daha çok "pop" eder, göz aktif
kelimeye kilitlenir (karaoke ritmi keskinleşir). Küçük, izole, tek-değişkenli edit: sadece C_UNSUNG rengi.

**NEDEN ENTEGRE ETMEDİM (disiplin — eşzamanlılık tavanı):** caption rengi = ort retention % metriğine roll-up.
Açık `08-27-1` (hook bold-claim, ~09-01 olgun) o metriği izliyor + kuyrukta ZATEN daha yüksek kaldıraçlı
SEAMLESS-LOOP (#2) var. Caption-dim düşük kaldıraçlı sub-saniye görsel sınıfına yakın (bkz 08-23 "sub-saniye
micro-edit'ler düşük-n retention'da çözünmez, 9x teyit") → yüksek-kaldıraç kuyruğun ÖNÜNE geçmez.
**Karar:** loop (#2) ve series (#3) sonrası, düşük-öncelik caption-MarginV(#6) ile birleştir.

**İçerik sinerjisi (web↔YT köprüsü, bugünkü /altin-getiri):** Yeni /altin-getiri istatistiği KAZANAN formatın
(shock_number, skor 315 + altın=DNA #1 konu) birebir yakıtı: **"10.000 TL'yi 10 yıl önce altına koysaydın bugün
551.892 TL olurdu — ama dolar bazında sadece %243."** Bu bizim #1 YT videomuzun ('10.000 TL altına koysaydın',
962 izlenme, %55 retention) veri-güncellenmiş, kur-etkisini-ayıran versiyonu. viral konu havuzuna eklenebilir
(veri→Short→sayfa hunisi, halka-arz-getiri fikriyle aynı hat).

**Sıradaki gece kuyruğu (GÜNCEL):** (1) 08-27-1 kapat (~09-01). (2) SEAMLESS-LOOP (retention, tek-izole).
(3) series-labeling X/N (abone). (4) cut-synced SFX. (5) Manim tek-odak/dim. (6) **caption inactive-word DIM +
MarginV (birleşik, düşük öncelik).** (7) dedike kapak. (8) bed.mp3.

---
## 2026-09-04 — 2026 pacing/motion + TTS AUDIT: pipeline zaten hizalı; iki lever kapalı (yeni-iş yok, dürüst sonuç)

**Araştırdım (WebSearch — bugün):** (1) "YouTube Shorts retention 2026 faceless finance b-roll pacing dynamic
zoom ken burns" (2) "best free Turkish TTS 2026 open source alternative".
Kaynaklar: aibrify.com/blog/youtube-shorts-retention-curve-playbook, socialync.io/blog/youtube-shorts-algorithm-2026,
lenostube.com/en/youtube-audience-retention-average-good-and-best-benchmarks, fluxnote.io/guides/faceless-channel-retention-strategies-2026,
elevenlabs.io/text-to-speech/turkish, github.com/Rumeysakeskin/free-turkish-tts-models (XTTS-v2/Coqui).

**2026 pacing/motion consensus:** görsel değişim her **1.5-2sn** (altı 1.2sn = "gürültü"/tune-out, üstü 2.5sn+
= stimulus düşük, retention düşer); statik kare **>4sn = swipe**; still görselde **sürekli yavaş zoom/pan
(Ken Burns) = "kamera hareketi"** sayılır, gözü hareket ettirir; %70-85 sessiz izleniyor → baked caption şart.

**AUDIT — bizim pipeline (`shorts-build-v4.py`):** 2026 consensus'ü ZATEN karşılıyoruz, yeni-iş çıkmadı:
- `_kenburns(motion, D)` (satır 636/705): **sahne-başına DEĞİŞEN** Ken Burns (hook güçlü zoom-in, sonraki
  sahneler farklı zoom/pan yönü) — "her klip aynı zoom" hissi zaten kırık, still'ler hareketli. ✓
- micro-cut faz süresi 1.8sn (08-23) = 2026 hedef 1.5-2sn bandının tam içinde. ✓
- baked karaoke caption (\k highlight, 08-29 audit) + %85-sessiz için tasarlı. ✓
- v5.1 hook klibinde from-black fade KESİK (ilk kare tam parlak) = swipe-stop best-practice. ✓
→ **Ken Burns "ekle" tavsiyesi bizde YENİ İŞ DEĞİL** (zaten var + varyasyonlu). Pacing/motion/caption ekseninde
  2026 ile hizalıyız; buraya ek retention hamlesi yapmak düşük kaldıraç + zaten açık seamless-loop'la confound olur.

**TTS lever — DEĞERLENDİRİLDİ, REDDEDİLDİ:** ElevenLabs TR sesleri kaliteli ama ücretsiz **10k karakter/ay**
(~1-2 Short) → günlük üretim hattına yetmez. XTTS-v2/Coqui self-host ses-klonlama yapıyor ama Coqui 2024'te
kapandı (community-maintained), kurulum/kalite riski. Bizim Google Chirp3-HD öğrenme motorunda KAZANIYOR
(google skor 170.6/n=53 vs edge 87.2/n=2). **Karar:** Google Chirp3-HD'de KAL; ElevenLabs'ı yalnız özel/pin'li
tek video için manuel opsiyon olarak not et (ücretli anahtar gerekirse tasks-for-user). Kod değişikliği YOK.

**Bu gecenin R&D çıktısı (dürüst):** araştırma iki leveri de kapattı — biri (Ken Burns/pacing) zaten entegre,
diğeri (TTS switch) maliyet/kalite gerekçesiyle reddedildi. Yeni entegrasyon açmadım çünkü (a) seamless-loop
(09-02-1) tek açık retention deneyi = eşzamanlılık tavanı, (b) araştırılan lev- ler yeni değer getirmiyor.
Kuyruk değişmedi.

**Sıradaki gece kuyruğu (GÜNCEL):** (1) SEAMLESS-LOOP (09-02-1, retention, ~09-07 olgun) — bekle+ölç.
(2) audio-callback kapanış cümlesi (cta-spoken=hook callback; retention, loop kapanınca izole).
(3) series-labeling X/N (abone). (4) cut-synced SFX. (5) Manim tek-odak/dim. (6) caption inactive-word DIM+MarginV.
(7) dedike kapak. (8) bed.mp3.

---
## 2026-09-05 — Hook R&D: "text-visual contradiction" pattern-interrupt (YENİ lever bulundu, kuyruğa — confound riski)

**Araştırdım (WebSearch — bugün):** "YouTube Shorts hook retention 2026 first frame text pattern interrupt B-roll faceless".
Kaynaklar: truefan.ai/blogs/trending-hook-formats-2026, air.io/en/youtube-hacks/advanced-retention-editing-cutting-patterns,
prepublish.ai/guides/youtube-shorts-retention, easymeaningz.com/short-form-video-fatigue-hook-first-3-seconds,
influencers-time.com/youtube-shorts-algorithm-a-brand-guide-to-hooks-and-loops.

**2026 consensus (bizde AUDIT):**
- Swipe kararı ilk **1-1.5sn** (bilinçli işlemeden ÖNCE); ilk 3sn'de >%25 kayıp → algoritma reach'i kısar. → bizde v5.1
  hook klibi from-black fade KESİK (ilk kare tam parlak) + baked bold caption ✓ zaten hizalı.
- Pattern-interrupt **her 10-15sn** (jump-cut/B-roll/grafik) sıkıcılık saatini sıfırlar. → bizde micro-cut **1.8sn**
  (08-23) = bu cadence'ın ÇOK üstünde (daha sık), yeni-iş değil ✓.
- Caption sessizde (%70-85 sessiz izleme) → baked karaoke ✓.

**TEK genuinely-yeni lever (kuyruğa):** _"text-visual CONTRADICTION hook"_ — ilk 1-2sn'de ekrandaki metnin B-roll
görselle ÇELİŞMESİ (ör. görsel: parlak altın bilezik / metin: "BU SENİ ZENGİN ETMEZ") = pattern-interrupt +
merak boşluğu. Bu bir SENARYO/PROMPT leveri: viral-script.py hook-beat'inde görsel-seçimi ile hook-metni bilerek
zıtlaştırılır. Kazanan DNA'mızla (myth/kayıp-korkusu + altın) doğal örtüşüyor.

**NEDEN ŞİMDİ ENTEGRE ETMEDİM (disiplin — eşzamanlılık tavanı):** contradiction-hook = ort. retention % + ilk-3sn
tutma metriğine roll-up. Açık `09-02-1` SEAMLESS-LOOP tam bu metriği izliyor = TEK açık retention deneyi. İkinci
retention leveri şimdi açarsam confound (08-17 kök hatasının tekrarı). Loop ~09-07 olgunlaşıp kapanınca, İZOLE
tek-değişkenli olarak aç: hook-beat görsel/metin zıtlığı, exp.py ile kaydet.

**Kuyruk (GÜNCEL — sıra değişti):** (1) SEAMLESS-LOOP (09-02-1) bekle+ölç ~09-07. (2) **contradiction-hook**
(yeni, retention, loop kapanınca izole — audio-callback'in önüne alındı: ilk-3sn tutma en yüksek kaldıraç).
(3) audio-callback kapanış cümlesi. (4) series-labeling X/N (abone). (5) cut-synced SFX. (6) Manim tek-odak/dim.
(7) caption inactive-word DIM+MarginV. (8) dedike kapak. (9) bed.mp3.

---
## 2026-09-06 — Cut-synced SFX: SOMUT dB spesifikasyonu bulundu (kuyruktaki #5'e ölçü eklendi, confound riski → bekliyor)

**Araştırdım (WebSearch — bugün):** "YouTube Shorts sound design SFX whoosh retention 2026 faceless finance editing".
Kaynaklar: soundstripe.com/blogs/royalty-free-sound-effects-for-youtube-shorts, alibimusic.com/blog/how-to-use-royalty-free-music-and-sfx,
videoeditingsfx.com/free-sound-effects-youtube-shorts (CC0/no-copyright MP3), youtubesfx.com/free-sfx-pack (40 CC0 ses),
github.com/hassancs91/claude-faceless-shorts-creator ("library-first sound design: function-first cues, layered hero moments").

**AUDIT — bizim pipeline (`shorts-build-v4.py`):** müzik bed'i VAR (`public/social/assets/bed.mp3`, volume=0.13 amix, satır 966-968)
ama **cut-senkron SFX YOK** (her micro-cut'ta whoosh, kilit beat'te impact hit yok). Bu, R&D kuyruğundaki #5 ("cut-synced SFX")
ile örtüşüyor — şimdiye kadar soyuttu, artık SOMUT ölçü var.

**SOMUT SPEC (2026 consensus, entegrasyon hazır):**
- **Whoosh her cut'ta:** −18 dB … −24 dB (görsel geçişini duyulur ama bastırmayan şekilde vurgular).
- **Impact/hit kilit beat'te** (sayı-şoku, myth reveal, hook sonu): −12 dB … −18 dB.
- **Library-first:** tekrar-kullanılabilir CC0 SFX kütüphanesi (`public/social/assets/sfx/` altına whoosh.mp3 + impact.mp3),
  ffmpeg `adelay` ile cut zaman-damgalarına hizala, mevcut `amix`'e ek input olarak kat (bed + TTS + SFX).
- Kaynak: youtubesfx.com/free-sfx-pack (40 CC0), videoeditingsfx.com (CC0 MP3) — telif-güvenli.

**NEDEN ŞİMDİ ENTEGRE ETMEDİM (disiplin — eşzamanlılık tavanı, 08-17 kök hatası):** cut-synced SFX = ort. retention %
metriğine roll-up. Açık `09-02-1` SEAMLESS-LOOP tek açık retention deneyi. İkinci retention leveri şimdi açmak confound.
Loop ~09-07 kapanınca kuyruk sırasıyla izole aç. Bugün araştırma çıktısı: soyut "SFX ekle" → SOMUT dB+kaynak+ffmpeg planı
(gelecek-gece tekrar araştırmaya gerek yok).

**Kuyruk (GÜNCEL — sıra korunuyor, spec eklendi):** (1) SEAMLESS-LOOP (09-02-1) kapat/ölç ~09-07. (2) contradiction-hook (izole).
(3) audio-callback kapanış. (4) series-labeling X/N. (5) **cut-synced SFX — SPEC HAZIR** (whoosh −18/−24dB + impact −12/−18dB,
CC0 kütüphane, adelay+amix). (6) Manim tek-odak/dim. (7) caption inactive-word DIM+MarginV. (8) dedike kapak.

---
## 2026-09-07 — Contradiction-hook ENTEGRE EDİLDİ (seamless-loop kapandı → slot açıldı)

**Adım 0:** seamless-loop (09-02-1) olgunlaştı, KAPANDI (inconclusive). 09-02/03 kohortu retention n=5:
44/34.25/43.17/13.47/25.55 → ort ~32%, baseline 35-45 bandının altında, loop-outlier (>95%) YOK. Mikro-görsel
edit sınıfı gibi düşük-n retention'da temiz verdict vermedi. İyi-pratik korunuyor, retention slotu boşaldı.

**Entegrasyon (kuyruk #2, izole tek-değişken):** contradiction-hook → `viral-script.py` hook prompt'una
"HOOK GÖRSEL-METİN ZITLIĞI" kuralı eklendi. Hook beat görseli çekici/beklenen olumlu yüzeyi (parlak altın
bilezik, yeni ev, dolu cüzdan, yükselen grafik) gösterir; metin kaybı/miti söyler → göz+kulak çelişkisi ilk
1-2sn kaydırmayı keser. İSTİSNA: person/place/logo hook (news_reaction) birebir kalır; point'ler örtüşen.
Syntax ✓, commit 02b1915. exp `2026-09-07-1` (retention, TEK açık = eşzamanlılık tavanı, ~09-12 olgun).

**Araştırma değil, entegrasyon gecesiydi:** 09-05 (contradiction-hook spec) + 09-06 (cut-synced SFX spec)
zaten araştırılmıştı; bu gece slot açılınca #2'yi hayata geçirdim. Yeni WebSearch yapmadım (kuyrukta 2 hazır-spec
lever bekliyor, tekrar araştırma israf olurdu).

**Kuyruk (GÜNCEL):** (1) contradiction-hook (09-07-1) AKTİF — ölç ~09-12. (2) audio-callback kapanış cümlesi.
(3) series-labeling X/N (abone). (4) cut-synced SFX — SPEC HAZIR (whoosh −18/−24dB + impact −12/−18dB, CC0, adelay+amix).
(5) Manim tek-odak/dim. (6) caption inactive-word DIM+MarginV. (7) dedike kapak. (8) bed.mp3 tuning.

---
## 2026-09-10 — Intro-retention benchmark (>%70 ilk-3sn) + Veo 3 Fast taraması (WebSearch)

**Araştırdım (WebSearch):** "YouTube Shorts retention 2026 first 3 seconds hook faceless finance new tools".
Kaynaklar: opus.pro/blog/youtube-shorts-hook-formulas, aibrify.com/blog/youtube-shorts-retention-curve-playbook,
virvid.ai/blog/first-3-seconds-hook-faceless-shorts-2026, techcrunch (Veo 3 Fast on Shorts).

**Bulgular:**
1. **ÖLÇÜLEBİLİR HEDEF — intro retention >%70** (ilk 3sn'yi geçenlerin oranı). vidIQ: <2sn hook'lu Shorts,
   uzun-intro'lulardan %30 daha yüksek ort. izleme süresi. → Bizim retention verimiz çoğu videoda %30-45;
   asıl kayıp ilk-3sn'de. Bu, açık `09-07-1` contradiction-hook deneyinin TAM hedefi = doğru lever'daymışız.
   **Aksiyon:** 09-12 Adım 0'da 09-07 kohortunu ölçerken sadece ort. retention değil, mümkünse **ilk-3sn tutma
   (intro retention) %'sini** de YouTube Analytics'ten çek; benchmark %70. Yeni deney AÇMA (tavan dolu).
2. **Bold-claim > curiosity-gap** faceless kanallarda (kişisel marka yokken ani-değer sinyali daha hızlı tutuyor).
   → Bizde bold-claim (08-27) + contradiction-hook (09-07) zaten var; teyit, yeni-iş yok.
3. **Veo 3 Fast (YouTube native text-to-video, Shorts)** — 480p düşük-gecikme B-roll üretimi. **Bizim için ŞİMDİLİK
   DEĞİL:** 480p dikey-Short kalitesi bizim Manim/Wikimedia hattının altında; ayrıca API/erişim belirsiz.
   İzlemeye al; kalite 1080p'ye çıkarsa jenerik-stok yerine değerlendir.

**Entegrasyon YOK (disiplin):** slot `09-07-1` ile dolu; bulgu 1 zaten aktif deneyle örtüşüyor, 2 teyit, 3 erken.
Net yeni-iş: 09-12 ölçümünde intro-retention %'yi baseline'a ekle.

**Kuyruk (değişmedi):** (1) contradiction-hook (09-07-1) AKTİF — ölç ~09-12 (+intro-retention %). (2) audio-callback.
(3) series-labeling X/N. (4) cut-synced SFX (SPEC HAZIR). (5) Manim tek-odak/dim. (6) caption DIM. (7) dedike kapak.

---
## 2026-09-11 — Karaoke/word-level caption 2026-standardı: BİZDE ZATEN VAR (audit-teyit)

**Araştırdım (WebSearch):** "YouTube Shorts caption subtitle style 2026 word-by-word karaoke retention faceless".
Kaynaklar: vocallab.ai/blog/word-highlighting-subtitles, blitzcutai.com/blog/best-caption-style-youtube-shorts-2026,
vocallab.ai/blog/word-level-timestamped-subtitles-for-videos, fluxnote.io/best/best-ai-caption-tools-short-form-video.

**Bulgu:** 2026 konsensüsü — **word-by-word karaoke highlight** (konuşuldukça her kelime renk değiştirir)
statik altyazıya göre retention'ı **%30-40 artırıyor**; faceless/anlatı ağırlıklı içerikte baskın stil.
Standart biçim: kalın beyaz + ince siyah kontur, 2-5 kelimelik chunk, alt-orta üçte bir.

**AUDIT — bizim `shorts-build-v4.py`:** ZATEN bu standartta. Kanıt: faster-whisper `word_timestamps=True`
→ `align_words` (difflib ile script'e hizala) → ASS `\k` centi-saniye timing ile **gerçek senkron karaoke**;
aktif kelime SARI (`C_SUNG`), okunmamış beyaz (`C_UNSUNG`), kontur+gölge (Outline=8, Shadow=5). 2-5 kelime
chunk (`chunk_words`), MarginV=84 (alt-orta). = 2026 best-practice birebir.

**Sonuç: yeni-iş YOK — teyit.** Bir yıl önce (v3→v4) doğru bahse girmişiz; piyasa şimdi oraya geldi.
Enerji boşa harcanmadı. **Entegrasyon YOK** (zaten var + retention slotu `09-07-1` ile dolu = tavan).
İyileştirme fikri (gelecek, izole): kelime-vurgu rengini formata göre değiştir (myth=kırmızı-uyarı,
shock_number=sarı) — ama bu #7 (caption inactive-word DIM) ile aynı kohortu paylaşır, sıra korunur.

**Kuyruk (değişmedi):** (1) contradiction-hook (09-07-1) AKTİF — ölç ~09-12 (+intro-retention %).
(2) audio-callback. (3) series-labeling X/N. (4) cut-synced SFX (SPEC HAZIR). (5) Manim tek-odak/dim.
(6) caption inactive-word DIM+MarginV (+word-color-by-format fikri). (7) dedike kapak.

---
## 2026-09-22 — Cut-synced SFX kaynağı bulundu (VideoEditingSFX CC0) + retention slot AÇILDI

**Adım 0:** `09-07-1` contradiction-hook KAPANDI (inconclusive — 15 gün, retention bandı 29-55% kımıldamadı,
tüm hook-edit sınıfının 4. teyidi). Retention eşzamanlılık-slotu artık BOŞ → kuyruk #4 (cut-synced SFX,
SPEC HAZIR) izole açılabilir.

**Araştırdım (WebSearch):** "YouTube Shorts SFX whoosh impact retention faceless 2026 free CC0".
Kaynaklar: soundstripe.com/blogs/royalty-free-sound-effects-for-youtube-shorts,
videoeditingsfx.com/free-sound-effects-youtube-shorts, youtubesfx.com/free-sfx-pack, mixkit.co/free-sound-effects.

**Bulgu (somut kaynak):** **VideoEditingSFX** — TAMAMI CC0 + **Content ID'ye kayıtlı DEĞİL** (monetize
Short'ta telif iddiası riski YOK, bizim hat için ideal). Kategoriler: Whoosh & Transitions (26), Impacts (11),
Risers (5), Buildups (9), UI (19). = #4 spec'inin tam ihtiyacı (whoosh her cut'ta, impact her key-point'te).
Konsensüs: "Shorts pacing'le yaşar/ölür; her cut'ta whoosh + her vurguda impact loop'a kadar izletir."

**Entegrasyon planı (sıradaki gece, slot açık):** VideoEditingSFX Whoosh+Impact CC0 paketini `assets/sfx/`'e
indir → `shorts-build-v4.py` ffmpeg zincirine cut noktalarında `adelay`+`amix` ile whoosh (−18/−24dB) +
key-beat'lerde impact (−12/−18dB) bindir (spec zaten hazır). İZOLE tek-değişken → yeni exp `add` (retention,
tek açık = eşzamanlılık tavanı). Bu gece indirme/kod YAPILMADI (bütçe IG kök-hata düzeltmesine gitti);
kaynak+plan kesinleşti, slot açık, sıradaki gece uygulanacak.

**Kuyruk (GÜNCEL):** (1) cut-synced SFX — SPEC HAZIR + kaynak (VideoEditingSFX CC0) ← SIRADAKİ, slot açık.
(2) audio-callback kapanış. (3) series-labeling X/N. (4) Manim tek-odak/dim. (5) caption inactive-word DIM.
(6) dedike kapak. (7) bed.mp3 tuning.

---
## 2026-09-24 — Cut-synced SFX ENTEGRE EDİLDİ (kuyruk #1 tamam) + retention exp açıldı

**Adım 0:** Açık deney yoktu (0). 09-23 kısmi oturumu SFX asset'lerini (`assets/sfx/whoosh.wav`,
`impact.wav` — VideoEditingSFX CC0, Content-ID'siz) indirip commit'lemiş ama `shorts-build-v4.py`
ENTEGRASYONU yapmamış (session limitle düşmüş, rapor yazılmamış). Bu gece entegrasyon tamamlandı.

**Yapıldı (shorts-build-v4.py):**
- `SFX_DIR` sabiti + `build_sfx_track(cues, total, path)` helper: her cue'yu `adelay`+`volume` ile
  konumlayıp `amix=normalize=0` ile tek track'e indirger, `apad` ile video boyuna uzatır. Savunmacı:
  kaynak/ffmpeg düşerse None → hat kırılmaz.
- Cue mantığı (segment döngüsünde): kanca (t≈0.03) + orta-video punch-in (rehook_idx) = **impact**
  (~−12dB, key beat); diğer her sahne kesişimi (i≥1) = **whoosh** (~−18dB). tcur = klip başlangıç anı.
- Final mux: müzik+SFX → 3'lü amix (ses + ducked bed + sfx); müziksiz → ses+sfx; ikisi de yoksa eski yol.
  `--no-sfx` bayrağı ile kapatılabilir. SFX düşük ses + sidechain'e girmez (konuşmayı bastırmaz).

**Test (kanıt):** py_compile ✓; `build_sfx_track` izole test → 15.0s track, peak −28dB (sübtil, doğru);
her iki yeni mux filtergraph'ı gerçek ffmpeg ile dummy input'larda doğrulandı → duration=first çalışıyor
(çıktı = joined uzunluğu). Tam-build (TTS+broll+whisper) çalıştırılmadı; ffmpeg katmanı kanıtlandı.

**Deney:** `2026-09-24-1` (youtube, retention) — baseline SFX-öncesi ort. retention ~%38-45 (medyan ~43).
Eşzamanlılık: retention'da TEK açık deney = tavan tutuldu. ~5-7 SFX'li video biriktikçe Adım 0'da ölç.
İzole tek-değişken (yalnız SFX eklendi) → önceki hook-edit confound hatasını tekrarlamıyor.

**Kuyruk (GÜNCEL):** (1) cut-synced SFX — ✅ ENTEGRE (exp 09-24-1 açık). (2) audio-callback kapanış.
(3) series-labeling X/N. (4) Manim tek-odak/dim. (5) caption inactive-word DIM. (6) dedike kapak. (7) bed.mp3 tuning.

---
## 2026-09-25 — Hook 3sn ölçüm sinyali + progress-bar (mute value cue) araştırması

**Adım 0:** retention slotu SFX (09-24-1) ile DOLU → yeni retention-entegrasyonu AÇMA. Bu gece =
saf Ar-Ge + ölçüm-kaldıracı (entegrasyon yok, kohort bekleniyor).

**Araştırdım (WebSearch):** "YouTube Shorts retention 2026 hook first 3 seconds pattern interrupt
faceless finance". Kaynaklar: opus.pro/blog/youtube-shorts-hook-formulas ·
shorta.ai/blog/2026-01-04-youtube-shorts-hook-patterns · tubeanalytics.net/blog/youtube-shorts-retention-guide ·
virvid.ai/blog/first-3-seconds-hook-faceless-shorts-2026 · fliki.ai/blog/youtube-shorts-algorithm-explained.

**3 somut bulgu:**
1. **"Viewed vs. Swiped Away" (YouTube Studio Short-özel metrik)** — izleyicinin %50-60'ı ilk 3sn'de
   düşüyor; 3sn işaretindeki keskin düşüş = kanca başarısız. Bu, bizim yüksek-varyanslı GENEL retention
   %'mizden DAHA İZOLE bir kanca sinyali. **KALDIRAÇ:** genel retention (n düşük, gürültülü) yerine
   3sn-hold'a bakabilirsek hook-edit deneyleri (bugüne dek hep inconclusive kapandı) NİHAYET ayrışabilir.
   → Görev: YouTube Analytics API'de `audienceWatchRatio`/elapsedVideoTimeRatio ile ilk-3sn retention
   çekilebilir mi araştır (ölçüm scriptine ekleme adayı — learn/ hattı). Bu, hook-confound'un kök çözümü olabilir.
2. **Progress bar / ilerleme çubuğu (mute/faceless value cue)** — 2026 konsensüsü: sesi kapalı izleyen için
   kinetik metin + emoji-checklist + **ilerleme çubuğu** değeri sesten bağımsız iletir. Bizde YOK. Aday:
   Shorts'a ince üst/alt ilerleme çubuğu (video boyunca dolar) → "bitişe ne kadar kaldı" belirsizliğini
   azaltır, loop'a kadar tutar. İZOLE tek-değişken; retention slotu boşalınca (SFX kohortu olgunlaşınca) dene.
3. **Pacing hedefi 1.5-2sn'de bir görsel değişim (cut/zoom/whip-pan/metin değişimi)** — bizde micro-cut
   1.8sn ZATEN bu bandda (teyit, yeni-iş yok). Whip-pan/dramatik-zoom "filmy" pattern-interrupt olarak
   öneriliyor; bizim Manim + broll geçişleri buna yakın. Ek fikir: sahne geçişlerinde hafif zoom-punch
   (SFX whoosh ile senkron) — ama bu SFX kohortuyla confound olur, SIRA korunur.

**Sonuç:** entegrasyon YOK (slot dolu). En yüksek kaldıraçlı bulgu = #1 (3sn-hold ölçümü) çünkü ölçüm
darboğazımızı (hook-edit'ler hep inconclusive) çözebilir. Sıradaki gece slot açıksa: önce #1 ölçüm
scriptini araştır/kur (deney ayrıştırıcı), sonra #2 progress-bar entegre + izole exp.

**Kuyruk (GÜNCEL):** (1) cut-synced SFX — ✅ ENTEGRE (exp 09-24-1 açık, ölç ~09-30). (2) **3sn-hold ölçümü
(YT Analytics API) — ölçüm kaldıracı, hook-confound kök çözümü ← YENİ, yüksek öncelik.** (3) progress-bar
mute value-cue (izole retention denemesi). (4) audio-callback kapanış. (5) series-labeling X/N.
(6) Manim tek-odak/dim. (7) caption inactive-word DIM. (8) dedike kapak.

---
## 2026-09-26 — 3sn-hold ÖLÇÜM SCRIPTİ KURULDU (kuyruk #2 tamam) — hook-confound kök çözümü

**Adım 0:** Retention slotu SFX (09-24-1) ile DOLU → yeni retention-ENTEGRASYONU açılmadı. Bu gece =
ÖLÇÜM kaldıracı (deney ayrıştırıcı), üretim hattına dokunmadan.

**Araştırdım (WebSearch):** YouTube Analytics API `elapsedVideoTimeRatio` (dim) + `audienceWatchRatio` /
`relativeRetentionPerformance` (metrics). Kaynaklar: developers.google.com/youtube/analytics/dimensions ·
/metrics · humbleandbrag.com/blog/youtube-audience-retention-benchmarks · retensis.com/blog/youtube-shorts-analytics-metrics-explained.
Bulgu: `elapsedVideoTimeRatio` video başına 100 nokta (0.01..1.0) retention eğrisi verir; ilk-3sn noktası =
"swipe or stay" penceresi. 2026 hedefi: <30sn Short'ta 3sn swipe-away <%25, 30-60sn'de <%35.

**Kurdum:** `scripts/learn/hook_retention.py` — ledger'daki en yeni 20 Short için video başına 1 Analytics
sorgusu: süreyi (contentDetails) çekip 3sn→ratio çevirir, eğride o noktaya en yakın audienceWatchRatio +
relativeRetentionPerformance'ı alır → `data/learning/hook-retention.json` + konsol tablosu (medyan/en iyi/
en kötü). Savunmacı: tek video düşse hat kırılmaz; scope yoksa atlar. `learn-daily.sh`'a eklendi (nightly).

**İlk çalıştırma (14 video):** medyan 3sn-hold %104 (loop nedeniyle >100 normal), en iyi %159 (iKuJtsN_9ck),
en kötü %100 (hqK7s0bMkHU). NOT: Shorts'ta audienceWatchRatio 1.0'ı aşar (loop/rewatch = güçlü kanca sinyali);
cross-video kıyas için relativeRetentionPerformance (0-1 yüzdelik) daha temiz — ikisi de kaydediliyor.

**Neden yüksek kaldıraç:** hook/başlık edit deneyleri bugüne dek HEP inconclusive kapandı çünkü genel
retention düşük-n + yüksek varyans. Artık İZOLE 3sn-hold sinyali birikiyor → sıradaki hook-edit deneyi
(progress-bar / kanca-yazım) NİHAYET ayrışabilir. Birkaç gün veri biriktir, sonra hook deneyi aç.

**Kuyruk (GÜNCEL):** (1) cut-synced SFX — ✅ ENTEGRE (exp 09-24-1, ölç ~09-30). (2) 3sn-hold ölçümü —
✅ KURULDU + nightly (birkaç gün veri biriktir). (3) progress-bar mute value-cue (izole retention denemesi —
slot açılınca; artık 3sn-hold ile ölçülebilir). (4) audio-callback kapanış. (5) series-labeling X/N.
(6) Manim tek-odak/dim. (7) caption inactive-word DIM. (8) dedike kapak.

---
## 2026-09-28 — 65% AVD eşiği (algoritma-kapısı) + kinetik-caption "hook-anim/beat-hold" rafinesi

**Adım 0:** Retention slotu SFX (09-24-1, ~09-30 matür) ile DOLU → yeni retention-ENTEGRASYONU AÇILMADI.
Bu gece = saf Ar-Ge + kaydetme.

**Araştırdım (WebSearch):** "YouTube Shorts progress bar retention 2026 kinetic captions faceless finance
value cue". Kaynaklar: socialync.io/blog/youtube-shorts-algorithm-2026 · fluxnote.io/guides/good-audience-retention-youtube-shorts ·
cutup.shop/blog/best-subtitle-workflow-youtube-shorts-2026 · zebracat.ai/post/youtube-shorts-statistics ·
truefan.ai/blogs/youtube-shorts-attention-grabbing-hooks-tips.

**3 somut bulgu:**
1. **65% AVD ALGORİTMA KAPISI (<30sn Short) — YENİ, ölçülebilir hedef.** 2026 konsensüsü: <30sn Short'ta
   ortalama izleme süresi ~%65'i geçmeden algoritma videoyu topic-cluster + high-intent izleyiciye
   EŞLEŞTİRMİYOR. Bu, bizim dağıtım darboğazımızın (yüksek retention'lı videolar bile siteye/keşfe akmıyor)
   SAYISAL kapısı olabilir. Bizim retention tablosu: medyan ~%43, ama birçok video %28-38 bandında = KAPININ
   ALTINDA → algoritma dağıtmıyor olabilir. **KALDIRAÇ:** hook_retention.py'ye Short başına genel AVD%'yi de
   ekleyip "%65 kapısını geçen video oranı"nı izlemek → hangi format/konu kapıyı geçiyor net görülür. (Ölçüm
   scripti adayı — slot/ölçüm işi, üretim-confound YOK.)
2. **Progress-bar mute value-cue** — 2026 konsensüsü teyit (kuyruk #3 zaten planlı). 3sn-hold ölçümü kurulduğu
   için artık İZOLE ölçülebilir; SFX kohortu olgunlaşınca (slot boşalınca) dene.
3. **Kinetik-caption RAFİNESİ (yeni, düşük-risk iyi-pratik): "hook'u anime et, açıklama beat'inde SABİT tut."**
   Her hecede kelime-animasyonu (bizde caption her kelime pop yapıyor olabilir) tempoyu "frantik" yapıp
   açıklama beat'lerinde okumayı zorlaştırıyor. Öneri: kanca beat'inde kinetik vurgu KALSIN, açıklama
   beat'lerinde altyazı sakin/sabit görünsün. Bu kuyruk #7'deki (caption inactive-word DIM) ile örtüşür —
   ikisini birleştir: açıklama beat'lerinde pasif kelime DIM + daha az pop.

**Sonuç:** entegrasyon YOK (slot dolu). En yüksek kaldıraç = #1 (65% AVD kapısı ölçümü) — dağıtım
darboğazının sayısal teşhisi; 3sn-hold ölçümünü tamamlar. Sıradaki gece slot/ölçüm işi olarak:
hook_retention.py'ye genel-AVD% + "65% kapısını geçen oran" ekle. Sonra slot boşalınca #2 progress-bar.

**Kuyruk (GÜNCEL):** (1) cut-synced SFX — ✅ ENTEGRE (exp 09-24-1, ölç ~09-30). (2) 3sn-hold ölçümü —
✅ KURULDU + nightly. (2b) **65% AVD kapısı ölçümü — hook_retention.py'ye ekle (ölçüm, confound yok) ← YENİ.**
(3) progress-bar mute value-cue (slot boşalınca izole). (4) audio-callback kapanış. (5) series-labeling X/N.
(6) Manim tek-odak/dim. (7) caption inactive-word DIM + hook-anim/beat-hold rafinesi (birleştir).
(8) dedike kapak.

---
## 2026-09-29 — 65% AVD kapısı ölçümü ENTEGRE + İLK TEŞHİS (kuyruk #2b tamam)

**Adım 0:** Retention slotu SFX (09-24-1, ~09-30 matür) ile hâlâ DOLU → yeni retention-ENTEGRASYONU
açılmadı. Bu gece = kuyruk #2b (ölçüm kaldıracı, üretim-confound YOK).

**Entegre ettim:** `scripts/learn/hook_retention.py`'ye genel `averageViewPercentage` eklendi — TEK
batched sorgu (dimensions=video, video başına ekstra sorgu YOK). Çıktıya `avg_view_pct` (video başına)
+ payload'a `median_avg_view_pct`, `avd_gate_pct=65`, `gate_pass_share`, `gate_pass_n`. Konsol satırı:
"AVD: medyan %X · %65 kapısını geçen: N/M". nightly (learn-daily.sh zaten çağırıyor).

**İLK TEŞHİS (12 video, 2026-09-29):** medyan AVD **%41** · **%65 kapısını geçen yalnız 1/12 (%8)**.
→ Bu, dağıtım darboğazının SAYISAL kanıtı: videoların %92'si 2026 algoritma-eşleştirme kapısının
ALTINDA → yüksek 3sn-hold (medyan %103, loop güçlü) olsa BİLE algoritma topic-cluster'a dağıtmıyor.
Kanca güçlü ama ORTALAMA-İZLEME zayıf = izleyici ilk saniyeden sonra bırakıyor (orta-video sarkması).

**Kaldıraç yorumu:** Bugüne dek "kanca" (3sn) üzerine çalıştık; ölçüm gösteriyor ki asıl kayıp
ORTA-VİDEO (3sn sonrası → %65). retention tablosundaki kapıyı GEÇEN türler: enflasyon-verisi-altın
(%75), jackson-hole (%76), ev-aldım-borç (%61), 10000TL-altın (%55), kira-getiri (%53) = NET
ANLATI-YAYLI + tek-merak-kancası konular. Kapının ALTINDA kalanlar: profesyonel-fon (%29), abd-faiz-
yükseltirse-dolar (%28), sgk-prim (%28), maaşın-artıyor (%31) = "açıklayıcı/kavram" ağırlıklı.
→ HİPOTEZ: orta-video retention'ı konu-türüyle korele (merak-yaylı hikaye > kavram-açıklama).
Sonraki ölçüm işi: gate_pass'i FORMAT/KONU'ya kır (hook_retention'a format etiketi ekle) → hangi
format kapıyı geçiyor net çıkar → learnings'e yaz → format seçimini oraya kaydır.

**Kuyruk (GÜNCEL):** (1) SFX — ✅ ENTEGRE (exp 09-24-1, ölç ~09-30). (2) 3sn-hold ölçümü — ✅ nightly.
(2b) 65% AVD kapısı ölçümü — ✅ ENTEGRE + ilk teşhis (%8 geçiyor). (2c) **gate_pass'i format/konuya
kır ← YENİ sıradaki ölçüm işi.** (3) progress-bar mute value-cue (slot boşalınca izole). (4) audio-
callback kapanış. (5) series-labeling X/N. (6) Manim tek-odak/dim. (7) caption inactive-word DIM +
hook-anim/beat-hold. (8) dedike kapak.

---
## 2026-09-30 — gate_pass × FORMAT ölçümü ENTEGRE (kuyruk #2c tamam) + orta-video-drift mekanizması doğrulandı

**Adım 0:** SFX kohortu (09-24-1) 6 günde izole edilemedi (yeni videolar top-views'e girmedi, aggregate düz) → **inconclusive KAPATILDI** (11. teyit: pacing/hook mikro-edit'i düşük-n retention'da çözülmez). Retention slotu artık BOŞ → ama ders: slotu mikro-edit'e harcama, kaldıraç ORTA-VİDEO/format.

**Entegre ettim (kuyruk #2c):** `hook_retention.py`'ye `gate_by_format` — 65% AVD kapısını FORMAT'a kırar. AVD tek batched sorgu (dimensions=video) → curve gerekmeden son 90 videoyu ledger `attrs.format` ile eşleştirir; per-video maliyet YOK. Çıktı + konsol: format başına medyan AVD + kapı-geçen oranı.

**İLK TEŞHİS (n=43):**
| format | medyan AVD | 65% kapı | n |
|---|---|---|---|
| backtest_return | %65 | 2/5 (%40) | 5 |
| myth | %64 | 1/4 (%25) | 4 |
| single_concept | %44 | 1/4 (%25) | 4 |
| daily-short | %28 | 2/16 (%12) | 16 |
| news_reaction | %27 | 0/6 (%0) | 6 |
| shock_number | %16 | 0/7 (%0) | 7 |

→ **KRİTİK ÇELİŞKİ:** views-ağırlıklı öğrenme motoru shock_number'ı #1 (471) seçiyordu — ama shock_number 65% kapısını 0/7 GEÇMİYOR = dağıtım-katili. Bu, "16K izlenme → 0 site" (learnings 08-04) sayısal açıklaması: izlenme-kazandıran format (güçlü kanca) = kapıyı-geçemeyen format (orta-video çöküyor). **EYLEM:** viral rotasyon gate-geçenlere kaydırıldı (myth×2/backtest×2/single×2/shock×1, news çıkarıldı) — exp 2026-09-30-1 gate_pass_share izler; learnings'e yazıldı.

**WebSearch R&D (mecburi):** "YouTube Shorts mid-video retention 2026 faceless finance pacing". Kaynaklar: aibrify.com/blog/youtube-shorts-retention-curve-playbook · virvid.ai/blog/faceless-youtube-algorithm-retention-2026 · virvid.ai/blog/first-3-seconds-hook-faceless-shorts-2026 · fluxnote.io/guides/finance-youtube-shorts-ideas.
**2 somut bulgu:**
1. **"Gradual decline = pacing/content DRIFT" (orta-video), "sharp 3s drop = hook fail".** Bizim tablo: 3sn-hold medyan %103 (kanca güçlü, loop) ama orta AVD düşük = KLASİK DRIFT. shock/news muhtemelen tüm payoff'u kancada boşaltıp açık-döngü bırakmıyor → drift. backtest/myth narrative arc (problem→reveal→outcome) sürdürüyor. → gate ölçümüyle birebir örtüşüyor.
2. **"Value loop / open loop + orta-video retention-spike (soru/sürpriz/ton değişimi)."** Uygulanabilir script-fix: shock/news beat'lerine orta-video AÇIK-DÖNGÜ re-hook. AMA düşük-n retention'da script-edit çözülmez (kanıtlı) → şimdilik exp AÇMA; format rebalans (gate-izlenen tek değişiklik) olgunlaşınca değerlendir.

**Sonuç:** en yüksek kaldıraç bu gece = format rebalans (izlenme değil DAĞITIM KAPISI optimize). Sıradaki ölçüm: rebalans kohortu olgunlaşınca (~7-10 video) gate_pass_share'i yeniden ölç, backtest/myth üstünlüğü teyit olursa shock/news'i TAMAMEN ele.

**Kuyruk (GÜNCEL):** (1) SFX — ✅ KAPANDI (inconclusive, mikro-edit çıkmazı). (2/2b) 3sn-hold + 65% kapı ölçümü — ✅ nightly. (2c) gate × format — ✅ ENTEGRE + rebalans + exp 09-30-1. (3) progress-bar mute value-cue (slot BOŞ, izole açılabilir). (4) orta-video açık-döngü re-hook (script-fix, format kohortu olgunlaşınca). (5) audio-callback kapanış. (6) Manim tek-odak/dim. (7) caption inactive-word DIM + hook-anim/beat-hold. (8) dedike kapak.
