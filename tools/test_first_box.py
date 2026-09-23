"""The front box on load (.001) compared with the others once centred, at high resolution."""
import sys, os
from playwright.sync_api import sync_playwright
from PIL import Image
REF = r"M:\MAIN PROJECTS\lazar\prototype\ref"
with sync_playwright() as p:
    br = p.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
    pg = br.new_page(viewport={"width": 405, "height": 720}, device_scale_factor=2)
    pg.goto("http://127.0.0.1:8792/?v=%d&ui=0%s" % (os.getpid(), sys.argv[1] if len(sys.argv) > 1 else "")); pg.wait_for_function("window.__proto !== undefined", timeout=180000)
    pg.wait_for_timeout(9000)
    box = (130, 480, 680, 1000)          # 810x1440: the front box
    pg.screenshot(path=os.path.join(REF, "first_0.png"))
    for n in (1, -1):
        pg.evaluate("window.__proto.turn(%d)" % n); pg.wait_for_timeout(4000)
        pg.screenshot(path=os.path.join(REF, "first_%d.png" % n))
        pg.evaluate("window.__proto.turn(%d)" % (-n)); pg.wait_for_timeout(4000)
    im = Image.new("RGB", (3 * 550, 520))
    for i, n in enumerate(("primera_0", "primera_1", "primera_-1")):
        im.paste(Image.open(os.path.join(REF, n + ".png")).convert("RGB").crop(box), (i * 550, 0))
    im.save(os.path.join(REF, "first_cmp.png"))
    sys.stdout.flush(); os._exit(0)
