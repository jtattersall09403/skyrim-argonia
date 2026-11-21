// The look of water in the studio's scene (water_look.js says what a water's record gives). A placed water is a
// Lambert surface like everything else, so the lights, the night, the game's fog and the instancing all apply, with
// the liquid's own shading added to it:
//   colour    the water type's shallow colour at the rim, its deep colour where the water is deeper (the depth is the
//             surface over the ground under it, a small texture baked from the ground, so a hollow is darker in the middle);
//   body      transparent and soft at the shore (the bank shows through), as opaque as the record says toward the deep;
//             a thin darker wet line where it meets the ground;
//   surface   a tiling ripple normal map made in code (still unless a time is set), and a fresnel sheen of the record's
//             reflection colour that brightens at grazing angles; no environment render.
// The land's own cell water (terrain_mesh.js) takes the same sheen, analytic only, so the two agree.
import * as THREE from 'three';
import { DEPTH_MAX, INLAND_UNIT, depthGrid, rippleNormals, waterLook } from './water_look.js';

export const waterTime = { value: 0 };
// Ripples drift when a time is given (seconds); headless captures and a view at rest keep it at 0: still.
export function setWaterTime(t) { waterTime.value = t; }

let rippleTex = null, noDepth = null;
const ripple = () => {
  if (!rippleTex) {
    rippleTex = new THREE.DataTexture(rippleNormals(64), 64, 64, THREE.RGBAFormat);
    rippleTex.wrapS = rippleTex.wrapT = THREE.RepeatWrapping; rippleTex.magFilter = rippleTex.minFilter = THREE.LinearFilter; rippleTex.needsUpdate = true;
  }
  return rippleTex;
};
const emptyDepth = () => {
  if (!noDepth) { noDepth = new THREE.DataTexture(new Uint8Array([0, 0]), 1, 1, THREE.RGFormat); noDepth.needsUpdate = true; }
  return noDepth;
};

// the sheen both waters share: fresnel from the view angle against the up normal, in the water's reflection colour
const SHEEN = `
  vec3 wV = normalize( cameraPosition - vLpW );
  float wC = clamp( dot( WN, wV ), 0.0, 1.0 );
  float wF = WF0 + ( 1.0 - WF0 ) * pow( 1.0 - wC, 4.0 );
  float wLit = clamp( dot( reflectedLight.directDiffuse + reflectedLight.indirectDiffuse, vec3( 0.333 ) ) / max( dot( diffuseColor.rgb, vec3( 0.333 ) ), 0.02 ), 0.0, 1.0 );
  outgoingLight += WREFL * wF * WK * wLit;`;

// A shader patch for the shared Lambert patch to follow (lighting.js sets it for every Lambert material).
function surfacePatch(u) {
  return (shader) => {
    THREE.MeshLambertMaterial.prototype.onBeforeCompile.call(null, shader);
    Object.assign(shader.uniforms, u);
    shader.fragmentShader = `uniform sampler2D wDepth; uniform sampler2D wRip; uniform vec2 wMin; uniform vec2 wSize; uniform float wHas;
uniform vec3 wShallow; uniform vec3 wDeep; uniform vec3 wRefl; uniform vec4 wP; uniform float wTime;
` + shader.fragmentShader
      .replace('#include <alphamap_fragment>', `#include <alphamap_fragment>
  float wD = 120.0, wIn = 0.0;
  if ( wHas > 0.5 ) {
    vec2 wB = texture2D( wDepth, ( vLpW.xy - wMin ) / wSize ).rg * 255.0;
    wD = max( wB.x - 1.0, 0.0 ) * ( ${DEPTH_MAX.toFixed(1)} / 254.0 );
    wIn = wB.y * ${INLAND_UNIT.toFixed(1)};
  }
  float wT = smoothstep( 0.0, 1.0, clamp( ( wD + 0.5 * wIn ) / wP.y, 0.0, 1.0 ) );
  vec2 wR = vLpW.xy / 190.0 + vec2( wTime * 0.03, wTime * 0.02 );
  vec2 wS = texture2D( wRip, wR ).xy * 2.0 - 1.0;
  wS += ( texture2D( wRip, wR * -2.3 + vec2( 0.37 - wTime * 0.02, 0.11 ) ).xy * 2.0 - 1.0 ) * 0.7;
  vec3 wN = normalize( vec3( wS * 2.2, 1.0 ) );
  vec3 wCol = mix( wShallow, wDeep, wT );
  wCol *= 1.0 - 0.3 * smoothstep( 0.0, 6.0, wIn ) * ( 1.0 - smoothstep( 6.0, 26.0, wIn ) );
  float wO = wP.x;
  diffuseColor.rgb = wCol;
  diffuseColor.a *= smoothstep( 0.0, mix( 14.0, 1.5, smoothstep( 0.5, 1.0, wO ) ), wD ) * mix( wO * mix( 0.35, 1.0, wO ), wO, wT );`)
      .replace('#include <normal_fragment_maps>', `#include <normal_fragment_maps>
  normal = normalize( ( viewMatrix * vec4( wN, 0.0 ) ).xyz );`)
      .replace('#include <opaque_fragment>', SHEEN.replaceAll('WN', 'wN').replaceAll('WF0', 'wP.z').replaceAll('WREFL', 'wRefl').replaceAll('WK', '( 0.6 + 2.2 * length( wN.xy ) ) * wP.w') + '\n#include <opaque_fragment>');
  };
}

// One placed water base's surface: its look, and the depth grid over its placed refs.
export class WaterSurface {
  constructor(water) {
    const L = this.look = waterLook(water);
    const c = (a) => new THREE.Color().setRGB(a[0], a[1], a[2], THREE.SRGBColorSpace);
    // the record's reflectivity scales the sheen; fresnel is where it starts at the top view
    this.u = { wDepth: { value: emptyDepth() }, wRip: { value: ripple() }, wMin: { value: new THREE.Vector2() }, wSize: { value: new THREE.Vector2(1, 1) },
      wHas: { value: 0 }, wShallow: { value: c(L.shallow) }, wDeep: { value: c(L.deep) }, wRefl: { value: c(L.reflect) },
      wP: { value: new THREE.Vector4(L.opacity, L.fogFar, L.fresnel, L.reflectivity) }, wTime: waterTime };
    this.mats = [];
  }
  // refs: [{pos, r}] in game units; origin the layer's; groundAt(x, y) the ground's height or null
  setGrid(refs, origin, groundAt) {
    const g = groundAt ? depthGrid(refs, groundAt) : null, u = this.u;
    if (u.wDepth.value !== noDepth) u.wDepth.value.dispose();
    if (!g) { u.wDepth.value = emptyDepth(); u.wHas.value = 0; return; }
    const t = new THREE.DataTexture(g.data, g.w, g.h, THREE.RGFormat);
    t.magFilter = t.minFilter = THREE.LinearFilter; t.wrapS = t.wrapT = THREE.ClampToEdgeWrapping; t.unpackAlignment = 1; t.needsUpdate = true;
    u.wDepth.value = t; u.wHas.value = 1;
    u.wMin.value.set(g.min[0] - origin[0], g.min[1] - origin[1]); u.wSize.value.set(g.size[0], g.size[1]);
  }
  // The material for one part of the water's model: the source's sides, its own look. The model's vertex colours are not
  // used: a puddle's alpha (at most 0.44) is the game's own shore cue, and a record that says the water is opaque must show opaque.
  material(src) {
    const m = new THREE.MeshLambertMaterial({ color: 0xffffff, side: src.side, transparent: true, depthWrite: false,
      polygonOffset: true, polygonOffsetFactor: -1, polygonOffsetUnits: -1, name: 'water' });
    m.onBeforeCompile = surfacePatch(this.u); m.userData.water = true; this.mats.push(m);
    return m;
  }
}

// The land's own cell water: the same fresnel sheen on the up normal, nothing sampled.
export function worldWaterPatch(shader) {
  THREE.MeshLambertMaterial.prototype.onBeforeCompile.call(null, shader);
  shader.fragmentShader = shader.fragmentShader.replace('#include <opaque_fragment>',
    SHEEN.replaceAll('WN', 'vec3( 0.0, 0.0, 1.0 )').replaceAll('WF0', '0.06').replaceAll('WREFL', 'vec3( 0.55, 0.66, 0.72 )').replaceAll('WK', '0.35') + '\n#include <opaque_fragment>');
}
