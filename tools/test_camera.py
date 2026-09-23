"""Compares the carousel's camera and boxes against frame 290 of the sequence."""
import sys, os, json
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    br = p.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
    pg = br.new_page(viewport={"width": 405, "height": 720}, device_scale_factor=540 / 405)
    pg.goto("http://127.0.0.1:8792/?v=%d&ui=0" % os.getpid()); pg.wait_for_function("window.__proto !== undefined", timeout=180000)
    pg.wait_for_timeout(1500)
    js = """() => { const P = window.__proto, T = P.THREE, out = {};
      const cam = P.composer ? null : null;
      const r = v => Math.round(v * 1000) / 1000;
      let cams = []; P.scene.traverse(o => { if (o.isCamera) cams.push(o); });
      const c = P.activeCam(); c.updateMatrixWorld && P.scene.updateMatrixWorld(true);
      out.cam = c.matrixWorld.elements.map(r); out.fov = r(c.fov);
      out.boxes = P.boxPositions().map(v => v.map(r)); return out; }"""
    a = pg.evaluate(js)
    pg.evaluate("window.__proto.jumpTo(290)"); pg.wait_for_timeout(1500)
    b = pg.evaluate(js)
    print("cam carousel", a["cam"][12:15], "fov", a["fov"]); print("cam seq290  ", b["cam"][12:15], "fov", b["fov"])
    print("rot carousel", a["cam"][:11]); print("rot seq290  ", b["cam"][:11])
    for x, y in zip(a["boxes"], b["boxes"]): print(x, y)
    sys.stdout.flush(); os._exit(0)
