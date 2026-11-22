// The helpers the game never shows in play (markers of every kind), what each is in one plain sentence, and what in
// the place uses one. Pure: no three.js, no page (test/markers.test.mjs). The one table of the words is HELPERS.

// [test on the base, the sentence]: the first that matches says what it is.
export const HELPERS = [
  [(b) => /^MapMarker/i.test(b.edid), 'The map marker: where this place shows on the world map and where fast travel brings the player.'],
  [(b) => /^COCMarker/i.test(b.edid), "The editor's start point: where the Creation Kit's centre-on-cell command puts the player; the game never uses it in play."],
  [(b) => /^NorthMarker/i.test(b.edid), 'The north marker: tells the local map which way is north in this room.'],
  [(b) => /patrol/i.test(b.edid), "A patrol point: one stop on a guard's walk, where they pause."],
  [(b) => b.type === 'IdleMarker' || /idlemarker/i.test(b.edid), 'An idle marker: a spot where a person stops for a while to do something (warm their hands, look about).'],
  [(b) => /^XMarkerHeading/i.test(b.edid), "A heading marker: an invisible point with a facing, where the game puts someone or something (a person's spot, a quest thing, where one arrives)."],
  [(b) => /^XMarker/i.test(b.edid), 'An invisible marker: a point the game refers to, to switch other things on and off together (their enable parent) or as a spot a package, a quest or a script names.'],
  [(b) => b.type === 'SoundMarker' || /soundmarker|^amb/i.test(b.edid), "A sound marker: plays a sound here (a fire's crackle, birdsong, wind)."],
  [(b) => /roommarker|portal|occlu|multibound/i.test(b.edid), 'A room marker: tells the game which part of a room to draw from where the player stands.'],
  [(b) => /lightmarker|^light.*marker/i.test(b.edid), 'A light marker: shows where a light belongs; the light itself is what shines.'],
  [(b) => b.type === 'Furniture' && /marker|invisible/i.test(b.edid), 'A furniture marker: an invisible seat or work spot people use (to sit, lean, eat or work).'],
  [(b) => /door.*teleport|teleportmarker/i.test(b.edid), 'A door marker: where one arrives coming through a door.'],
  [(b) => /marker/i.test(`${b.edid || ''} ${b.model || ''}`), 'An invisible helper the game uses; it is never seen in play.'],
];

// Whether a ref is one of the helpers the Markers switch hides: a marker (never an invisible wall or a light, shown
// with their own switch).
export function isHelper(ref, base) {
  if (ref.primitive || ref.kind === 'light') return false;
  return ref.kind === 'marker' || HELPERS.some(([t], i) => i < HELPERS.length - 1 && t(base || {})) || /marker/i.test(base?.edid || '');
}
export function helperWhat(base) { const hit = HELPERS.find(([t]) => t(base || {})); return hit ? hit[1] : HELPERS.at(-1)[1]; }

// What uses a ref, in plain words: the things it switches on and off (their enable parent), the things linked to it,
// the doors that lead to it, the people whose routine names it, the quest spots and quest states that name it.
// { refs, people, quests, states, nameOf(ref) }
export function usesOf(ref, { refs = [], people = [], quests = [], states = [], nameOf = (r) => r.id }) {
  const id = ref.id, out = [];
  const kids = refs.filter((r) => (r.enable_parent?.ref ?? r.enable_parent) === id);
  if (kids.length) out.push(`switches ${kids.length === 1 ? `${nameOf(kids[0])}` : `${kids.length} things`} on and off with it (it is their enable parent)`);
  for (const r of refs) if ((r.linked || []).some((l) => l.ref === id)) out.push(`${nameOf(r)} is linked to it`);
  for (const r of refs) if (r.door?.to_ref === id) out.push(`${nameOf(r)} leads here`);
  const names = (at) => at && (at.ref === id);
  for (const p of people) {
    const pts = Array.isArray(p.patrol) ? p.patrol : p.patrol?.points || [];
    if (names(p.work) || (p.routine || []).some((s) => names(s.at)) || pts.some((q) => !Array.isArray(q) && names(q)) || p.bed === id || p.bed?.ref === id)
      out.push(`${p.name || 'a person'}'s routine names it`);
  }
  for (const q of quests) if (q.ref === id || q.on === id || q.at?.ref === id) out.push(`the quest spot ${q.name || q.ref || q.id} stands on it`);
  for (const s of states) if (JSON.stringify(s).includes(`"${id}"`)) out.push(`the quest state ${s.label || s.name || s.id} uses it`);
  return out.length ? out : ['nothing we can see uses it'];
}
