"""End of part one (knob to the right) vs the sequence's first frame: the side boxes must look the same."""
import sys, os
from playwright.sync_api import sync_playwright
from PIL import Image
import numpy as np
REF = r"M:\MAIN PROJECTS\lazar\prototype\ref"
with sync_playwright() as p:
    br = p.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
    pg = br.new_page(viewport={"width": 405, "height": 720}, device_scale_factor=540 / 405)
    pg.goto("http://127.0.0.1:8792/?v=%d&ui=0" % os.getpid()); pg.wait_for_function("window.__proto !== undefined", timeout=180000)
    pg.wait_for_timeout(8000)
    pg.evaluate("window.__proto.setKnob(1)"); pg.wait_for_timeout(2500)
    def m(name_):
        path = os.path.join(REF, "bk_%s.png" % name_); pg.screenshot(path=path)
        a = np.asarray(Image.open(path).convert("L"), float)
        return a, "left %.1f  right_side %.1f  front %.1f" % (a[380:540, 0:60].mean(), a[380:540, 480:540].mean(), a[400:640, 130:400].mean())
    a, t = m("carousel"); print("final carousel:", t)
    pg.evaluate("window.__proto.jumpTo(290)"); pg.wait_for_timeout(2500)
    b, t = m("seq290"); print("sequence 290 :", t)
    print("difference mean %.2f" % abs(a - b).mean())
    im = Image.new("RGB", (1080, 960)); im.paste(Image.open(os.path.join(REF, "bk_carousel.png")).convert("RGB"), (0, 0)); im.paste(Image.open(os.path.join(REF, "bk_seq290.png")).convert("RGB"), (540, 0)); im.save(os.path.join(REF, "bk_cmp.png"))
    sys.stdout.flush(); os._exit(0)
