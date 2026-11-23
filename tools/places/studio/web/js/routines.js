// A person's day read as data, with no scene (pure, run under node by test/routines.test.mjs): their patrol points,
// who names a ref in their day, and the plain sentence the studio shows for them.

export const patrolOf = (p) => (Array.isArray(p.patrol) ? p.patrol : p.patrol?.points) || [];
export function setPatrol(x, pts) {
  if (!pts.length) { delete x.patrol; return; }
  x.patrol = { points: pts, loop: Array.isArray(x.patrol) ? true : (x.patrol?.loop ?? true) };
}

// Who names a ref in their day (pure): [{person, how}] where how is 'sleeps' (their bed or a sleep stop), 'works',
// 'eats' or 'stops' (another stop), each at most once per person. A routine names a bed, a station or any spot by
// its ref, so moving that ref moves where they go: nothing of theirs needs changing.
export function usersOf(people, refId, srcId) {
  const out = [], is = (at) => at && (at.ref === refId || (srcId && at.ref === srcId));
  const HOW = { sleep: 'sleeps', work: 'works', eat: 'eats' };
  for (const p of people) {
    const bed = typeof p.bed === 'string' ? { ref: p.bed } : p.bed;
    const hows = new Set();
    if (is(bed)) hows.add('sleeps');
    if (is(p.work)) hows.add('works');
    for (const s of p.routine || []) if (is(s.at)) hows.add(HOW[s.kind] || 'stops');
    for (const q of patrolOf(p)) if (!Array.isArray(q) && is(q)) hows.add('patrols');
    for (const how of hows) out.push({ person: p, how });
  }
  return out;
}
// The plain sentence for the people a ref serves: "Hara-Jeel sleeps here: his routine follows this bed."
export function followsLine(users, thing = 'this') {
  if (!users.length) return '';
  const by = new Map(); for (const u of users) { if (!by.has(u.person.id)) by.set(u.person.id, { p: u.person, hows: [] }); by.get(u.person.id).hows.push(u.how); }
  const one = (x) => `${x.p.name || 'Someone'} ${x.hows.join(' and ')} here`;
  const list = [...by.values()].map(one);
  const who = list.length === 1 ? list[0] : `${list.slice(0, -1).join('; ')} and ${list.at(-1)}`;
  return `${who}: ${by.size === 1 ? 'their routine follows' : 'their routines follow'} ${thing}.`;
}
