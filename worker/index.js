// ParaFOMO — kanonik adres kapısı (Workers Static Assets önünde).
//
// Statik asset sunumu sonda '/' olmayan yolları 307 (GEÇİCİ) ile yönlendiriyordu;
// http:// ve www. ise hiç yönlendirilmeden 200 dönüyordu → Google aynı sayfanın
// kopyalarını ayrı URL olarak indeksliyordu (GSC, 2026-10-10). Burada hepsi tek
// adımda KALICI 301 ile https://parafomo.com/<yol>/ adresine gider; gerisi asset.
const CANONICAL_HOST = 'parafomo.com';

// Birleştirilen / kaldırılan sayfalar → kalıcı yeni adres (sonda '/' ile).
const REDIRECTS = {
  // 2026-11-18 (W10): 89–120 gündür 'Tarandı - dizine eklenmedi' kalan 7 genel yazı → aynı niyetli güçlü sayfa.
  '/blog/reel-faiz-nedir/': '/mevduat-faizi-hesaplama/',
  '/blog/mevduat-faizi-nedir-vadeli-mevduat/': '/mevduat-faizi-hesaplama/',
  '/blog/ppi-nedir-uretici-fiyat-endeksi/': '/ekonomik-takvim/',
  '/blog/ingiltere-cpi-nedir-sterlin-etkisi/': '/ekonomik-takvim/',
  '/blog/nft-nedir-yatirim-mantikli-mi/': '/bitcoin-getiri/',
  '/blog/altin-fonu-nedir-gram-altindan-farki/': '/blog/altin-hesabi-nedir-mantikli-mi-fiziki-altin-fon-karsilastirma/',
  '/blog/abd-faiz-artarsa-ne-olur/': '/fed-faiz-takvimi/',
  // 2026-11-17 (R30): Google'ın 'Tarandı - dizine eklenmedi' dediği 22 genel yazı → aynı niyetli güçlü sayfa.
  '/blog/ab-enflasyonu-cpi-nedir-turkiye-etkisi/': '/enflasyon-takvimi/',
  '/blog/aciga-satis-nedir-short-selling/': '/blog/borsa-istanbul-nedir-seans-saatleri-pazarlar-takas/',
  '/blog/acil-durum-fonu-nedir/': '/blog/enflasyondan-nasil-korunur/',
  '/blog/bitcoin-nedir-nasil-alinir/': '/bitcoin-getiri/',
  '/blog/borsaya-nasil-baslanir/': '/blog/borsa-istanbul-nedir-seans-saatleri-pazarlar-takas/',
  '/blog/dca-nedir-maliyet-ortalamasi/': '/blog/turkiyede-en-iyi-yatirim-araclari-2026/',
  '/blog/ethereum-nedir/': '/bitcoin-getiri/',
  '/blog/faiz-nedir-ekonomiyi-nasil-etkiler/': '/tcmb-faiz-takvimi/',
  '/blog/findeks-kredi-notu-nedir-nasil-yukselir/': '/kredi-hesaplama/',
  '/blog/fomc-toplanti-tutanaklari-nedir/': '/fed-faiz-takvimi/',
  '/blog/halka-arz-nedir-ipo/': '/blog/halka-arza-nasil-katilinir-esit-dagitim-lot-hesabi/',
  '/blog/hisse-senedi-nasil-secilir/': '/blog/borsa-istanbul-nedir-seans-saatleri-pazarlar-takas/',
  '/blog/kriz-doneminde-butce-nasil-yonetilir/': '/blog/enflasyondan-nasil-korunur/',
  '/blog/pce-nedir-fed-enflasyon-gostergesi/': '/fed-faiz-takvimi/',
  '/blog/risk-getiri-iliskisi/': '/blog/turkiyede-en-iyi-yatirim-araclari-2026/',
  '/blog/stop-loss-nedir-zarar-kesme/': '/blog/borsa-istanbul-nedir-seans-saatleri-pazarlar-takas/',
  // 2026-11-17: videolarda ekranda yazılan kısa adresler (Shorts'ta linkler tıklanmıyor; yazılabilir adres lazım).
  '/zam/': '/emekli-zammi-hesaplama/', '/zam': '/emekli-zammi-hesaplama/',
  '/refah/': '/emekli-refah-payi-seyyanen-zam/', '/refah': '/emekli-refah-payi-seyyanen-zam/',
  '/enflasyon/': '/enflasyon-hesaplama/', '/enflasyon': '/enflasyon-hesaplama/',
  // 2026-10-13: neredeyse birebir kopya, aynı sorgularda birbirini yiyordu (GSC sıra 27-29).
  '/blog/abd-faiz-karari-altin-dolar-tl-etkisi/': '/fed-faiz-takvimi/',
  // 2026-10-13: eski sitedeki portföy mini-uygulaması kaldırıldı; tek ürün app.parafomo.com.
  '/portfoy-takip/': 'https://app.parafomo.com/portfoy/',
  '/portfoy/panel/': 'https://app.parafomo.com/portfoy/',
  // 2026-10-22: GSC yamyamlaşma temizliği — aynı arama niyeti için tek URL; içerik kalan yazıya birleştirildi.
  '/blog/abd-faiz-yukseltirse-dolar-ne-olur/': '/fed-faiz-takvimi/',
  '/blog/abd-faiz-artarsa-altin-ne-olur/': '/fed-faiz-takvimi/',
  '/blog/2026-fed-toplanti-tarihleri/': '/fed-faiz-takvimi/',
  '/blog/jackson-hole-2026-ne-zaman-warsh-konusmasi/': '/blog/jackson-hole-sempozyumu-nedir/',
  '/blog/altin-cesitleri-farki/': '/blog/altin-cesitleri-gram-ceyrek-ons-ziynet/',
  '/blog/etf-nasil-alinir/': '/blog/etf-nedir-borsa-yatirim-fonu/',
  '/blog/endeks-fonu-nedir/': '/blog/etf-nedir-borsa-yatirim-fonu/',
  '/blog/boj-faiz-karari-nedir-etkisi/': '/blog/boj-nedir-japonya-merkez-bankasi/',
  '/blog/bilesik-faiz-nedir/': '/bilesik-faiz-hesaplama/',
  '/blog/abd-cpi-enflasyon-verisi-nedir/': '/blog/cekirdek-cpi-nedir-fed-enflasyon-gostergesi/',
  '/blog/ecb-eylul-2026-faiz-karari-euro-tl-etkisi/': '/blog/ecb-faiz-karari-nedir-etkisi/',
  '/blog/kredi-karti-borcundan-kurtulma/': '/blog/borc-kapatma-yontemi-kartopu-cig/',
  '/blog/tufe-enflasyon-verisi-nasil-okunur/': '/blog/tufe-sepeti-nedir-enflasyon-nasil-hesaplanir/',
  '/blog/temettu-hisseleri-pasif-gelir/': '/blog/temettu-verimi-nedir/',
};

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.hostname !== CANONICAL_HOST && url.hostname !== `www.${CANONICAL_HOST}`) {
      return env.ASSETS.fetch(request);
    }
    let moved = false;
    if (url.protocol === 'http:') {
      url.protocol = 'https:';
      moved = true;
    }
    if (url.hostname === `www.${CANONICAL_HOST}`) {
      url.hostname = CANONICAL_HOST;
      moved = true;
    }
    const last = url.pathname.slice(url.pathname.lastIndexOf('/') + 1);
    if (!url.pathname.endsWith('/') && !last.includes('.')) {
      url.pathname += '/';
      moved = true;
    } else if (url.pathname.endsWith('/index.html')) {
      url.pathname = url.pathname.slice(0, -'index.html'.length);
      moved = true;
    }
    const target = REDIRECTS[url.pathname];
    if (target?.startsWith('https://')) {
      return Response.redirect(target + url.search, 301);
    }
    if (target) {
      url.pathname = target;
      moved = true;
    }
    if (moved && (request.method === 'GET' || request.method === 'HEAD')) {
      return Response.redirect(url.toString(), 301);
    }
    return withCache(url.pathname, await env.ASSETS.fetch(request));
  },

  // ajan@parafomo.com → (Email Routing: "Send to a Worker" → parafomo) → sunucudaki gelen kutusu.
  // INBOX_SECRET dashboard'da worker secret'ı olarak tanımlanır (repo herkese açık, koda yazılmaz).
  async email(message, env) {
    if (!env.INBOX_SECRET) {
      message.setReject('Gelen kutusu yapılandırılmamış');
      return;
    }
    if (message.rawSize > 5 * 1024 * 1024) {
      message.setReject('Mesaj çok büyük');
      return;
    }
    const raw = await new Response(message.raw).arrayBuffer();
    const res = await fetch('https://api.parafomo.com/inbox/ingest', {
      method: 'POST',
      headers: {
        'Content-Type': 'message/rfc822',
        'X-Inbox-Secret': env.INBOX_SECRET,
        'X-Mail-From': message.from,
        'X-Mail-To': message.to,
      },
      body: raw,
    });
    if (!res.ok) message.setReject(`Gelen kutusu hatası (${res.status})`);
  },
};

// Asset sunumu her şeyi `max-age=0, must-revalidate` ile veriyordu: her sayfa açılışında
// fontlar ve görseller yeniden doğrulanıyordu. HTML ve .json veri dosyaları (canlı
// rakamlar) dokunulmadan kalır.
const IMMUTABLE = 'public, max-age=31536000, immutable';
const IMAGE = 'public, max-age=604800, stale-while-revalidate=86400';
function cachePolicy(path) {
  if (path.startsWith('/_astro/') || path.startsWith('/fonts/')) return IMMUTABLE;
  if (/\.(?:webp|jpe?g|png|svg|ico|avif)$/.test(path)) return IMAGE;
  return null;
}
// Temel güvenlik başlıkları (denetim 2026-10-22: hiçbir sayfada yoktu). CSP bilinçli olarak yok —
// inline script/stil ve gtag'i kırmamak için ayrı, test edilmiş bir adım gerektirir.
const SECURITY_HEADERS = {
  'Strict-Transport-Security': 'max-age=31536000',
  'X-Content-Type-Options': 'nosniff',
  'Referrer-Policy': 'strict-origin-when-cross-origin',
  'X-Frame-Options': 'SAMEORIGIN',
  // 2026-11-17 (web yönetimi S2): site kamera/mikrofon/konum/ödeme kullanmıyor → tarayıcıya kapalı olduğunu bildir
  'Permissions-Policy': 'camera=(), microphone=(), geolocation=(), payment=(), usb=()',
};
function withCache(path, res) {
  const policy = res.status === 200 ? cachePolicy(path) : null;
  const out = new Response(res.body, res);
  if (policy) out.headers.set('Cache-Control', policy);
  for (const [k, v] of Object.entries(SECURITY_HEADERS)) out.headers.set(k, v);
  // /embed/ araçları başka sitelerde iframe ile gösterilmek için var (/sitene-ekle/): çerçeve yasağı yalnız orada kalkar.
  if (path.startsWith('/embed/')) {
    out.headers.delete('X-Frame-Options');
    out.headers.set('Content-Security-Policy', 'frame-ancestors *');
  }
  return out;
}
