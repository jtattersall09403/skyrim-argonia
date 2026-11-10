// One 3D view: a renderer, an orbit camera driven by touch, pen and mouse, the land, the things on it, and
// the pointer routed to the active tool. Z is up throughout, as in the game.
import * as THREE from 'three';
import { drainReady } from './objects.js';

THREE.Object3D.DEFAULT_UP.set(0, 0, 1);
const TAP_MS = 350, TAP_PX = 10;

// One renderer and one canvas for every view: a tablet keeps each texture and mesh once, and one set of shaders.
// The canvas lies behind the views and each view draws into its own rectangle of it. The drawing buffer is kept
// between frames, so a view that has not changed is not drawn again.
const shared = { renderer: null, canvas: null, views: [] };
function sharedRenderer(host) {
  if (shared.renderer) return shared.renderer;
  const r = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance', preserveDrawingBuffer: true });
  r.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5)); r.outputColorSpace = THREE.SRGBColorSpace;
  r.setScissorTest(true); r.autoClear = true;
  const c = r.domElement; c.className = 'stage-canvas'; c.setAttribute('aria-hidden', 'true'); host.prepend(c);
  const fit = () => {
    const b = host.getBoundingClientRect(); if (!b.width || !b.height) return;
    r.setSize(b.width, b.height, false); for (const v of shared.views) v.resize();
  };
  new ResizeObserver(fit).observe(host); shared.fit = fit;
  // a tablet may take the graphics context away (memory pressure, a long sleep): draw everything again when it returns
  c.addEventListener('webglcontextlost', (e) => { e.preventDefault(); shared.lost = true; });
  c.addEventListener('webglcontextrestored', () => { shared.lost = false; for (const v of shared.views) { for (const o of v.objects || []) o.dirty?.(); v.redraw(); } });
  shared.renderer = r; shared.canvas = c; fit();
  return r;
}

export class View {
  constructor(el, { name, app }) {
    this.el = el; this.name = name; this.app = app;
    this.canvas = el.querySelector('.canvas-holder'); this.canvas.setAttribute('aria-label', name);
    this.renderer = sharedRenderer(el.parentElement); shared.views.push(this);
    this.scene = new THREE.Scene();
    this.scene.add(new THREE.HemisphereLight('#e8f0ff', '#4a4636', 1.6));
    const sun = new THREE.DirectionalLight('#fff4e0', 1.4); sun.position.set(0.4, -0.6, 1); this.scene.add(sun);
    this.camera = new THREE.PerspectiveCamera(50, 1, 20, 120000);
    this.rig = { target: new THREE.Vector3(), dist: 6000, yaw: -Math.PI / 2, pitch: 0.75 };
    this.world = new THREE.Group(); this.scene.add(this.world);
    this.overlay = new THREE.Group(); this.scene.add(this.overlay);
    this.pointers = new Map(); this.needs = true; this.lastCull = 0;
    this.listen(); this.resize();
    new ResizeObserver(() => this.resize()).observe(el);
    this.setTheme(false);
  }
  setTheme(dark) {
    this.scene.background = new THREE.Color(dark ? '#1d2528' : '#cfdbe0');
    this.scene.fog = new THREE.Fog(this.scene.background, 30000, 90000); this.redraw();
  }
  // What this view shows: origin (subtracted from all game positions), terrain, objects.
  setContent({ origin, terrain = null, objects = [], interior = false }) {
    this.world.clear(); this.origin = origin; this.terrain = terrain; this.objects = objects; this.interior = interior;
    if (terrain) this.world.add(terrain.group);
    for (const o of objects) { this.world.add(o.root); o.onDirty = () => this.redraw(); }
    this.redraw();
  }
  frame(box) { // box: [x0,y0,x1,y1,z] in game units
    this.rig.target.set((box[0] + box[2]) / 2 - this.origin[0], (box[1] + box[3]) / 2 - this.origin[1], (box[4] ?? 0) - this.origin[2]);
    this.rig.dist = Math.max(800, Math.max(box[2] - box[0], box[3] - box[1]) * 1.5); this.changed();
  }
  resize() {
    const r = this.el.getBoundingClientRect(); if (!r.width || !r.height) return;
    this.camera.aspect = r.width / r.height; this.camera.updateProjectionMatrix(); this.redraw();
  }
  // Hidden under the other view shown full screen.
  hidden() { const full = this.el.parentElement?.querySelector('.view.full'); return !this.el.offsetWidth || (full && full !== this.el); }
  // Draw this view into its own rectangle of the shared canvas.
  draw() {
    const r = this.el.getBoundingClientRect(), b = shared.canvas.getBoundingClientRect();
    const x = r.left - b.left, y = b.bottom - r.bottom;
    this.renderer.setViewport(x, y, r.width, r.height); this.renderer.setScissor(x, y, r.width, r.height);
    this.renderer.render(this.scene, this.camera);
  }
  redraw() { this.needs = true; }
  changed(fromLink) {
    this.updateCamera(); this.redraw();
    if (!fromLink) this.app.cameraMoved?.(this);
  }
  updateCamera() {
    const r = this.rig, cp = Math.cos(r.pitch);
    this.camera.position.set(r.target.x + r.dist * cp * Math.cos(r.yaw), r.target.y + r.dist * cp * Math.sin(r.yaw), r.target.z + r.dist * Math.sin(r.pitch));
    this.camera.near = Math.max(5, r.dist / 400); this.camera.far = Math.max(120000, r.dist * 2 + 60000); this.camera.updateProjectionMatrix();
    if (this.scene.fog) { this.scene.fog.near = Math.max(20000, r.dist * 2.5); this.scene.fog.far = this.scene.fog.near * 4; }
    this.camera.lookAt(r.target); this.camera.updateMatrixWorld();
  }
  render(now) {
    if (!this.needs || shared.lost || this.hidden()) return false;
    const waiting = drainReady(this.renderer, this.objects || [], this.scene, this.camera);
    if (now - this.lastCull > 120 || this.objects?.some((o) => o._dirty)) {
      for (const o of this.objects || []) o.cull(this.camera); this.lastCull = now;
    }
    this.draw();
    this.needs = waiting > 0 || !!this.objects?.some((o) => o._dirty);
    return true;
  }
  // ---- pointer: fingers navigate when a pen is about; the pen (or a finger with no pen) works the tool ----
  listen() {
    const c = this.el.querySelector('.canvas-holder');
    c.addEventListener('pointerdown', (e) => this.down(e));
    c.addEventListener('pointermove', (e) => this.move(e));
    c.addEventListener('pointerup', (e) => this.up(e));
    c.addEventListener('pointercancel', (e) => this.up(e, true));
    c.addEventListener('wheel', (e) => { e.preventDefault(); this.zoom(Math.exp(e.deltaY * 0.0012)); }, { passive: false });
    c.addEventListener('contextmenu', (e) => e.preventDefault());
  }
  info(e) {
    const r = this.canvas.getBoundingClientRect();
    const ndc = new THREE.Vector2(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1);
    const rc = new THREE.Raycaster(); rc.setFromCamera(ndc, this.camera);
    return { view: this, x: e.clientX - r.left, y: e.clientY - r.top, ndc, ray: rc.ray, pressure: e.pointerType === 'pen' ? (e.pressure || 0.5) : 0.5,
      pointerType: e.pointerType, ground: () => this.groundAt(rc.ray), shift: e.shiftKey };
  }
  role(e) {
    if (e.pointerType === 'pen') this.app.penSeen = true;
    if (e.pointerType === 'mouse') return e.button === 0 ? 'tool' : (e.button === 2 || e.shiftKey ? 'pan' : 'orbit');
    if (e.pointerType === 'touch' && this.app.penSeen) return 'nav';
    if (e.pointerType === 'touch') return 'touch';
    return 'tool';
  }
  down(e) {
    this.canvas.setPointerCapture?.(e.pointerId);
    this.el.parentElement?.querySelectorAll('.view').forEach((v) => v.classList.toggle('focus', v === this.el));
    this.app.focusView?.(this);
    const role = this.role(e);
    const p = { id: e.pointerId, role, x: e.clientX, y: e.clientY, x0: e.clientX, y0: e.clientY, t0: performance.now(), moved: false, toolActive: false };
    this.pointers.set(e.pointerId, p);
    const navs = [...this.pointers.values()].filter((q) => q.role !== 'tool');
    if (navs.length >= 2) { // a second finger: cancel any tool gesture it began
      for (const q of navs) if (q.toolActive) { this.app.tool?.cancel?.(this.info(e)); q.toolActive = false; }
      this.pinch = null;
    }
    const tool = this.app.toolFor(this);
    if (role === 'tool' || (role === 'touch' && navs.length < 2 && tool?.wantsDrag?.(this.info(e)))) {
      if (tool?.down?.(this.info(e)) !== false && tool?.wantsDrag?.(this.info(e))) p.toolActive = true;
    }
  }
  move(e) {
    const p = this.pointers.get(e.pointerId);
    if (!p) { if (e.pointerType !== 'touch') this.app.toolFor(this)?.hover?.(this.info(e)); return; }
    const dx = e.clientX - p.x, dy = e.clientY - p.y; p.x = e.clientX; p.y = e.clientY;
    if (Math.hypot(e.clientX - p.x0, e.clientY - p.y0) > TAP_PX) p.moved = true;
    if (p.toolActive) { this.app.toolFor(this)?.move?.(this.info(e)); return; }
    const navs = [...this.pointers.values()].filter((q) => q.role !== 'tool' && !q.toolActive);
    if (navs.length >= 2) {
      const [a, b] = navs, cx = (a.x + b.x) / 2, cy = (a.y + b.y) / 2, d = Math.hypot(a.x - b.x, a.y - b.y);
      const ang = Math.atan2(b.y - a.y, b.x - a.x);
      if (this.pinch) {
        this.zoom(this.pinch.d / Math.max(1, d), true); this.pan(cx - this.pinch.cx, cy - this.pinch.cy, true);
        this.rig.yaw -= ang - this.pinch.ang; this.changed();
      }
      this.pinch = { cx, cy, d, ang }; return;
    }
    if (p.role === 'pan') this.pan(dx, dy);
    else if (p.role !== 'tool' && p.moved) this.orbit(dx, dy);
  }
  up(e, cancelled) {
    const p = this.pointers.get(e.pointerId); if (!p) return;
    this.pointers.delete(e.pointerId); this.pinch = null;
    const tool = this.app.toolFor(this);
    if (p.toolActive) { cancelled ? tool?.cancel?.(this.info(e)) : tool?.up?.(this.info(e)); return; }
    const isTap = !cancelled && !p.moved && performance.now() - p.t0 < TAP_MS * 2 && this.pointers.size === 0;
    // with a pen about, a finger tap only selects (a resting palm never edits)
    if (isTap && (p.role === 'tool' || p.role === 'touch' || (p.role === 'nav' && tool?.fingerTap))) tool?.tap?.(this.info(e));
  }
  orbit(dx, dy) {
    this.rig.yaw -= dx * 0.006; this.rig.pitch = Math.max(0.08, Math.min(1.52, this.rig.pitch + dy * 0.005)); this.changed();
  }
  pan(dx, dy, quiet) {
    const k = this.rig.dist * 0.0016, c = Math.cos(this.rig.yaw), s = Math.sin(this.rig.yaw);
    // dragging right slides the land right; dragging down pulls the land towards the camera
    this.rig.target.x += (s * dx - c * dy) * k;
    this.rig.target.y += (-c * dx - s * dy) * k;
    if (!quiet) this.changed(); else this.updateCamera();
  }
  zoom(f, quiet) { this.rig.dist = Math.max(150, Math.min(80000, this.rig.dist * f)); quiet ? this.updateCamera() : this.changed(); }
  // ---- the ground under a ray: the land (or an interior's floor) ----
  groundAt(ray) {
    const t = this.terrainData;
    if (t) {
      let prev = 0, step = 64; const o = ray.origin, d = ray.direction, P = new THREE.Vector3();
      const above = (s) => { P.copy(d).multiplyScalar(s).add(o); const h = t.heightAt(P.x + this.origin[0], P.y + this.origin[1]); return h == null ? null : P.z + this.origin[2] - h; };
      let a0 = above(0);
      for (let s = step; s < 150000; s += step, step *= 1.04) {
        const a = above(s);
        if (a != null && a0 != null && a <= 0) { let lo = prev, hi = s; for (let i = 0; i < 20; i++) { const m = (lo + hi) / 2; (above(m) > 0 ? lo = m : hi = m); } P.copy(d).multiplyScalar(hi).add(o); return [P.x + this.origin[0], P.y + this.origin[1], P.z + this.origin[2]]; }
        prev = s; a0 = a;
      }
      return null;
    }
    const z = (this.floorZ ?? this.origin[2]) - this.origin[2];
    if (Math.abs(ray.direction.z) < 1e-6) return null;
    const s = (z - ray.origin.z) / ray.direction.z; if (s < 0) return null;
    const P = ray.origin.clone().addScaledVector(ray.direction, s);
    return [P.x + this.origin[0], P.y + this.origin[1], P.z + this.origin[2]];
  }
  toScreen(gp) { // game point -> css px in this view
    const v = new THREE.Vector3(gp[0] - this.origin[0], gp[1] - this.origin[1], gp[2] - this.origin[2]).project(this.camera);
    const r = this.canvas.getBoundingClientRect();
    return { x: (v.x + 1) / 2 * r.width, y: (1 - v.y) / 2 * r.height, behind: v.z > 1 };
  }
}
