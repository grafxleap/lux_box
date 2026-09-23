"""Bit at the top of the detail view: tries hiding groups (open box, lid, watch, wall, reflection, light)."""
import sys, os
from playwright.sync_api import sync_playwright
from PIL import Image
import numpy as np
REF = r"M:\MAIN PROJECTS\lazar\prototype\ref"
Z = (slice(70, 105), slice(230, 300))
with sync_playwright() as p:
    br = p.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
    pg = br.new_page(viewport={"width": 405, "height": 720}, device_scale_factor=540 / 405)
    pg.goto("http://127.0.0.1:8792/?v=%d&ui=0" % os.getpid()); pg.wait_for_function("window.__proto !== undefined", timeout=180000)
    pg.wait_for_timeout(1500)
    pg.evaluate("window.__proto.jumpTo(929)"); pg.wait_for_timeout(2500)
    def z(name_):
        path = os.path.join(REF, "det_%s.png" % name_); pg.screenshot(path=path)
        a = np.asarray(Image.open(path).convert("L"), float); return a[Z].max()
    print("all", z("all"))
    Image.open(os.path.join(REF, "det_tot.png")).convert("RGB").crop((180, 40, 360, 140)).resize((540, 300)).save(os.path.join(REF, "det_zoom.png"))
    groups = {
      "lid": "/^MASTER_Lid/.test(n)",
      "base_mesh": "/^MASTER_Base/.test(n) && o.isMesh",
      "logos": "/Logo/i.test(n)",
      "clasp": "/Clasp/i.test(n)",
      "wall": "/^Wall/.test(n)",
      "reflection": "o.type === 'Reflector'",
      "icosphere": "/Icosphere/.test(n)",
      "no_name": "!n",
    }
    for g, cond in groups.items():
        pg.evaluate("() => { window.__proto.scene.traverse(o => { const n = o.userData.name || o.name; if (o.isMesh && (%s)) { o.userData.vis0 = o.visible; o.visible = false; o.userData.hidden = true; } }); }" % cond)
        pg.wait_for_timeout(700); print("without %-10s %.0f" % (g, z(g)))
        pg.evaluate("() => { window.__proto.scene.traverse(o => { if (o.userData.hidden) { o.visible = o.userData.vis0; o.userData.hidden = false; } }); }")
    sys.stdout.flush(); os._exit(0)
