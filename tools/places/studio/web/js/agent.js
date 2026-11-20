// The agent view: the studio's own scene drawn on request by tools/places/look.py. The page shows one canvas and no
// interface; window.agent answers the look tool: when the place is ready, apply or undo edits through the studio's
// own edit log, and draw one shot from a camera the tool chose (game coordinates, Z up) into a PNG.
import * as THREE from 'three';
import { pendingModels, drainAll } from './objects.js';

const css = `html.agent body > *:not(#stage) { display: none !important; }
html.agent #stage > *:not(#views), html.agent #views > *:not(#view-ours):not(.stage-canvas), html.agent #view-ours > *:not(.canvas-holder) { display: none !important; }
html.agent body, html.agent #stage, html.agent #views { margin: 0; padding: 0; overflow: hidden; }
html.agent #stage { position: fixed; inset: 0; } html.agent .view { flex: 1; }
html.agent dialog, html.agent .toast, html.agent .sheet, html.agent .panel { display: none !important; }`;

const tick = () => new Promise((r) => setTimeout(r, 30));

export function install(studio) {
  const st = document.createElement('style'); st.textContent = css; document.head.append(st);
  const v = () => studio.ours.view;
  const agent = {
    async ready(timeoutMs = 600000) {
      const t0 = performance.now();
      while (!studio.ready) { if (performance.now() - t0 > timeoutMs) throw new Error('the place did not load'); await new Promise((r) => setTimeout(r, 200)); }
      for (const d of document.querySelectorAll('dialog[open]')) d.close();
      return { place: studio.place.place_id, origin: studio.ours.origin, ops: studio.log.cursor, ms: Math.round(performance.now() - t0) };
    },
    // Edits: the same ops a save holds, pushed through the studio's own log (one stroke per call); undo takes the last stroke.
    push(ops) { const out = studio.log.push(ops.map((o) => ({ ...o }))); return out.map((o) => o.n); },
    undo() { return studio.log.undo().length; },
    reset() { studio.log.goto(0); studio.log.ops.length = 0; studio.log.cursor = 0; return true; },
    applied() { return studio.log.applied ? studio.log.applied() : studio.log.ops.slice(0, studio.log.cursor); },
    // One shot. cam: {w, h, pos, target, up?, fov?, ortho?: {halfW, halfH}, near?, far?, clip?: [[nx,ny,nz,d], ...]
    // (keeps n.p + d >= 0, game coordinates), grass?: bool}. Returns {png (data URL), ms, waits}.
    async shot(cam) {
      const t0 = performance.now(), view = v(), o = studio.ours.origin, r = view.renderer;
      const L = (p) => new THREE.Vector3(p[0] - o[0], p[1] - o[1], p[2] - o[2]);
      const w = cam.w || 768, h = cam.h || 576;
      const c = cam.ortho
        ? new THREE.OrthographicCamera(-cam.ortho.halfW, cam.ortho.halfW, cam.ortho.halfH, -cam.ortho.halfH, cam.near ?? 1, cam.far ?? 200000)
        : new THREE.PerspectiveCamera(cam.fov || 50, w / h, cam.near ?? 10, cam.far ?? 200000);
      c.up.set(...(cam.up || [0, 0, 1])); c.position.copy(L(cam.pos)); c.lookAt(L(cam.target)); c.updateMatrixWorld(); c.updateProjectionMatrix();
      c.userData.focus = L(cam.target);
      if (studio.ours.grass) studio.ours.grass.root.visible = !!cam.grass;
      // the editor's helpers (light bulbs, collision boxes) only when asked: the agent judges what the player sees
      for (const l of [studio.ours.place, studio.ours.world]) l?.setShowLights(!!cam.helpers);
      view.overlay.visible = !!cam.helpers;
      const tgt = L(cam.target);
      studio.ours.terrainMesh?.update(tgt);
      r.clippingPlanes = (cam.clip || []).map(([nx, ny, nz, d]) => new THREE.Plane(new THREE.Vector3(nx, ny, nz), d + nx * o[0] + ny * o[1] + nz * o[2]));
      // every model the camera can see, loaded and switched on; the land's near cells baked
      let waits = 0;
      for (;;) {
        for (const lay of view.objects || []) lay.cull(c);
        drainAll(r);
        const tm = studio.ours.terrainMesh;
        if (!pendingModels() && !(tm && (tm.pumping || tm.queue.length))) break;
        if (performance.now() - t0 > 120000) break;
        waits++; await tick();
      }
      for (const lay of view.objects || []) lay.cull(c);
      const tw = performance.now();
      r.setPixelRatio(1); r.setSize(w, h, false); r.setScissorTest(false); r.setViewport(0, 0, w, h);
      view.lighting?.beforeDraw();
      r.render(view.scene, c);
      r.getContext().finish();
      const tr = performance.now();
      const png = r.domElement.toDataURL('image/png');
      r.clippingPlanes = []; r.setScissorTest(true);
      const info = { calls: r.info.render.calls, triangles: r.info.render.triangles, render_ms: Math.round(tr - tw) };
      return { png, ms: Math.round(performance.now() - t0), draw_ms: Math.round(performance.now() - tw), waits, ...info };
    },
  };
  window.agent = agent;
}
