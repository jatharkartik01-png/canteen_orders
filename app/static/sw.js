// app/static/sw.js

self.addEventListener('install', (event) => {
    console.log('[Service Worker] Installed');
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    console.log('[Service Worker] Activated');
});

// A dummy fetch handler is required by Chrome to trigger the "Install App" prompt
self.addEventListener('fetch', (event) => {
    // We aren't caching anything yet, just letting requests pass through normally
    event.respondWith(fetch(event.request));
});