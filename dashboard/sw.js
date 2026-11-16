// Parafomo Panel — uygulama kabuğu önbelleği. Veri (/api/) asla önbelleğe alınmaz.
const CACHE = 'pf-panel-v3';
const KABUK = ['/', '/app.css', '/app.js', '/manifest.webmanifest', '/logo.png', '/icon-192.png'];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(KABUK)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys()
      .then((ks) => Promise.all(ks.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

// Önce ağ (her açılışta güncel arayüz), ağ yoksa son kopya.
self.addEventListener('fetch', (e) => {
  const u = new URL(e.request.url);
  if (e.request.method !== 'GET' || u.origin !== self.location.origin || u.pathname.startsWith('/api/')) return;
  e.respondWith(
    fetch(e.request)
      .then((r) => {
        if (r.ok) {
          const kopya = r.clone();
          caches.open(CACHE).then((c) => c.put(e.request, kopya));
        }
        return r;
      })
      .catch(() => caches.match(e.request).then((r) => r || caches.match('/')))
  );
});
