import assert from 'node:assert/strict';
import { modelFromFiles } from '../js/edits.js';

// two rows of one cell (a carried ground, then a sap hollow dug on top of it): the drawn change at a vertex is their
// sum, as the build and the seat tool add them, never the last row's alone
const m = modelFromFiles({ land: [
  { cell: [-14, -124], verts: [[16, 17, -88.7], [0, 0, 21.5]], by: 'ground' },
  { cell: [-14, -124], verts: [[16, 17, -22.6]], by: 'sap' },
] });
const cm = m.land.get('-14,-124');
assert.ok(Math.abs(cm.get(16 * 33 + 17) - (-111.3)) < 1e-9);
assert.equal(cm.get(0), 21.5);
console.log('land rows ok');
