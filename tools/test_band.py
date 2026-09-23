"""Band on the right half of the first box at the pulse's peak: what produces it?
For each condition it measures, at the edges (above and below the seam), the pulse's rise (phase 1 - phase 0) along the
esquerre i dret.   python tools/test_band.py <turn_n>"""
import sys, os
from playwright.sync_api import sync_playwright
from PIL import Image
import numpy as np
REF = r"M:\MAIN PROJECTS\lazar\prototype\ref"
turn_n = int(sys.argv[1]) if len(sys.argv) > 1 else 0
QUIET = "() => { const e = window.__proto.state(); return Math.abs(e.angle - e.goal) < 1e-6; }"
CONDITIONS = [
    ("normal", "", None),
    ("no glow", "&bloom=0", None),
    ("no env", "&env=0", None),
    ("no direct light", "", "() => window.__proto.scene.traverse(o => { if (o.isLight && !o.isAmbientLight) o.intensity = 0; })"),
    ("no floor reflection", "&reflect=0", None),
]
with sync_playwright() as p:
    br = p.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
    for name_, q, js in CONDITIONS:
        pg = br.new_page(viewport={"width": 405, "height": 720}, device_scale_factor=2)
        pg.goto("http://127.0.0.1:8792/?v=%d&ui=0%s" % (os.getpid(), q)); pg.wait_for_function("window.__proto !== undefined", timeout=180000)
        pg.wait_for_timeout(9000)
        if turn_n: pg.evaluate("window.__proto.turn(%d)" % turn_n)
        pg.wait_for_function(QUIET, timeout=180000, polling=200)
        if js: pg.evaluate(js)
        A = {}
        for f in (0, 0.75, 1):
            pg.evaluate("window.__proto.holdPulse(%s)" % f); pg.wait_for_timeout(1200)
            path = os.path.join(REF, "band_tmp.png"); pg.screenshot(path=path)
            A[f] = np.asarray(Image.open(path).convert("L"), float)
        m = A[1]
        zone = np.concatenate([m[700:900, 170:360], m[700:900, 450:640]], 1); y = 700 + int(np.argmax(zone.mean(1)))
        row = m[y, 100:710]; cols = np.where(row > 0.5 * row.max())[0] + 100; x0, x1 = cols.min(), cols.max(); n = x1 - x0
        def stretch(img, f0, f1, a, b): return img[a:b, x0 + int(n * f0):x0 + int(n * f1)].mean()
        res = []
        for t, a, b in (("above", y - 14, y - 3), ("below", y + 3, y + 14)):
            e1 = stretch(A[1], .05, .4, a, b) - stretch(A[0], .05, .4, a, b); d1 = stretch(A[1], .6, .95, a, b) - stretch(A[0], .6, .95, a, b)
            e75 = stretch(A[0.75], .05, .4, a, b) - stretch(A[0], .05, .4, a, b); d75 = stretch(A[0.75], .6, .95, a, b) - stretch(A[0], .6, .95, a, b)
            res.append("%s left %.1f/%.1f right %.1f/%.1f" % (t, e75, e1, d75, d1))
        print("turn %d %-20s (rise at phase 0.75 / 1)  %s" % (turn_n, name_, "  |  ".join(res))); sys.stdout.flush()
        pg.close()
    os._exit(0)
