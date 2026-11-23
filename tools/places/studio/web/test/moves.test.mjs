// A unit's move as data (units.js spotsMoved, edits.js unit.move) and a seated thing's raise: what goes with the
// unit, what stays, and that one undo gives everything back. The browser proves only that a drag makes such an op.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { rigid, spotsMoved } from '../js/units.js';
import { emptyModel, applyOp, inverse } from '../js/edits.js';
import { usersOf, followsLine } from '../js/routines.js';

const clone = (o) => JSON.parse(JSON.stringify(o));
const snap = (m) => JSON.stringify({ refs: [...m.spaces.exterior.refs], people: [...m.people], paths: [...m.paths], quests: [...m.quests], walk: [...m.walk] });

function place() {
  const m = emptyModel();
  m.spaces.exterior = { refs: new Map([
    ['b1', { id: 'b1', base: 'house', kind: 'building', pos: [1000, 1000, 0], rot: [0, 0, 0] }],
    ['d1', { id: 'd1', base: 'door', kind: 'door', pos: [1100, 1000, 0], rot: [0, 0, 0], door: { to_space: 'R', to_ref: 'r1', arrival: [1150, 1000, 0] } }],
    ['far', { id: 'far', base: 'rock', kind: 'static', pos: [5000, 5000, 0], rot: [0, 0, 0] }],
  ]) };
  m.people.set('p2', { id: 'p2', name: 'Bram Fixguard', work: { pos: [1050, 1000, 0] }, bed: 'bed1',
    routine: [{ kind: 'sleep', at: { ref: 'bed1', space: 'R' } }, { kind: 'eat', at: { pos: [4000, 4000, 0] } }] });
  m.paths.set('w9', { id: 'w9', kind: 'street', to: 'd1', points: [[0, 0], [600, 500], [1100, 1000]] });
  m.quests.set('q1', { id: 'q1', pos: [1020, 1020, 0], rot: [0, 0, 0] });
  m.walk.set('z1', { id: 'z1', outline: [[950, 950], [960, 950], [960, 960]] });
  return m;
}
const UNIT = { id: 'h01', name: 'Smithy', members: ['b1', 'd1'], box: { x0: 900, x1: 1200, y0: 900, y1: 1100, z0: 0, z1: 500 } };

test('a unit carries the spots standing in it; a stop that names a ref, and what lies outside, stay as they are', () => {
  const m = place(), moved = rigid([1000, 1000], 0, [10, 0, 0]);
  const s = spotsMoved(m, 'exterior', UNIT, moved, 0, m.spaces.exterior.refs);
  const bram = s.people[0].person;
  assert.deepEqual(bram.work.pos, [1060, 1000, 0], 'the work spot goes with it');
  assert.deepEqual(bram.routine[0].at, { ref: 'bed1', space: 'R' }, 'the sleep stop names its bed, so it needs no change');
  assert.deepEqual(bram.routine[1].at.pos, [4000, 4000, 0], 'a stop outside the unit stays');
  assert.deepEqual(s.quests[0].quest.pos, [1030, 1020, 0]);
  assert.deepEqual(s.walks[0].walk.outline[0], [960, 950]);
  const pts = s.paths[0].path.points;
  assert.deepEqual(pts[2], [1110, 1000], "a street ending at its door: the end follows the door");
  assert.deepEqual(pts[1], [605, 500], 'the point before it half as far, so the street bends');
  assert.deepEqual(pts[0], [0, 0], 'the far end stays');
});

test('a turned unit turns the quest spot it carries, about the unit centre', () => {
  const m = place(), turn = Math.PI / 2, moved = rigid([1000, 1000], turn, [0, 0, 0]);
  const q = spotsMoved(m, 'exterior', UNIT, moved, turn, m.spaces.exterior.refs).quests[0].quest;
  assert.deepEqual(q.pos.map(Math.round), [1020, 980, 0]);
  assert.equal(Math.round(q.rot[2] * 100) / 100, 1.57);
});

test('a unit move applies as one op, the door arrival with it, and one undo gives everything back', () => {
  const m = place(), start = snap(m), moved = rigid([1000, 1000], 0, [10, 0, 0]);
  const at = (id) => m.spaces.exterior.refs.get(id);
  const refs = ['b1', 'd1'].map((id) => {
    const r = at(id), before = clone({ pos: r.pos, rot: r.rot }), after = clone({ pos: moved(r.pos), rot: r.rot });
    if (r.door) { before.door = clone(r.door); after.door = { ...clone(r.door), arrival: moved(r.door.arrival) }; }
    return { id, before, after };
  });
  const op = { n: 1, op: 'unit.move', unit: 'h01', refs, ...spotsMoved(m, 'exterior', UNIT, moved, 0, m.spaces.exterior.refs) };
  applyOp(m, op);
  assert.deepEqual(at('b1').pos, [1010, 1000, 0]);
  assert.deepEqual(at('d1').door.arrival, [1160, 1000, 0]);
  assert.deepEqual(at('far').pos, [5000, 5000, 0]);
  assert.deepEqual(m.people.get('p2').work.pos, [1060, 1000, 0]);
  assert.deepEqual(m.paths.get('w9').points.at(-1), [1110, 1000]);
  applyOp(m, inverse(op));
  assert.equal(snap(m), start);
});

test('a thing seated on another keeps a raise: the seat height is the op, and undo gives it back', () => {
  const m = place();
  const door = m.spaces.exterior.refs.get('d1');
  door.seat = { mode: 'on', on: 'b1', dz: 120 };
  const op = { n: 1, op: 'ref.move', id: 'd1', before: { pos: [...door.pos], seat: { ...door.seat } },
    after: { pos: [1100, 1000, 128], seat: { mode: 'on', on: 'b1', dz: 128 } } };
  applyOp(m, op);
  assert.equal(m.spaces.exterior.refs.get('d1').seat.dz, 128);
  assert.equal(m.spaces.exterior.refs.get('d1').seat.on, 'b1');
  applyOp(m, inverse(op));
  assert.equal(m.spaces.exterior.refs.get('d1').seat.dz, 120);
});

test('a bed named in a routine: the studio says whose day follows it', () => {
  const m = place(), people = [...m.people.values()];
  const users = usersOf(people, 'bed1');
  assert.deepEqual(users.map((u) => u.how), ['sleeps']);
  const line = followsLine(users, 'this bed');
  assert.ok(line.startsWith('Bram Fixguard sleeps') && line.includes('routine follows this bed'), line);
  assert.equal(followsLine(usersOf(people, 'nobody')), '');
});

test('people, paths and paint strokes as rows: each op applies, a second add of a row is refused, undo and redo agree', () => {
  const m = place(), start = snap(m) + JSON.stringify([...m.paint]);
  const ops = [
    { n: 1, op: 'person.add', person: { id: 'p9', name: 'New Hand', work: { pos: [10, 10, 0] } } },
    { n: 2, op: 'person.edit', person: { ...clone(m.people.get('p2')), work: { pos: [1, 2, 0] } }, before: clone(m.people.get('p2')) },
    { n: 3, op: 'path.remove', path: clone(m.paths.get('w9')) },
    { n: 4, op: 'paint.add', paint: { id: 1, texture: 'mud', brush: 'hard', points: [[0, 0, 0.9], [200, 0, 0.9]] } },
    { n: 5, op: 'paint.add', paint: { id: 2, erase: true, brush: 'hard', points: [[0, 0, 0.5]] } },
  ];
  for (const op of ops) applyOp(m, op);
  assert.equal(m.people.get('p9').name, 'New Hand');
  assert.deepEqual(m.people.get('p2').work.pos, [1, 2, 0]);
  assert.ok(!m.paths.has('w9'));
  assert.deepEqual([...m.paint.keys()], [1, 2], 'strokes keep their order');
  assert.throws(() => applyOp(m, ops[0]), /already exists/);
  for (const op of [...ops].reverse()) applyOp(m, inverse(op));
  assert.equal(snap(m) + JSON.stringify([...m.paint]), start);
  for (const op of ops) applyOp(m, op);
  assert.equal(m.paint.size, 2);
});
