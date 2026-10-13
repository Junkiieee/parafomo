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
    if (target) {
      url.pathname = target;
      moved = true;
    }
    if (moved && (request.method === 'GET' || request.method === 'HEAD')) {
      return Response.redirect(url.toString(), 301);
    }
    return withCache(url.pathname, await env.ASSETS.fetch(request));
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
