"""Tilt of the seam on screen (the line's vertical center per column), boxes 1, 2 and 4, at 1x and 2x."""
import sys, os
from playwright.sync_api import sync_playwright
from PIL import Image
import numpy as np
REF = r"M:\MAIN PROJECTS\lazar\prototype\ref"
QUIET = "() => { const e = window.__proto.state(); return Math.abs(e.angle - e.goal) < 1e-6; }"
with sync_playwright() as p:
    br = p.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
    for dpr in (2,):
        pg = br.new_page(viewport={"width": 405, "height": 720}, device_scale_factor=dpr)
        pg.goto("http://127.0.0.1:8792/?v=%d&ui=0&bloom=0&exp=0.25" % os.getpid()); pg.wait_for_function("window.__proto !== undefined", timeout=180000)
        pg.wait_for_timeout(9000); pg.evaluate("window.__proto.holdPulse(1)")
        for turn_n, name_ in ((0, "box 1"), (1, "box 2"), (2, "box 4")):
            if turn_n: pg.evaluate("window.__proto.turn(%d)" % turn_n)
            pg.wait_for_function(QUIET, timeout=180000, polling=200); pg.wait_for_timeout(1500)
            path = os.path.join(REF, "tilt_tmp.png"); pg.screenshot(path=path)
            a = np.asarray(Image.open(path).convert("L"), float)
            H, W = a.shape
            y0 = int(H * 0.52); y1 = int(H * 0.62)
            zone = a[y0:y1]
            depth = zone[:, int(W * .2):int(W * .45)].mean(1); y = y0 + int(np.argmax(depth))
            hundredths = []
            for fx in (0.25, 0.32, 0.4, 0.6, 0.68, 0.75):
                x = int(W * fx); col = a[y - 6:y + 7, x - 2:x + 3].mean(1)
                w = np.clip(col - col.min(), 0, None); hundredths.append((w * np.arange(-6, 7)).sum() / max(1e-6, w.sum()) + y)
            print("dpr %d %s: seam center per column (left -> right):" % (dpr, name_), " ".join("%.2f" % c for c in hundredths),
                  "| tilt %.2f px" % (hundredths[-1] - hundredths[0])); sys.stdout.flush()
        pg.close()
    os._exit(0)
