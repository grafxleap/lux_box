"""Captures mid-turn of the carousel: the boxes at the back must not show (the hider covers them)."""
import sys, os
from playwright.sync_api import sync_playwright
REF = r"M:\MAIN PROJECTS\lazar\prototype\ref"
with sync_playwright() as p:
    br = p.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
    pg = br.new_page(viewport={"width": 405, "height": 720}, device_scale_factor=540 / 405)
    pg.goto("http://127.0.0.1:8792/?v=%d&ui=0%s" % (os.getpid(), sys.argv[1] if len(sys.argv) > 1 else "")); pg.wait_for_function("window.__proto !== undefined", timeout=180000)
    pg.wait_for_timeout(8000)
    # angle held halfway (dragging without releasing)
    pg.mouse.move(300, 330); pg.mouse.down()
    for i, dx in enumerate((60, 120, 180)):
        for k in range(1, 5): pg.mouse.move(300 - (dx - 60) - 15 * k, 330); pg.wait_for_timeout(40)
        pg.wait_for_timeout(1200); pg.screenshot(path=os.path.join(REF, "turn_n%s_%d.png" % (sys.argv[2] if len(sys.argv) > 2 else "", i)))
    pg.mouse.up()
    sys.stdout.flush(); os._exit(0)
