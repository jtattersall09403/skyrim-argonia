// The helpers the game never shows (js/markers.js): one sentence each, and what uses one.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { helperWhat, isHelper, usesOf } from '../js/markers.js';

test('each kind of helper says what it is', () => {
  assert.match(helperWhat({ edid: 'MapMarker' }), /world map/);
  assert.match(helperWhat({ edid: 'XMarkerHeading' }), /facing/);
  assert.match(helperWhat({ edid: 'XMarker' }), /enable parent/);
  assert.match(helperWhat({ edid: 'WarmHandsIdleMarker', type: 'IdleMarker' }), /idle marker/);
  assert.match(helperWhat({ edid: 'PatrolIdleMarker', type: 'IdleMarker' }), /patrol point/);
  assert.match(helperWhat({ edid: 'COCMarkerHeading' }), /never uses it/);
  assert.ok(isHelper({ kind: 'marker' }, { edid: 'XMarker' }));
  assert.ok(!isHelper({ kind: 'marker', primitive: { bounds: [1, 1, 1] } }, { edid: 'CollisionMarker' }));
  assert.ok(!isHelper({ kind: 'static' }, { edid: 'Barrel01' }));
});

test('what uses a helper, or nothing', () => {
  const x = { id: 'x' }, kid = { id: 'k', enable_parent: { ref: 'x' } };
  const people = [{ name: 'Ah-ja', routine: [{ kind: 'eat', at: { ref: 'x' } }] }];
  const uses = usesOf(x, { refs: [x, kid], people, nameOf: (r) => r.id });
  assert.ok(uses.some((u) => /enable parent/.test(u)) && uses.some((u) => /Ah-ja's routine/.test(u)), uses);
  assert.deepEqual(usesOf({ id: 'y' }, { refs: [x, kid] }), ['nothing we can see uses it']);
});
