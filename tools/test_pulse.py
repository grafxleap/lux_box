"""Front box's pulse: brightness of the edges (above and below the seam) along the seam, with the pulse at its lowest and at
maxim, per a la first box i la next_.  python tools/test_pulse.py [query extra]"""
import sys, os
from playwright.sync_api import sync_playwright
from PIL import Image
import numpy as np
REF = r"M:\MAIN PROJECTS\lazar\prototype\ref"
extra = sys.argv[1] if len(sys.argv) > 1 else ""
with sync_playwright() as p:
    br = p.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
    pg = br.new_page(viewport={"width": 405, "height": 720}, device_scale_factor=2)
    pg.goto("http://127.0.0.1:8792/?v=%d&ui=0%s" % (os.getpid(), extra)); pg.wait_for_function("window.__proto !== undefined", timeout=180000)
    pg.wait_for_timeout(9000)
    def profile(name_):
        out = {}
        for phase in (0, 1):
            pg.evaluate("window.__proto.holdPulse(%d)" % phase); pg.wait_for_timeout(1500)
            path = os.path.join(REF, "pols_%s_%d.png" % (name_, phase)); pg.screenshot(path=path)
            out[phase] = np.asarray(Image.open(path).convert("L"), float)
        a0, a1 = out[0], out[1]
        # seam row: the brightest one in the front box's area
        # seam row without the clasp (the center): the brightest one in the two side stretches
        zone = np.concatenate([a1[700:900, 170:360], a1[700:900, 450:640]], 1); y = 700 + int(np.argmax(zone.mean(1)))
        row = a1[y, 150:660]; cols = np.where(row > 0.5 * row.max())[0] + 150; x0, x1 = cols.min(), cols.max()
        xs = [int(x0 + (x1 - x0) * f) for f in (0.05, 0.15, 0.3, 0.7, 0.85, 0.95)]
        for strip, a, b in (("above", y - 10, y - 3), ("below", y + 3, y + 10)):
            d = [ (a1[a:b, x - 3:x + 4] - a0[a:b, x - 3:x + 4]).mean() for x in xs ]
            print("  %s %-5s delta pulse:" % (name_, strip), "  ".join("%.1f" % v for v in d))
    print("first box:"); profile("c1")
    pg.evaluate("window.__proto.turn(1)"); pg.wait_for_timeout(5000)
    print("next box:"); profile("c2")
    sys.stdout.flush(); os._exit(0)
