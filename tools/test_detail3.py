"""That bit in the detail view: is it the direct light (Point.018), the environment or the base material's emission?"""
import sys, os
from playwright.sync_api import sync_playwright
from PIL import Image
import numpy as np
REF = r"M:\MAIN PROJECTS\lazar\prototype\ref"
Z = (slice(70, 105), slice(230, 300))
with sync_playwright() as p:
    br = p.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
    pg = br.new_page(viewport={"width": 405, "height": 720}, device_scale_factor=540 / 405)
    pg.goto("http://127.0.0.1:8792/?v=%d&ui=0%s" % (os.getpid(), sys.argv[1] if len(sys.argv) > 1 else "")); pg.wait_for_function("window.__proto !== undefined", timeout=180000)
    pg.wait_for_timeout(3000); pg.evaluate("window.__proto.jumpTo(929)"); pg.wait_for_timeout(2500)
    def z():
        path = os.path.join(REF, "tmp_d3.png"); pg.screenshot(path=path)
        return np.asarray(Image.open(path).convert("L"), float)[Z].max()
    print("all", z())
    tests_ = {
      "no direct lights": "o => { if (o.isLight && !o.isAmbientLight) { o.userData.i0 = o.intensity; o.intensity = 0; } }",
      "no env": "o => { if (o.isMesh && o.material && o.material.envMapIntensity !== undefined) { o.userData.e0 = o.material.envMapIntensity; o.material.envMapIntensity = 0; } }",
      "no emission": "o => { if (o.isMesh && o.material && o.material.emissiveIntensity !== undefined) { o.userData.m0 = o.material.emissiveIntensity; o.material.emissiveIntensity = 0; } }",
    }
    undo = "o => { if (o.userData.i0 !== undefined) { o.intensity = o.userData.i0; delete o.userData.i0; } if (o.userData.e0 !== undefined) { o.material.envMapIntensity = o.userData.e0; delete o.userData.e0; } if (o.userData.m0 !== undefined) { o.material.emissiveIntensity = o.userData.m0; delete o.userData.m0; } }"
    for name_, f in tests_.items():
        pg.evaluate("() => window.__proto.scene.traverse(%s)" % f); pg.wait_for_timeout(700)
        print(name_, z())
        pg.evaluate("() => window.__proto.scene.traverse(%s)" % undo); pg.wait_for_timeout(400)
    print("box:", pg.evaluate("window.__proto.state().boxK"))
    sys.stdout.flush(); os._exit(0)
