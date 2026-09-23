"""The swiper's text layer with new wording, fitted between two horizontal limits (in design pt, 360 pt screen).
Same font, material, light and camera as tools/swiper_layers.py (frame 1, Cycles, everything else on holdout).

  blender -b luxbox_realtime.blend -P tools/swipe_text_layer.py -- "SWIPE TO OPEN" 129.3 294.0
Writes web/ui/swipe_word.png (the previous one stays at tools/swipe_word_SWIPE.png).
"""
import bpy, os, sys, shutil
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view as w2c
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
TEXT = args[0] if args else "SWIPE TO OPEN"
PT0, PT1 = (float(args[1]), float(args[2])) if len(args) > 2 else (129.3, 294.0)
PROTO = os.path.dirname(os.path.abspath(bpy.data.filepath))
UI = os.path.join(PROTO, "web", "ui")
sc = bpy.data.scenes["LOOP"]
if bpy.context.window: bpy.context.window.scene = sc
sc.frame_set(1)
cam = sc.camera
PX_PT = 1080 / 360                       # the 1080 px frame is the screen's 360 pt
X0, X1 = PT0 * PX_PT, PT1 * PX_PT
pair = bpy.data.objects["Swipe_Word"]; t = pair.data
# the x position is animated (it slides on ON): for this render it is pinned to frame 1's
ad = pair.animation_data
if ad and ad.action:
    for fc in list(ad.action.fcurves):
        if fc.data_path == "location": ad.action.fcurves.remove(fc)
t.body = TEXT
def box():
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get(); oe = pair.evaluated_get(dg)
    xs = []; ys = []
    for c in oe.bound_box:
        p = w2c(sc, cam, oe.matrix_world @ Vector(c)); xs.append(p.x * 1080); ys.append((1 - p.y) * 1920)
    return min(xs), max(xs), min(ys), max(ys)
a0, a1, b0, b1 = box(); print("before fit:", round(a0), round(a1), "height", round(b1 - b0))
# uniform scale (same relative spacing as SWIPE) until the width is X1 - X0
for _ in range(3):
    a0, a1, _b0, _b1 = box(); t.size *= (X1 - X0) / (a1 - a0)
# offset: the center halfway between the limits (local numeric derivative -> px)
for _ in range(4):
    a0, a1, _b0, _b1 = box(); c = (a0 + a1) / 2
    pair.location.x += 0.001; a0b, a1b, _, _ = box(); pair.location.x -= 0.001
    dpx = ((a0b + a1b) / 2 - c) / 0.001
    pair.location.x += ((X0 + X1) / 2 - c) / dpx
a0, a1, b0, b1 = box(); print("fitted: x %.1f - %.1f (limits %.1f - %.1f), height %.1f px, size %.4f, x local %.4f" % (a0, a1, X0, X1, b1 - b0, t.size, pair.location.x))
sys.stdout.flush()
# render as in tools/swiper_layers.py (the word only)
r = sc.render; r.engine = 'CYCLES'
try:
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'OPTIX'; prefs.get_devices()
    for d in prefs.devices: d.use = True
    sc.cycles.device = 'GPU'
except Exception as e: print("GPU", e)
r.resolution_x, r.resolution_y, r.resolution_percentage = 1080, 1920, 100
r.pixel_aspect_x = r.pixel_aspect_y = 1
r.film_transparent = True
sc.use_nodes = False
sc.cycles.samples = 96
r.image_settings.file_format = 'PNG'; r.image_settings.color_mode = 'RGBA'; r.image_settings.color_depth = '8'
vl = sc.view_layers[0]
lc = vl.layer_collection.children.get("UI_TOP")
if lc: lc.exclude = True
all_of = ["Swipe_Rim", "Swipe_Inner", "Swipe_Word", "Swipe_Knob", "Swipe_Knob_Rim", "Swipe_Arrow"]
for o in sc.objects:
    if o.type not in ('MESH', 'CURVE', 'FONT'): continue
    if o.name in all_of: o.hide_render = o.name != "Swipe_Word"; o.is_holdout = False
    else: o.is_holdout = True
BOX = [94, 1587, 986, 1871]            # the same crop as the other layers (web/ui/swipe.json)
x0, y0, x1, y1 = BOX
r.use_border = True; r.use_crop_to_border = True
r.border_min_x, r.border_max_x = x0 / 1080, x1 / 1080
r.border_min_y, r.border_max_y = 1 - y1 / 1920, 1 - y0 / 1920
dest = os.path.join(UI, "swipe_word.png")
copy_of = os.path.join(PROTO, "tools", "swipe_word_SWIPE.png")
if not os.path.exists(copy_of): shutil.copy2(dest, copy_of)
r.filepath = dest; bpy.ops.render.render(write_still=True)
print("DONE", dest); sys.stdout.flush()
