"""Full journey: open (tap the box), wait for the detail view, Continue, back to the carousel.
  python tools/test_travel.py <port> <prefix> [channel]     (channel: msedge for H.264 in version A)
"""
import sys, os, time
from playwright.sync_api import sync_playwright
port, pre = sys.argv[1], sys.argv[2]
channel = sys.argv[3] if len(sys.argv) > 3 else None
REF = r"M:\MAIN PROJECTS\lazar\prototype\ref"
with sync_playwright() as p:
    kw = dict(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist", "--autoplay-policy=no-user-gesture-required"])
    if channel: kw["channel"] = channel
    br = p.chromium.launch(**kw)
    pg = br.new_page(viewport={"width": 405, "height": 720}, device_scale_factor=540 / 405)
    errs = []
    pg.on("pageerror", lambda e: errs.append("pageerror: " + str(e)))
    pg.on("console", lambda m: errs.append(m.type + ": " + m.text) if m.type == "error" else None)
    pg.goto("http://127.0.0.1:%s/?v=%d" % (port, os.getpid())); pg.wait_for_function("window.__proto !== undefined", timeout=180000)
    pg.wait_for_timeout(8000)   # let the intro finish
    e0 = pg.evaluate("window.__proto.state()"); print("start:", e0["state"], "goal", round(e0["goal"], 3))
    pg.mouse.click(202, 410)                                  # tap on the center box
    t0 = time.time()
    shots = {3: "opening", 9: "revealing"}
    done = set()
    while time.time() - t0 < 90:
        e = pg.evaluate("window.__proto.state()")
        dt = time.time() - t0
        for s, name_ in shots.items():
            if dt > s and s not in done:
                done.add(s); pg.screenshot(path=os.path.join(REF, "%s_%s.png" % (pre, name_))); print("  %4.1fs %s frame %.0f" % (dt, e["state"], e["seqFrame"]))
        if e["state"] == "detail": break
        pg.wait_for_timeout(500)
    print("detail at %.1f s:" % (time.time() - t0), e["state"], "frame %.0f" % e["seqFrame"])
    pg.wait_for_timeout(800); pg.screenshot(path=os.path.join(REF, "%s_detail.png" % pre))
    pg.click("#continue", force=True); t1 = time.time()
    while time.time() - t1 < 90:
        e = pg.evaluate("window.__proto.state()")
        if e["state"] == "rest": break
        pg.wait_for_timeout(500)
    print("from the watch back to the carousel at %.1f s:" % (time.time() - t1), e["state"], "| goal in boxes", round(e["goal"] / 0.785398, 3))
    pg.wait_for_timeout(1500); pg.screenshot(path=os.path.join(REF, "%s_returned.png" % pre))
    for x in errs[:10]: print("ERR", x)
    sys.stdout.flush(); os._exit(0)
