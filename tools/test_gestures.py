"""Carousel gestures: turn direction against the finger, endless recents strip and the front box's pulse."""
import sys, os, time
from playwright.sync_api import sync_playwright
from PIL import Image
import numpy as np
REF = r"M:\MAIN PROJECTS\lazar\prototype\ref"
PROJ = """() => { const P = window.__proto, T = P.THREE, cam = P.activeCam(), out = [];
  for (const p of P.boxPositions()) { const v = new T.Vector3(...p).project(cam); out.push([+v.x.toFixed(3), +v.z.toFixed(3)]); }
  return out; }"""
with sync_playwright() as p:
    br = p.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
    pg = br.new_page(viewport={"width": 405, "height": 720}, device_scale_factor=540 / 405)
    errs = []
    pg.on("pageerror", lambda e: errs.append("pageerror: " + str(e)))
    pg.goto("http://127.0.0.1:8792/?v=%d" % os.getpid()); pg.wait_for_function("window.__proto !== undefined", timeout=180000)
    pg.wait_for_timeout(8000)   # let the intro finish
    # 1. direction: drag left (without releasing) and watch where the center box goes
    a = pg.evaluate(PROJ); i0 = min((i for i in range(len(a)) if abs(a[i][0]) < 0.35 and a[i][1] < 1), key=lambda i: a[i][1])   # the front one: the closest
    pg.mouse.move(300, 330); pg.mouse.down()
    for k in range(1, 9): pg.mouse.move(300 - 12 * k, 330); pg.wait_for_timeout(60)
    pg.wait_for_timeout(500)
    b = pg.evaluate(PROJ)
    print("finger to the left: center box x %.3f -> %.3f (%s)" % (a[i0][0], b[i0][0], "follows the finger" if b[i0][0] < a[i0][0] else "REVERSED"))
    pg.mouse.up(); pg.wait_for_timeout(2500)
    c = pg.evaluate(PROJ)
    right_side = [i for i in range(len(a)) if a[i][1] < a[i0][1] + 0.02 and 0.3 < a[i][0] < 1.6]
    print("on release: the one that was on the right", [(a[i][0], c[i][0]) for i in right_side], "state", pg.evaluate("window.__proto.state().goal"))
    # 2. recents: drag the strip and check that the cards move and wrap around
    xs0 = pg.evaluate("[...document.querySelectorAll('#group-recents .card')].map(t => +getComputedStyle(t).getPropertyValue('--x'))")
    pg.mouse.move(250, 180); pg.mouse.down()
    for k in range(1, 11): pg.mouse.move(250 - 25 * k, 180); pg.wait_for_timeout(16)
    pg.mouse.up(); pg.wait_for_timeout(1500)
    xs1 = pg.evaluate("[...document.querySelectorAll('#group-recents .card')].map(t => +getComputedStyle(t).getPropertyValue('--x'))")
    print("recents --x prev", xs0); print("recents --x after", xs1)
    pg.screenshot(path=os.path.join(REF, "gestures_recents.png"))
    # 3. pulse: brightness of the front box's seam over time
    vals = []
    for k in range(10):
        pg.screenshot(path=os.path.join(REF, "tmp_pulse.png"))
        im = np.asarray(Image.open(os.path.join(REF, "tmp_pulse.png")).convert("L"), float)
        vals.append(round(im[535:548, 130:400].mean(), 1)); pg.wait_for_timeout(300)
    print("seam over time:", vals)
    for e in errs: print("ERR", e)
    sys.stdout.flush(); os._exit(0)
