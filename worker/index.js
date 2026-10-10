// ParaFOMO — kanonik adres kapısı (Workers Static Assets önünde).
//
// Statik asset sunumu sonda '/' olmayan yolları 307 (GEÇİCİ) ile yönlendiriyordu;
// http:// ve www. ise hiç yönlendirilmeden 200 dönüyordu → Google aynı sayfanın
// kopyalarını ayrı URL olarak indeksliyordu (GSC, 2026-10-10). Burada hepsi tek
// adımda KALICI 301 ile https://parafomo.com/<yol>/ adresine gider; gerisi asset.
const CANONICAL_HOST = 'parafomo.com';

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
    if (moved && (request.method === 'GET' || request.method === 'HEAD')) {
      return Response.redirect(url.toString(), 301);
    }
    return env.ASSETS.fetch(request);
  },
};
