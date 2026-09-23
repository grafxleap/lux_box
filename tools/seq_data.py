"""Frame-by-frame data of the sequence (290 -> 1400) for version B (all in real time).

  blender -b luxbox_realtime.blend -P tools/seq_data.py
Writes web/seq/data.json: matrices (already in three.js coordinates) of the camera, the watch, the base and the lid
of box .008, the camera's vertical angle and your timeline's curves (Reveal, Appear, UI opacities).
"""
import bpy, os, json, math
from mathutils import Matrix
PROTO = os.path.dirname(os.path.abspath(bpy.data.filepath))
OUT = os.path.join(PROTO, "web", "seq"); os.makedirs(OUT, exist_ok=True)
sc = bpy.data.scenes["LOOP"]
if bpy.context.window: bpy.context.window.scene = sc
F0, F1 = 290, 1400
# Blender (Z up) -> three.js (Y up): (x, y, z) -> (x, z, -y)
C = Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, -1, 0, 0), (0, 0, 0, 1)))
Ci = C.inverted()
def m3(M, camera=False):
    # meshes: the local axes are converted too (the glTF exporter rotates the vertices);
    # camera: Blender and three.js both look down -Z with +Y up, so only the world is converted
    T = (C @ M) if camera else (C @ M @ Ci)
    return [round(T[r][c], 6) for c in range(4) for r in range(4)]   # column-major, like Matrix4.fromArray
cam = sc.camera
watch_ = bpy.data.objects["Watch.001"]
base = bpy.data.objects["MASTER_Base.008"]; lid = bpy.data.objects["MASTER_Lid.008"]
ctrl = {n: bpy.data.objects.get(n) for n in ("UI_Header", "UI_Recents", "UI_Back", "UI_Info")}
circle = bpy.data.objects["Circle"]
# interior light of box .008 (the closest one to the base)
light = min((o for o in sc.objects if o.type == "LIGHT"), key=lambda o: (o.matrix_world.translation - base.matrix_world.translation).length)
lining = next(n for n in bpy.data.materials["Material.013"].node_tree.nodes if n.type == "BSDF_PRINCIPLED")
print("interior light:", light.name)
res_x, res_y = sc.render.resolution_x, sc.render.resolution_y
fr = []
for f in range(F0, F1 + 1):
    sc.frame_set(f)
    cd = cam.data
    # vertical angle (AUTO fit in portrait: the large sensor goes on the height)
    vfov = 2 * math.atan((cd.sensor_width / 2) / cd.lens)
    d = {"f": f, "cam": m3(cam.matrix_world, camera=True), "vfov": round(math.degrees(vfov), 5),
         "watch": m3(watch_.matrix_world), "base": m3(base.matrix_world), "lid": m3(lid.matrix_world),
         "reveal": round(watch_["Reveal"], 5), "appear": round(watch_["Appear silhouette"], 5)}
    for n, o in ctrl.items():
        if o is not None: d[n] = round(o["Opacity"], 4)
    d["circle"] = m3(circle.matrix_world)
    d["light"] = [round(c, 5) for c in (C @ light.matrix_world.translation)]
    d["light_w"] = round(light.data.energy * 2 ** light.data.exposure, 4)          # effective watts
    d["lining"] = round(lining.inputs["Base Color"].default_value[0], 4)           # 1 white -> 0.01 black
    d["lining_spec"] = round(lining.inputs["Specular IOR Level"].default_value, 4)
    fr.append(d)
m = bpy.data.materials["Watch_Silhouette"].node_tree
info = {"fps": sc.render.fps / sc.render.fps_base, "f0": F0, "f1": F1, "wait": 929,
        "light_radius": light.data.shadow_soft_size, "base8": m3(base.matrix_world),
        "silhouette_color": list(next(n for n in m.nodes if n.type == 'RGB').outputs[0].default_value)[:3],
        "max_blur": m.nodes["blur maxim"].outputs[0].default_value,
        "brightness": m.nodes["brightness"].outputs[0].default_value,
        "watch_mesh": [[round(c, 6) for c in (v.co.x, v.co.z, -v.co.y)] for v in watch_.data.vertices],
        "watch_uv": [[round(c, 6) for c in l.uv] for l in watch_.data.uv_layers.active.data],
        "watch_faces": [list(p.vertices) for p in watch_.data.polygons],
        "frames": fr}
json.dump(info, open(os.path.join(OUT, "data.json"), "w"), separators=(",", ":"))
print("DATA", len(fr), "frames ->", os.path.getsize(os.path.join(OUT, "data.json")) // 1024, "KB")
