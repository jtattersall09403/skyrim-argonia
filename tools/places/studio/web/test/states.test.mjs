import { test } from 'node:test';
import assert from 'node:assert/strict';
import { stateView, findState, defaultState, stateLabel, OPPOSITE } from '../js/states.js';

const refs = [
  { id: 'P', kind: 'marker' },
  { id: 'HIST', enable_parent: { ref: 'P', flags: '0' } },
  { id: 'DEAD', enable_parent: { ref: 'P', flags: OPPOSITE } },
  { id: 'POT' },
];
const states = [
  { id: 'living', name: 'Hist living', default: true, parents: { P: true }, key: ['HIST'] },
  { id: 'dead', name: 'Hist dead (ending)', set_by: { quest: 'quest.main.mn19', endings: ['e-take', 'e-give'] },
    parents: { P: false }, hide: ['person.1'], moves: { 'person.2': [1, 2, 3] }, key: ['DEAD'] },
];

test('the default state is the game start and hides the dead twin', () => {
  assert.equal(defaultState(states).id, 'living');
  const v = stateView(states, null, refs);
  assert.deepEqual([...v.hidden], ['DEAD']);
});

test('a state by id or name shows its parents as the game does, hides and moves people', () => {
  const v = stateView(states, 'Hist dead (ending)', refs);
  assert.deepEqual([...v.hidden].sort(), ['HIST', 'person.1']);
  assert.deepEqual(v.moves.get('person.2'), [1, 2, 3]);
  assert.equal(findState(states, 'DEAD').id, 'dead');
  assert.equal(findState(states, 'burnt'), null);
});

test('no states: nothing hidden', () => {
  assert.equal(stateView([], null, refs).hidden.size, 0);
});

test('the switch names what sets a state', () => {
  assert.equal(stateLabel(states[0]), "Hist living (the game's start)");
  assert.equal(stateLabel(states[1]), 'Hist dead (ending) (MN19 ending e-take or e-give)');
});
