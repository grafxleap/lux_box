"""Calibrates version B's interior light against Cycles frames (ref/cycles_fNNN.png)."""
import subprocess, os, sys
from PIL import Image
import numpy as np
REF = r"M:\MAIN PROJECTS\lazar\prototype\ref"
frames = [450, 600, 700, 760]
values_ = sys.argv[1:] or ["1", "0.3", "0.1", "0.03"]
def loading(p, crop_=False):
    im = Image.open(p).convert('L')
    if crop_: im = im.crop((0, 120, 540, 1080))       # 9:20 -> the central 9:16 band
    return np.asarray(im.resize((270, 480)), float)
refs = {f: loading(os.path.join(REF, "cycles_f%d.png" % f), True) for f in frames}
for k in values_:
    pre = "Bcal_" + k.replace(".", "p")
    subprocess.run(["python", os.path.join(os.path.dirname(__file__), "capture_seq.py"), "8792", pre, *map(str, frames)],
                   capture_output=True, timeout=900, env=dict(os.environ, EXTRA_Q="&ui=0&inner_light=" + k))
    line = []
    for f in frames:
        w = loading(os.path.join(REF, "%s_f%d.png" % (pre, f)))
        line.append("f%d web %5.1f / cycles %5.1f" % (f, w.mean(), refs[f].mean()))
    print("inner_light", k, "|", " | ".join(line)); sys.stdout.flush()
