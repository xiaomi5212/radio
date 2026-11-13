/* 网络电台 · 离线缓存（只缓存页面外壳，音频与接口始终走网络） */
const CACHE = 'radio-shell-v6';
const ROOT = './';
const PAGE = './index.html';
const ASSETS = [ROOT, PAGE, './manifest.webmanifest', './icon-192.png', './icon-512.png', './apple-touch-icon.png'];

const FALLBACK = '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
  + '<meta name="viewport" content="width=device-width,initial-scale=1"><title>网络电台</title>'
  + '<style>html,body{background:#181411;color:#f4efe6;font-family:system-ui,sans-serif;'
  + 'display:grid;place-items:center;height:100%;margin:0}div{text-align:center;color:#9a8f80;font-size:14px}</style></head>'
  + '<body><div><p>网络电台</div></body></html>';

self.addEventListener('install', function(e){
  e.waitUntil(
    caches.open(CACHE).then(function(c){
      return Promise.all(ASSETS.map(function(a){
        return c.add(a).catch(function(){});
      }));
    }).then(function(){ return self.skipWaiting(); })
  );
});

self.addEventListener('activate', function(e){
  e.waitUntil(caches.keys().then(function(keys){
    return Promise.all(keys.filter(function(k){ return k !== CACHE; }).map(function(k){ return caches.delete(k); }));
  }).then(function(){ return self.clients.claim(); }));
});

function shell(){
  return caches.match(PAGE).then(function(r){ return r || caches.match(ROOT); });
}

self.addEventListener('fetch', function(e){
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);

  /* 电台接口：先用上次结果，后台再更新，避免每次都等欧洲服务器 */
  if (url.hostname.indexOf('radio-browser.info') >= 0){
    e.respondWith(caches.open(CACHE).then(function(c){
      return c.match(req).then(function(cached){
        const net = fetch(req).then(function(res){
          if (res && res.ok) c.put(req, res.clone()).catch(function(){});
          return res;
        }).catch(function(){ return cached; });
        return cached || net;
      });
    }));
    return;
  }

  /* 自己的电台清单：先用缓存，同时后台更新 */
  if (url.origin === self.location.origin && (url.pathname.endsWith('stations.json') || url.pathname.endsWith('blog.json'))){
    e.respondWith(caches.open(CACHE).then(function(c){
      return c.match(req).then(function(cached){
        const net = fetch(req).then(function(res){
          if (res && res.ok) c.put(req, res.clone()).catch(function(){});
          return res;
        }).catch(function(){ return cached; });
        return cached || net;
      });
    }));
    return;
  }

  if (url.origin !== self.location.origin) return;

  if (req.mode === 'navigate'){
    /* 立刻用缓存渲染，同时后台更新，保证从桌面点开不白屏 */
    e.respondWith(shell().then(function(cached){
      const net = fetch(req).then(function(res){
        if (res && res.ok){
          const copy = res.clone();
          caches.open(CACHE).then(function(c){ c.put(PAGE, copy); }).catch(function(){});
        }
        return res;
      }).catch(function(){ return null; });
      if (cached) return cached;
      return net.then(function(res){
        if (res) return res;
        return new Response(FALLBACK, { headers: { 'Content-Type': 'text/html; charset=utf-8' } });
      });
    }));
    return;
  }

  e.respondWith(
    caches.match(req).then(function(r){
      if (r) return r;
      return fetch(req).then(function(res){
        const copy = res.clone();
        caches.open(CACHE).then(function(c){ c.put(req, copy); }).catch(function(){});
        return res;
      });
    })
  );
});
//（注：内容由AI生成）
