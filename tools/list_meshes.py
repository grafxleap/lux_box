"""Lists the visible meshes that are not part of the boxes (name, type, material, bounding box in world coordinates)."""
import sys, os
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    br = p.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
    pg = br.new_page(viewport={"width": 405, "height": 720})
    pg.goto("http://127.0.0.1:8792/?v=%d&ui=0" % os.getpid()); pg.wait_for_function("window.__proto !== undefined", timeout=180000)
    for l in pg.evaluate("""() => { const T = window.__proto.THREE, out = []; window.__proto.scene.updateMatrixWorld(true);
        window.__proto.scene.traverse(o => { if (!(o.isMesh || o.isLine || o.isPoints)) return;
        const n = o.userData.name || o.name; if (/^(MASTER|Logo|Clasp|Silver|Box)/i.test(n)) return;
        const b = new T.Box3().setFromObject(o);
        out.push([n, o.type, o.visible, o.material && o.material.name, o.material && o.material.type, o.material && ['map','aoMap','roughnessMap','metalnessMap','normalMap','emissiveMap','lightMap'].filter(k => o.material[k]).join('+'), o.material && o.material.aoMapIntensity, o.castShadow, o.receiveShadow, o.material && o.material.transparent, o.renderOrder,
                  b.min.toArray().map(x => +x.toFixed(2)), b.max.toArray().map(x => +x.toFixed(2))].join(' | ')); }); return out; }"""):
        print(l)
    sys.stdout.flush(); os._exit(0)
