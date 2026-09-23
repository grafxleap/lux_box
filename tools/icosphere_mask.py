"""Icosphere mask on the environment map: the same equirectangular camera as tools/references.py (from
box .001, frame 1), with the Icosphere alone in white. Used to erase it from web/env.hdr (tools/remove_env_icosphere.py).

  blender -b luxbox_realtime.blend -P tools/icosphere_mask.py
"""
import bpy, os, math, sys
from mathutils import Vector
PROTO = os.path.dirname(os.path.abspath(bpy.data.filepath))
TMP = os.path.join(PROTO, "tools", "tmp_icosfera"); os.makedirs(TMP, exist_ok=True)
sc = bpy.data.scenes["LOOP"]
if bpy.context.window: bpy.context.window.scene = sc
sc.frame_set(1)
ico = bpy.data.objects["Icosphere"]
print("icosphere frame 1:", tuple(round(x, 3) for x in ico.matrix_world.translation), "scale", tuple(round(x, 3) for x in ico.scale))
for o in sc.objects:
    if o.type in ('MESH', 'CURVE', 'FONT', 'SURFACE', 'META') and o is not ico: o.hide_render = True
m = bpy.data.materials.new("MASK"); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
e = nt.nodes.new("ShaderNodeEmission"); e.inputs['Strength'].default_value = 1.0
o_ = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(e.outputs[0], o_.inputs[0])
for s in ico.material_slots: s.material = m
if sc.world:
    sc.world.use_nodes = True
    for n in sc.world.node_tree.nodes:
        if n.type == 'BACKGROUND': n.inputs['Strength'].default_value = 0.0
r = sc.render; r.engine = 'CYCLES'
try:
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'OPTIX'; prefs.get_devices()
    for d in prefs.devices: d.use = True
    sc.cycles.device = 'GPU'
except Exception as ex: print("GPU", ex)
box = bpy.data.objects["MASTER_Base.001"]
cd = bpy.data.cameras.new("Cam_Entorn"); cd.type = 'PANO'
try:
    cd.panorama_type = 'EQUIRECTANGULAR'
except AttributeError:
    cd.cycles.panorama_type = 'EQUIRECTANGULAR'
co = bpy.data.objects.new("Cam_Entorn", cd); sc.collection.objects.link(co)
co.location = box.matrix_world.translation + Vector((0, 0, 0.5))
co.rotation_euler = (math.radians(90), 0, math.radians(-90))
sc.camera = co
r.resolution_x, r.resolution_y, r.resolution_percentage = 1024, 512, 100
r.use_border = False; r.pixel_aspect_x = r.pixel_aspect_y = 1
sc.cycles.samples = 16; sc.cycles.use_denoising = False
sc.use_nodes = False
r.film_transparent = True
r.image_settings.file_format = 'PNG'; r.image_settings.color_mode = 'RGBA'
r.filepath = os.path.join(TMP, "mask.png")
bpy.ops.render.render(write_still=True)
print("DONE", r.filepath); sys.stdout.flush()
