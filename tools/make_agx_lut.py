"""3D LUT of Blender's AgX (the same OCIO) for the web prototype.

LUT input: log2 of the linear light, normalised between MIN_EV and MAX_EV per channel.
Output: sRGB screen colour (8 bits), exactly what Blender's AgX view gives.
  blender -b --factory-startup -P tools/make_agx_lut.py
"""
import bpy, os, json
import numpy as np
import PyOpenColorIO as OCIO
WEB = r"M:\MAIN PROJECTS\lazar\prototype\web"
N = 48
MIN_EV, MAX_EV = -14.0, 8.0
cfg = OCIO.Config.CreateFromFile(os.path.join(bpy.utils.resource_path('LOCAL'), "datafiles", "colormanagement", "config.ocio"))
cpu = cfg.getProcessor(OCIO.DisplayViewTransform(src="Linear Rec.709", display="sRGB", view="AgX")).getDefaultCPUProcessor()
t = np.linspace(0, 1, N, dtype=np.float64)
ev = MIN_EV + t * (MAX_EV - MIN_EV)
lin = np.power(2.0, ev).astype(np.float32)
lin[0] = 0.0
# Data3DTexture order: x (r) fastest, then y (g), then z (b)
b, g, r = np.meshgrid(lin, lin, lin, indexing='ij')
rgb = np.stack([r, g, b], axis=-1).reshape(-1, 3).astype(np.float32).copy()
cpu.applyRGB(rgb.reshape(-1))
rgba = np.concatenate([np.clip(rgb, 0, 1), np.ones((rgb.shape[0], 1), np.float32)], axis=1)
data = np.round(rgba * 255).astype(np.uint8)
data.tofile(os.path.join(WEB, "agx_lut.bin"))
json.dump({"N": N, "minEV": MIN_EV, "maxEV": MAX_EV, "format": "RGBA8, r fastest"}, open(os.path.join(WEB, "agx_lut.json"), "w"))
# check against the values measured earlier: background 0.01884 -> 30.5/255, 0.18 -> 0.461
for v in (0.01884, 0.18, 1.0, 14.86):
    a = np.array([[v, v, v]], np.float32); cpu.applyRGB(a.reshape(-1)); print("AgX(%g) = %.1f/255" % (v, a[0, 0] * 255))
print("LUT", N, "->", os.path.getsize(os.path.join(WEB, "agx_lut.bin")) // 1024, "KB")
