"""Tests the interface: at rest, dragging the swiper knob to ON, and a tap on the center box."""
import sys, os, json
from playwright.sync_api import sync_playwright
REF = r"M:\MAIN PROJECTS\lazar\prototype\ref"
with sync_playwright() as p:
    br = p.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
    pg = br.new_page(viewport={"width": 405, "height": 720}, device_scale_factor=540 / 405)
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append(m.type + ": " + m.text) if m.type == "error" else None)
    pg.goto("http://127.0.0.1:8792/?v=%d" % os.getpid() + ""); pg.wait_for_function("window.__proto !== undefined", timeout=120000)
    pg.wait_for_timeout(2500); pg.screenshot(path=REF + r"\ui_repos.png")
    u = 405 / 360
    # swiper knob: center at (31.33 + 47.33, bottom 16.33 + 94.67 - 47.33) in pt
    bx = (31.33 + 47.33) * u; by = 720 - (16.33 + 94.67 - 47.33) * u
    pg.mouse.move(bx, by); pg.mouse.down()
    for i in range(1, 9): pg.mouse.move(bx + 26 * u * i, by); pg.wait_for_timeout(30)
    pg.wait_for_timeout(200); print("during l'dragging:", pg.evaluate("window.__proto.state()")); pg.screenshot(path=REF + r"\ui_arrossegant.png")
    pg.mouse.up(); pg.wait_for_timeout(400); print("en release-lo:", pg.evaluate("window.__proto.state()").get("state"))
    pg.wait_for_timeout(2600); print("after:", pg.evaluate("window.__proto.state()").get("state")); pg.screenshot(path=REF + r"\ui_obert.png")
    # back (provisional) and test the tap on the center box
    pg.mouse.click(200, 300); pg.wait_for_timeout(800); print("returned:", pg.evaluate("window.__proto.state()").get("state"))
    pg.mouse.click(202, 410); pg.wait_for_timeout(300); print("tap on the box:", pg.evaluate("window.__proto.state()").get("state"))
    pg.wait_for_timeout(3500); print("after the tap:", pg.evaluate("window.__proto.state()"))
    for e in errs[:8]: print("ERR", e)
    sys.stdout.flush(); os._exit(0)
