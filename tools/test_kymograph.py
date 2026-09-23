"""Replays the pulse video: the phase is held step by step (0 -> 1 -> 0) and the front box's seam is captured.
Writes a kymograph (x along the seam, time downwards) for the bands above, on and below the seam.

  python tools/test_kymograph.py <turn> <name> [extra query]      turn: how many boxes to turn first (0 = the first one)
"""
import sys, os
from playwright.sync_api import sync_playwright
from PIL import Image
import numpy as np
REF = r"M:\MAIN PROJECTS\lazar\prototype\ref"
turn_n, name_ = int(sys.argv[1]), sys.argv[2]
extra = sys.argv[3] if len(sys.argv) > 3 else ""
QUIET = "() => { const e = window.__proto.state(); return Math.abs(e.angle - e.goal) < 1e-6; }"
phases = [i / 8 for i in range(9)] + [1 - i / 8 for i in range(1, 9)]
with sync_playwright() as p:
    br = p.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
    pg = br.new_page(viewport={"width": 405, "height": 720}, device_scale_factor=2)
    pg.goto("http://127.0.0.1:8792/?v=%d&ui=0%s" % (os.getpid(), extra)); pg.wait_for_function("window.__proto !== undefined", timeout=180000)
    pg.wait_for_timeout(9000)
    if turn_n: pg.evaluate("window.__proto.turn(%d)" % turn_n)
    pg.wait_for_function(QUIET, timeout=180000, polling=200)
    imgs = []
    for f in phases:
        pg.evaluate("window.__proto.holdPulse(%s)" % f); pg.wait_for_timeout(900)
        path = os.path.join(REF, "kymo_tmp.png"); pg.screenshot(path=path)
        imgs.append(np.asarray(Image.open(path).convert("L"), float))
    A = np.stack(imgs)
    m = A.mean(0)
    zone = np.concatenate([m[700:900, 170:360], m[700:900, 450:640]], 1); y = 700 + int(np.argmax(zone.mean(1)))
    row = m[y, 100:710]; cols = np.where(row > 0.5 * row.max())[0] + 100; x0, x1 = cols.min() - 30, cols.max() + 30
    strips = []
    for t, a, b in (("above", y - 14, y - 3), ("seam", y - 2, y + 3), ("below", y + 3, y + 14)):
        K = A[:, a:b, x0:x1].mean(1)
        K = np.repeat(K, 12, 0)
        strips.append(K)
        S = A[:, a:b, x0:x1].mean(1)
        amp = S.max(0) - S.min(0)
        n = amp.shape[0]; stretches = [amp[int(n * f0):int(n * f1)].mean() for f0, f1 in ((0.03, 0.2), (0.2, 0.4), (0.6, 0.8), (0.8, 0.97))]
        # phase at which each stretch reaches half its travel (if the light runs, it shifts along x)
        mid = []
        for f0, f1 in ((0.03, 0.2), (0.2, 0.4), (0.6, 0.8), (0.8, 0.97)):
            c = S[:9, int(n * f0):int(n * f1)].mean(1); c = (c - c[0]) / max(1e-6, c[-1] - c[0])
            mid.append(next((phases[i] for i in range(9) if c[i] >= 0.5), 1.0))
        print("%s %-6s amplitude per stretch (left -> right): %s | phase at half travel: %s" % (name_, t, " ".join("%.1f" % v for v in stretches), " ".join("%.2f" % v for v in mid)))
    alt = sum(k.shape[0] for k in strips) + 20
    out = np.zeros((alt, strips[0].shape[1]))
    yy = 0
    for k in strips: out[yy:yy + k.shape[0]] = k; yy += k.shape[0] + 10
    lo, hi_ = np.percentile(out, 1), np.percentile(out, 99.5)
    Image.fromarray(np.clip((out - lo) / max(1e-6, hi_ - lo) * 255, 0, 255).astype(np.uint8)).save(os.path.join(REF, "kymo_%s.png" % name_))
    pg.evaluate("window.__proto.holdPulse(0.5)"); pg.wait_for_timeout(900)
    pg.screenshot(path=os.path.join(REF, "kymo_%s_view.png" % name_))
    sys.stdout.flush(); os._exit(0)
