// service-worker.js – cache static assets and background sync

const CACHE_NAME = 'expense-pwa-v1';
const ASSETS = [
  '/pwa/index.html',
  '/pwa/app.js',
  '/pwa/manifest.json',
  '/pwa/icons/icon-192.png',
  '/pwa/icons/icon-512.png',
];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS)));
});

self.addEventListener('activate', (e) => {
  e.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url);
  if (ASSETS.includes(url.pathname)) {
    e.respondWith(caches.match(e.request).then((cached) => cached || fetch(e.request)));
  } else {
    // fallback to network for API calls
    e.respondWith(fetch(e.request));
  }
});

// Background sync – attempt to send pending transactions
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-transactions') {
    event.waitUntil(self.clients.matchAll().then((clients) => {
      for (const client of clients) {
        client.postMessage({action: 'sync'});
      }
    }));
  }
});
