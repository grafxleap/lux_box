"""Sequence captures, jumping to given frames:  python tools/capture_seq.py <port> <prefix> f1 f2 ..."""
import sys, os
from playwright.sync_api import sync_playwright
port, prefix = sys.argv[1], sys.argv[2]
frames = [int(x) for x in sys.argv[3:]]
REF = r"M:\MAIN PROJECTS\lazar\prototype\ref"
with sync_playwright() as p:
    br = p.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
    pg = br.new_page(viewport={"width": 405, "height": 720}, device_scale_factor=540 / 405)
    errs = []
    pg.on("pageerror", lambda e: errs.append("pageerror: " + str(e)))
    pg.on("console", lambda m: errs.append(m.type + ": " + m.text) if m.type == "error" else None)
    extra = os.environ.get("EXTRA_Q", "")
    pg.goto("http://127.0.0.1:%s/?v=%d%s" % (port, os.getpid(), extra)); pg.wait_for_function("window.__proto !== undefined", timeout=180000)
    pg.wait_for_timeout(1500)
    for f in frames:
        pg.evaluate("window.__proto.jumpTo(%d)" % f); pg.wait_for_timeout(1800)
        pg.screenshot(path=os.path.join(REF, "%s_f%d.png" % (prefix, f)))
        print("frame", f, pg.evaluate("window.__proto.state()"))
    for e in errs[:10]: print("ERR", e)
    sys.stdout.flush(); os._exit(0)
