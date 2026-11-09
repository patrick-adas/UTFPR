/* Service worker da Rede Farmácia.
 * - Arquivos estáticos: cache-first.
 * - Páginas (navegação): network-first, com a página /offline/ como fallback.
 * - Requisições não-GET e do HTMX (polling) nunca são cacheadas.
 */
const VERSAO = "rede-farmacia-v1";
const OFFLINE_URL = "/offline/";
const PRE_CACHE = [OFFLINE_URL{% for url in estaticos %}, "{{ url|escapejs }}"{% endfor %}];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(VERSAO).then((cache) => cache.addAll(PRE_CACHE)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((chaves) => Promise.all(chaves.filter((c) => c !== VERSAO).map((c) => caches.delete(c))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;
  if (req.headers.get("HX-Request")) return;

  if (req.mode === "navigate") {
    event.respondWith(fetch(req).catch(() => caches.match(OFFLINE_URL)));
    return;
  }

  if (url.pathname.startsWith("/static/")) {
    event.respondWith(
      caches.match(req).then((emCache) =>
        emCache || fetch(req).then((resp) => {
          if (resp.ok) {
            const copia = resp.clone();
            caches.open(VERSAO).then((cache) => cache.put(req, copia));
          }
          return resp;
        })
      )
    );
  }
});
