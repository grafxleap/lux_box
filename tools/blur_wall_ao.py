"""Background depth without patches: the wall's original AO (with the boxes) blurred until no box shape is
left, only the general darkening of the ring and the corner (the same from any carousel angle).

  python tools/blur_wall_ao.py [sigma_px] [gamma]
Input: bake/Wall_ao.png (AO with boxes, 2048) and web/Wall_ao.png (AO without boxes, used as the UV-island mask).
Output: web/Wall_ao.png. The blur is normalised inside each island (the black outside does not bleed in).
"""
import sys, os
import numpy as np, cv2
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sigma = float(sys.argv[1]) if len(sys.argv) > 1 else 80
gamma = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0   # >1: darker where it already was (more depth)
old = cv2.imread(os.path.join(ROOT, "bake", "Wall_ao.png"), cv2.IMREAD_GRAYSCALE).astype(np.float32) / 255
net = cv2.imread(os.path.join(ROOT, "tools", "wall_ao_no_boxes.png"), cv2.IMREAD_GRAYSCALE).astype(np.float32) / 255
mask = (net > 0.04).astype(np.float32)
k = (0, 0)
num = cv2.GaussianBlur(old * mask, k, sigma); den = cv2.GaussianBlur(mask, k, sigma)
smooth = np.where(den > 1e-4, num / np.maximum(den, 1e-4), 1.0) ** gamma * mask + (1 - mask) * old
cv2.imwrite(os.path.join(ROOT, "web", "Wall_ao.png"), np.clip(smooth * 255 + 0.5, 0, 255).astype(np.uint8))
print("done, sigma", sigma, "gamma", gamma, "mean", round(float(smooth[mask > 0].mean()), 3), "old", round(float(old[mask > 0].mean()), 3))
