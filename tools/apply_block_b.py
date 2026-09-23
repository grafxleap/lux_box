"""Replaces version A's sequence block with version B's (tools/block_b.js) in web/index.html."""
import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "web", "index.html")
s = open(p, encoding="utf-8").read()
start_ = s.index("// =====================================================================================\n// VERSIO A")
end = s.index("</script>\n</body>")
b = open(os.path.join(ROOT, "tools", "block_b.js"), encoding="utf-8").read()
s = s[:start_] + b + s[end:]
old = """if (wall) wall.traverse(o => { if (o.isMesh) {
  o.material = new THREE.MeshBasicMaterial({ colorWrite: false, depthWrite: true, side: THREE.DoubleSide });
  o.renderOrder = -1;
} });"""
new = """if (wall) wall.traverse(o => { if (o.isMesh) {
  o.userData.matOriginal = o.material;
  o.material = o.userData.matHider = new THREE.MeshBasicMaterial({ colorWrite: false, depthWrite: true, side: THREE.DoubleSide });
  o.renderOrder = -1;
} });"""
assert old in s
s = s.replace(old, new)
open(p, "w", encoding="utf-8").write(s)
print("ok", len(s))
