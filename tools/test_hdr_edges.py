"""Real brightness (no glow, low exposure) of the seam's edges, left half vs right, with the pulse at its peak.
First box, second and fourth; with and without the environment.   python tools/test_hdr_edges.py"""
import sys, os
from playwright.sync_api import sync_playwright
from PIL import Image
import numpy as np
REF = r"M:\MAIN PROJECTS\lazar\prototype\ref"
QUIET = "() => { const e = window.__proto.state(); return Math.abs(e.angle - e.goal) < 1e-6; }"
with sync_playwright() as p:
    br = p.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
    for q, nameq in (("", "with env"), ("&env=0", "no env")):
        pg = br.new_page(viewport={"width": 405, "height": 720}, device_scale_factor=2)
        pg.goto("http://127.0.0.1:8792/?v=%d&ui=0&bloom=0&exp=0.25%s" % (os.getpid(), q)); pg.wait_for_function("window.__proto !== undefined", timeout=180000)
        pg.wait_for_timeout(9000); pg.evaluate("window.__proto.holdPulse(1)")
        for turn_n, name_ in ((0, "box 1"), (1, "box 2"), (2, "box 4")):
            if turn_n: pg.evaluate("window.__proto.turn(%d)" % turn_n)
            pg.wait_for_function(QUIET, timeout=180000, polling=200); pg.wait_for_timeout(1500)
            path = os.path.join(REF, "hdredges_tmp.png"); pg.screenshot(path=path)
            a = np.asarray(Image.open(path).convert("L"), float)
            zone = np.concatenate([a[700:900, 170:360], a[700:900, 450:640]], 1); y = 700 + int(np.argmax(zone.mean(1)))
            row = a[y, 100:710]; cols = np.where(row > 0.5 * row.max())[0] + 100; x0, x1 = cols.min(), cols.max(); n = x1 - x0
            def t(f0, f1, r0, r1): return a[y + r0:y + r1, x0 + int(n * f0):x0 + int(n * f1)].mean()
            print("%-12s %s: above left %.1f right %.1f | below left %.1f right %.1f | seam left %.1f right %.1f" % (
                nameq, name_, t(.05, .4, -14, -3), t(.6, .95, -14, -3), t(.05, .4, 3, 14), t(.6, .95, 3, 14), t(.05, .4, -1, 2), t(.6, .95, -1, 2)))
            sys.stdout.flush()
        pg.close()
    os._exit(0)
