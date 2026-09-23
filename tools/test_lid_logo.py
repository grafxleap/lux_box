"""Where each lid logo is (and lids .001 and .008): parent, center, size and position on screen."""
import sys, os
from playwright.sync_api import sync_playwright
JS = r"""() => { const P = window.__proto, T = P.THREE, out = [], cam = P.activeCam(); P.scene.updateMatrixWorld(true);
  P.scene.traverse(o => { const n = o.userData.name || o.name;
    if (/Logo_?lid/i.test(n) || /^MASTER_Lid\.?00[18]$/.test(n)) {
      const b = new T.Box3().setFromObject(o), c = b.getCenter(new T.Vector3()), s = b.getSize(new T.Vector3());
      const q = c.clone().project(cam);
      out.push(n + ' <- ' + (o.parent.userData.name || o.parent.name) + ' | center ' + c.toArray().map(x => x.toFixed(2)) + ' size ' + s.toArray().map(x => x.toFixed(2)) + ' | screen ' + q.x.toFixed(2) + ',' + q.y.toFixed(2) + ' vis ' + o.visible + ' mat ' + (o.material ? o.material.name : '-')); } });
  return out.join(' ;; '); }"""
with sync_playwright() as p:
    br = p.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
    pg = br.new_page(viewport={"width": 405, "height": 720})
    pg.goto("http://127.0.0.1:8792/?v=%d&ui=0" % os.getpid()); pg.wait_for_function("window.__proto !== undefined", timeout=180000)
    pg.wait_for_timeout(9000)
    for l in pg.evaluate(JS).split(" ;; "): print(l)
    sys.stdout.flush(); os._exit(0)
