"""The page's intro: LOADING, then boxes (fade + from the right), recents (fade) and swiper (from the bottom)."""
import sys, os
from playwright.sync_api import sync_playwright
REF = r"M:\MAIN PROJECTS\lazar\prototype\ref"
PROJ = """() => { const P = window.__proto; if (!P) return null; const T = P.THREE, cam = P.activeCam(); let best = null;
  const q = P.boxPositions()[0]; const v = new T.Vector3(...q).project(cam); best = [v.x, v.z];
  return { x: best && +best[0].toFixed(3), canvas: getComputedStyle(document.querySelector('canvas')).opacity,
           recents: getComputedStyle(document.getElementById('group-recents')).opacity,
           baix: getComputedStyle(document.getElementById('bottom')).transform, loading: !!document.getElementById('loading') }; }"""
with sync_playwright() as p:
    br = p.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
    pg = br.new_page(viewport={"width": 405, "height": 720}, device_scale_factor=540 / 405)
    errs = []
    pg.on("pageerror", lambda e: errs.append("pageerror: " + str(e)))
    pg.goto("http://127.0.0.1:8792/?v=%d" % os.getpid(), wait_until="commit")
    pg.wait_for_timeout(300); pg.screenshot(path=os.path.join(REF, "intro_0.png"))
    print("loading:", pg.evaluate("document.getElementById('loading') && document.getElementById('loading').textContent"))
    pg.wait_for_function("window.__proto !== undefined", timeout=180000)
    pg.wait_for_function("document.body.classList.contains('ready')", timeout=180000, polling=50)
    for i in range(8):
        print("%d" % i, pg.evaluate(PROJ))
        if i in (1, 3): pg.screenshot(path=os.path.join(REF, "intro_%d.png" % i))
        pg.wait_for_timeout(150)
    pg.wait_for_timeout(1500); print("final", pg.evaluate(PROJ)); pg.screenshot(path=os.path.join(REF, "intro_end.png"))
    for e in errs: print("ERR", e)
    sys.stdout.flush(); os._exit(0)
