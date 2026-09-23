"""Captures the prototype with Chromium (Playwright) at 540x960, to compare against the Cycles render.

  python tools/capture.py <output.png> [query] [js actions...]
"""
import sys, os, json
from playwright.sync_api import sync_playwright
out = sys.argv[1]
query = sys.argv[2] if len(sys.argv) > 2 else ""
actions = sys.argv[3:]
with sync_playwright() as p:
    br = p.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
    pg = br.new_page(viewport={"width": 405, "height": 720}, device_scale_factor=540 / 405)
    errs = []
    pg.on("console", lambda m: errs.append(m.type + ": " + m.text) if m.type in ("error", "warning") else None)
    pg.on("pageerror", lambda e: errs.append("pageerror: " + str(e)))
    pg.goto("http://127.0.0.1:8791/" + query)
    pg.wait_for_function("window.__proto !== undefined", timeout=120000)
    for a in actions:
        pg.evaluate(a); pg.wait_for_timeout(300)
    pg.wait_for_timeout(2500)
    print("state:", json.dumps(pg.evaluate("window.__proto.state()")))
    pg.screenshot(path=out)
    for e in errs[:10]: print(e)
    print("DONE", out); sys.stdout.flush()
    os._exit(0)
