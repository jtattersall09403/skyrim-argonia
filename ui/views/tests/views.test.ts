// L1: the four views over the schema's fixtures (1.2 §b-e), with no browser. Every push fixture renders and shows
// what it carried; every intent a view can send has the schema's shape (encodeIntent accepts it) and every fixture
// intent is one a view produces; the dialogue window renders 300 topics as 300 buttons. The layout itself (no break
// at 300 topics, the four viewports, the minimum text size) is the L3 harness's (tools/ui_harness).
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import {
  encodeIntent, messageTable, type ChartState, type DialogueState, type HudState, type IntentMessage,
  type JournalState, type PushMessage,
} from "../../schema/generated/messages.ts";
import { esc, intentsIn, textOf } from "../core/html.ts";
import { remFor } from "../core/scale.ts";
import { type CellIndex, pan, panIntent, revealRects, toPx, toUnits, transform } from "../chart/geom.ts";
import { render as chart } from "../chart/render.ts";
import { backIntent, render as dialogue } from "../dialogue/render.ts";
import { barLength, render as hud, renderBars } from "../hud/render.ts";
import { render as journal, turn } from "../journal/render.ts";

const root = new URL("../../../", import.meta.url);
type Fixture = { states: Record<string, PushMessage>; intents: Record<string, IntentMessage> };
const fx = (s: string): Fixture => JSON.parse(readFileSync(new URL(`ui/fixtures/${s}.json`, root), "utf8"));
const screens = ["dialogue", "journal", "hud", "chart"] as const;

// Every HTML a push can produce (the dialogue's with the persuasion panel open as well), keyed by fixture state.
function renders(screen: string, m: PushMessage): string[] {
  switch (m.type) {
    case "dialogue.state": return [dialogue(m.body), dialogue(m.body, { persuading: true })];
    case "journal.state": return [journal(m.body)];
    case "hud.state": return [hud(m.body)];
    case "hud.bars": return [renderBars(m.body.bars)];
    case "chart.state": return [chart(m.body)];
  }
  throw new Error(`${screen}: no view renders ${(m as PushMessage).type}`);
}

// The intents a view sends outside its buttons: Escape/B, page-turn keys, a chart pan.
function programmatic(m: PushMessage): IntentMessage[] {
  const out: (IntentMessage | null)[] = [];
  if (m.type === "dialogue.state") out.push(backIntent(m.body));
  if (m.type === "journal.state") out.push(turn(m.body, -1), turn(m.body, 1), { type: "view.close", v: 1, body: { view: "journal" } });
  if (m.type === "chart.state") out.push(panIntent(m.body.view), { type: "view.close", v: 1, body: { view: "chart" } });
  return out.filter((x): x is IntentMessage => x !== null);
}

const ok = (m: unknown, where: string) => {
  const r = encodeIntent(m as IntentMessage);
  assert.ok(r.ok, `${where}: ${r.ok ? "" : r.error}`);
};

test("every push fixture renders through its view, and every schema push has a view", () => {
  const rendered = new Set<string>();
  for (const s of screens) {
    for (const [name, m] of Object.entries(fx(s).states)) {
      for (const html of renders(s, m)) assert.ok(html.length > 20, `${s}.${name} rendered nothing`);
      rendered.add(m.type);
    }
  }
  for (const m of messageTable.filter((x) => x.dir === "push")) assert.ok(rendered.has(m.type), `${m.type}: no view`);
});

test("each view shows what the push carried", () => {
  for (const [name, m] of Object.entries(fx("dialogue").states)) {
    const s = (m as { body: DialogueState }).body;
    const t = textOf(dialogue(s, { persuading: true }));
    assert.ok(t.includes(s.speaker.name), name);
    for (const e of s.entries) for (const r of e.runs) assert.ok(t.includes(r.text.trim()), `${name}: ${r.text}`);
    for (const tp of s.topics) assert.ok(t.includes(tp.label), `${name}: topic ${tp.label}`);
    assert.ok(t.includes(`Disposition ${s.disposition.value}`), name);
    assert.equal(t.includes("Goodbye"), s.canLeave, `${name}: Goodbye iff canLeave`);
    if (s.persuasion.available) for (const o of s.persuasion.options) assert.ok(t.includes(o.label), `${name}: ${o.label}`);
  }
  for (const [name, m] of Object.entries(fx("journal").states)) {
    const s = (m as { body: JournalState }).body;
    const t = textOf(journal(s));
    for (const e of s.entries) assert.ok(t.includes(e.date.text) && t.includes(e.questName), name);
    if (s.tab === "quests") for (const q of s.quests) {
      assert.ok(t.includes(q.name), name);
      if (q.directions) assert.ok(t.includes(q.directions), `${name}: directions`);
    }
    assert.ok(t.includes(`${s.page + 1} of ${s.pageCount}`), name);
  }
  for (const [name, m] of Object.entries(fx("hud").states)) {
    if (m.type !== "hud.state") continue;
    const s = (m as { body: HudState }).body;
    const html = hud(s), t = textOf(html);
    if (!s.visible) { assert.match(html, /hud hidden/); continue; }
    assert.equal((html.match(/class="bar /g) ?? []).length, s.bars.filter((b) => b.shown).length, `${name}: bars`);
    for (const e of s.effects) assert.ok(t.includes(e.label), name);
    for (const n of s.notices) assert.ok(t.includes(n.text), name);
    if (s.banner) assert.ok(t.includes(s.banner.name), name);
    if (s.prompt) {
      assert.ok(t.includes(s.prompt.verb) && t.includes(s.prompt.target), name);
      for (const g of s.prompt.inputs) assert.ok(html.includes(`data-device="${g.device}" data-glyph="${g.glyph}"`), name);
    }
    assert.ok(t.includes(String(s.vastei.carried)), name);
    assert.equal(html.includes('class="sneak"'), s.sneak.sneaking, `${name}: the eye iff sneaking`);
    assert.doesNotMatch(html, /compass|marker/i, `${name}: no compass, no marker`);
  }
  for (const [name, m] of Object.entries(fx("chart").states)) {
    const s = (m as { body: ChartState }).body;
    const html = chart(s);
    for (const p of s.places) assert.equal(html.includes(`data-place="${p.id}"`), p.discovered, `${name}: ${p.id}`);
    assert.doesNotMatch(html, /player|marker/i, `${name}: no player marker (C9)`);
  }
});

test("every intent a view sends has the schema's shape, and every fixture intent is one a view sends", () => {
  for (const s of screens) {
    const f = fx(s);
    const sent: string[] = [];
    for (const [name, m] of Object.entries(f.states)) {
      for (const html of renders(s, m)) for (const i of intentsIn(html)) { ok(i, `${s}.${name}`); sent.push(JSON.stringify(i)); }
      for (const i of programmatic(m)) { ok(i, `${s}.${name} (programmatic)`); sent.push(JSON.stringify(i)); }
    }
    for (const [name, i] of Object.entries(f.intents)) {
      const want = JSON.stringify(i);
      const has = sent.some((x) => JSON.stringify(JSON.parse(x)) === want) ||
        (i.type === "chart.pan" && sent.some((x) => JSON.parse(x).type === "chart.pan"));
      assert.ok(has, `${s}: fixture intent ${name} (${want}) is never sent`);
    }
  }
});

test("the dialogue window renders 300 topics, each a button sending its own topic", () => {
  const s = (fx("dialogue").states.threeHundredTopics as { body: DialogueState }).body;
  assert.equal(s.topics.length, 300);
  const html = dialogue(s);
  const topics = intentsIn(html).filter((i) => (i as IntentMessage).type === "dialogue.topic") as { body: { topic: string } }[];
  assert.equal(topics.length, 300);
  assert.equal(new Set(topics.map((t) => t.body.topic)).size, 300);
  assert.equal((html.match(/data-key="topic:/g) ?? []).length, 300);
});

test("bars grow with their stat's maximum; text is escaped", () => {
  const b = (max: number) => barLength({ kind: "health", current: 1, max, shown: true });
  assert.ok(b(200) > b(120) && b(120) > b(80));
  const s = (fx("dialogue").states.greeting as { body: DialogueState }).body;
  const evil = { ...s, speaker: { id: "x", name: `<img src=x onerror="alert(1)">` } };
  const html = dialogue(evil);
  assert.ok(!html.includes("<img") && html.includes(esc(evil.speaker.name)));
});

test("no Nordic or Skyrim word in what the views draw", () => {
  const NORDIC = /\b(skyrim|nord|nordic|dragonborn|septim|jarl|hold|whiterun|tamriel's north|thane|dovah)\b/i;
  for (const s of screens) for (const [name, m] of Object.entries(fx(s).states)) {
    for (const html of renders(s, m)) {
      // The place names and lines are the world db's; the static strings are ours: test the HTML minus the data.
      assert.doesNotMatch(textOf(html).replace(/Stormhold/g, ""), NORDIC, `${s}.${name}`);
    }
  }
});

test("the type scale: 1rem meets 1.9 mm on the folded Magic V5 and 28 px at 1080p", () => {
  const mm = (px: number, ppi: number) => (px / ppi) * 25.4;
  assert.ok(mm(remFor(2376, 1060), 404) >= 1.9, `folded ${mm(remFor(2376, 1060), 404)}`);
  assert.ok(mm(remFor(2352, 2172), 403) >= 1.9);
  assert.ok(remFor(1920, 1080) >= 28);
});

test("chart geometry: cells map to the index's rects, a pan stays in bounds, zoom clamps", () => {
  const cells: CellIndex["cells"] = {};
  for (let x = -2; x <= 2; x++) for (let y = -2; y <= 2; y++) cells[`${x},${y}`] = [100 + 32 * x, 100 - 32 * y, 32, 32];
  const ix: CellIndex = { size: 200, cells };
  assert.deepEqual(toPx(ix, 0, 0), [100, 132]);
  assert.deepEqual(toUnits(ix, ...toPx(ix, 1.5, -0.25)), [1.5, -0.25]);
  const { rects, unknown } = revealRects(ix, [{ x: 0, y: 0 }, { x: 9, y: 9 }]);
  assert.deepEqual(rects, [[100, 100, 32, 32]]);
  assert.deepEqual(unknown, ["9,9"]);
  const v = { centreX: 0, centreY: 0, zoom: 1 };
  const t = transform(ix, v, 400, 200);
  assert.equal(t.scale, 1);
  const far = pan(ix, v, 400, 200, 1e6, -1e6, 1000);
  assert.equal(far.zoom, 16);
  const [px, py] = toPx(ix, far.centreX, far.centreY);
  assert.ok(px >= 0 && px <= 200 && py >= 0 && py <= 200);
  ok(panIntent(pan(ix, v, 400, 200, 30, 10, 1.5)), "pan");
  // The paper fills the sheet: a view centred on a corner stops at the edge.
  const edge = transform(ix, { centreX: -2, centreY: 2, zoom: 4 }, 400, 200);
  assert.ok(edge.tx <= 0 && edge.tx >= 400 - 200 * edge.scale && edge.ty <= 0 && edge.ty >= 200 - 200 * edge.scale);
});
