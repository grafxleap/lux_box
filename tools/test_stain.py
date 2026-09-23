"""Dark patches under the side boxes: which object draws them (hiding them one by one)."""
import sys, os
from playwright.sync_api import sync_playwright
from PIL import Image
import numpy as np
REF = r"M:\MAIN PROJECTS\lazar\prototype\ref"
with sync_playwright() as p:
    br = p.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
    pg = br.new_page(viewport={"width": 405, "height": 720}, device_scale_factor=540 / 405)
    pg.goto("http://127.0.0.1:8792/?v=%d&ui=0" % os.getpid()); pg.wait_for_function("window.__proto !== undefined", timeout=180000)
    pg.wait_for_timeout(2000)
    # visible mesh objects, by name
    names = pg.evaluate("""() => { const s = new Set(); window.__proto.scene.traverse(o => { if (o.isMesh && o.visible) s.add(o.userData.name || o.name); }); return [...s]; }""")
    print(len(names), "meshes")
    print(pg.evaluate("""() => { const out = []; window.__proto.scene.traverse(o => { if ((o.isMesh || o.isLine || o.isPoints) && o.visible) {
        const n = o.userData.name || o.name; if (/^(MASTER|Logo|Clasp|Silver|Box)/.test(n)) return;
        o.geometry.computeBoundingBox(); const b = o.geometry.boundingBox;
        out.push(n + ' ' + o.type + ' ' + (o.material && o.material.name) + ' ' + b.min.toArray().map(x => x.toFixed(2)) + ' / ' + b.max.toArray().map(x => x.toFixed(2))); } }); return out; }"""))
    def capture(name_):
        path = os.path.join(REF, "stain_%s.png" % name_); pg.screenshot(path=path)
        return np.asarray(Image.open(path).convert("L"), float)
    base = capture("base")
    zone = (slice(500, 560), slice(470, 540))   # under the right-hand box
    print("zone base %.1f" % base[zone].mean())
    # hide by groups: reflection, each box, wall
    groups = {"reflection": "o.isMesh && o.type === 'Mesh' && o.material && o.material.uniforms && o.material.uniforms.strength",
             "wall": "(o.userData.name||o.name).startsWith('Wall')"}
    for g, cond in groups.items():
        pg.evaluate("() => { window.__proto.scene.traverse(o => { if (%s) o.visible = false; }); }" % cond); pg.wait_for_timeout(1200)
        a = capture(g); print("without %-8s zone %.1f" % (g, a[zone].mean()))
        pg.evaluate("() => { window.__proto.scene.traverse(o => { if (%s) o.visible = true; }); }" % cond); pg.wait_for_timeout(600)
    # the right-hand box (whole)
    i = pg.evaluate("""() => { const P = window.__proto, T = P.THREE, cam = P.activeCam(); let m = -1, x = 0;
        P.boxPositions().forEach((q, k) => { const v = new T.Vector3(...q).project(cam); if (v.z < 1 && v.x > 0.6 && v.x < 1.4 && (m < 0 || v.z < x)) { m = k; x = v.z; } }); return m; }""")
    print("right-hand box index", i)
    pg.evaluate("() => { window.__proto.scene.traverse(o => { if ((o.userData.name || o.name).startsWith('MASTER_Base')) o.visible = false; }); }")
    pg.wait_for_timeout(1200); a = capture("nobox"); print("without the right-hand box, zone %.1f" % a[zone].mean())
    im = Image.new("RGB", (540, 200)); im.paste(Image.open(os.path.join(REF, "stain_base.png")).convert("RGB").crop((270, 420, 540, 620)), (0, 0))
    im.paste(Image.open(os.path.join(REF, "stain_nobox.png")).convert("RGB").crop((270, 420, 540, 620)), (270, 0)); im.save(os.path.join(REF, "stain_zona.png"))
    sys.stdout.flush(); os._exit(0)
