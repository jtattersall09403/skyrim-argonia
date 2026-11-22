// A place's quest states (the place's states.jsonl, tools/places/states.py): which refs, people and quest things
// each state shows and hides, and where it moves someone. A ref follows its enable parent as the game does: enabled
// when its parent is, or the opposite with SetEnableStateToOppositeOfParent; a state lists its parents' enable state
// (an unlisted parent is enabled) and may hide or show people and quest things beyond them.
export const OPPOSITE = 'SetEnableStateToOppositeOfParent';

export function defaultState(states) {
  return (states || []).find((s) => s.default) || (states || [])[0] || null;
}

export function findState(states, name) {
  if (!name) return defaultState(states);
  const n = String(name).trim().toLowerCase();
  return (states || []).find((s) => s.id.toLowerCase() === n || (s.name || '').toLowerCase() === n) || null;
}

export function enabledIn(ref, state) {
  if (!state) return true;
  const id = ref?.id;
  if ((state.hide || []).includes(id)) return false;
  if ((state.show || []).includes(id)) return true;
  const ep = ref?.enable_parent;
  if (!ep?.ref) return true;
  const parents = state.parents || {};
  const on = ep.ref in parents ? !!parents[ep.ref] : true;
  return String(ep.flags || '').includes(OPPOSITE) ? !on : on;
}

// {state, hidden: Set of ids, moves: Map id -> pos} of one state over the place's refs (any iterable of rows)
export function stateView(states, name, refs) {
  const state = findState(states, name);
  const hidden = new Set(), moves = new Map();
  if (!state) return { state: null, hidden, moves };
  for (const r of refs || []) if (!enabledIn(r, state)) hidden.add(r.id);
  for (const id of state.hide || []) hidden.add(id);
  for (const [id, pos] of Object.entries(state.moves || {})) moves.set(id, pos);
  return { state, hidden, moves };
}

// The words for a state in the switch: its name, and what sets it
export function stateLabel(s) {
  if (!s) return '';
  const by = s.set_by;
  if (!by) return `${s.name || s.id} (the game's start)`;
  const q = String(by.quest || '').split('.').pop().toUpperCase();
  const when = by.endings ? `ending ${by.endings.join(' or ')}` : by.ending ? `ending ${by.ending}` : by.stage != null ? `stage ${by.stage}` : by.flag || '';
  return `${s.name || s.id}${q || when ? ` (${[q, when].filter(Boolean).join(' ')})` : ''}`;
}
