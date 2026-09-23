"""Real brightness (no glow and low exposure, so it does not clip) of the seam along the front box:
first box and its two neighbours once centred.  python tools/test_seam_hdr.py [query extra]"""
import sys, os
from playwright.sync_api import sync_playwright
from PIL import Image
import numpy as np
REF = r"M:\MAIN PROJECTS\lazar\prototype\ref"
extra = sys.argv[1] if len(sys.argv) > 1 else ""
with sync_playwright() as p:
    br = p.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
    pg = br.new_page(viewport={"width": 405, "height": 720}, device_scale_factor=2)
    pg.goto("http://127.0.0.1:8792/?v=%d&ui=0&bloom=0&exp=0.08%s" % (os.getpid(), extra)); pg.wait_for_function("window.__proto !== undefined", timeout=180000)
    pg.wait_for_timeout(9000)
    pg.evaluate("window.__proto.holdPulse(1)")
    def profile(name_):
        pg.wait_for_timeout(1500); path = os.path.join(REF, "hdr_%s.png" % name_); pg.screenshot(path=path)
        a = np.asarray(Image.open(path).convert("L"), float)
        zone = np.concatenate([a[700:900, 170:360], a[700:900, 450:640]], 1); y = 700 + int(np.argmax(zone.mean(1)))
        row = a[y - 1:y + 2, 150:660].max(0); cols = np.where(row > 0.4 * row.max())[0] + 150; x0, x1 = cols.min(), cols.max()
        xs = [int(x0 + (x1 - x0) * f) for f in (0.03, 0.1, 0.2, 0.3, 0.4, 0.6, 0.7, 0.8, 0.9, 0.97)]
        print("  %-4s seam (row_ %d, x %d-%d):" % (name_, y, x0, x1), "  ".join("%.0f" % a[y - 1:y + 2, x - 2:x + 3].max(0).mean() for x in xs))
    profile("c1")
    for n, name_ in ((1, "c2"), (-2, "c0")):
        pg.evaluate("window.__proto.turn(%d)" % n); pg.wait_for_timeout(5000); profile(name_)
    sys.stdout.flush(); os._exit(0)
