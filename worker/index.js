// ParaFOMO — kanonik adres kapısı (Workers Static Assets önünde).
//
// Statik asset sunumu sonda '/' olmayan yolları 307 (GEÇİCİ) ile yönlendiriyordu;
// http:// ve www. ise hiç yönlendirilmeden 200 dönüyordu → Google aynı sayfanın
// kopyalarını ayrı URL olarak indeksliyordu (GSC, 2026-10-10). Burada hepsi tek
// adımda KALICI 301 ile https://parafomo.com/<yol>/ adresine gider; gerisi asset.
const CANONICAL_HOST = 'parafomo.com';

// Birleştirilen / kaldırılan sayfalar → kalıcı yeni adres (sonda '/' ile).
const REDIRECTS = {
  // 2026-10-13: neredeyse birebir kopya, aynı sorgularda birbirini yiyordu (GSC sıra 27-29).
  '/blog/abd-faiz-karari-altin-dolar-tl-etkisi/': '/blog/abd-faiz-artarsa-ne-olur/',
  // 2026-10-13: eski sitedeki portföy mini-uygulaması kaldırıldı; tek ürün app.parafomo.com.
  '/portfoy-takip/': 'https://app.parafomo.com/portfoy/',
  '/portfoy/panel/': 'https://app.parafomo.com/portfoy/',
  // 2026-10-22: GSC yamyamlaşma temizliği — aynı arama niyeti için tek URL; içerik kalan yazıya birleştirildi.
  '/blog/abd-faiz-yukseltirse-dolar-ne-olur/': '/blog/abd-faiz-artarsa-ne-olur/',
  '/blog/abd-faiz-artarsa-altin-ne-olur/': '/blog/abd-faiz-artarsa-ne-olur/',
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
function withCache(path, res) {
  const policy = res.status === 200 ? cachePolicy(path) : null;
  if (!policy) return res;
  const out = new Response(res.body, res);
  out.headers.set('Cache-Control', policy);
  return out;
}
