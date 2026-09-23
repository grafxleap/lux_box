"""Wall AO WITHOUT the boxes (the background's depth, with none of the boxes' contact shadows).
Only the boxes are hidden: the rest of the scene still plays its part.

  blender -b luxbox_realtime_baked.blend -P tools/bake_wall_ao.py
The first bake carried the boxes' shadows where they sat in Blender; the wall turns with the camera and those shadows
stayed still on screen. Here everything but the wall is hidden. Writes web/Wall_ao.png (same UVs as the GLB's wall).
"""
import bpy, os, sys, time
PROTO = os.path.dirname(os.path.abspath(bpy.data.filepath))
WEB = os.path.join(PROTO, "web")
sc = bpy.data.scenes["LOOP"] if "LOOP" in bpy.data.scenes else bpy.context.scene
if bpy.context.window: bpy.context.window.scene = sc
sc.frame_set(1)
wall = sc.objects["Wall_Frosted_Glass"]
# only the boxes (and their parts) are hidden; the rest of the scene still casts its shadow
for o in sc.objects:
    if o.name.startswith(("MASTER_", "Logo", "Clasp")) or any(o.name.startswith(k) for k in ("Box",)):
        o.hide_render = True
print("visible:", [o.name for o in sc.objects if not o.hide_render and o.type in ('MESH', 'CURVE', 'FONT')])
sc.render.engine = 'CYCLES'
try:
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'OPTIX'; prefs.get_devices()
    for d in prefs.devices: d.use = True
    sc.cycles.device = 'GPU'
except Exception as e: print("GPU", e)
sc.cycles.samples = 64
im = bpy.data.images.new("Wall_ao_clean", 2048, 2048, alpha=False, float_buffer=False)
im.colorspace_settings.name = "Non-Color"
mats = [s.material for s in wall.material_slots if s.material]
nodes = []
for m in mats:
    n = m.node_tree.nodes.new("ShaderNodeTexImage"); n.image = im; m.node_tree.nodes.active = n; nodes.append((m, n))
for o in bpy.context.view_layer.objects: o.select_set(False)
bpy.context.view_layer.objects.active = wall; wall.select_set(True)
t0 = time.time()
bpy.ops.object.bake(type='AO', margin=8, use_clear=True)
print("bake AO %.1fs" % (time.time() - t0))
for m, n in nodes: m.node_tree.nodes.remove(n)
im.filepath_raw = os.path.join(WEB, "Wall_ao.png"); im.file_format = 'PNG'; im.save()
print("DONE", im.filepath_raw); sys.stdout.flush()
