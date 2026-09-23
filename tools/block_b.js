// =====================================================================================
// VERSION B: the whole sequence in real time. The data from your timeline (camera, circle,
// lid, watch, interior light and lining) is played back relative to the centred box.
// =====================================================================================
const eBack = document.getElementById('back'), eInfo = document.getElementById('info'), eCont = document.getElementById('continueBtn');
// per-user data (by URL in the prototype; in the app it will come from their own data)
for (const [id, key] of [['info-mark', 'mark'], ['info-model', 'model'], ['info-price', 'price']])
  if (P.get(key)) document.getElementById(id).textContent = P.get(key);
const [data, watchPhoto, mLiningBase, mLiningLid] = await Promise.all([
  fetch('seq/data.json').then(r => r.json()),
  new THREE.TextureLoader().loadAsync(P.get('watch') || 'watch/watch-front.png'),
  new THREE.TextureLoader().loadAsync('Box_Base_lining.png'),
  new THREE.TextureLoader().loadAsync('Box_Lid_lining.png'),
]);
watchPhoto.colorSpace = THREE.SRGBColorSpace; watchPhoto.wrapS = watchPhoto.wrapT = THREE.ClampToEdgeWrapping;
for (const t of [mLiningBase, mLiningLid]) { t.flipY = false; t.colorSpace = THREE.NoColorSpace; }
const FPS = data.fps, F0 = data.f0, F1 = data.f1, WAIT = data.wait;
const dataAt = f => data.frames[THREE.MathUtils.clamp(Math.round(f) - F0, 0, data.frames.length - 1)];
const INNER_LIGHT = parseFloat(P.get('inner_light') ?? 1.0);   // interior light calibration (watts -> three.js)

// lining (Material.013): it darkens and loses its sheen as in your timeline; material shared by the 8 boxes
const uLining = { value: 1 }, uLiningSpec = { value: 1 };
function injectLining(mat, mask) {
  mat.onBeforeCompile = sh => {
    sh.uniforms.liningMask = { value: mask }; sh.uniforms.uLining = uLining; sh.uniforms.uLiningSpec = uLiningSpec;
    sh.fragmentShader = sh.fragmentShader
      .replace('#include <common>', '#include <common>\nuniform sampler2D liningMask; uniform float uLining, uLiningSpec;')
      .replace('#include <map_fragment>', '#include <map_fragment>\n  float mF = texture2D(liningMask, vMapUv).r;\n  diffuseColor.rgb *= mix(1.0, uLining, mF);')
      .replace('#include <lights_fragment_end>', '#include <lights_fragment_end>\n  reflectedLight.directSpecular *= mix(1.0, uLiningSpec, mF);\n  reflectedLight.indirectSpecular *= mix(1.0, uLiningSpec, mF);');
  };
  mat.needsUpdate = true;
}
let matBase = null, matLid = null;
gltf.scene.traverse(o => { if (o.isMesh && o.material) {
  if (o.material.name === 'Box_Base') matBase = o.material;
  if (o.material.name === 'Box_Lid') matLid = o.material;
} });
injectLining(matBase, mLiningBase); injectLining(matLid, mLiningLid);

// watch: Blender's plane with the same maths as your Watch_Silhouette material (silhouette and reveal)
const watchGeo = new THREE.BufferGeometry();
{ const face = data.watch_faces[0], pos = [], uv = [], idx = [];
  face.forEach((vi, k) => { pos.push(...data.watch_mesh[vi]); uv.push(...data.watch_uv[k]); });
  for (let i = 1; i < face.length - 1; i++) idx.push(0, i, i + 1);
  watchGeo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  watchGeo.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2)); watchGeo.setIndex(idx); }
const watchMat = new THREE.ShaderMaterial({
  transparent: true, depthWrite: false, side: THREE.DoubleSide,
  uniforms: { photo: { value: watchPhoto }, reveal: { value: 0 }, appear: { value: 0 },
              radius: { value: 0 }, silhouette: { value: new THREE.Color().fromArray(data.silhouette_color) }, brightness: { value: data.brightness } },
  vertexShader: `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
  fragmentShader: `
    uniform sampler2D photo; uniform float reveal, appear, radius, brightness; uniform vec3 silhouette; varying vec2 vUv;
    vec4 pick(vec2 p){ if (any(lessThan(p, vec2(0.0))) || any(greaterThan(p, vec2(1.0)))) return vec4(0.0); return texture2D(photo, p); }
    void main(){
      vec4 s = pick(vUv);
      for (int i = 0; i < 8; i++) { float a = float(i) * 0.785398;
        vec2 d = vec2(cos(a), sin(a)) * radius;
        s += pick(vUv + d * 0.5) + pick(vUv + d); }
      s /= 17.0;
      vec3 col = s.a > 0.0001 ? s.rgb / s.a : vec3(0.0);
      col = mix(silhouette, col, reveal) * brightness;
      gl_FragColor = vec4(col, s.a * appear * mix(0.78, 1.0, reveal));
    }`,
});
const watch = new THREE.Mesh(watchGeo, watchMat); watch.matrixAutoUpdate = false; watch.visible = false; scene.add(watch);

// interior light of the open box: real, with shadows (it only escapes through the open lid, as in Cycles)
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
const innerLight = new THREE.PointLight(0xffffff, 0, 0, 2);
innerLight.castShadow = true; innerLight.shadow.mapSize.set(512, 512); innerLight.shadow.bias = -0.003; innerLight.shadow.camera.near = 0.02;
innerLight.visible = false; scene.add(innerLight);
gltf.scene.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });

// real wall (in the sequence the camera moves relative to the wall and the fixed backdrop no longer works)
const segments = [];
if (wall) wall.traverse(o => { if (o.isMesh) segments.push(o); });
// In your scene the wall is EXCLUDED from every light (light linking): it only sees the world (0.004 x 5.7).
// three.js has no light linking: the wall gets its direct light removed and a uniform environment from the world.
const ENV_WALL = parseFloat(P.get('env_wall') ?? 1.0);
const worldScene = new THREE.Scene(); worldScene.background = new THREE.Color(0.0228, 0.0228, 0.0228);
const worldEnv = pmrem.fromScene(worldScene).texture;
for (const s of segments) {
  const m = s.userData.matOriginal;
  if (!m) continue;
  m.envMap = worldEnv; m.envMapIntensity = ENV_WALL;
  m.onBeforeCompile = sh => {
    sh.fragmentShader = sh.fragmentShader.replace('#include <lights_fragment_end>',
      '#include <lights_fragment_end>\n  reflectedLight.directDiffuse = vec3(0.0);\n  reflectedLight.directSpecular = vec3(0.0);');
  };
  m.needsUpdate = true;
}

// carousel angle that centers box .008 (the one the data comes from); the sequence ends with .001 centred (angle 0)
const A8 = (() => {
  const c8 = boxes.find(c => /008$/.test(c.userData.name || c.name)); const v = new THREE.Vector3();
  let best = 0, dist = 9;
  for (const a of [STEP, -STEP]) { layout(a); circle.updateMatrixWorld(true); camera.updateMatrixWorld(true);
    c8.getWorldPosition(v); v.project(camera); if (Math.abs(v.x) < dist) { dist = Math.abs(v.x); best = a; } }
  layout(angle); return best;
})();

const base8inv = new THREE.Matrix4().fromArray(data.base8).invert();
const Mk = new THREE.Matrix4(), tmp = new THREE.Matrix4();
const camSeq = new THREE.PerspectiveCamera(camera.fov, camera.aspect, 0.05, 200); camSeq.matrixAutoUpdate = false;
let boxK = null, lidK = null, lidParts = [], mode = 'carousel', seqFrame = F0, tSeq0 = 0, fSeq0 = F0, fSeqEnd = WAIT, swiperBack = false;
const q0inv = q0.clone().invert(), qTmp = new THREE.Quaternion(), vTmp = new THREE.Vector3(), sTmp = new THREE.Vector3();
function centredBox() {
  const v = new THREE.Vector3(); let best = null, dist = 9;
  for (const c of boxes) { c.getWorldPosition(v); v.project(camera); if (v.z < 1 && Math.abs(v.x) < dist) { dist = Math.abs(v.x); best = c; } }
  return best;
}
function applyFrame(f) {
  seqFrame = f; const d = dataAt(f);
  camSeq.matrixWorld.multiplyMatrices(Mk, tmp.fromArray(d.cam)); camSeq.matrix.copy(camSeq.matrixWorld);
  camSeq.matrixWorldInverse.copy(camSeq.matrixWorld).invert();
  camSeq.fov = camera.fov; camSeq.aspect = camera.aspect; camSeq.updateProjectionMatrix();
  circle.matrix.multiplyMatrices(Mk, tmp.fromArray(d.circle));
  lidK.matrix.multiplyMatrices(base8inv, tmp.fromArray(d.lid));
  watch.matrix.multiplyMatrices(Mk, tmp.fromArray(d.watch));
  innerLight.position.fromArray(d.light).applyMatrix4(Mk);
  innerLight.intensity = d.light_w / (4 * Math.PI) * INNER_LIGHT;
  uLining.value = d.lining; uLiningSpec.value = d.lining_spec / 0.5;
  matBase.emissiveIntensity = SETTINGS.seam * d.light_w / 742.866;        // the seam glows from the interior light
  const u = watchMat.uniforms; u.reveal.value = d.reveal; u.appear.value = d.appear;
  u.radius.value = THREE.MathUtils.clamp(1 - d.reveal, 0, 1) * data.max_blur;
  // the environment (the lights) turns with the circle
  circle.matrix.decompose(vTmp, qTmp, sTmp); qTmp.multiply(q0inv);
  const yaw = 2 * Math.atan2(qTmp.y, qTmp.w);
  for (const m of matsEnv) m.envMapRotation.set(0, ENV_SIGN * yaw, 0);
  // interface driven by your curves (by ON, header and recents have already faded)
  if (f > 363) { gHeader.style.opacity = d.UI_Header; gRec.style.opacity = d.UI_Recents; }
  eBack.style.opacity = d.UI_Back; eInfo.style.opacity = d.UI_Info;
  const active = state === 'detail';
  eBack.style.pointerEvents = active && d.UI_Back > 0.5 ? 'auto' : 'none';
  eCont.style.pointerEvents = active && d.UI_Info > 0.5 ? 'auto' : 'none';
  // on the way back the swiper comes in again (1216 -> 1311), at rest and with the knob on the left
  if (f >= 1216 && !swiperBack) {
    swiperBack = true; setSwipe(0); gBottom.getAnimations().forEach(a => a.cancel());
    gBottom.animate([{ transform: 'translateY(55%)', opacity: 0 }, { transform: 'translateY(0)', opacity: 1 }],
                  { duration: (1311 - 1216) / FPS * 1000, easing: 'cubic-bezier(.25,.6,.3,1)', fill: 'forwards' });
  }
}
function startSequence() {
  state = 'sequence'; swiperBack = false;
  boxK = centredBox();
  lidK = null; boxK.traverse(o => { if (!lidK && /^MASTER_Lid/.test(o.userData.name || o.name)) lidK = o; });
  Mk.multiplyMatrices(boxK.matrixWorld, base8inv);
  lidK.userData.restMatrix = lidK.matrix.clone(); lidK.matrixAutoUpdate = false;
  // on every box but .008, the lid's logo and tab hang from the base: they get attached to the lid
  lidParts = [];
  boxK.traverse(o => { if (o !== lidK && /Logo_?lid|Clasp_tab/i.test(o.userData.name || o.name)) {
    let insideLid = false; for (let p = o.parent; p; p = p.parent) if (p === lidK) insideLid = true;
    if (!insideLid) lidParts.push(o); } });
  boxK.updateMatrixWorld(true);
  for (const o of lidParts) { o.userData.restParent = o.parent; lidK.attach(o); }
  circle.matrixAutoUpdate = false;
  for (const s of segments) s.material = s.userData.matOriginal;
  scene.background = new THREE.Color(0.023, 0.023, 0.023);
  watch.visible = true; innerLight.visible = true;
  composer.passes[0].camera = camSeq;
  gHeader.style.transition = gRec.style.transition = 'opacity .5s linear';
  setTimeout(() => { gHeader.style.transition = gRec.style.transition = 'none'; }, 600);
  mode = 'seq'; tSeq0 = performance.now(); fSeq0 = F0; fSeqEnd = WAIT;
}
function backToCarousel() {
  if (state !== 'detail') return;
  state = 'sequence';
  eBack.style.pointerEvents = eCont.style.pointerEvents = 'none';
  tSeq0 = performance.now(); fSeq0 = WAIT; fSeqEnd = F1;
}
eBack.addEventListener('click', backToCarousel);
eCont.addEventListener('click', backToCarousel);
function endSequence() {
  // it ends with the next box centred (in your timeline, from .008 to .001)
  goal = goal - A8; angle = goal; angVel = 0;
  circle.matrixAutoUpdate = true; layout(angle);
  lidK.matrix.copy(lidK.userData.restMatrix); lidK.matrixAutoUpdate = true;
  boxK.updateMatrixWorld(true);
  for (const o of lidParts) o.userData.restParent.attach(o);
  for (const s of segments) s.material = s.userData.matHider;
  scene.background = back; watch.visible = false; innerLight.visible = false;
  composer.passes[0].camera = camera;
  uLining.value = 1; uLiningSpec.value = 1; matBase.emissiveIntensity = SETTINGS.seam;
  gHeader.style.transition = gRec.style.transition = ''; gHeader.style.opacity = gRec.style.opacity = '';
  gHeader.classList.remove('hidden'); gRec.classList.remove('hidden');
  eBack.style.opacity = eInfo.style.opacity = 0;
  mode = 'carousel'; state = 'rest';
}

// ---- loop ----
let tPrev = performance.now();
function frame(t) {
  const dt = Math.min(0.05, (t - tPrev) / 1000); tPrev = t;
  if (mode === 'carousel') {
    if (!drag) {
      // critically damped spring towards the snap
      const k = 90, c = 2 * Math.sqrt(k);
      const acc = -k * (angle - goal) - c * angVel;
      angVel += acc * dt; angle += angVel * dt;
      if (Math.abs(angle - goal) < 1e-5 && Math.abs(angVel) < 1e-4) { angle = goal; angVel = 0; }
    } else angVel = 0;
    layout(angle);
  } else {
    const f = Math.min(fSeqEnd, fSeq0 + (t - tSeq0) / 1000 * FPS);
    applyFrame(f);
    if (f >= fSeqEnd) {
      if (fSeqEnd === WAIT && state === 'sequence') { state = 'detail'; applyFrame(f); }
      else if (fSeqEnd === F1) endSequence();
    }
  }
  composer.render();
  requestAnimationFrame(frame);
}
document.getElementById('loading').remove();
requestAnimationFrame(frame);

// for automated tests
window.__proto = { THREE, scene, camera, gltf, SETTINGS, state: () => ({ angle, goal, boxes: boxes.length, SIGN, state, swipeProgress, mode, seqFrame, A8 }),
  turn: n => { goal += n * STEP; }, open, backToCarousel,
  jumpTo: f => { if (mode !== 'seq') startSequence(); fSeq0 = f; fSeqEnd = f; tSeq0 = performance.now(); } };
