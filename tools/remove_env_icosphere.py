"""Erases the Icosphere from web/env.hdr: it children_ its pixels (mask from tools/icosphere_mask.py, widened) with
the surrounding environment. The rest of the map stays the same, bit for bit.

  python tools/remove_env_icosphere.py
In your scene the Icosphere is the light that runs along box .008's edge (frames 86 -> 484). The environment map was
captured at frame 1 from box .001 with it switched on (2000): the first box reflected it on its edge.
"""
import os, sys
import numpy as np, cv2
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV = os.path.join(ROOT, "web", "env.hdr")
ORIG = os.path.join(ROOT, "tools", "tmp_icosfera", "env_original.hdr")
if not os.path.exists(ORIG):
    import shutil; shutil.copy2(ENV, ORIG)
env = cv2.imread(ORIG, cv2.IMREAD_ANYDEPTH | cv2.IMREAD_COLOR).astype(np.float32)
msk = cv2.imread(os.path.join(ROOT, "tools", "tmp_icosfera", "mask.png"), cv2.IMREAD_UNCHANGED)[..., 3] > 0
msk = cv2.dilate(msk.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0     # 2 px of margin (antialiased edge)
lum = env.mean(2)
ys, xs = np.where(msk)
print("pixels to fill:", len(ys), "| luminance in the mask: max %.1f mean %.1f | around %.2f" % (
    lum[msk].max(), lum[msk].mean(), lum[max(0, ys.min() - 6):ys.max() + 7, max(0, xs.min() - 6):xs.max() + 7][~msk[max(0, ys.min() - 6):ys.max() + 7, max(0, xs.min() - 6):xs.max() + 7]].mean()))
# fill by diffusion: each masked pixel takes the average of its known neighbours, repeated until it settles
out = env.copy(); known = ~msk
for _ in range(200):
    s = cv2.blur(np.where(known[..., None], out, 0), (3, 3)); w = cv2.blur(known.astype(np.float32), (3, 3))
    new_ = msk & (w > 0)
    out[new_] = s[new_] / w[new_][:, None]
    known = known | new_
out[~msk] = env[~msk]
cv2.imwrite(ENV, out)
back_ = cv2.imread(ENV, cv2.IMREAD_ANYDEPTH | cv2.IMREAD_COLOR).astype(np.float32)
out_ = np.abs(back_[~msk] - env[~msk]).max()
print("after: max inside the mask %.2f | biggest difference outside it %.5f" % (back_.mean(2)[msk].max(), out_))
