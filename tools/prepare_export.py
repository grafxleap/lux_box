"""Prepares the frozen copy for the web prototype (step 1: carousel).

It runs in a background Blender, never on the working file:
  blender -b luxbox_realtime.blend -P tools/prepare_export.py

It does: strips what step 1 does not need, applies modifiers, unwraps UVs,
bakes the procedural materials into standard PBR textures (colour, roughness,
metallic, normal, occlusion) and exports web/luxbox.glb.
"""
import bpy, bmesh, os, sys, time

PROTO = os.path.dirname(os.path.abspath(bpy.data.filepath))
TEX = os.path.join(PROTO, "bake")
WEB = os.path.join(PROTO, "web")
os.makedirs(TEX, exist_ok=True); os.makedirs(WEB, exist_ok=True)
T0 = time.time()
def log(*a):
    print("[%5.1fs]" % (time.time() - T0), *a); sys.stdout.flush()

sc = bpy.data.scenes["LOOP"]
if bpy.context.window: bpy.context.window.scene = sc
for s in list(bpy.data.scenes):
    if s != sc: bpy.data.scenes.remove(s)
sc.frame_set(1)

# ---------- 1. cleanup ----------
out_prefix = ("UI_", "Swipe", "SWIPER", "Index", "Reflex_", "Watch")
delete_objs = [o for o in sc.objects if o.name.startswith(out_prefix) or o.hide_render
            or o.name in ("MASTER_Base", "Circle.001")]
for o in delete_objs:
    bpy.data.objects.remove(o, do_unlink=True)
log("deleted", len(delete_objs), "objects_")

# subdivisions at render level (2 max): at viewport level the wall is 1.7 M vertices
for o in sc.objects:
    for m in getattr(o, "modifiers", []):
        if m.type == 'SUBSURF':
            m.levels = min(m.render_levels, 2)
log("subdivisions a level de render")

# ---------- 2. render / bake ----------
sc.render.engine = 'CYCLES'
try:
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'OPTIX'; prefs.get_devices()
    for d in prefs.devices: d.use = True
    sc.cycles.device = 'GPU'
except Exception as e:
    log("GPU no available:", e)
sc.cycles.samples = 16
sc.render.bake.margin = 8

def final_mesh(ob, name_):
    """New mesh with the modifiers applied (curves and text included)."""
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
    me.name = name_
    return me

def unwrap_uv(me, obj_name):
    tmp = bpy.data.objects.new(obj_name, me); sc.collection.objects.link(tmp)
    for o in bpy.context.view_layer.objects: o.select_set(False)
    bpy.context.view_layer.objects.active = tmp; tmp.select_set(True)
    while me.uv_layers: me.uv_layers.remove(me.uv_layers[0])
    me.uv_layers.new(name="UVMap")
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.004)
    bpy.ops.object.mode_set(mode='OBJECT')
    return tmp

def copy_tree(nt):
    """Copies the tree and the groups inside it (so they can be changed without touching the original)."""
    for n in nt.nodes:
        if n.type == 'GROUP' and n.node_tree:
            n.node_tree = n.node_tree.copy(); copy_tree(n.node_tree)

def material_channel(m, channel):
    """Copy of the material where every BSDF is replaced by an emission carrying the channel's value."""
    c = m.copy(); c.name = m.name + "__" + channel; copy_tree(c.node_tree)
    def make(nt):
        for n in list(nt.nodes):
            if n.type == 'GROUP' and n.node_tree: make(n.node_tree); continue
            if n.type not in ('BSDF_PRINCIPLED', 'BSDF_GLASS', 'BSDF_DIFFUSE', 'BSDF_GLOSSY', 'EMISSION', 'BSDF_TRANSPARENT'): continue
            e = nt.nodes.new("ShaderNodeEmission"); e.location = n.location; e.inputs['Strength'].default_value = 1.0
            name_ = {"base": "Base Color", "rough": "Roughness", "metal": "Metallic"}[channel]
            if n.type != 'BSDF_PRINCIPLED':
                name_ = {"base": "Color", "rough": "Roughness", "metal": None}[channel]
            src = n.inputs.get(name_) if name_ else None
            if src is not None and src.is_linked:
                nt.links.new(src.links[0].from_socket, e.inputs['Color'])
            else:
                if src is None: v = 0.0 if channel == "metal" else 0.5
                else: v = src.default_value
                if isinstance(v, float): e.inputs['Color'].default_value = (v, v, v, 1)
                else: e.inputs['Color'].default_value = tuple(v)
            outs = [l.to_socket for l in n.outputs[0].links]
            nt.nodes.remove(n)
            for s in outs: nt.links.new(e.outputs[0], s)
    make(c.node_tree)
    return c

def image_(name_, size, data):
    im = bpy.data.images.get(name_)
    if im: bpy.data.images.remove(im)
    im = bpy.data.images.new(name_, size, size, alpha=False, float_buffer=False)
    im.colorspace_settings.name = "Non-Color" if data else "sRGB"
    return im

def bake(ob, name_, size):
    """Bakes base, roughness, metallic, normal and occlusion of an object (with its materials)."""
    mats = [s.material for s in ob.material_slots]
    res = {}
    for channel, kind, data in (("base", 'EMIT', False), ("rough", 'EMIT', True), ("metal", 'EMIT', True),
                                ("normal", 'NORMAL', True), ("ao", 'AO', True)):
        im = image_("%s_%s" % (name_, channel), size, data)
        used = []
        for i, m in enumerate(mats):
            mm = material_channel(m, channel) if kind == 'EMIT' else m
            ob.material_slots[i].material = mm; used.append(mm)
            n = mm.node_tree.nodes.new("ShaderNodeTexImage"); n.image = im; n.name = "__bake"
            mm.node_tree.nodes.active = n
        for o in bpy.context.view_layer.objects: o.select_set(False)
        bpy.context.view_layer.objects.active = ob; ob.select_set(True)
        kw = dict(type=kind, margin=8, use_clear=True)
        if kind == 'NORMAL': kw.update(normal_space='TANGENT')
        sc.cycles.samples = 64 if kind == 'AO' else 4
        bpy.ops.object.bake(**kw)
        for i, m in enumerate(mats):
            ob.material_slots[i].material = m
            n = m.node_tree.nodes.get("__bake")
            if n: m.node_tree.nodes.remove(n)
        for mm in used:
            if mm not in mats: bpy.data.materials.remove(mm)
        im.filepath_raw = os.path.join(TEX, im.name + ".png"); im.file_format = 'PNG'; im.save()
        res[channel] = im
        log("  bake", name_, channel, "done")
    return res

def bake_mask(ob, name_, size, emitters, suffix="emission"):
    """White mask where the 'emitter' materials are (the seam's silver), black everywhere else."""
    mats = [s.material for s in ob.material_slots]
    im = image_(name_ + "_" + suffix, size, True)
    times = []
    for i, m in enumerate(mats):
        t = bpy.data.materials.new(name_ + "_msk_%d" % i); t.use_nodes = True; nt = t.node_tree; nt.nodes.clear()
        e = nt.nodes.new("ShaderNodeEmission"); v = 1.0 if (m and m.name in emitters) else 0.0
        e.inputs['Color'].default_value = (v, v, v, 1); o = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(e.outputs[0], o.inputs[0])
        n = nt.nodes.new("ShaderNodeTexImage"); n.image = im; nt.nodes.active = n
        ob.material_slots[i].material = t; times.append(t)
    for o in bpy.context.view_layer.objects: o.select_set(False)
    bpy.context.view_layer.objects.active = ob; ob.select_set(True)
    sc.cycles.samples = 1
    bpy.ops.object.bake(type='EMIT', margin=4, use_clear=True)
    for i, m in enumerate(mats): ob.material_slots[i].material = m
    for t in times: bpy.data.materials.remove(t)
    for dest in (os.path.join(TEX, im.name + ".png"), os.path.join(WEB, im.name + ".png")):
        im.filepath_raw = dest; im.file_format = 'PNG'; im.save()
    log("  mask", name_, "->", emitters)

def material_pbr(name_, t):
    """Standard PBR material that the glTF exporter understands directly."""
    m = bpy.data.materials.new(name_); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bs.outputs[0], out.inputs[0])
    def tex(im, x, y):
        n = nt.nodes.new("ShaderNodeTexImage"); n.image = im; n.location = (x, y); return n
    b = tex(t["base"], -700, 300); nt.links.new(b.outputs['Color'], bs.inputs['Base Color'])
    # metallicRoughness: G = roughness, B = metallic (the glTF layout)
    orm = image_(name_ + "_orm", t["rough"].size[0], True)
    import numpy as np
    R = np.array(t["ao"].pixels[:]).reshape(-1, 4); G = np.array(t["rough"].pixels[:]).reshape(-1, 4); B = np.array(t["metal"].pixels[:]).reshape(-1, 4)
    O = np.stack([R[:, 0], G[:, 0], B[:, 0], np.ones(len(R))], axis=1)
    orm.pixels[:] = O.ravel().tolist(); orm.filepath_raw = os.path.join(TEX, orm.name + ".png"); orm.file_format = 'PNG'; orm.save()
    o = tex(orm, -700, 0)
    sep = nt.nodes.new("ShaderNodeSeparateColor"); sep.location = (-400, 0)
    nt.links.new(o.outputs['Color'], sep.inputs[0])
    nt.links.new(sep.outputs['Green'], bs.inputs['Roughness']); nt.links.new(sep.outputs['Blue'], bs.inputs['Metallic'])
    nm = tex(t["normal"], -700, -300); nmap = nt.nodes.new("ShaderNodeNormalMap"); nmap.location = (-400, -300)
    nt.links.new(nm.outputs['Color'], nmap.inputs['Color']); nt.links.new(nmap.outputs['Normal'], bs.inputs['Normal'])
    # occlusion: the group the glTF exporter recognises
    g = bpy.data.node_groups.get("glTF Material Output")
    if not g:
        g = bpy.data.node_groups.new("glTF Material Output", 'ShaderNodeTree')
        g.interface.new_socket("Occlusion", in_out='INPUT', socket_type='NodeSocketFloat')
    gn = nt.nodes.new("ShaderNodeGroup"); gn.node_tree = g; gn.location = (0, -300)
    nt.links.new(sep.outputs['Red'], gn.inputs['Occlusion'])
    return m

# ---------- 3. box: base and lid (mesh shared by the 8) ----------
def prepare_shared(objs, name_, size):
    model = objs[0]
    me = final_mesh(model, name_ + "_mesh")
    tmp = unwrap_uv(me, name_ + "_bake")
    for i, s in enumerate(model.material_slots):
        if i < len(tmp.material_slots): tmp.material_slots[i].material = s.material
        else: tmp.data.materials.append(s.material)
    t = bake(tmp, name_, size)
    if name_ == "Box_Base": bake_mask(tmp, name_, 1024, {"Silver_Edge"})
    # version B: lining mask (Material.013), to darken it as in the timeline
    bake_mask(tmp, name_, 1024, {"Material.013", "Material.013_LOOP"}, "lining")
    pbr = material_pbr(name_, t)
    me.materials.clear(); me.materials.append(pbr)
    for p in me.polygons: p.material_index = 0
    for o in objs:
        o.modifiers.clear(); o.data = me
    bpy.data.objects.remove(tmp, do_unlink=True)
    log(name_, ": mesh", len(me.vertices), "verts, shared by", len(objs), "objects_")

bases = [o for o in sc.objects if o.name.startswith("MASTER_Base.")]
lids = [o for o in sc.objects if o.name.startswith("MASTER_Lid.")]
prepare_shared(bases, "Box_Base", 2048)
prepare_shared(lids, "Box_Lid", 2048)

# logos (text -> mesh, a flat silver material, as they look)
# identical logos share a single mesh, at a lower curve resolution
silver = bpy.data.materials["Silver_Edge"]
shared_ones = {}
for o in [o for o in sc.objects if o.type == 'FONT']:
    cu = o.data
    cu.resolution_u = min(cu.resolution_u, 4); cu.bevel_resolution = min(cu.bevel_resolution, 1)
    key = (cu.body, cu.font.name if cu.font else "", round(cu.size, 5), round(cu.extrude, 5), round(cu.bevel_depth, 5), round(cu.space_character, 3))
    if key not in shared_ones:
        shared_ones[key] = final_mesh(o, "Logo_mesh_%d" % len(shared_ones))
    me = shared_ones[key]
    ob = bpy.data.objects.new(o.name, me); sc.collection.objects.link(ob)
    ob.parent = o.parent; ob.matrix_parent_inverse = o.matrix_parent_inverse.copy(); ob.matrix_basis = o.matrix_basis.copy()
    if not me.materials or me.materials[0] != silver:
        me.materials.clear(); me.materials.append(silver)
    name_ = o.name; bpy.data.objects.remove(o, do_unlink=True); ob.name = name_
log("logos converted a mesh:", len(shared_ones), "meshes shared_ones", [ (k[0], len(v.vertices)) for k, v in shared_ones.items()])

# wall / floor
wall = sc.objects.get("Wall_Frosted_Glass")
if wall:
    me = final_mesh(wall, "Wall_mesh")
    mats = [s.material for s in wall.material_slots]
    tmp = unwrap_uv(me, "Wall_bake")
    for i, m in enumerate(mats):
        if i < len(tmp.material_slots): tmp.material_slots[i].material = m
        else: tmp.data.materials.append(m)
    t = bake(tmp, "Wall", 2048)
    pbr = material_pbr("Wall", t)
    me.materials.clear(); me.materials.append(pbr)
    for p in me.polygons: p.material_index = 0
    wall.modifiers.clear(); wall.data = me
    bpy.data.objects.remove(tmp, do_unlink=True)
    log("wall baked")

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(PROTO, "luxbox_realtime_baked.blend"), compress=True)
log("saved luxbox_realtime_baked.blend")

# ---------- 4. export ----------

for o in bpy.context.view_layer.objects: o.select_set(False)
bpy.ops.export_scene.gltf(filepath=os.path.join(WEB, "luxbox.glb"), export_format='GLB',
                          export_apply=True, export_animations=False, export_cameras=True,
                          export_lights=True, export_yup=True, export_image_format='WEBP', export_image_quality=90)
log("exported", os.path.join(WEB, "luxbox.glb"), os.path.getsize(os.path.join(WEB, "luxbox.glb")) // 1024, "KB")
