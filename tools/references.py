"""References for the web prototype: Cycles render of frame 1 (no UI) and 360 environment map.

  blender -b luxbox_realtime.blend -P tools/references.py
"""
import bpy, os, math, sys
from mathutils import Vector
PROTO = os.path.dirname(os.path.abspath(bpy.data.filepath))
REF = os.path.join(PROTO, "ref"); WEB = os.path.join(PROTO, "web")
os.makedirs(REF, exist_ok=True)
sc = bpy.data.scenes["LOOP"]
if bpy.context.window: bpy.context.window.scene = sc
sc.frame_set(1)
vl = sc.view_layers[0]
for name_ in ("UI_TOP", "SWIPER"):
    lc = vl.layer_collection.children.get(name_)
    if lc: lc.exclude = True
r = sc.render
r.engine = 'CYCLES'
try:
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'OPTIX'; prefs.get_devices()
    for d in prefs.devices: d.use = True
    sc.cycles.device = 'GPU'
except Exception as e:
    print("GPU:", e)
r.use_border = False; r.pixel_aspect_x = r.pixel_aspect_y = 1
r.image_settings.file_format = 'PNG'; r.image_settings.color_mode = 'RGB'

# 1) frame 1 reference, 540x960
r.resolution_x, r.resolution_y, r.resolution_percentage = 1080, 1920, 50
sc.cycles.samples = 64
r.filepath = os.path.join(REF, "ref_f1.png")
bpy.ops.render.render(write_still=True)
print("REF ->", r.filepath); sys.stdout.flush()

# 2) equirectangular environment from box .001 (without the box itself), oriented as three.js expects
# A camera does not see Cycles' point lights; for the metal reflections we put emissive spheres there
# of the same power and radius, visible to the camera only (they do not light the scene twice).
for o in [o for o in sc.objects if o.type == 'LIGHT' and not o.hide_render]:
    L = o.data
    P = L.energy * (2 ** getattr(L, 'exposure', 0.0))
    if P <= 0: continue
    inside = any((o.matrix_world.translation - c.matrix_world.translation).length < 1.2
               for c in sc.objects if c.name.startswith("MASTER_Base."))
    if inside: continue          # interior lights: inside closed boxes, they are not visible
    radius_ = max(L.shadow_soft_size, 0.05)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius_, location=o.matrix_world.translation, segments=24, ring_count=12)
    sph = bpy.context.active_object; sph.name = "EMISSOR_" + o.name
    m = bpy.data.materials.new(sph.name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    em = nt.nodes.new("ShaderNodeEmission"); em.inputs['Strength'].default_value = P / (4 * math.pi * math.pi * radius_ * radius_)
    out = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(em.outputs[0], out.inputs[0])
    sph.data.materials.append(m)
    sph.visible_diffuse = sph.visible_glossy = sph.visible_transmission = sph.visible_volume_scatter = sph.visible_shadow = False
    print("emitter", sph.name, "P", round(P, 1), "W r", round(radius_, 2), "strength", round(P / (4 * math.pi * math.pi * radius_ * radius_), 3))
box = bpy.data.objects["MASTER_Base.001"]
hidden_objs = [box] + list(box.children_recursive)
for o in hidden_objs: o.hide_render = True
cd = bpy.data.cameras.new("Cam_Entorn"); cd.type = 'PANO'
try:
    cd.panorama_type = 'EQUIRECTANGULAR'
except AttributeError:
    cd.cycles.panorama_type = 'EQUIRECTANGULAR'
co = bpy.data.objects.new("Cam_Entorn", cd); sc.collection.objects.link(co)
co.location = box.matrix_world.translation + Vector((0, 0, 0.5))
co.rotation_euler = (math.radians(90), 0, math.radians(-90))   # image center = Blender's +X = three.js's +X
sc.camera = co
r.resolution_x, r.resolution_y, r.resolution_percentage = 1024, 512, 100
sc.cycles.samples = 128
sc.use_nodes = False    # no glare in the environment map
r.image_settings.file_format = 'HDR'
r.filepath = os.path.join(WEB, "env.hdr")
bpy.ops.render.render(write_still=True)
print("ENV ->", r.filepath, os.path.getsize(r.filepath) // 1024, "KB")

# 3) fixed backdrop (wall + floor, no boxes) from the frame 1 camera, in linear (HDR).
#    Wall, lights and camera hang from Circle: the backdrop looks the same for every box.
#    Taller than 9:16 (9:20) keeping the horizontal angle, to cover long phones.
import bpy as _b
for o in list(sc.objects):
    if o.name.startswith("EMISSOR_") or o.name == "Cam_Entorn":
        _b.data.objects.remove(o, do_unlink=True)
cam = _b.data.objects["Camera.001"]; sc.camera = cam
for o in sc.objects:
    n = o.name
    if n.startswith(("MASTER_", "Logo_", "Icosphere", "Watch", "Reflex_")) or (o.parent and o.parent.name.startswith("MASTER_")):
        o.hide_render = True
cd = cam.data
cd.sensor_fit = 'HORIZONTAL'; cd.sensor_width = 36.0 * 1080 / 1920
r.resolution_x, r.resolution_y, r.resolution_percentage = 540, 1200, 100
sc.cycles.samples = 256
sc.use_nodes = False
r.image_settings.file_format = 'HDR'
r.filepath = os.path.join(WEB, "backdrop.hdr")
_b.ops.render.render(write_still=True)
print("BACKDROP ->", r.filepath, os.path.getsize(r.filepath) // 1024, "KB")
