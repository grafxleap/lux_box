"""Swiper layers in the ON state (the light from your timeline at the end of ON: arrow emission 50.5, rims 0.558).

  blender -b luxbox_realtime.blend -P tools/swiper_layers_on.py
Writes web/ui/swipe_pill_on.png and ref/tmp/swipe_knob_on_raw.png (the knob not recentred yet).
The page cross-fades between the rest layer and this one with the knob, as in your animation (arrow 232 -> 365, rims 328 -> 367).
"""
import bpy, os, sys
import numpy as np
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view as w2c
PROTO = os.path.dirname(os.path.abspath(bpy.data.filepath))
UI = os.path.join(PROTO, "web", "ui")
TMP = os.path.join(PROTO, "tools", "tmp_on"); os.makedirs(TMP, exist_ok=True)
sc = bpy.data.scenes["LOOP"]
if bpy.context.window: bpy.context.window.scene = sc
sc.frame_set(1)
# ON state: without the curves (otherwise rendering frame 1 would put them back at rest)
for name_, do_ in (("Material.006", lambda nt: next(n for n in nt.nodes if n.type == 'EMISSION').inputs['Strength'].__setattr__('default_value', 50.5)),
                 ("Clasp_Polished_Steel.002", lambda nt: next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED').inputs['Base Color'].__setattr__('default_value', (0.558, 0.558, 0.558, 1.0)))):
    m = bpy.data.materials[name_]
    if m.node_tree.animation_data: m.node_tree.animation_data_clear()
    do_(m.node_tree)
    print("ON", name_); sys.stdout.flush()
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
def render(visible_objs, output_, box):
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
render(PILL, os.path.join(UI, "swipe_pill_on.png"), box)
render(PILL + KNOB, os.path.join(TMP, "knob_beauty.png"), box)
opaque = bpy.data.materials.new("MASK"); opaque.use_nodes = True
nt = opaque.node_tree; nt.nodes.clear()
e = nt.nodes.new("ShaderNodeEmission"); o_ = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(e.outputs[0], o_.inputs[0])
for n in KNOB:
    for s in bpy.data.objects[n].material_slots: s.material = opaque
hidden_objs = [o for o in sc.objects if o.name not in KNOB and o.name not in all_of and o.type in ('MESH', 'CURVE', 'FONT') and not o.hide_render]
for o in hidden_objs: o.hide_render = True
render(KNOB, os.path.join(TMP, "knob_mask.png"), box)
bel = bpy.data.images.load(os.path.join(TMP, "knob_beauty.png")); msk = bpy.data.images.load(os.path.join(TMP, "knob_mask.png"))
B = np.array(bel.pixels[:], np.float32).reshape(-1, 4); M = np.array(msk.pixels[:], np.float32).reshape(-1, 4)
B[:, 3] = M[:, 3]
out = bpy.data.images.new("swipe_knob_on", bel.size[0], bel.size[1], alpha=True)
out.pixels[:] = B.ravel().tolist(); out.filepath_raw = os.path.join(TMP, "swipe_knob_on_raw.png"); out.file_format = 'PNG'; out.save()
print("DONE"); sys.stdout.flush()
