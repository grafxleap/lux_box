"""Compares in Cycles the box lit by the real lights vs by emissive spheres (the ones in the environment map)."""
import bpy, os, math, sys
PROTO = os.path.dirname(os.path.abspath(bpy.data.filepath)); REF = os.path.join(PROTO, "ref")
sc = bpy.data.scenes["LOOP"]; sc.frame_set(1)
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
r.resolution_x, r.resolution_y, r.resolution_percentage = 1080, 1920, 25
sc.cycles.samples = 128; sc.use_nodes = False
r.image_settings.file_format = 'PNG'
lights = [o for o in sc.objects if o.type == 'LIGHT' and not o.hide_render]
external = []
for o in lights:
    L = o.data; P = L.energy * (2 ** getattr(L, 'exposure', 0.0))
    inside = any((o.matrix_world.translation - c.matrix_world.translation).length < 1.2 for c in sc.objects if c.name.startswith("MASTER_Base."))
    if P > 0 and not inside: external.append((o, P, max(L.shadow_soft_size, 0.05)))
import os.path as _p
if not _p.exists(os.path.join(REF, "cal_lights.png")):
    r.filepath = os.path.join(REF, "cal_lights.png"); bpy.ops.render.render(write_still=True)
for o, P, radius_ in external:
    o.hide_render = True
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius_, location=o.matrix_world.translation, segments=32, ring_count=16)
    e = bpy.context.active_object
    m = bpy.data.materials.new("E"); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    em = nt.nodes.new("ShaderNodeEmission"); em.inputs['Strength'].default_value = P / (4 * math.pi * math.pi * radius_ * radius_)
    out = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(em.outputs[0], out.inputs[0]); e.data.materials.append(m)
    e.visible_camera = False
    ll, le = o.light_linking, e.light_linking
    le.receiver_collection = ll.receiver_collection; le.blocker_collection = ll.blocker_collection
    # the same light linking as the light (the wall gets no light from these)
    print("emitter for", o.name, "P", round(P, 1), "radius_", radius_)
r.filepath = os.path.join(REF, "cal_spheres.png"); bpy.ops.render.render(write_still=True)
print("DONE")
