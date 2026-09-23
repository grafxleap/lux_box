"""Brightness of the side boxes with the swiper knob at 0 and at 90% (they must not light up)."""
import sys, os
from playwright.sync_api import sync_playwright
from PIL import Image
import numpy as np
REF = r"M:\MAIN PROJECTS\lazar\prototype\ref"
with sync_playwright() as p:
    br = p.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
    pg = br.new_page(viewport={"width": 405, "height": 720}, device_scale_factor=540 / 405)
    pg.goto("http://127.0.0.1:8792/?v=%d&ui=0%s" % (os.getpid(), sys.argv[1] if len(sys.argv) > 1 else "")); pg.wait_for_function("window.__proto !== undefined", timeout=180000)
    pg.wait_for_timeout(8000)
    def measure(name_):
        path = os.path.join(REF, "side_%s.png" % name_); pg.screenshot(path=path)
        a = np.asarray(Image.open(path).convert("L"), float)
        return "left %.1f  right_side %.1f  front %.1f" % (a[380:540, 0:60].mean(), a[380:540, 480:540].mean(), a[400:640, 130:400].mean())
    print("knob 0 :", measure("0"))
    pg.evaluate("window.__proto.setKnob(0.9)"); pg.wait_for_timeout(2000)
    print("knob 90:", measure("90"))
    sys.stdout.flush(); os._exit(0)
