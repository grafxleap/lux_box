"""First box with the original environment map (with the Icosphere) and the new one: difference, at pulse phases 0, 0.5 and 1."""
import sys, os
from playwright.sync_api import sync_playwright
from PIL import Image
import numpy as np
REF = r"M:\MAIN PROJECTS\lazar\prototype\ref"
with sync_playwright() as p:
    br = p.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
    photos = {}
    for name_, q in (("old", "&env=env_old_icosphere.hdr"), ("new_", "")):
        pg = br.new_page(viewport={"width": 405, "height": 720}, device_scale_factor=2)
        pg.goto("http://127.0.0.1:8792/?v=%d&ui=0%s" % (os.getpid(), q)); pg.wait_for_function("window.__proto !== undefined", timeout=180000)
        pg.wait_for_timeout(9000)
        for phase in (0, 0.5, 1):
            pg.evaluate("window.__proto.holdPulse(%s)" % phase); pg.wait_for_timeout(1500)
            path = os.path.join(REF, "ico_%s_%s.png" % (name_, phase)); pg.screenshot(path=path)
            photos[(name_, phase)] = np.asarray(Image.open(path).convert("L"), float)
        pg.close()
    for phase in (0, 0.5, 1):
        d = photos[("old", phase)] - photos[("new_", phase)]
        ys, xs = np.where(np.abs(d) > 4)
        print("phase %s: pixels that change %d, max %.0f" % (phase, len(ys), np.abs(d).max()), "zone", (xs.min(), ys.min(), xs.max(), ys.max()) if len(ys) else "")
    box = (130, 600, 680, 1000)
    im = Image.new("RGB", (550 * 2, 400 * 2))
    for i, name_ in enumerate(("old", "new_")):
        for j, phase in enumerate((0, 1)):
            im.paste(Image.open(os.path.join(REF, "ico_%s_%s.png" % (name_, phase))).convert("RGB").crop(box), (i * 550, j * 400))
    im.save(os.path.join(REF, "ico_cmp.png"))
    sys.stdout.flush(); os._exit(0)
