const CACHE_NAME = "aksjeradar-cache-v1";
const urlsToCache = [
  "/",
  "/static/css/style.css",
  "/static/js/main.js",
  "/static/images/logo.png"
  // legg til flere statiske filer ved behov
];

self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(urlsToCache))
  );
});

self.addEventListener("fetch", event => {
  event.respondWith(
    caches.match(event.request).then(response => {
      return response || fetch(event.request);
    })
  );
});
