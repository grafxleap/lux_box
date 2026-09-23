"""Brightness of the front box with the swiper knob: at rest, halfway and almost at the end (without releasing it)."""
import sys, os
from playwright.sync_api import sync_playwright
REF = r"M:\MAIN PROJECTS\lazar\prototype\ref"
with sync_playwright() as p:
    br = p.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
    pg = br.new_page(viewport={"width": 405, "height": 720}, device_scale_factor=540 / 405)
    errs = []
    pg.on("pageerror", lambda e: errs.append("pageerror: " + str(e)))
    pg.goto("http://127.0.0.1:8792/?v=%d" % os.getpid()); pg.wait_for_function("window.__proto !== undefined", timeout=180000)
    pg.wait_for_timeout(8000)
    u = 405 / 360
    bx = (31.33 + 47.33) * u; by = 720 - (16.33 + 94.67 - 47.33) * u
    pg.screenshot(path=os.path.join(REF, "bright_0.png"))
    pg.mouse.move(bx, by); pg.mouse.down()
    for i, (dx, name_) in enumerate(((101 * u, "bright_50"), (184 * u, "bright_90"))):
        for k in range(1, 7): pg.mouse.move(bx + dx * k / 6, by); pg.wait_for_timeout(40)
        pg.wait_for_timeout(1200)
        print(name_, pg.evaluate("window.__proto.state().swipeProgress"))
        pg.screenshot(path=os.path.join(REF, name_ + ".png"))
    pg.mouse.move(bx, by); pg.mouse.up()
    for e in errs: print("ERR", e)
    sys.stdout.flush(); os._exit(0)
