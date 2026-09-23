"""While the carousel turns, the boxes heading to the back fade out (opacity) instead of vanishing in one step."""
import sys, os
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    br = p.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
    pg = br.new_page(viewport={"width": 405, "height": 720})
    pg.goto("http://127.0.0.1:8792/?v=%d&ui=0" % os.getpid()); pg.wait_for_function("window.__proto !== undefined", timeout=180000)
    pg.wait_for_timeout(8000)
    pg.evaluate("window.__proto.turn(1)")
    for i in range(14):
        print(pg.evaluate("""() => { const o = []; window.__proto.scene.traverse(c => { const n = c.userData.name || c.name;
            if (n.startsWith('MASTER_Base') && c.isMesh) o.push(n.slice(-3) + ':' + (c.visible ? c.material.opacity.toFixed(2) : '-')); }); return o.join(' '); }"""))
        pg.wait_for_timeout(120)
    sys.stdout.flush(); os._exit(0)
