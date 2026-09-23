"""Dotted line on the left side box: what is it? (ray at the pixel, plus tests with the emission and the environment off)."""
import sys, os
from playwright.sync_api import sync_playwright
from PIL import Image
import numpy as np
REF = r"M:\MAIN PROJECTS\lazar\prototype\ref"
RAY = r"""([pts]) => { const P = window.__proto, T = P.THREE, cam = P.activeCam(), rc = new T.Raycaster(), out = [];
  for (const [px, py] of pts) { rc.setFromCamera(new T.Vector2(px / 810 * 2 - 1, 1 - py / 1440 * 2), cam);
    const h = rc.intersectObjects(P.scene.children, true).find(h => h.object.visible && h.object.type !== 'Reflector');
    if (!h) { out.push('-'); continue; }
    let n = h.object.userData.name || h.object.name, q = h.object.parent;
    while (q && !(q.userData.name || q.name).startsWith('MASTER_Base')) q = q.parent;
    out.push(n + ' [' + (q ? (q.userData.name || q.name) : '') + '] mat ' + h.object.material.name + ' uv ' + (h.uv ? h.uv.toArray().map(x => x.toFixed(3)).join(',') : '')); }
  return out; }"""
with sync_playwright() as p:
    br = p.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
    res = {}
    for name_, q in (("normal", ""), ("no emission", "&seam=0"), ("no env", "&env=0")):
        pg = br.new_page(viewport={"width": 405, "height": 720}, device_scale_factor=2)
        pg.goto("http://127.0.0.1:8792/?v=%d&ui=0%s" % (os.getpid(), q)); pg.wait_for_function("window.__proto !== undefined", timeout=180000)
        pg.wait_for_timeout(9000)
        path = os.path.join(REF, "line_%s.png" % name_.replace(" ", "_")); pg.screenshot(path=path)
        a = np.asarray(Image.open(path).convert("L"), float)
        left = a[750:800, 0:100]; right = a[750:800, 710:810]
        print("%-14s line left_side: max %.0f (pixels > 60: %d) | right_side: max %.0f (pixels > 60: %d)" % (name_, left.max(), (left > 60).sum(), right.max(), (right > 60).sum()))
        if name_ == "normal":
            ys, xs = np.where(left > 60)
            pts = [[int(x), int(y) + 750] for x, y in list(zip(xs, ys))[:6]]
            for pt, r in zip(pts, pg.evaluate(RAY, [pts])): print("   ", pt, r)
            ys, xs = np.where(right > 40)
            pts = [[int(x) + 710, int(y) + 750] for x, y in list(zip(xs, ys))[:4]]
            for pt, r in zip(pts, pg.evaluate(RAY, [pts])): print("   right_side", pt, r)
        pg.close()
    sys.stdout.flush(); os._exit(0)
