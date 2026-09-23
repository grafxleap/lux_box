"""Frames of the intro (as the page loads), at 2x: to see whether any light sweeps across the box."""
import sys, os
from playwright.sync_api import sync_playwright
from PIL import Image
REF = r"M:\MAIN PROJECTS\lazar\prototype\ref"
with sync_playwright() as p:
    br = p.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
    pg = br.new_page(viewport={"width": 405, "height": 720}, device_scale_factor=2)
    pg.goto("http://127.0.0.1:8792/?v=%d&ui=0" % os.getpid(), wait_until="commit")
    pg.wait_for_function("document.body && document.body.classList.contains('ready')", timeout=180000, polling=30)
    photos = []
    for i in range(12):
        path = os.path.join(REF, "intro_%02d.png" % i); pg.screenshot(path=path); photos.append(path)
        pg.wait_for_timeout(60)
    pg.wait_for_timeout(3000); path = os.path.join(REF, "intro_end.png"); pg.screenshot(path=path); photos.append(path)
    im = Image.new("RGB", (4 * 405, 4 * 360))
    for k, f in enumerate(photos[:12] + [photos[-1]][:0]):
        a = Image.open(f).convert("RGB").crop((0, 440, 810, 1160)).resize((405, 360))
        im.paste(a, ((k % 4) * 405, (k // 4) * 360))
    a = Image.open(photos[-1]).convert("RGB").crop((0, 440, 810, 1160)).resize((405, 360)); im.paste(a, (0, 3 * 360))
    im.save(os.path.join(REF, "intro_grid.png"))
    sys.stdout.flush(); os._exit(0)
