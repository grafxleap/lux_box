"""Carousel -> sequence bridge: captures the carousel at rest and the sequence's first frame (290), with no interface."""
import sys, os
from playwright.sync_api import sync_playwright
REF = r"M:\MAIN PROJECTS\lazar\prototype\ref"
pre = sys.argv[1] if len(sys.argv) > 1 else "bridge"
with sync_playwright() as p:
    br = p.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
    pg = br.new_page(viewport={"width": 405, "height": 720}, device_scale_factor=540 / 405)
    errs = []
    pg.on("pageerror", lambda e: errs.append("pageerror: " + str(e)))
    pg.goto("http://127.0.0.1:8792/?v=%d&ui=0%s" % (os.getpid(), os.environ.get("EXTRA_Q", ""))); pg.wait_for_function("window.__proto !== undefined", timeout=180000)
    pg.wait_for_timeout(2500)
    pg.screenshot(path=os.path.join(REF, pre + "_carousel.png"))
    pg.evaluate("window.__proto.jumpTo(290)"); pg.wait_for_timeout(2500)
    pg.screenshot(path=os.path.join(REF, pre + "_seq290.png"))
    for e in errs: print("ERR", e)
    sys.stdout.flush(); os._exit(0)
