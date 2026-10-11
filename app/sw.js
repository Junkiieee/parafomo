/* ParaFOMO Uygulamalar — service worker.
   Strateji: ağ-öncelikli (içerik hep taze), ağ yoksa önbellekten; API asla önbelleklenmez
   (zaten farklı origin). Sürümü artırmak eski önbelleği temizler. */
const VERSION = 'pf-v1';
const SHELL = [
  '/', '/lobby.css', '/theme.css',
  '/portfoy/', '/portfoy/app.css', '/portfoy/app.js',
  '/bist-symbols.json', '/tufe-aylik.json', '/favicon.svg',
];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(VERSION).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== VERSION).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  if (e.request.method !== 'GET' || url.origin !== self.location.origin) return;
  e.respondWith(
    fetch(e.request)
      .then(res => {
        if (res.ok) {
          const copy = res.clone();
          caches.open(VERSION).then(c => c.put(e.request, copy)).catch(() => {});
        }
        return res;
      })
      .catch(() =>
        caches.match(e.request).then(hit =>
          hit || (e.request.mode === 'navigate'
            ? caches.match(url.pathname.startsWith('/portfoy') ? '/portfoy/' : '/')
            : Response.error())
        )
      )
  );
});
