"""Detail (frame 929): what is that bit showing at the top, next to the logo? Hides candidates one by one.
   And the clasp with the swiper knob at 90% (large crop)."""
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
    # clasp with the knob at 90%
    pg.evaluate("window.__proto.setKnob(0.9)"); pg.wait_for_timeout(1500)
    pg.screenshot(path=os.path.join(REF, "clasp_90.png"))
    pg.evaluate("window.__proto.setKnob(0)"); pg.wait_for_timeout(1200)
    pg.screenshot(path=os.path.join(REF, "clasp_0.png"))
    im = Image.new("RGB", (400, 200))
    for i, n in enumerate(("clasp_0", "clasp_90")):
        im.paste(Image.open(os.path.join(REF, n + ".png")).convert("RGB").crop((220, 500, 320, 600)).resize((200, 200)), (i * 200, 0))
    im.save(os.path.join(REF, "clasp_cmp.png"))
    # detail
    pg.evaluate("window.__proto.jumpTo(929)"); pg.wait_for_timeout(2500)
    def zone():
        pg.screenshot(path=os.path.join(REF, "tmp_det.png"))
        a = np.asarray(Image.open(os.path.join(REF, "tmp_det.png")).convert("L"), float)
        return a[60:110, 200:330].max()
    print("top zone, everything:", zone())
    names = pg.evaluate("""() => { const s = []; window.__proto.scene.traverse(o => { if (o.isMesh && o.visible) s.push(o.uuid + '|' + (o.userData.name || o.name || o.type)); }); return s; }""")
    for e in names:
        uuid, name_ = e.split("|", 1)
        pg.evaluate("u => { window.__proto.scene.traverse(o => { if (o.uuid === u) o.visible = false; }); }", uuid); pg.wait_for_timeout(400)
        z = zone()
        pg.evaluate("u => { window.__proto.scene.traverse(o => { if (o.uuid === u) o.visible = true; }); }", uuid)
        if z < 60: print("  without", name_, "->", z)
    im = Image.open(os.path.join(REF, "tmp_det.png")).convert("RGB").crop((150, 30, 400, 140)).resize((500, 220)); im.save(os.path.join(REF, "detail_top.png"))
    sys.stdout.flush(); os._exit(0)
