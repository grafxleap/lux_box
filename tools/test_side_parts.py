"""Part-by-part brightness of the side boxes (lid and base, left and right), masked with rays.

  python tools/test_side_parts.py [extra query]
States: knob 0 / 50 / 90 / 100 % in the carousel, and sequence frames 290, 1250, 1300, 1350, 1380.
"""
import sys, os
from playwright.sync_api import sync_playwright
from PIL import Image
import numpy as np
REF = r"M:\MAIN PROJECTS\lazar\prototype\ref"
extra = sys.argv[1] if len(sys.argv) > 1 else ""
MASK = """() => { const P = window.__proto, T = P.THREE, cam = P.activeCam(), rc = new T.Raycaster(), out = [];
  const boxes = []; P.scene.traverse(o => { const n = o.userData.name || o.name; if (/^MASTER_Base\\.?\\d{3}$/.test(n)) boxes.push(o); });
  const v = new T.Vector3();
  // visible side boxes: the two closest to the screen center (not counting the front one)
  const info = boxes.filter(c => c.visible).map(c => { c.getWorldPosition(v); const p = v.clone().project(cam); return { c, x: p.x, z: p.z }; })
    .filter(o => o.z < 1).sort((a, b) => Math.abs(a.x) - Math.abs(b.x));
  // the closest to the camera on each side (the ones behind, hidden, also have a large |x|)
  const closest = l => l.sort((a, b) => a.z - b.z)[0];
  const left = closest(info.filter(o => o.x < -0.3)), right = closest(info.filter(o => o.x > 0.3));
  const which_ = obj => { let o = obj; while (o && !boxes.includes(o)) { if (/^MASTER_Lid/.test(o.userData.name || o.name)) { let q = o; while (q && !boxes.includes(q)) q = q.parent; return [q, 'lid']; } o = o.parent; }
    return [o, (obj === o) ? 'base' : 'altre']; };
  for (let py = 250; py < 700; py += 4) for (let px = 0; px < 540; px += 4) {
    if (px > 150 && px < 390) continue;
    rc.setFromCamera(new T.Vector2(px / 540 * 2 - 1, 1 - py / 960 * 2), cam);
    const h = rc.intersectObjects(P.scene.children, true).find(h => h.object.visible && h.object.type !== 'Reflector' && !(h.object.userData.name || '').startsWith('Wall'));
    if (!h) continue;
    const [c, part] = which_(h.object);
    if (part === 'altre' || !c) continue;
    const side_ = left && c === left.c ? 'E' : right && c === right.c ? 'D' : null;
    if (side_) out.push([px, py, side_ + '_' + part]);
  }
  return out; }"""
with sync_playwright() as p:
    br = p.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
    pg = br.new_page(viewport={"width": 405, "height": 720}, device_scale_factor=540 / 405)
    pg.goto("http://127.0.0.1:8792/?v=%d&ui=0%s" % (os.getpid(), extra)); pg.wait_for_function("window.__proto !== undefined", timeout=180000)
    pg.wait_for_timeout(8000)
    def measure(name_):
        mask = pg.evaluate(MASK)
        path = os.path.join(REF, "pl_%s.png" % name_); pg.screenshot(path=path)
        a = np.asarray(Image.open(path).convert("L"), float)
        groups = {}
        for px, py, k in mask: groups.setdefault(k, []).append(a[py, px])
        return "  ".join("%s %5.1f" % (k, np.mean(groups[k])) if k in groups else "%s   -  " % k for k in ("E_tapa", "E_base", "D_tapa", "D_base"))
    knob_only = len(sys.argv) > 2 and sys.argv[2] == "knob"
    for b in ((1.0,) if knob_only else (0, 0.5, 0.9, 1.0)):
        pg.evaluate("window.__proto.setKnob(%s)" % b); pg.wait_for_timeout(2000)
        print("knob %3d%%  %s" % (b * 100, measure("b%d" % (b * 100)))); sys.stdout.flush()
    if knob_only: sys.stdout.flush(); os._exit(0)
    pg.evaluate("window.__proto.jumpTo(290)"); pg.wait_for_timeout(2500); print("seq 290   %s" % measure("f290")); sys.stdout.flush()
    for f in (1250, 1300, 1350, 1380):
        pg.evaluate("window.__proto.jumpTo(%d)" % f); pg.wait_for_timeout(2500); print("seq %d  %s" % (f, measure("f%d" % f))); sys.stdout.flush()
    sys.stdout.flush(); os._exit(0)
