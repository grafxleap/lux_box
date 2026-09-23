"""Lowest point (y) of each box and of the wall around it: the reflection plane must line up with the base."""
import sys, os
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    br = p.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
    pg = br.new_page(viewport={"width": 405, "height": 720})
    pg.goto("http://127.0.0.1:8792/?v=%d&ui=0" % os.getpid()); pg.wait_for_function("window.__proto !== undefined", timeout=180000)
    print(pg.evaluate("""() => { const P = window.__proto, T = P.THREE, out = []; P.scene.updateMatrixWorld(true);
      P.scene.traverse(o => { if ((o.userData.name || o.name).startsWith('MASTER_Base')) { const b = new T.Box3().setFromObject(o);
        out.push((o.userData.name || o.name) + ' min y ' + b.min.y.toFixed(3) + ' max y ' + b.max.y.toFixed(3) + ' xz ' + b.getCenter(new T.Vector3()).toArray().map(x => x.toFixed(2))); } });
      let r; P.scene.traverse(o => { if (o.isReflector || o.type === 'Reflector') r = o; }); out.push('reflector y ' + (r && r.getWorldPosition(new T.Vector3()).y.toFixed(3)));
      return out.join(' ;; '); }"""))
    sys.stdout.flush(); os._exit(0)
