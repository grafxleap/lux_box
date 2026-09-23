"""Which object sits at the pixel of that bit in the detail view? (ray from the camera)"""
import sys, os
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    br = p.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
    pg = br.new_page(viewport={"width": 405, "height": 720}, device_scale_factor=540 / 405)
    pg.goto("http://127.0.0.1:8792/?v=%d&ui=0" % os.getpid()); pg.wait_for_function("window.__proto !== undefined", timeout=180000)
    pg.wait_for_timeout(1500); pg.evaluate("window.__proto.jumpTo(929)"); pg.wait_for_timeout(2500)
    for px, py in ((255, 87), (265, 87), (275, 86)):
        r = pg.evaluate("""([x, y]) => { const P = window.__proto, T = P.THREE, cam = P.activeCam();
          const rc = new T.Raycaster(); rc.setFromCamera(new T.Vector2(x / 540 * 2 - 1, 1 - y / 960 * 2), cam);
          return rc.intersectObjects(P.scene.children, true).filter(h => h.object.visible).slice(0, 4).map(h => {
            let n = h.object.userData.name || h.object.name || h.object.type; let q = h.object.parent; let chain = n;
            while (q && q !== P.scene) { chain += ' < ' + (q.userData.name || q.name); q = q.parent; }
            return chain + ' d=' + h.distance.toFixed(2) + ' mat=' + (h.object.material && h.object.material.name); }); }""", [px, py])
        print(px, py, r)
    sys.stdout.flush(); os._exit(0)
