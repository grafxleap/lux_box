"""Tests the carousel by dragging with the mouse (like a finger): short snaps back, medium moves one, long moves only one."""
import sys, os, json, math
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    br = p.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
    pg = br.new_page(viewport={"width": 405, "height": 720})
    pg.goto("http://127.0.0.1:8791/?v=21"); pg.wait_for_function("window.__proto !== undefined", timeout=120000)
    STEP = math.radians(45)
    def state(): return pg.evaluate("window.__proto.state()")
    def drag(dx, steps=12, wait_ms=16):
        pg.mouse.move(200, 400); pg.mouse.down()
        for i in range(1, steps + 1):
            pg.mouse.move(200 + dx * i / steps, 400); pg.wait_for_timeout(wait_ms)
        pg.mouse.up(); pg.wait_for_timeout(1500)
        e = state(); return round(e["goal"] / STEP, 3), round(e["angle"] / STEP, 3)
    print("start:", state())
    print("short  (-40 px)   -> goal/angle en boxes:", drag(-40))
    print("mid   (-160 px)  -> ", drag(-160))
    print("long (-400 px)  -> ", drag(-400))
    print("fast (-60 px in 3 steps) -> ", drag(-60, steps=3, wait_ms=8), pg.evaluate("window.__ultimGest"))
    print("towards the right (+160 px) -> ", drag(160))
    pg.screenshot(path=r"M:\MAIN PROJECTS\lazar\prototype\ref\web_despres_swipes.png")
    sys.stdout.flush(); os._exit(0)
