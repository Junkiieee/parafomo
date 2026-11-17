#!/usr/bin/env python3
"""Telefon genişliğinde yatay taşma taraması (2026-11-17; web planı "her hafta" kontrolü).

dist/'i yerelde sunar, her sayfayı 375 px'lik (iPhone SE/mini) bir iframe'de açar, kaydırma çubuğunu gizler (telefondaki gibi)
ve belge genişliği ekranı aşıyorsa taşan ilk öğeleri listeler. Ağ yok, dış paket yok (headless_shell + stdlib).

  /root/.venvs/parafomo/bin/python scripts/tasma-tara.py            # kök sayfalar + ilk 30 blog yazısı
  /root/.venvs/parafomo/bin/python scripts/tasma-tara.py --hepsi    # bütün blog yazıları
Çıkış: 0 taşma yok, 1 taşma var. Önce `npm run build`.
"""
import argparse
import functools
import glob
import html
import http.server
import json
import os
import re
import subprocess
import sys
import tempfile
import threading

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = "/root/.cache/ms-playwright/chromium_headless_shell-1148/chrome-linux/headless_shell"
GEN = 375

TEST = """<!doctype html><meta charset=utf-8><body style="margin:0"><pre id=out>bekliyor</pre>
<iframe id=f style="width:%dpx;height:900px;border:0"></iframe><script>
const P = %s; const out = []; const f = document.getElementById('f'); let i = 0;
function olc(u) {
  try {
    const d = f.contentDocument, W = d.documentElement.clientWidth, sw = d.documentElement.scrollWidth;
    if (sw <= W + 1) { out.push('ok ' + u); return; }
    const kotu = [];
    for (const el of d.body.querySelectorAll('*')) {
      const r = el.getBoundingClientRect();
      if (r.right <= W + 1 || r.width === 0) continue;
      let p = el.parentElement, kirp = false;
      while (p && p !== d.body) { const o = getComputedStyle(p).overflowX; if (o !== 'visible') { kirp = true; break; } p = p.parentElement; }
      if (!kirp) kotu.push(el.tagName.toLowerCase() + (typeof el.className === 'string' && el.className.trim() ? '.' + el.className.trim().split(/\\s+/).slice(0, 2).join('.') : '') + '(' + Math.round(r.right) + ')');
    }
    out.push('TASMA ' + u + ' genislik=' + sw + ' ' + kotu.slice(0, 5).join(' '));
  } catch (e) { out.push('HATA ' + u + ' ' + e); }
}
function sonraki() {
  if (i >= P.length) { document.getElementById('out').textContent = 'BITTI\\n' + out.join('\\n'); return; }
  const u = P[i++];
  f.onload = () => { try { f.contentDocument.documentElement.style.scrollbarWidth = 'none'; } catch (e) {} setTimeout(() => { olc(u); sonraki(); }, 300); };
  f.src = u;
}
sonraki();
</script>"""


def sayfalar(dist, hepsi):
    s = ["/"] + sorted("/" + os.path.relpath(os.path.dirname(p), dist) + "/" for p in glob.glob(f"{dist}/*/index.html"))
    s = [x for x in s if not x.startswith(("/en/", "/embed", "/_"))]
    blog = sorted(glob.glob(f"{dist}/blog/*/index.html"))
    s += ["/" + os.path.relpath(os.path.dirname(p), dist) + "/" for p in (blog if hepsi else blog[:30])]
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dist", default=os.path.join(ROOT, "dist"))
    ap.add_argument("--hepsi", action="store_true")
    ap.add_argument("--port", type=int, default=8796)
    a = ap.parse_args()
    if not os.path.exists(os.path.join(a.dist, "index.html")):
        sys.exit("dist yok: önce npm run build")
    P = sayfalar(a.dist, a.hepsi)
    test = (TEST % (GEN, json.dumps(P))).encode()

    class H(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *x):
            pass

        def do_GET(self):
            if self.path == "/__tasma.html":
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(test)))
                self.end_headers()
                self.wfile.write(test)
                return
            return super().do_GET()

    srv = http.server.ThreadingHTTPServer(("127.0.0.1", a.port), functools.partial(H, directory=a.dist))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    with tempfile.TemporaryDirectory() as prof:
        r = subprocess.run(["nice", "-n", "19", CHROME, "--headless", "--no-sandbox", "--disable-gpu", f"--user-data-dir={prof}",
                            "--window-size=420,1000", f"--virtual-time-budget={max(60000, 3000 * len(P))}", "--dump-dom",
                            f"http://127.0.0.1:{a.port}/__tasma.html"], capture_output=True, text=True, timeout=900)
    srv.shutdown()
    m = re.search(r'<pre id="out">(.*?)</pre>', r.stdout, re.S)
    satir = html.unescape(m.group(1)).splitlines() if m else []
    if not satir or satir[0] != "BITTI":
        sys.exit(f"tarama bitmedi ({len(satir)} satır)")
    kotu = [x for x in satir[1:] if not x.startswith("ok ")]
    print(f"[taşma] {len(satir) - 1} sayfa, {GEN} px: {len(kotu)} sorun")
    for x in kotu:
        print("  " + x[:300])
    return 1 if kotu else 0


if __name__ == "__main__":
    sys.exit(main())
