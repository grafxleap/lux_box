"""Layers of the bottom swiper rendered in Cycles (frame 1, at rest) for the HTML interface.

  blender -b luxbox_realtime.blend -P tools/swiper_layers.py
Writes web/ui/swipe_pill.png, swipe_word.png, swipe_knob.png and swipe.json (positions in px of the 1080x1920 frame).
"""
import bpy, os, json, sys
import numpy as np
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view as w2c
PROTO = os.path.dirname(os.path.abspath(bpy.data.filepath))
UI = os.path.join(PROTO, "web", "ui"); os.makedirs(UI, exist_ok=True)
TMP = os.path.join(PROTO, "ref", "tmp"); os.makedirs(TMP, exist_ok=True)
sc = bpy.data.scenes["LOOP"]
if bpy.context.window: bpy.context.window.scene = sc
sc.frame_set(1)
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
cam = sc.camera
PILL = ["Swipe_Rim", "Swipe_Inner"]
WORD = ["Swipe_Word"]
KNOB = ["Swipe_Knob", "Swipe_Knob_Rim", "Swipe_Arrow"]
all_of = PILL + WORD + KNOB

def box_px(names, margin=10):
    xs, ys = [], []
    for n in names:
        o = bpy.data.objects[n]
        dg = bpy.context.evaluated_depsgraph_get()
        oe = o.evaluated_get(dg)
        for c in oe.bound_box:
            p = w2c(sc, cam, oe.matrix_world @ Vector(c))
            xs.append(p.x * 1080); ys.append((1 - p.y) * 1920)
    return [int(max(0, min(xs) - margin)), int(max(0, min(ys) - margin)), int(min(1080, max(xs) + margin)), int(min(1920, max(ys) + margin))]

def center_px(n):
    o = bpy.data.objects[n]; p = w2c(sc, cam, o.matrix_world.translation)
    return [p.x * 1080, (1 - p.y) * 1920]

def render(visible_objs, output_, box):
    # the rest of the scene stays (the metal reflects and lights it) but is not drawn: holdout
    # the swiper's other parts are hidden (as holdout they would punch a hole in their own shape)
    for o in sc.objects:
        if o.type not in ('MESH', 'CURVE', 'FONT'): continue
        if o.name in all_of:
            o.hide_render = o.name not in visible_objs; o.is_holdout = False
        else:
            o.is_holdout = True
    x0, y0, x1, y1 = box
    r.use_border = True; r.use_crop_to_border = True
    r.border_min_x, r.border_max_x = x0 / 1080, x1 / 1080
    r.border_min_y, r.border_max_y = 1 - y1 / 1920, 1 - y0 / 1920
    r.filepath = output_; bpy.ops.render.render(write_still=True)

box = box_px(all_of, 16)
print("swiper box px", box); sys.stdout.flush()
# 1) pill alone
render(PILL, os.path.join(UI, "swipe_pill.png"), box)
# 2) word alone
render(WORD, os.path.join(UI, "swipe_word.png"), box)
# 3) knob: beauty pass (with the pill behind it for the glass) + mask (the opaque knob) -> alpha
render(PILL + KNOB, os.path.join(TMP, "knob_beauty.png"), box)
opaque = bpy.data.materials.new("MASK"); opaque.use_nodes = True
nt = opaque.node_tree; nt.nodes.clear()
e = nt.nodes.new("ShaderNodeEmission"); o_ = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(e.outputs[0], o_.inputs[0])
guard = {}
for n in KNOB:
    ob = bpy.data.objects[n]; guard[n] = [s.material for s in ob.material_slots]
    for s in ob.material_slots: s.material = opaque
hidden_objs = [o for o in sc.objects if o.name not in KNOB and o.name not in all_of and o.type in ('MESH', 'CURVE', 'FONT') and not o.hide_render]
for o in hidden_objs: o.hide_render = True
render(KNOB, os.path.join(TMP, "knob_mask.png"), box)
for o in hidden_objs: o.hide_render = False
for n, ms in guard.items():
    for s, m in zip(bpy.data.objects[n].material_slots, ms): s.material = m
bel = bpy.data.images.load(os.path.join(TMP, "knob_beauty.png")); msk = bpy.data.images.load(os.path.join(TMP, "knob_mask.png"))
B = np.array(bel.pixels[:], np.float32).reshape(-1, 4); M = np.array(msk.pixels[:], np.float32).reshape(-1, 4)
B[:, 3] = M[:, 3]
out = bpy.data.images.new("swipe_knob", bel.size[0], bel.size[1], alpha=True)
out.pixels[:] = B.ravel().tolist(); out.filepath_raw = os.path.join(UI, "swipe_knob.png"); out.file_format = 'PNG'; out.save()

# positions: knob on the left (rest) and on the right (ON), word before and after ON
knob = bpy.data.objects["Swipe_Knob"]; pair = bpy.data.objects["Swipe_Word"]
left = center_px("Swipe_Knob"); x0 = knob.location.x
knob.location.x = 0.2161; bpy.context.view_layer.update(); right = center_px("Swipe_Knob"); knob.location.x = x0
p0 = center_px("Swipe_Word"); px0 = pair.location.x
pair.location.x = -0.1196; bpy.context.view_layer.update(); p1 = center_px("Swipe_Word"); pair.location.x = px0
info = {"frame": [1080, 1920], "box": box, "knob_left": left, "knob_right": right,
        "word_start": p0, "word_on": p1}
json.dump(info, open(os.path.join(UI, "swipe.json"), "w"), indent=1)
print("INFO", json.dumps(info))
