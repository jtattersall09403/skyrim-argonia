// What a place holds and who its people are (docs/design/place-studio.md, Stock): the pure part. No DOM: node tests
// it. Rows are the stock and people sources' own (the server's GET /api/place/<id>/stock); every change is built here
// as the whole row after, and the panel pushes it as a content op (identity.edit, stock.*) with the row before.

export const OWNER_WHY = 'The owner added it in the studio.';
const clone = (o) => (o == null ? o : JSON.parse(JSON.stringify(o)));

// ---------- the owner's own words (edits.py owner_marks) ----------
// A reason (`why`) or note text (`text`) a row holds that its before did not is the owner's, recorded at the owner's
// statement tier (`why_tier` beside a reason, a note's `tier`); a word the row keeps keeps the tier it had.
export const OWNER_TIER = 'OWNER_STATED';
function words(x, out) {
  if (Array.isArray(x)) for (const v of x) words(v, out);
  else if (x && typeof x === 'object') {
    if (typeof x.why === 'string') out.set(`why\u0000${x.why}`, x.why_tier ?? null);
    if (typeof x.text === 'string' && 'aspect' in x) out.set(`text\u0000${x.text}`, x.tier ?? null);
    for (const [k, v] of Object.entries(x)) if (k !== 'why' && k !== 'text') words(v, out);
  }
  return out;
}
export function ownerMarks(row, before) {
  const old = before == null ? new Map() : words(before, new Map());
  const walk = (x) => {
    if (Array.isArray(x)) { for (const v of x) walk(v); return; }
    if (!x || typeof x !== 'object') return;
    if (typeof x.why === 'string') {
      const k = `why\u0000${x.why}`;
      if (!old.has(k)) x.why_tier = OWNER_TIER; else if (old.get(k) && !x.why_tier) x.why_tier = old.get(k);
    }
    if (typeof x.text === 'string' && 'aspect' in x) {
      const k = `text\u0000${x.text}`;
      if (!old.has(k)) x.tier = OWNER_TIER; else if (old.get(k) && !x.tier) x.tier = old.get(k);
    }
    for (const [k, v] of Object.entries(x)) if (k !== 'why' && k !== 'text') walk(v);
  };
  const out = clone(row); walk(out); return out;
}

// ---------- the scale ----------
export const tierRank = (scale) => Object.fromEntries((scale?.tiers || []).map((t, i) => [t.id, t.rank ?? i + 1]));
export function tierLabel(scale, t) {
  if (!t) return 'tier not measured yet';
  const row = (scale?.tiers || []).find((x) => x.id === t);
  return row ? `${t} ${row.label}` : t;
}
export function bandLabel(scale, w) {
  const row = (scale?.person_wealth_bands || []).find((x) => x.id === w);
  return row ? `${w} ${row.label}` : (w || 'not set');
}
// May the place hold this item? As tools/places/studio/stock.py `allowed`: never-list items and items above the
// place's ceiling are refused with the reason; an item whose tier is not measured yet is allowed and said so.
export function allowedItem(facts, ceiling, scale) {
  if (!facts) return { ok: true, why: 'Allowed; nothing is known of it yet.' };
  if (facts.never) return { ok: false, why: `Not allowed: ${facts.never}.` };
  const rank = tierRank(scale), t = facts.tier;
  if (t && ceiling && (rank[t] || 0) > (rank[ceiling] ?? 99)) {
    return { ok: false, why: `Not allowed: it is ${tierLabel(scale, t)}, above this place's ceiling ${tierLabel(scale, ceiling)}.` };
  }
  if (!t) return { ok: true, why: 'Allowed; its tier is not measured yet.' };
  return { ok: true, why: `Allowed: ${tierLabel(scale, t)}, within this place's ceiling ${ceiling || 'none'}.` };
}
// A container's kind from its base's editor id, name and model (scale.json split.container_kinds, first match).
export function containerKind(base, scale) {
  const text = [base?.edid, base?.name, base?.model].filter(Boolean).join(' ').toLowerCase();
  for (const [kind, words] of scale?.container_kinds || []) {
    if (words.some((w) => new RegExp(w).test(text))) return { kind, always: (scale.always_significant_containers || []).includes(kind) };
  }
  return { kind: 'other', always: false };
}

// ---------- finding a holder's row ----------
export const containerOf = (stock, space, ref) => (stock?.containers || []).find((c) => c.ref === ref && (c.space || 'exterior') === space) || null;
export const looseAt = (stock, space, ref) => (stock?.loose || []).filter((l) => (l.space || 'exterior') === space && (l.id === ref || l.on === ref));
export const possessionsOf = (stock, person) => (stock?.possessions || []).find((x) => x.person === person) || null;
export const traderOf = (stock, person) => (stock?.traders || []).find((x) => x.person === person) || null;
export const identityOf = (ids, person) => (ids?.people || []).find((x) => x.id === person) || null;
export const householdOf = (ids, id) => (ids?.households || []).find((x) => x.id === id) || null;
export const backstoryOf = (p) => (p?.notes || []).find((n) => n.aspect === 'backstory')?.text || '';

// ---------- changes as whole rows ----------
// The row with one more item (or a higher count when it already holds that item).
export function withItem(row, item, count = 1, why = OWNER_WHY) {
  const out = clone(row); out.items = out.items || [];
  const have = out.items.find((i) => i.item === item);
  if (have) have.count += count; else out.items.push({ item, count, why: why || OWNER_WHY });
  return out;
}
export function withCount(row, item, count) {
  const out = clone(row); const it = out.items.find((i) => i.item === item);
  if (it) it.count = Math.max(1, Math.round(count));
  return out;
}
export function withoutItem(row, item) { const out = clone(row); out.items = out.items.filter((i) => i.item !== item); return out; }
export function withLock(row, lock) { const out = clone(row); if (lock) out.lock = lock; else delete out.lock; return out; }
export function withGold(row, gold) { const out = clone(row); out.gold = Math.max(0, Math.round(Number(gold) || 0)); return out; }
export function withBackstory(person, text) {
  const out = clone(person); out.notes = out.notes || [];
  const n = out.notes.find((x) => x.aspect === 'backstory');
  if (n) n.text = text; else out.notes.unshift({ aspect: 'backstory', text, tier: 'AGENT_INVENTED', cites: [] });
  return out;
}
// A container the owner stocks in the studio: its kind from the base, private when someone owns it, the lowest tier.
export function newContainer(ref, space, kind, owner) {
  const row = { ref, space, kind: kind || 'other', security: owner ? 'S1' : 'S0', tier: 'T1', gold: 0, items: [], why: 'The owner stocked it in the studio.', cites: [] };
  if (owner?.person) row.owner_person = owner.person; else if (owner?.household) row.owner_household = owner.household;
  return row;
}
export const newPossessions = (person) => ({ person, items: [], why: 'The owner gave them these in the studio.' });

// The op for a holder's row before and after (the panel pushes it).
export function opFor(holder, before, after) {
  after = after == null ? after : ownerMarks(after, before);   // the studio's edits are the owner's words
  switch (holder) {
    case 'container': return before ? { op: 'stock.container.set', container: after, before } : { op: 'stock.container.set', container: after };
    case 'possessions': return { op: 'stock.possessions.set', possessions: after, before: before ?? null };
    case 'trader': return { op: 'stock.trader.set', trader: after, before };
    case 'loose': return after ? { op: 'stock.loose.edit', loose: after, before } : { op: 'stock.loose.remove', loose: before };
    case 'identity': return { op: 'identity.edit', person: after, before };
    default: throw new Error(`no holder ${holder}`);
  }
}

// ---------- plain words for the history ----------
function itemChanges(b, a, nameOf) {
  const bm = new Map((b?.items || []).map((i) => [i.item, i])), am = new Map((a?.items || []).map((i) => [i.item, i])), out = [];
  for (const [k, i] of am) {
    const was = bm.get(k);
    if (!was) out.push(`added ${i.count} × ${nameOf(k)}`);
    else if (was.count !== i.count) out.push(`${nameOf(k)} ${was.count} → ${i.count}`);
  }
  for (const [k] of bm) if (!am.has(k)) out.push(`took out ${nameOf(k)}`);
  if ((b?.gold ?? 0) !== (a?.gold ?? 0)) out.push(`gold ${b?.gold ?? 0} → ${a?.gold ?? 0}`);
  if ((b?.lock || null) !== (a?.lock || null)) out.push(`lock ${b?.lock || 'none'} → ${a?.lock || 'none'}`);
  return out;
}
export function describeContent(op, nameOf = (k) => k) {
  const list = (xs, none) => (xs.length ? xs.join('; ') : none);
  switch (op.op) {
    case 'identity.edit': {
      const a = op.person, b = op.before || {}, what = [];
      if (a.name !== b.name) what.push(`name ${b.name} → ${a.name}`);
      if (a.trade !== b.trade) what.push('trade');
      if (a.wealth !== b.wealth) what.push(`wealth ${b.wealth} → ${a.wealth}`);
      if (backstoryOf(a) !== backstoryOf(b)) what.push('backstory');
      return `${a.name}: ${list(what, 'who they are changed')}`;
    }
    case 'stock.container.set': return op.before ? `${nameOf(op.container.ref)}: ${list(itemChanges(op.before, op.container, nameOf), 'its stock list changed')}` : `Stocked ${nameOf(op.container.ref)}`;
    case 'stock.container.remove': return `Took the stock list off ${nameOf(op.container.ref)}`;
    case 'stock.possessions.set': {
      const who = nameOf((op.possessions || op.before).person);
      return op.possessions ? `${who} carries: ${list(itemChanges(op.before, op.possessions, nameOf), 'changed')}` : `${who} carries nothing of note`;
    }
    case 'stock.trader.set': return op.trader ? `${nameOf(op.trader.person)}'s wares: ${list(itemChanges(op.before, op.trader, nameOf), 'changed')}` : `${nameOf(op.before.person)} sells nothing`;
    case 'stock.loose.add': return `Laid out ${op.loose.count} × ${nameOf(op.loose.item)}`;
    case 'stock.loose.remove': return `Took away ${nameOf(op.loose.item)}`;
    case 'stock.loose.edit': return `${nameOf(op.loose.item)} laid out: ${op.before.count} → ${op.loose.count}`;
    case 'stock.delivery.set': return `Promise ${(op.delivery || op.before).give_seq}: ${op.delivery ? op.delivery.status : 'no longer delivered here'}`;
    default: return op.op;
  }
}
