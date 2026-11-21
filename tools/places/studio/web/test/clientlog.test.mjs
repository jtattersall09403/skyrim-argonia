// The client log says why a view is blank: window errors and unhandled rejections, the graphics context taken away and
// given back, and what each view drew a moment after a place is ready (out/places/studio-client.log).
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const js = (f) => readFileSync(new URL(`../js/${f}`, import.meta.url), 'utf8');

test('errors, rejections and context loss reach the client log', () => {
  const main = js('main.js'), view = js('view.js');
  assert.match(main, /addEventListener\('error',[^\n]*report\('error'/);
  assert.match(main, /addEventListener\('unhandledrejection',[^\n]*report\('rejection'/);
  assert.match(main, /onRendererEvent\(\(stage, extra\) => report\(stage, extra\)\)/);
  assert.match(view, /webglcontextlost[^\n]*shared\.onEvent\?\.\('context-lost'/);
  assert.match(view, /webglcontextrestored[^\n]*shared\.onEvent\?\.\('context-restored'/);
});

test('each ready place reports what its views drew', () => {
  const main = js('main.js'), view = js('view.js');
  assert.match(main, /report\('drawn', \{ place: id, \.\.\.st,/);
  assert.match(main, /report\('blank', \{ place: id, why/);
  assert.match(main, /this\.watchDrawn\(id\)/);
  for (const k of ['lost', 'glError', 'canvas', 'calls', 'triangles', 'views', 'over', 'drew']) assert.ok(view.includes(`${k}:`), k);
});
