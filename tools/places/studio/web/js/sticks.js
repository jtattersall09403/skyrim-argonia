// Two thumb sticks over the views, as in a game: the left moves the camera (forward, back, strafe), the right turns
// it and looks up and down. In walk mode the camera stays at a person's eye height on the ground or deck under it.
// The maths is pure (tested in test/sticks.test.mjs); the Sticks class wires it to the page and to one View.
export const WALK = 160;            // game units a second at a full push short of the edge (Skyrim's walk is ~ 100-170)
export const RUN = 370;             // at the edge: Skyrim's run
export const RUN_AT = 0.92;         // deflection past which the stick runs
export const DEAD = 0.08;           // a resting thumb moves nothing
export const YAW_RATE = 1.8;        // radians a second at full deflection
export const PITCH_RATE = 1.1;
export const PITCH_MIN = -1.45, PITCH_MAX = 1.3;   // look down / look up limits (radians from level)
export const EYE = 120;             // a person's eye above the ground (game units; a Skyrim player's camera is ~ 120)
export const STEP_UP = 70;          // a deck this far above the feet is stepped onto
export const STEPS = [1, 2, 4];

// A stick's offset in pixels to a deflection in the unit disc, with a dead zone.
export function deflection(dx, dy, radius) {
  let x = dx / radius, y = dy / radius; const m = Math.hypot(x, y);
  if (m > 1) { x /= m; y /= m; }
  if (m < DEAD) return { x: 0, y: 0, m: 0 };
  const k = (Math.min(1, m) - DEAD) / (1 - DEAD) / Math.min(1, m);   // rescaled past the dead zone
  return { x: x * k, y: y * k, m: Math.min(1, m) };
}
// Left stick: forward (stick up, negative y on screen) and strafe (right), in game units a second.
export function moveVelocity(d, step = 1) {
  const m = Math.hypot(d.x, d.y); if (!m) return { forward: 0, strafe: 0, speed: 0 };
  const speed = (d.m >= RUN_AT ? RUN : WALK * Math.min(1, m)) * step;
  return { forward: (-d.y / m) * speed, strafe: (d.x / m) * speed, speed };
}
// Right stick: yaw rate (stick right turns right: the heading angle falls) and pitch rate (stick up looks up).
export function turnRates(d) { return { yaw: -d.x * YAW_RATE, pitch: -d.y * PITCH_RATE }; }
export const clampPitch = (p) => Math.max(PITCH_MIN, Math.min(PITCH_MAX, p));

// One frame: cam {x, y, z, yaw, pitch} (yaw the facing angle from +X, pitch the look angle from level, up positive)
// moved by the sticks over dt seconds. ground(x, y) gives the walking surface (null where unknown) in walk mode;
// rise is the up/down rate (units a second) when flying.
export function stepCamera(cam, { move = { x: 0, y: 0 }, look = { x: 0, y: 0 }, rise = 0 }, dt, { step = 1, walk = false, ground = null } = {}) {
  dt = Math.max(0, Math.min(0.1, dt));   // a stalled frame never throws the camera across the place
  const t = turnRates(look), out = { ...cam };
  out.yaw = cam.yaw + t.yaw * dt;
  out.pitch = clampPitch(cam.pitch + t.pitch * dt);
  const v = moveVelocity(move, step), c = Math.cos(out.yaw), s = Math.sin(out.yaw);
  out.x = cam.x + (c * v.forward + s * v.strafe) * dt;
  out.y = cam.y + (s * v.forward - c * v.strafe) * dt;
  if (walk && ground) { const g = ground(out.x, out.y, cam.z - EYE); out.z = g == null ? cam.z : g + EYE; }
  else out.z = cam.z + rise * step * dt;
  return out;
}

// The page side: two sticks drawn over #views; they drive the view last touched (one pair for both views, where the
// thumbs are when the tablet is held in two hands).
const KEY = 'studio.sticks.v1';
const load = () => { try { return { shown: null, walk: false, step: 1, ...JSON.parse(localStorage.getItem(KEY) || '{}') }; } catch { return { shown: null, walk: false, step: 1 }; } };
export class Sticks {
  constructor(app, host) {
    this.app = app; this.host = host; this.state = load();
    this.move = { x: 0, y: 0, m: 0 }; this.look = { x: 0, y: 0, m: 0 }; this.rise = 0; this.held = new Map();
    const touchDevice = matchMedia('(pointer: coarse)').matches || navigator.maxTouchPoints > 0;
    if (this.state.shown == null) this.state.shown = touchDevice;
    const el = document.createElement('div'); el.className = 'sticks'; el.setAttribute('aria-label', 'Thumb sticks');
    el.innerHTML = `<div class="stick left" data-stick="move" aria-label="Move: forward, back, left and right"><i></i></div>
      <div class="stick-tools left"><button type="button" class="stick-btn" data-act="up" aria-label="Raise the camera">▲</button><button type="button" class="stick-btn" data-act="down" aria-label="Lower the camera">▼</button></div>
      <div class="stick right" data-stick="look" aria-label="Turn and look up or down"><i></i></div>
      <div class="stick-tools right"><button type="button" class="stick-btn walk" data-act="walk" aria-pressed="false" aria-label="Walk at eye height on the ground">Walk</button><button type="button" class="stick-btn" data-act="step" aria-label="Speed">x1</button></div>`;
    host.appendChild(el); this.el = el;
    for (const s of el.querySelectorAll('.stick')) this.wireStick(s);
    for (const b of el.querySelectorAll('.stick-btn')) this.wireButton(b);
    this.render();
  }
  save() { try { localStorage.setItem(KEY, JSON.stringify(this.state)); } catch { /* private window */ } }
  render() {
    this.el.hidden = !this.state.shown; this.host.classList.toggle('has-sticks', !!this.state.shown);
    const w = this.el.querySelector('[data-act=walk]'); w.setAttribute('aria-pressed', String(!!this.state.walk));
    this.el.querySelector('[data-act=step]').textContent = `x${this.state.step}`;
    for (const b of this.el.querySelectorAll('[data-act=up],[data-act=down]')) b.hidden = !!this.state.walk;
  }
  setShown(on) { this.state.shown = on; this.save(); this.render(); }
  setWalk(on) { this.state.walk = on; this.save(); this.render(); if (on) this.toEye(); }
  view() { return this.app.focused === this.app.src?.view ? this.app.src.view : this.app.ours.view; }
  wireStick(s) {
    const knob = s.querySelector('i'), which = s.dataset.stick;
    s.addEventListener('pointerdown', (e) => {
      e.stopPropagation(); e.preventDefault();
      if (e.pointerType === 'pen' || this.held.has(which)) return;   // the pen never moves a stick
      s.setPointerCapture?.(e.pointerId);
      const r = s.getBoundingClientRect();
      this.held.set(which, { id: e.pointerId, cx: r.left + r.width / 2, cy: r.top + r.height / 2, radius: r.width / 2 });
      if (this.state.walk && which === 'move') this.toEye();
      this.drag(which, e, knob);
    });
    s.addEventListener('pointermove', (e) => { const h = this.held.get(which); if (h && h.id === e.pointerId) { e.stopPropagation(); this.drag(which, e, knob); } });
    const end = (e) => { const h = this.held.get(which); if (!h || h.id !== e.pointerId) return; this.held.delete(which); this[which] = { x: 0, y: 0, m: 0 }; knob.style.transform = ''; s.classList.remove('active'); };
    s.addEventListener('pointerup', end); s.addEventListener('pointercancel', end); s.addEventListener('lostpointercapture', end);
  }
  drag(which, e, knob) {
    const h = this.held.get(which), dx = e.clientX - h.cx, dy = e.clientY - h.cy;
    this[which] = deflection(dx, dy, h.radius);
    const m = Math.hypot(dx, dy), k = m > h.radius ? h.radius / m : 1;
    knob.style.transform = `translate(${dx * k}px, ${dy * k}px)`; knob.parentElement.classList.add('active');
    this.app.focusView?.(this.view());
  }
  wireButton(b) {
    const act = b.dataset.act;
    b.addEventListener('pointerdown', (e) => {
      e.stopPropagation(); if (e.pointerType === 'pen' && (act === 'up' || act === 'down')) return;
      if (act === 'up' || act === 'down') { b.setPointerCapture?.(e.pointerId); this.rise = act === 'up' ? WALK : -WALK; }
    });
    const stop = () => { if (act === 'up' || act === 'down') this.rise = 0; };
    b.addEventListener('pointerup', stop); b.addEventListener('pointercancel', stop); b.addEventListener('lostpointercapture', stop);
    b.addEventListener('click', () => {
      if (act === 'walk') this.setWalk(!this.state.walk);
      if (act === 'step') { this.state.step = STEPS[(STEPS.indexOf(this.state.step) + 1) % STEPS.length]; this.save(); this.render(); }
    });
  }
  active() { return !!(this.move.m || this.look.m || this.rise); }
  // The camera as an eye: where it is and which way it looks, from the view's orbit rig (and back).
  eyeOf(v) {
    const r = v.rig; v.updateCamera(); const p = v.camera.position;
    return { x: p.x + v.origin[0], y: p.y + v.origin[1], z: p.z + v.origin[2], yaw: r.yaw + Math.PI, pitch: -r.pitch };
  }
  setEye(v, cam) {
    const r = v.rig, d = r.dist, cp = Math.cos(cam.pitch);
    r.yaw = cam.yaw - Math.PI; r.pitch = -cam.pitch;
    r.target.set(cam.x - v.origin[0] + d * cp * Math.cos(cam.yaw), cam.y - v.origin[1] + d * cp * Math.sin(cam.yaw), cam.z - v.origin[2] + d * Math.sin(cam.pitch));
    v.changed();
  }
  // Walk mode puts the eye at a person's height over the surface under it, looking level, near what it looks at.
  toEye() {
    const v = this.view(); if (!v.origin) return;
    if (v.rig.dist > 600) {   // from high above: come down where the view looks
      v.rig.dist = 400; v.rig.pitch = Math.min(Math.max(v.rig.pitch, -0.2), 0.2); v.updateCamera();
    }
    const cam = this.eyeOf(v), g = this.groundAt(v, cam.x, cam.y, null);
    if (g != null) cam.z = g + EYE;
    this.setEye(v, cam);
  }
  // The walking surface: the land (or a room's floor), or the highest walkable face of a placed model's real mesh under
  // the feet (a deck, a floor, a step), no higher than STEP_UP over them. Each model's box is only the first reject.
  groundAt(v, x, y, feet) {
    let g = v.terrainData ? v.terrainData.heightAt(x, y) : (v.floorZ ?? null);
    const T = globalThis.THREE; if (!T || !v.objects) return g;
    const top = (feet ?? g ?? 0) + STEP_UP, lx = x - v.origin[0], ly = y - v.origin[1];
    const rc = this._rc || (this._rc = new T.Raycaster()); rc.far = 6000;
    rc.set(new T.Vector3(lx, ly, top - v.origin[2]), new T.Vector3(0, 0, -1));
    const tmp = this._mesh || (this._mesh = new T.Mesh()), inv = new T.Matrix4(), lr = new T.Ray(), box = new T.Box3(), p = new T.Vector3(), n = new T.Vector3();
    let best = null;
    for (const layer of v.objects) {
      if (layer.isGrass || !layer.groups || !layer.root.visible) continue;
      for (const grp of layer.groups.values()) {
        if (!grp.fullParts || grp.ghost || grp.fx || grp.bulb || grp.prim || grp.unseen) continue;
        box.min.set(...grp.bmin); box.max.set(grp.bmin[0] + grp.bsize[0], grp.bmin[1] + grp.bsize[1], grp.bmin[2] + grp.bsize[2]);
        for (let i = 0; i < grp.refs.length; i++) {
          const m = grp.matrices[i]; p.setFromMatrixPosition(m);
          const r = grp.radius * (grp.refs[i].scale ?? 1) + 1; if (Math.abs(p.x - lx) > r || Math.abs(p.y - ly) > r) continue;
          inv.copy(m).invert(); lr.copy(rc.ray).applyMatrix4(inv); if (!lr.intersectsBox(box)) continue;
          tmp.matrixWorld.copy(m);
          for (const part of grp.fullParts) {
            tmp.geometry = part.geometry; tmp.material = part.material;
            for (const h of rc.intersectObject(tmp, false)) {
              if (!h.face) continue;
              n.copy(h.face.normal).transformDirection(m); if (Math.abs(n.z) < 0.6) continue;
              if (best == null || h.point.z > best) best = h.point.z;
              break;
            }
          }
        }
      }
    }
    if (best != null) { const z = best + v.origin[2]; if (g == null || z > g) g = z; }
    return g;
  }
  // Called every animation frame by the studio's loop: moves the view while a stick is held.
  frame(now) {
    const dt = this.last ? (now - this.last) / 1000 : 0; this.last = now;
    if (!this.active()) return false;
    const v = this.view(); if (!v.origin) return false;
    const walk = !!this.state.walk, cam = this.eyeOf(v);
    let ground = null;
    if (walk) {   // the ray down is cast only when the eye has moved a little
      ground = (x, y, feet) => {
        const c = this._gc;
        if (c && Math.hypot(c.x - x, c.y - y) < 12) return c.g;
        const g = this.groundAt(v, x, y, feet); this._gc = { x, y, g }; return g;
      };
    }
    this.setEye(v, stepCamera(cam, { move: this.move, look: this.look, rise: this.rise }, dt, { step: this.state.step, walk, ground }));
    return true;
  }
}
