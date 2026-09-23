"""Local matrix of the front box's lid at rest vs the timeline's (.008) and with the knob at 90%."""
import sys, os
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    br = p.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
    pg = br.new_page(viewport={"width": 405, "height": 720})
    pg.goto("http://127.0.0.1:8792/?v=%d&ui=0" % os.getpid()); pg.wait_for_function("window.__proto !== undefined", timeout=180000)
    pg.wait_for_timeout(1500)
    js = """() => { const P = window.__proto, out = [];
      P.scene.traverse(o => { const n = o.userData.name || o.name; if (/^MASTER_Lid/.test(n) && o.parent && /001$/.test(o.parent.userData.name || o.parent.name)) {
        out.push(n + ' local ' + o.matrix.elements.map(x => x.toFixed(3)).join(','));
        const kids = []; o.traverse(k => { if (k !== o) kids.push(k.userData.name || k.name); }); out.push('  children_ ' + kids.join(','));
        const g = []; o.parent.children.forEach(k => g.push(k.userData.name || k.name)); out.push('  siblings ' + g.join(',')); } });
      out.push('closed .008 ' + P.lidClosed().elements.map(x => x.toFixed(3)).join(','));
      return out.join(' ;; '); }"""
    for l in pg.evaluate(js).split(" ;; "): print(l)
    pg.evaluate("window.__proto.setKnob(0.9)"); pg.wait_for_timeout(1500)
    print("--- knob 90%")
    for l in pg.evaluate(js).split(" ;; "): print(l)
    sys.stdout.flush(); os._exit(0)
