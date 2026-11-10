// Day and night in each view (docs/design/place-studio.md, What the views draw: day and night). By day the studio's
// own light, as always. By night the game's: outside, the sky, ambient, moonlight and fog of the worldspace's
// climate's weather at night (the bundle's exterior `sky`); inside, the cell's own lighting (ambient, directional,
// fog; a field the cell inherits from its lighting template). Every placed light lights its surroundings with its
// colour, radius, fade and Skyrim's falloff, 1 - (d / r)^2 in the game's gamma space. No shadows.
//
// Hundreds of lights cannot each be a real light on a tablet, so: the REAL lights nearest where the view looks are
// real unshadowed point lights (a fixed number in every view, so no shader is ever rebuilt), and every other light
// is a pool: drawn once into a light map seen from above (additive discs, one draw for all of them) that every
// surface adds in, by its position, times its own colour. Each light's fixture glows. The map is drawn again only
// when a light changes or the view moves well away.
import * as THREE from 'three';
import { colourOf } from './lights.js';

export const REAL = 6;           // real point lights per view, always present (by day at nothing)
const MAP = 1024;                // light map texels a side
const GAMMA = 2.2;

// ---------- the shaders: Skyrim's falloff, the light map, the game's fog ----------
// A point light with decay 0 is one of ours: the game's falloff, taken from its gamma space to the studio's linear.
THREE.ShaderChunk.lights_pars_begin = THREE.ShaderChunk.lights_pars_begin.replace(
  'float distanceFalloff = 1.0 / max( pow( lightDistance, decayExponent ), 0.01 );',
  'if ( decayExponent == 0.0 && cutoffDistance > 0.0 ) return pow( saturate( 1.0 - pow2( lightDistance / cutoffDistance ) ), 2.2 );\n\tfloat distanceFalloff = 1.0 / max( pow( lightDistance, decayExponent ), 0.01 );');

// One set of values for every lit surface; each view sets them before it draws (the views draw one after the other).
const U = { lpMap: { value: null }, lpMin: { value: new THREE.Vector2() }, lpSize: { value: new THREE.Vector2(1, 1) }, lpGain: { value: 0 },
  gameFog: { value: 0 }, fogMax: { value: 1 }, fogPower: { value: 1 } };
function lambertPatch(shader) {
  Object.assign(shader.uniforms, U);
  shader.vertexShader = 'varying vec3 vLpW;\n' + shader.vertexShader.replace('#include <project_vertex>', `#include <project_vertex>
  vec4 lpW = vec4( transformed, 1.0 );
  #ifdef USE_INSTANCING
    lpW = instanceMatrix * lpW;
  #endif
  vLpW = ( modelMatrix * lpW ).xyz;`);
  shader.fragmentShader = `varying vec3 vLpW;
uniform sampler2D lpMap; uniform vec2 lpMin; uniform vec2 lpSize; uniform float lpGain;
uniform float gameFog; uniform float fogMax; uniform float fogPower;
` + shader.fragmentShader.replace('#include <lights_fragment_end>', `#include <lights_fragment_end>
  if ( lpGain > 0.0 ) {
    vec2 lpUv = ( vLpW.xy - lpMin ) / lpSize;
    if ( lpUv.x > 0.0 && lpUv.y > 0.0 && lpUv.x < 1.0 && lpUv.y < 1.0 ) reflectedLight.directDiffuse += lpGain * texture2D( lpMap, lpUv ).rgb * diffuseColor.rgb;
  }`).replace('#include <fog_fragment>', `#ifdef USE_FOG
  float fogFactor = gameFog > 0.5 ? min( fogMax, pow( saturate( ( vFogDepth - fogNear ) / max( fogFar - fogNear, 1.0 ) ), fogPower ) ) : smoothstep( fogNear, fogFar, vFogDepth );
  gl_FragColor.rgb = mix( gl_FragColor.rgb, fogColor, fogFactor );
#endif`);
}
THREE.MeshLambertMaterial.prototype.onBeforeCompile = lambertPatch;

// ---------- the game's data ----------
// A colour as the bundles write it: [r, g, b] bytes, or those bytes in base64 (the extractor's byte arrays).
export const rgb = colourOf;
const lin = (c, k = 1) => new THREE.Color().setRGB(...c.map((x) => Math.min(1, (x / 255) * k)), THREE.SRGBColorSpace);
const hhmm = (s, d) => { const m = /^(\d+):(\d+)/.exec(String(s || '')); return m ? Number(m[1]) + Number(m[2]) / 60 : d; };

// A placed light: its base's light data with the ref's own radius and fade offset. Null for anything else, and for
// a negative light (one that darkens: the studio leaves it out).
export function lightOf(ref, base) {
  const L = base?.light; if (!L || /Negative/.test(L.flags || '')) return null;
  return { radius: Number(ref.radius ?? L.radius ?? 256) || 256, fade: Math.max(0, Number(L.fade ?? 1) + Number(ref.light_data?.fade ?? 0)),
    colour: rgb(L.colour) || [255, 255, 255] };
}

// The weather a climate's night is drawn with: the one picked, else its likeliest.
export function weatherOf(sky, key) {
  const ws = sky?.weathers || []; if (!ws.length) return null;
  return ws.find((w) => w.key === key) || [...ws].sort((a, b) => (b.chance || 0) - (a.chance || 0))[0];
}
// Night outside, from a weather: {ambient: {up, down, side}, sun: {colour, dir}, sky, fog: {colour, near, far, power, max}}.
export function nightOutside(sky, key) {
  const w = weatherOf(sky, key);
  if (!w) return { ...PLAIN_NIGHT, plain: true };
  const n = (f) => rgb(w[f]?.Night);
  const dalc = w.DirectionalAmbientLightingColors?.Night;
  const amb = dalc ? ambientOf(dalc) : ambientOf(null, n('AmbientColor'));
  const near = n('FogNearColor') || [40, 45, 50], far = n('FogFarColor') || near;
  return { weather: w.edid || w.key, chance: w.chance, ambient: amb, sun: { colour: n('SunlightColor') || [40, 45, 60], dir: [0.35, 0.55, 1] },
    sky: n('SkyUpperColor') || far, fog: { colour: near.map((v, i) => (v + far[i]) / 2), near: w.FogDistanceNightNear ?? 0, far: w.FogDistanceNightFar ?? 20000,
      power: w.FogDistanceNightPower ?? 1, max: w.FogDistanceNightMax ?? 1 } };
}
// The six directional ambient colours (Skyrim's DALC) as up, down and side; or one ambient colour all round.
function ambientOf(dalc, one) {
  if (!dalc) { const c = one || [40, 40, 45]; return { up: c, down: c, side: c }; }
  const g = (k) => rgb(dalc[k]) || [0, 0, 0];
  const sides = ['DirectionalXPlus', 'DirectionalXMinus', 'DirectionalYPlus', 'DirectionalYMinus'].map(g);
  return { up: g('DirectionalZPlus'), down: g('DirectionalZMinus'), side: [0, 1, 2].map((i) => sides.reduce((s, c) => s + c[i], 0) / 4) };
}
// Inside: the cell's lighting, a field it inherits taken from its lighting template.
export function lightInside(info) {
  const L = info?.light, T = info?.lighting_template_light;
  if (!L || !Object.keys(L).length) return { ...PLAIN_ROOM, plain: true };
  const inh = String(L.Inherits || '');
  const pick = (field, flag, tfield = field) => (T && inh.includes(flag) ? T[tfield] : L[field]) ?? L[field] ?? T?.[tfield];
  const dalc = T && inh.includes('AmbientColor') ? T.DirectionalAmbientColors : L.AmbientColors;
  const scaled = dalc && Number(dalc.Scale ?? 1) > 0 && ['DirectionalZPlus', 'DirectionalXPlus'].some((k) => (rgb(dalc[k]) || [0]).some((v) => v > 0));
  const amb = scaled ? ambientOf(dalc) : ambientOf(null, rgb(pick('AmbientColor', 'AmbientColor')) || [40, 40, 40]);
  const dirCol = rgb(pick('DirectionalColor', 'DirectionalColor')) || [0, 0, 0], fade = Number(pick('DirectionalFade', 'DirectionalFade') ?? 1);
  const xy = (Number(pick('DirectionalRotationXY', 'DirectionalRotation')) || 0) * Math.PI / 180, z = (Number(pick('DirectionalRotationZ', 'DirectionalRotation')) || 0) * Math.PI / 180;
  const near = rgb(pick('FogNearColor', 'FogColor')) || [0, 0, 0], far = rgb(pick('FogFarColor', 'FogColor')) || near;
  return { ambient: amb, sun: { colour: dirCol.map((v) => v * Math.max(0, fade)), dir: [Math.sin(xy) * Math.cos(z), Math.cos(xy) * Math.cos(z), Math.sin(z) || 1] },
    sky: far, fog: { colour: near.map((v, i) => (v + far[i]) / 2), near: Number(pick('FogNear', 'FogNear')) || 0, far: Number(pick('FogFar', 'FogFar')) || 8000,
      power: Number(pick('FogPower', 'FogPower')) || 1, max: Number(pick('FogMax', 'FogMax') ?? 1) } };
}
// When the data cannot be had: a neutral night, said so in the studio.
const PLAIN_NIGHT = { ambient: { up: [38, 44, 56], down: [30, 32, 34], side: [34, 38, 46] }, sun: { colour: [40, 46, 64], dir: [0.35, 0.55, 1] }, sky: [16, 20, 30],
  fog: { colour: [24, 28, 34], near: 0, far: 20000, power: 1, max: 0.9 } };
const PLAIN_ROOM = { ambient: { up: [45, 42, 40], down: [35, 33, 30], side: [40, 38, 35] }, sun: { colour: [0, 0, 0], dir: [0, 0, 1] }, sky: [0, 0, 0],
  fog: { colour: [0, 0, 0], near: 0, far: 8000, power: 1, max: 1 } };
// Night by the climate's hours: from the end of sunset to the start of sunrise.
export function isNight(t, sky) { const a = hhmm(sky?.SunriseBegin, 6), b = hhmm(sky?.SunsetEnd, 20); return t < a || t >= b; }

// ---------- one view's light ----------
const glowTex = (() => {
  let tex = null;
  return () => {
    if (tex) return tex;
    const c = document.createElement('canvas'); c.width = c.height = 64; const g = c.getContext('2d');
    const r = g.createRadialGradient(32, 32, 0, 32, 32, 32); r.addColorStop(0, 'rgba(255,255,255,1)'); r.addColorStop(0.25, 'rgba(255,255,255,0.55)'); r.addColorStop(1, 'rgba(255,255,255,0)');
    g.fillStyle = r; g.fillRect(0, 0, 64, 64); tex = new THREE.CanvasTexture(c); return tex;
  };
})();

export class ViewLighting {
  // source(): {lights: [{pos: [x, y, z] game units, radius, fade, colour}], night: nightOutside(...) | lightInside(...),
  // ground: (x, y) => z or null}
  constructor(view, source) {
    this.view = view; this.source = source; this.mode = 'day'; this.stale = true; this.mapStale = true;
    const s = view.scene;
    this.hemi = s.children.find((o) => o.isHemisphereLight); this.sun = s.children.find((o) => o.isDirectionalLight);
    this.day = { hemi: [this.hemi.color.clone(), this.hemi.groundColor.clone(), this.hemi.intensity], sun: [this.sun.color.clone(), this.sun.intensity, this.sun.position.clone()] };
    this.real = [];
    for (let i = 0; i < REAL; i++) { const p = new THREE.PointLight(0xffffff, 0, 1, 0); s.add(p); this.real.push(p); }
    this.glow = new THREE.Points(new THREE.BufferGeometry(), new THREE.PointsMaterial({ size: 60, sizeAttenuation: true, map: glowTex(), vertexColors: true,
      transparent: true, depthWrite: false, blending: THREE.AdditiveBlending }));
    this.glow.frustumCulled = false; this.glow.visible = false; this.glow.renderOrder = 2; s.add(this.glow);
    this.lights = []; this.night = null; this.nearest = []; this.maxReal = REAL;
  }
  invalidate() { this.stale = true; this.mapStale = true; this.view.redraw(); }
  setMode(mode) {
    if (mode === this.mode) return;
    this.mode = mode; this.stale = true; this.mapStale = true; this.apply(); this.view.redraw();
    this.onMode?.(mode);
  }
  // The view's theme set its background: by night the game's sky replaces it.
  applyBackground() {
    const s = this.view.scene;
    if (this.mode === 'night' && this.night) { s.background = lin(this.night.sky); if (s.fog) s.fog.color = lin(this.night.fog.colour); this.cameraMoved(); }
  }
  apply() {
    const h = this.hemi, sun = this.sun;
    if (this.mode !== 'night') {
      [h.color, h.groundColor, h.intensity] = [this.day.hemi[0].clone(), this.day.hemi[1].clone(), this.day.hemi[2]];
      sun.color.copy(this.day.sun[0]); sun.intensity = this.day.sun[1]; sun.position.copy(this.day.sun[2]);
      for (const p of this.real) p.intensity = 0;
      this.glow.visible = false;
      this.view.setTheme(this.view.dark);
      return;
    }
    this.collect();
    const n = this.night, a = n.ambient;
    // the hemisphere gives a level face the side colour exactly, and up and down faces their own (in the game's terms)
    const mid = a.up.map((v, i) => (v + a.down[i]) / 2), up = a.up.map((v, i) => Math.max(0, v + a.side[i] - mid[i])), down = a.down.map((v, i) => Math.max(0, v + a.side[i] - mid[i]));
    h.color = lin(up); h.groundColor = lin(down); h.intensity = Math.PI;
    sun.color = lin(n.sun.colour); sun.intensity = Math.PI; sun.position.set(...n.sun.dir).normalize();
    this.glow.visible = this.lights.length > 0;
    this.view.setTheme(this.view.dark);
  }
  collect() {
    if (!this.stale && this.night) return;
    const src = this.source() || {};
    this.lights = src.lights || []; this.night = src.night || { ...PLAIN_NIGHT, plain: true }; this.ground = src.ground || (() => null);
    this.stale = false; this.mapStale = true;
    const pos = new Float32Array(this.lights.length * 3), col = new Float32Array(this.lights.length * 3), o = this.view.origin || [0, 0, 0];
    this.lights.forEach((l, i) => {
      pos.set([l.pos[0] - o[0], l.pos[1] - o[1], l.pos[2] - o[2]], i * 3);
      const c = lin(l.colour, Math.min(1.5, Math.max(0.4, l.fade))); col.set([c.r, c.g, c.b], i * 3);
    });
    const g = this.glow.geometry;
    g.setAttribute('position', new THREE.BufferAttribute(pos, 3)); g.setAttribute('color', new THREE.BufferAttribute(col, 3)); g.computeBoundingSphere();
  }
  // Called as the camera moves: the game's fog as the player standing where the view looks would see it, and the
  // light map drawn again when the view has moved well away from where it was drawn.
  cameraMoved() {
    if (this.mode !== 'night' || !this.night) return;
    const f = this.view.scene.fog, n = this.night.fog, d = this.view.rig.dist;
    if (f) { f.near = n.near + d * 0.9; f.far = f.near + Math.max(500, n.far - n.near); }
    const t = this.view.rig.target, m = this.mapAt;
    if (!m || Math.hypot(t.x - m.x, t.y - m.y) > m.size / 4 || d * 3 > m.size * 1.5 || d * 3 < m.size / 3) this.mapStale = true;
  }
  // Before the view draws: by night, pick the nearest lights, draw the map if it is out of date, set the values.
  beforeDraw() {
    if (this.mode !== 'night') { U.lpGain.value = 0; U.gameFog.value = 0; return; }
    if (this.stale) this.apply();
    if (this.mapStale) this.drawMap();
    const n = this.night.fog;
    U.gameFog.value = 1; U.fogMax.value = n.max; U.fogPower.value = n.power;
    U.lpMap.value = this.rt?.texture || null; U.lpGain.value = this.rt ? 1 / this.scale : 0;
    U.lpMin.value.set(this.mapAt?.x0 ?? 0, this.mapAt?.y0 ?? 0); U.lpSize.value.set(this.mapAt?.size ?? 1, this.mapAt?.size ?? 1);
  }
  drawMap() {
    this.mapStale = false;
    const v = this.view, r = v.renderer, t = v.rig.target, o = v.origin || [0, 0, 0];
    const size = Math.min(65536, Math.max(8192, v.rig.dist * 3));
    this.mapAt = { x: t.x, y: t.y, size, x0: t.x - size / 2, y0: t.y - size / 2 };
    // the nearest lights to where the view looks are real; the rest are pools
    const near = this.lights.map((l, i) => [i, Math.hypot(l.pos[0] - o[0] - t.x, l.pos[1] - o[1] - t.y, (l.pos[2] - o[2] - t.z) * 0.5) - l.radius * 0.25])
      .sort((a, b) => a[1] - b[1]).slice(0, this.maxReal).map(([i]) => i);
    this.nearest = near;
    this.real.forEach((p, k) => {
      const l = this.lights[near[k]];
      if (!l) { p.intensity = 0; return; }
      p.position.set(l.pos[0] - o[0], l.pos[1] - o[1], l.pos[2] - o[2]); p.distance = l.radius; p.decay = 0;
      p.color = lin(l.colour); p.intensity = Math.PI * Math.pow(l.fade, GAMMA);
    });
    const real = new Set(near), pools = [];
    for (let i = 0; i < this.lights.length; i++) {
      if (real.has(i)) continue;
      const l = this.lights[i], x = l.pos[0] - o[0], y = l.pos[1] - o[1];
      if (x + l.radius < this.mapAt.x0 || y + l.radius < this.mapAt.y0 || x - l.radius > this.mapAt.x0 + size || y - l.radius > this.mapAt.y0 + size) continue;
      // the pool where the light's sphere meets the ground under it: narrower and dimmer the higher the light
      const g = this.ground(l.pos[0], l.pos[1]), h = g == null ? 0 : Math.max(0, l.pos[2] - g), k = 1 - (h / l.radius) ** 2;
      if (k <= 0) continue;
      const c = lin(l.colour), w = Math.pow(l.fade, GAMMA) * Math.pow(k, GAMMA);
      pools.push([x, y, l.radius * Math.sqrt(k), Math.max(h, 1), c.r * w, c.g * w, c.b * w]);
    }
    this.pools = pools.length;
    this.ensurePools(r);
    const geo = this.poolGeo, n = pools.length;
    if (geo.attributes.iPos.count < n) this.growPools(n);
    const P = geo.attributes.iPos.array, C = geo.attributes.iCol.array;
    pools.forEach(([x, y, rad, h, cr, cg, cb], i) => { P.set([x, y, rad, h], i * 4); C.set([cr * this.scale, cg * this.scale, cb * this.scale], i * 3); });
    geo.attributes.iPos.needsUpdate = true; geo.attributes.iCol.needsUpdate = true; geo.instanceCount = n;
    this.poolMat.uniforms.uMin.value.set(this.mapAt.x0, this.mapAt.y0); this.poolMat.uniforms.uSize.value = size;
    const keep = r.getRenderTarget(), cc = r.getClearColor(new THREE.Color()), ca = r.getClearAlpha();
    r.setRenderTarget(this.rt); r.setClearColor(0x000000, 0); r.clear(true, false, false);
    if (n) r.render(this.poolScene, this.poolCam);
    r.setRenderTarget(keep); r.setClearColor(cc, ca);
  }
  ensurePools(r) {
    if (this.rt) return;
    const half = r.extensions.has('EXT_color_buffer_float') || r.extensions.has('EXT_color_buffer_half_float');
    this.scale = half ? 1 : 0.25;   // an 8-bit map keeps four lights' worth before it saturates
    this.rt = new THREE.WebGLRenderTarget(MAP, MAP, { type: half ? THREE.HalfFloatType : THREE.UnsignedByteType, depthBuffer: false,
      minFilter: THREE.LinearFilter, magFilter: THREE.LinearFilter, generateMipmaps: false });
    this.poolMat = new THREE.ShaderMaterial({
      uniforms: { uMin: { value: new THREE.Vector2() }, uSize: { value: 1 } }, transparent: true, depthTest: false, depthWrite: false,
      blending: THREE.CustomBlending, blendEquation: THREE.AddEquation, blendSrc: THREE.OneFactor, blendDst: THREE.OneFactor,
      vertexShader: `attribute vec4 iPos; attribute vec3 iCol; uniform vec2 uMin; uniform float uSize; varying vec2 vUv; varying vec3 vCol; varying float vH;
        void main() { vUv = position.xy; vCol = iCol; vH = iPos.w / iPos.z; vec2 p = iPos.xy + position.xy * iPos.z; gl_Position = vec4( ( p - uMin ) / uSize * 2.0 - 1.0, 0.0, 1.0 ); }`,
      // the ground's angle to the light (as a real light lights it), never under a third, so walls round it keep some
      fragmentShader: `varying vec2 vUv; varying vec3 vCol; varying float vH;
        void main() { float d2 = dot( vUv, vUv ); if ( d2 >= 1.0 ) discard; float ndl = max( 0.35, vH / sqrt( d2 + vH * vH ) );
          gl_FragColor = vec4( vCol * ndl * pow( 1.0 - d2, ${GAMMA.toFixed(1)} ), 1.0 ); }`,
    });
    this.poolScene = new THREE.Scene(); this.poolCam = new THREE.OrthographicCamera();
    this.growPools(256);
    const mesh = new THREE.Mesh(this.poolGeo, this.poolMat); mesh.frustumCulled = false; this.poolScene.add(mesh);
  }
  growPools(n) {
    const cap = Math.max(256, 2 ** Math.ceil(Math.log2(n)));
    const g = this.poolGeo || (this.poolGeo = new THREE.InstancedBufferGeometry());
    if (!g.index) { g.setIndex([0, 1, 2, 0, 2, 3]); g.setAttribute('position', new THREE.BufferAttribute(new Float32Array([-1, -1, 0, 1, -1, 0, 1, 1, 0, -1, 1, 0]), 3)); }
    g.setAttribute('iPos', new THREE.InstancedBufferAttribute(new Float32Array(cap * 4), 4));
    g.setAttribute('iCol', new THREE.InstancedBufferAttribute(new Float32Array(cap * 3), 3));
  }
  // What a test or the help can read: how many lights, how many real, how many pools.
  state() { return { mode: this.mode, lights: this.lights.length, real: this.real.filter((p) => p.intensity > 0).length, pools: this.pools || 0,
    weather: this.night?.weather || null, plain: !!this.night?.plain }; }
}
