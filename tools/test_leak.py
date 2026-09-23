"""Interior light leaking through the logos: tries shadow bias values at frame 290."""
import sys, os
from playwright.sync_api import sync_playwright
from PIL import Image
import numpy as np
REF = r"M:\MAIN PROJECTS\lazar\prototype\ref"
with sync_playwright() as p:
    br = p.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
    pg = br.new_page(viewport={"width": 405, "height": 720}, device_scale_factor=540 / 405)
    pg.goto("http://127.0.0.1:8792/?v=%d&ui=0" % os.getpid()); pg.wait_for_function("window.__proto !== undefined", timeout=180000)
    pg.wait_for_timeout(1500)
    pg.evaluate("window.__proto.jumpTo(290)"); pg.wait_for_timeout(1500)
    for b, nb in ((-0.003, 0), (0, 0), (-0.0005, 0), (0, 0.01), (0.002, 0), (-0.003, 0.02)):
        pg.evaluate("""([b, nb]) => { let L; window.__proto.scene.traverse(o => { if (o.isPointLight && o.castShadow) L = o; });
            L.shadow.bias = b; L.shadow.normalBias = nb; L.shadow.needsUpdate = true; }""", [b, nb])
        pg.wait_for_timeout(1500)
        path = os.path.join(REF, "leak_%s_%s.png" % (b, nb)); pg.screenshot(path=path)
        a = np.asarray(Image.open(path).convert("L"), float)
        print(b, nb, "logo lid %.1f" % a[410:440, 200:340].mean(), "logo base %.1f" % a[610:630, 220:320].mean(), "seam %.1f" % a[535:545, 130:400].mean())
    sys.stdout.flush(); os._exit(0)
