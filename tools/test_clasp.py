"""The clasp's tab darkens with the swiper knob: is it the interior light (shadow) or the lid moving?"""
import sys, os
from playwright.sync_api import sync_playwright
from PIL import Image
import numpy as np
REF = r"M:\MAIN PROJECTS\lazar\prototype\ref"
extra = sys.argv[1] if len(sys.argv) > 1 else ""
with sync_playwright() as p:
    br = p.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
    pg = br.new_page(viewport={"width": 405, "height": 720}, device_scale_factor=540 / 405)
    pg.goto("http://127.0.0.1:8792/?v=%d&ui=0%s" % (os.getpid(), extra)); pg.wait_for_function("window.__proto !== undefined", timeout=180000)
    pg.wait_for_timeout(1500)
    def tab_(name_):
        path = os.path.join(REF, "clasp_%s.png" % name_); pg.screenshot(path=path)
        return np.asarray(Image.open(path).convert("L"), float)[528:548, 258:278].mean()
    print("knob 0   : %.1f" % tab_("p0"))
    pg.evaluate("window.__proto.setKnob(0.9)"); pg.wait_for_timeout(1500)
    print("knob 90  : %.1f" % tab_("p90"))
    sys.stdout.flush(); os._exit(0)
