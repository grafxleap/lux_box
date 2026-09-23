"""Interface check: progress bar while loading, and the swiper (text, arrow light) at 0/50/100%."""
import sys, os
from playwright.sync_api import sync_playwright
from PIL import Image
REF = r"M:\MAIN PROJECTS\lazar\prototype\ref"
with sync_playwright() as p:
    br = p.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
    pg = br.new_page(viewport={"width": 405, "height": 720}, device_scale_factor=2)
    errs = []
    pg.on("pageerror", lambda e: errs.append("pageerror: " + str(e)))
    pg.on("console", lambda m: errs.append(m.type + ": " + m.text) if m.type == "error" else None)
    pg.goto("http://127.0.0.1:8792/?v=%d" % os.getpid(), wait_until="commit")
    vals = []
    for i in range(40):
        try:
            v = pg.evaluate("(() => { const b = document.getElementById('bar-fill'); return b ? getComputedStyle(b).transform : 'out_'; })()")
        except Exception as e:
            v = "err"
        vals.append(v)
        if i == 3: pg.screenshot(path=os.path.join(REF, "loading_bar.png"))
        if v == "out_": break
        pg.wait_for_timeout(250)
    print("bar (scaleX) while loading:", [x.split(",")[0].replace("matrix(", "") if x.startswith("matrix") else x for x in vals][:40])
    pg.wait_for_function("window.__proto !== undefined", timeout=180000); pg.wait_for_timeout(9000)
    for b in (0, 0.5, 1):
        pg.evaluate("window.__proto.setKnob(%s)" % b); pg.wait_for_timeout(1500)
        pg.screenshot(path=os.path.join(REF, "ui_knob_%d.png" % (b * 100)))
    im = Image.new("RGB", (3 * 810, 300))
    for i, b in enumerate((0, 50, 100)):
        im.paste(Image.open(os.path.join(REF, "ui_knob_%d.png" % b)).convert("RGB").crop((0, 1140, 810, 1440)), (i * 810, 0))
    im.resize((3 * 405, 150)).save(os.path.join(REF, "ui_swiper_3.png"))
    for e in errs: print("ERR", e)
    sys.stdout.flush(); os._exit(0)
