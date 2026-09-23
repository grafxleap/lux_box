"""Cycles reference frames (no interface) to calibrate version B.
  blender -b luxbox_realtime.blend -P tools/ref_frames.py -- 450 600 700 760
Same framing as the web page: 9:20 with the design's horizontal angle; saved at 540x1200.
"""
import bpy, os, sys
PROTO = os.path.dirname(os.path.abspath(bpy.data.filepath))
REF = r"M:\MAIN PROJECTS\lazar\prototype\ref"
frames = [int(x) for x in sys.argv[sys.argv.index("--") + 1:]]
sc = bpy.data.scenes["LOOP"]
if bpy.context.window: bpy.context.window.scene = sc
vl = sc.view_layers[0]
for name_ in ("UI_TOP", "SWIPER"):
    lc = vl.layer_collection.children.get(name_)
    if lc: lc.exclude = True
r = sc.render; r.engine = 'CYCLES'
try:
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'OPTIX'; prefs.get_devices()
    for d in prefs.devices: d.use = True
    sc.cycles.device = 'GPU'
except Exception as e: print("GPU", e)
r.resolution_x, r.resolution_y, r.resolution_percentage = 540, 1200, 100
cd = sc.camera.data; cd.sensor_fit = 'HORIZONTAL'; cd.sensor_width = 36.0 * 1080 / 1920
r.use_border = False; r.film_transparent = False
sc.cycles.samples = 48
r.image_settings.file_format = 'PNG'; r.image_settings.color_mode = 'RGB'
for f in frames:
    sc.frame_set(f)
    r.filepath = os.path.join(REF, "cycles_f%d.png" % f)
    bpy.ops.render.render(write_still=True)
    print("REF", f); sys.stdout.flush()
