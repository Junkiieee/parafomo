/* ParaFOMO Uygulamalar — service worker.
   Strateji: ağ-öncelikli (içerik hep taze), ağ yoksa önbellekten; API asla önbelleklenmez
   (zaten farklı origin). Sürümü artırmak eski önbelleği temizler.
   Ağ isteği tarayıcının HTTP önbelleğini olduğu gibi kullanmaz, sunucuya doğrulatır
   (cache:'no-cache' → değişmediyse 304): Caddy Cache-Control göndermediğinden tarayıcı
   dosyaları sezgisel olarak "taze" sayıyor, yayından sonra eski HTML/JS saatlerce kalıyordu. */
const VERSION = 'pf-v4';
const SHELL = [
  '/', '/lobby.css', '/theme.css',
  '/portfoy/', '/portfoy/app.css', '/portfoy/app.js',
  '/birikim/', '/birikim/app.css', '/birikim/app.js',
  '/bist-symbols.json', '/tufe-aylik.json', '/benchmarks.json', '/favicon.svg', '/kvkk/',
];
// çevrimdışı gezinme: yolun ait olduğu uygulamanın kabuğu (utm vb. sorgu dizesinden bağımsız)
const shellFor = p => p.startsWith('/portfoy') ? '/portfoy/' : p.startsWith('/birikim') ? '/birikim/'
  : p.startsWith('/kvkk') ? '/kvkk/' : '/';

self.addEventListener('install', e => {
  // kurulumda da HTTP önbelleğini atla: yeni sürümün önbelleğine bayat kopya girmesin
  e.waitUntil(caches.open(VERSION)
    .then(c => c.addAll(SHELL.map(u => new Request(u, { cache: 'reload' }))))
    .then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== VERSION).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  const req = e.request;
  const url = new URL(req.url);
  // oturumlu istek (Authorization) aynı origin'e taşınsa bile önbelleğe girmesin: ortak cihazda
  // çıkıştan sonra başkasına önceki kullanıcının verisi sunulmasın
  if (req.method !== 'GET' || url.origin !== self.location.origin || req.headers.has('Authorization')) return;
  const nav = req.mode === 'navigate';
  const key = nav ? shellFor(url.pathname) : req;
  // gezinme isteği init ile kopyalanamıyor (Chromium TypeError) → URL'den kur; yönlendirme
  // (Caddy /dizin → /dizin/) tarayıcıya aynen dönsün diye redirect:'manual'
  let fresh = req;
  try {
    fresh = nav ? new Request(req.url, { cache: 'no-cache', credentials: 'same-origin', redirect: 'manual' })
      : new Request(req, { cache: 'no-cache' });
  } catch {}   // eski tarayıcı: olduğu gibi
  e.respondWith(
    fetch(fresh)
      .then(res => {
        // yalnız aynı yolun kabuğu saklansın (sorgu dizeli her ziyaret ayrı kopya biriktirmesin)
        if (res.ok && res.type === 'basic' && (!nav || url.pathname === key)) {
          const copy = res.clone();
          caches.open(VERSION).then(c => c.put(key, copy)).catch(() => {});
        }
        return res;
      })
      .catch(() =>
        caches.match(key).then(hit => hit || (nav ? caches.match('/') : Response.error()))
      )
  );
});
