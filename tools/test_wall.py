"""Does the wall cut the side boxes? A normal capture and one with the wall not writing depth."""
import sys, os
from playwright.sync_api import sync_playwright
from PIL import Image
REF = r"M:\MAIN PROJECTS\lazar\prototype\ref"
with sync_playwright() as p:
    br = p.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
    pg = br.new_page(viewport={"width": 405, "height": 720}, device_scale_factor=540 / 405)
    pg.goto("http://127.0.0.1:8792/?v=%d&ui=0" % os.getpid()); pg.wait_for_function("window.__proto !== undefined", timeout=180000)
    pg.wait_for_timeout(2000)
    pg.screenshot(path=os.path.join(REF, "wall_a.png"))
    print(pg.evaluate("""() => { const P = window.__proto, T = P.THREE, cam = P.activeCam(), out = [];
      P.scene.traverse(o => { const n = o.userData.name || o.name; if (n.startsWith('MASTER_Base')) {
        const v = o.getWorldPosition(new T.Vector3()).project(cam); out.push(n + ' x ' + v.x.toFixed(2) + ' z ' + v.z.toFixed(3)); } });
      return out.join(' | '); }"""))
    pg.evaluate("""() => { window.__proto.scene.traverse(o => { if ((o.userData.name || o.name).startsWith('Wall') && o.isMesh) o.material.depthWrite = false; }); }""")
    pg.wait_for_timeout(1500)
    pg.screenshot(path=os.path.join(REF, "wall_b.png"))
    im = Image.new("RGB", (540, 560))
    im.paste(Image.open(os.path.join(REF, "wall_a.png")).convert("RGB").crop((270, 380, 540, 940)), (0, 0))
    im.paste(Image.open(os.path.join(REF, "wall_b.png")).convert("RGB").crop((270, 380, 540, 940)), (270, 0))
    im.save(os.path.join(REF, "wall_ab.png"))
    sys.stdout.flush(); os._exit(0)
