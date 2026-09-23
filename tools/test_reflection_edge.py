"""Which part of the environment map is reflected on the first box's seam edges (right half vs left).
For points along the band it works out the reflection vector (as the three.js shader does) and the matching pixel of env.hdr."""
import sys, os, math
from playwright.sync_api import sync_playwright
import numpy as np, cv2
REF = r"M:\MAIN PROJECTS\lazar\prototype\ref"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JS = r"""([pts]) => { const P = window.__proto, T = P.THREE, cam = P.activeCam(), rc = new T.Raycaster(), out = [];
  cam.updateMatrixWorld(); const cp = new T.Vector3().setFromMatrixPosition(cam.matrixWorld);
  for (const [px, py] of pts) {
    rc.setFromCamera(new T.Vector2(px / 810 * 2 - 1, 1 - py / 1440 * 2), cam);
    const h = rc.intersectObjects(P.scene.children, true).find(h => h.object.visible && h.object.type !== 'Reflector' && !(h.object.userData.name || '').startsWith('Wall'));
    if (!h || !h.face) { out.push(null); continue; }
    const n = h.face.normal.clone().transformDirection(h.object.matrixWorld).normalize();
    const I = h.point.clone().sub(cp).normalize();
    const R = I.clone().sub(n.clone().multiplyScalar(2 * I.dot(n))).normalize();
    const m = h.object.material; const rough = m.roughness ?? 1;
    const Rb = R.clone().lerp(n, rough * rough).normalize();
    out.push({ obj: h.object.userData.name || h.object.name, mat: m.name, rough: +rough.toFixed(2), R: R.toArray().map(x => +x.toFixed(3)), Rb: Rb.toArray().map(x => +x.toFixed(3)), n: n.toArray().map(x => +x.toFixed(3)) });
  }
  return out; }"""
def uv(d):
    x, y, z = d
    u = math.atan2(z, x) / (2 * math.pi) + 0.5; v = math.asin(max(-1, min(1, y))) / math.pi + 0.5
    return int(u * 1024) % 1024, int((1 - v) * 512)
env = cv2.imread(os.path.join(ROOT, "web", "env.hdr"), cv2.IMREAD_ANYDEPTH | cv2.IMREAD_COLOR).astype(np.float32).mean(2)
with sync_playwright() as p:
    br = p.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
    pg = br.new_page(viewport={"width": 405, "height": 720}, device_scale_factor=2)
    pg.goto("http://127.0.0.1:8792/?v=%d&ui=0" % os.getpid()); pg.wait_for_function("window.__proto !== undefined", timeout=180000)
    pg.wait_for_timeout(9000)
    y = int(sys.argv[1]) if len(sys.argv) > 1 else 810
    pts = []
    for dy in (-8, -5, 5, 8):
        for fx in (0.15, 0.3, 0.7, 0.85):
            pts.append([int(186 + (611 - 186) * fx), y + dy])
    res = pg.evaluate(JS, [pts])
    for (px, py), r in zip(pts, res):
        if not r: print(px, py, "-"); continue
        ux, uy = uv(r["Rb"]); win = env[max(0, uy - 25):uy + 26, :]
        cols = [(ux + k) % 1024 for k in range(-40, 41)]
        loc = env[max(0, uy - 25):uy + 26][:, cols]
        print("%s px %d,%d %-22s %-14s rough %.2f  R %s -> env (%d,%d)  env around it: max %.2f mean %.3f" % (
            "RIGHT" if px > 400 else "left", px, py, r["obj"], r["mat"], r["rough"], r["Rb"], ux, uy, loc.max(), loc.mean()))
    sys.stdout.flush(); os._exit(0)
