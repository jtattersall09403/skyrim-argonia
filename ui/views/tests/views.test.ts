// L1: the four views over the schema's fixtures (1.2 §b-e), with no browser. Every push fixture renders and shows
// what it carried; every intent a view can send has the schema's shape (encodeIntent accepts it) and every fixture
// intent is one a view produces; the dialogue window renders 300 topics as 300 buttons. The layout itself (no break
// at 300 topics, the four viewports, the minimum text size) is the L3 harness's (tools/ui_harness).
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import {
  encodeIntent, messageTable, type ChartState, type DialogueState, type HudState, type IntentMessage,
  type CharsheetState, type InventoryState, type JournalState, type MagicState, type PushMessage, type SittingState,
} from "../../schema/generated/messages.ts";
import { esc, intentsIn, textOf } from "../core/html.ts";
import { remFor } from "../core/scale.ts";
import { type CellIndex, compositePlan, glide, hits, labelAt, levelFor, placeLabels, pan, panIntent, REVEAL, revealDiscs, revealRects, toPx, toUnits, toward, transform, visibleTiles, ZOOM_MAX } from "../chart/geom.ts";
import { discTransform, onDisc, REACH, turnTo } from "../hud/minimap.ts";
import { ME } from "../hud/me.ts";
import { render as chart } from "../chart/render.ts";
import { backIntent, filterTopics, render as dialogue } from "../dialogue/render.ts";
import { barLength, FILL_GLIDE, isLow, motion, render as hud, renderBars, shimmer, TRAIL_FOLLOW } from "../hud/render.ts";
import { render as journal, ribbonStep, searchIntent, turn } from "../journal/render.ts";
import { done as sittingDone, render as sitting } from "../sitting/render.ts";
import { close as magicClose, render as magic } from "../magic/render.ts";
import { close as invClose, detail as invDetail, render as inventory, step as invStep, TABS as invTabs, visible as invVisible } from "../inventory/render.ts";
import { close as charClose, render as charsheet, step as charStep, TABS as charTabs } from "../charsheet/render.ts";
import { close as systemClose, render as system } from "../system/render.ts";
import { clamp as waitClamp, close as waitClose, render as wait } from "../wait/render.ts";

const root = new URL("../../../", import.meta.url);
type Fixture = { states: Record<string, PushMessage>; intents: Record<string, IntentMessage> };
const fx = (s: string): Fixture => JSON.parse(readFileSync(new URL(`ui/fixtures/${s}.json`, root), "utf8"));
const screens = ["dialogue", "journal", "hud", "chart", "sitting", "magic", "system", "wait", "inventory", "charsheet"] as const;

// Every HTML a push can produce (the dialogue's with the persuasion panel open as well), keyed by fixture state.
function renders(screen: string, m: PushMessage): string[] {
  switch (m.type) {
    case "dialogue.state": return [dialogue(m.body), dialogue(m.body, { persuading: true })];
    case "journal.state": return [journal(m.body)];
    case "hud.state": return [hud(m.body)];
    case "hud.bars": return [renderBars(m.body.bars)];
    case "hud.minimap": return [];   // drawn on a canvas (minimap.ts); its geometry is tested below
    case "chart.state": return [chart(m.body)];
    case "sitting.state": return [sitting(m.body)];
    case "magic.state": return [magic(m.body)];
    case "system.state": return [system(m.body)];
    case "inventory.state": return invTabs.map(([tab]) => inventory(m.body, tab));
    case "charsheet.state": return charTabs.map(([tab]) => charsheet(m.body, tab));
    case "wait.state": return [wait(m.body), wait(m.body, 1), wait(m.body, 3), wait(m.body, m.body.max)];
  }
  throw new Error(`${screen}: no view renders ${(m as PushMessage).type}`);
}

// The intents a view sends outside its buttons: Escape/B, page-turn keys, a chart pan.
function programmatic(m: PushMessage): IntentMessage[] {
  const out: (IntentMessage | null)[] = [];
  if (m.type === "dialogue.state") out.push(backIntent(m.body));
  if (m.type === "journal.state") out.push(turn(m.body, -1), turn(m.body, 1), ribbonStep(m.body, -1), ribbonStep(m.body, 1),
    searchIntent(m.body, "c"), searchIntent(m.body, ""), { type: "view.close", v: 1, body: { view: "journal" } });
  if (m.type === "sitting.state") out.push(sittingDone());
  if (m.type === "magic.state") out.push(magicClose());
  if (m.type === "system.state") out.push(systemClose());
  if (m.type === "inventory.state") out.push(invClose());
  if (m.type === "charsheet.state") out.push(charClose());
  if (m.type === "wait.state") out.push(waitClose());
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
    for (const g of s.groups) {
      assert.ok(t.includes(g.label), `${name}: group ${g.label}`);
      for (const q of g.quests) assert.ok(t.includes(q.name), `${name}: ${q.name}`);
    }
    if (s.quest) {
      if (s.quest.directions) assert.ok(t.includes(s.quest.directions), `${name}: directions`);
      for (const e of s.quest.entries) assert.ok(t.includes(e.date.text) && t.includes(e.runs[0].text), `${name}: entry`);
    }
    if (s.tab === "all") assert.ok(t.includes(`${s.page + 1} of ${s.pageCount}`), name);
    for (const r of ["Current", "Finished", "All entries", "Topics"]) assert.ok(t.includes(r), `${name}: ribbon ${r}`);
    if (s.search !== undefined) assert.ok(t.includes(`${s.matches} found`), `${name}: the count`);
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
  for (const [name, m] of Object.entries(fx("sitting").states)) {
    const s = (m as { body: SittingState }).body;
    const html = sitting(s), t = textOf(html);
    assert.ok(t.includes(`Level ${s.level}`) && t.includes(String(s.vastei)), name);
    assert.ok(t.includes(String(s.health.before)) && t.includes(String(s.health.after)), name);
    if (s.notice) assert.ok(t.includes(s.notice), name);
    for (const a of s.attributes) {
      assert.ok(t.includes(a.name) && t.includes(`+${a.bought} / ${a.cap}`) && t.includes(String(a.cost)), `${name}: ${a.id}`);
      assert.equal(intentsIn(html).some((i) => JSON.stringify(i).includes(`"attribute":"${a.id}"`)), a.refusal === undefined, `${name}: ${a.id} Buy iff no refusal`);
    }
    assert.equal(intentsIn(html).filter((i) => (i as IntentMessage).type === "sitting.done").length, 1, name);
  }
  // Our magic pane: Powers, then Morrowind's six schools in order (Mysticism among them), every spell with its cost,
  // a right-hand and a left-hand equip per spell and a voice equip per power, the active effects, the notice.
  for (const [name, m] of Object.entries(fx("magic").states)) {
    const s = (m as { body: MagicState }).body;
    const html = magic(s), t = textOf(html);
    const heads = [...html.matchAll(/<h3 class="shead">([^<]*)<\/h3>/g)].map((x) => x[1]);
    assert.deepEqual(heads, ["Alteration", "Conjuration", "Destruction", "Illusion", "Mysticism", "Restoration"], name);
    assert.ok(t.indexOf("Powers") < t.indexOf("Alteration"), `${name}: Powers first`);
    const sent = intentsIn(html) as IntentMessage[];
    for (const g of s.groups) for (const sp of g.spells) {
      assert.ok(t.includes(sp.name) && t.includes(String(sp.cost)), `${name}: ${sp.name}`);
      for (const hand of ["right", "left"]) assert.ok(sent.some((i) => JSON.stringify(i) === JSON.stringify({ type: "magic.equip", v: 1, body: { spell: sp.id, hand } })), `${name}: ${sp.id} ${hand}`);
    }
    for (const p of s.powers) assert.ok(sent.some((i) => JSON.stringify(i).includes(`"spell":"${p.id}","hand":"voice"`)), `${name}: ${p.id}`);
    for (const e of s.effects) assert.ok(t.includes(e.name), `${name}: ${e.name}`);
    if (s.notice) assert.ok(t.includes(s.notice), name);
  }
  const kit = (fx("magic").states.kit as { body: MagicState }).body;
  const kt = textOf(magic(kit));
  const mys = textOf(magic(kit).split('<li class="school mysticism">')[1].split('<li class="school restoration">')[0]);
  assert.ok(mys.startsWith("Mysticism") && mys.includes("Mark 500") && mys.includes("Recall R 250"), `Mark and Recall under Mysticism: ${mys}`);
  assert.ok(kt.includes("Left Flames") && kt.includes("Right Recall") && kt.includes("Power Histskin"), "the readied hands");
  // Our inventory: ten tabs in order (All, then the nine categories) that cycle both ways, every stack with its name,
  // count, weight and value, a use intent per row and a drop in the detail, the carry line and gold; empty says so.
  assert.deepEqual(invTabs.map(([k]) => k), ["all", "weapons", "apparel", "potions", "scrolls", "food", "ingredients", "books", "keys", "misc"]);
  assert.equal(invStep("all", -1), "misc"); assert.equal(invStep("misc", 1), "all"); assert.equal(invStep("food", 1), "ingredients");
  for (const [name, m] of Object.entries(fx("inventory").states)) {
    const s = (m as { body: InventoryState }).body;
    for (const [tab] of invTabs) {
      const html = inventory(s, tab), t = textOf(html), rows = invVisible(s, tab);
      assert.equal((html.match(/<li class="row/g) ?? []).length, rows.length, `${name}/${tab}: one row per stack`);
      assert.equal((html.match(/data-list="items"/g) ?? []).length, 1, `${name}/${tab}: one list`);
      assert.equal((html.match(/data-ui="tab"/g) ?? []).length, 10, `${name}/${tab}: ten tab buttons`);
      const sent = intentsIn(html) as IntentMessage[];
      for (const i of rows) {
        assert.ok(t.includes(i.name) && t.includes(String(i.value)), `${name}/${tab}: ${i.name}`);
        assert.ok(sent.some((x) => JSON.stringify(x) === JSON.stringify({ type: "inventory.use", v: 1, body: { item: i.id } })), `${name}/${tab}: use ${i.id}`);
      }
      if (!rows.length) assert.ok(t.includes("Nothing carried here") && t.includes("Nothing to show"), `${name}/${tab}: empty says so`);
      assert.ok(t.includes(`Carry weight ${s.carried} / ${s.capacity}`) && t.includes(`Gold ${s.gold}`), `${name}/${tab}: carry and gold`);
    }
    const first = invVisible(s, "all")[0];
    if (first) {
      const d = invDetail(first), di = intentsIn(d) as IntentMessage[];
      assert.ok(di.some((x) => x.type === "inventory.drop") && di.some((x) => x.type === "inventory.use"), `${name}: detail use and drop`);
      assert.ok(textOf(inventory(s, "all", s.items[1]?.id)).includes(s.items[1] ? s.items[1].name : ""), name);
    }
  }
  {
    const full = (fx("inventory").states.full as { body: InventoryState }).body;
    assert.ok(full.items.length >= 55 && new Set(full.items.map((i) => i.category)).size === 9, "full: about sixty stacks over nine categories");
    assert.ok(full.items.some((i) => i.equipped) && inventory(full, "all").includes('class="eq" title="Equipped"'), "equipped mark");
    assert.ok(inventory(full, "weapons").includes('class="tab on"'), "the current tab is marked");
    const one = (fx("inventory").states.oneCategory as { body: InventoryState }).body;
    assert.ok(one.items.every((i) => i.category === "weapons") && invVisible(one, "potions").length === 0);
    assert.ok(textOf(inventory({ ...full, carried: 310, capacity: 300 })).length > 0 && inventory({ ...full, carried: 310, capacity: 300 }).includes("carry over"));
  }
  // Our character sheet: three tabs that cycle, the side column, each tab's list with a focusable row per entry, a
  // take intent on exactly the perks that can be taken.
  assert.deepEqual(charTabs.map(([k]) => k), ["attributes", "skills", "perks"]);
  assert.equal(charStep("attributes", -1), "perks"); assert.equal(charStep("perks", 1), "attributes");
  for (const [name, m] of Object.entries(fx("charsheet").states)) {
    const s = (m as { body: CharsheetState }).body;
    const at = charsheet(s, "attributes"), sk = charsheet(s, "skills"), pk = charsheet(s, "perks");
    const side = textOf(at);
    assert.ok(side.includes(s.name) && side.includes(s.race) && side.includes(`Level ${s.level}`) && side.includes(`${Math.round(s.health)}/${Math.round(s.healthMax)}`), `${name}: side column`);
    assert.equal(s.attributes.length, 7); assert.equal(s.skills.length, 27);
    for (const a of s.attributes) assert.ok(at.includes(`data-key="a:${a.id}"`) && textOf(at).includes(a.name), `${name}: ${a.id}`);
    for (const k of s.skills) assert.ok(sk.includes(`data-key="s:${k.id}"`) && textOf(sk).includes(k.name), `${name}: ${k.id}`);
    assert.equal((sk.match(/data-list="skills"/g) ?? []).length, 1); assert.equal((pk.match(/data-list="perks"/g) ?? []).length, 1);
    const take = (intentsIn(pk) as IntentMessage[]).filter((x) => x.type === "charsheet.perk").map((x) => (x as { body: { perk: string } }).body.perk);
    assert.deepEqual(take, s.perks.filter((p) => p.available && !p.taken).map((p) => p.id), `${name}: take only what can be taken`);
    for (const p of s.perks) assert.ok(pk.includes(`data-key="p:${p.id}"`) && textOf(pk).includes(p.name) && textOf(pk).includes(p.description), `${name}: ${p.name}`);
  }
  assert.equal((intentsIn(charsheet((fx("charsheet").states.main as { body: CharsheetState }).body, "perks")) as IntentMessage[]).filter((x) => x.type === "charsheet.perk").length, 0, "main: none takeable");
  assert.equal((intentsIn(charsheet((fx("charsheet").states.perkAvailable as { body: CharsheetState }).body, "perks")) as IntentMessage[]).filter((x) => x.type === "charsheet.perk").length, 2, "perkAvailable: two takeable");
  for (const [name, m] of Object.entries(fx("chart").states)) {
    const s = (m as { body: ChartState }).body;
    const html = chart(s);
    // Every pushed place is a discovered one and has its marker; nothing else is marked; no place travels.
    assert.equal((html.match(/class="place"/g) ?? []).length, s.places.length, `${name}: one marker per discovered place`);
    for (const p of s.places) assert.ok(html.includes(`data-place="${p.id}"`) && html.includes('class="pin"'), `${name}: ${p.id}`);
    assert.equal(html.includes("data-player"), s.player !== undefined, `${name}: the player's marker`);
    assert.doesNotMatch(html, /travel|quest/i, `${name}: no fast travel, no quest marker`);
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

test("typed letters narrow the topic list (1.2 §0's filter); the filter shows, the intents stay the topics'", () => {
  const s = (fx("dialogue").states.threeHundredTopics as { body: DialogueState }).body;
  const labels = s.topics.map((t) => t.label);
  const want = labels.filter((l) => l.toLowerCase().includes("2"));
  assert.ok(want.length > 0 && want.length < 300);
  assert.deepEqual(filterTopics(s.topics, "2").map((t) => t.label), want);
  assert.equal(filterTopics(s.topics, "").length, 300);
  const html = dialogue(s, { persuading: false, filter: "2" });
  assert.equal((html.match(/data-key="topic:/g) ?? []).length, want.length);
  assert.ok(html.includes('<div class="filter"'));
  assert.ok(!dialogue(s).includes('class="filter"'));
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

test("the type scale: 1rem meets 2.5 mm on the Magic V5 and 28 px at 1080p", () => {
  const mm = (px: number, ppi: number) => (px / ppi) * 25.4;
  assert.ok(mm(remFor(2376, 1060), 404) >= 2.5, `folded ${mm(remFor(2376, 1060), 404)}`);
  assert.ok(mm(remFor(2352, 2172), 403) >= 2.5);
  assert.ok(remFor(1920, 1080) >= 28);
  // A 21:9 monitor keeps the desktop scale (1080 / 34), not the phone's (1080 / 26); the fold, at 1:1 or at its own
  // density, keeps the phone's.
  assert.equal(remFor(2560, 1080), 1080 / 34);
  assert.equal(remFor(3440, 1440), 1440 / 34);
  assert.equal(remFor(2560, 1080, 2), 1080 / 34);
  assert.equal(remFor(2376, 1060), 1060 / 26);
  assert.equal(remFor(2376 / 2.6, 1060 / 2.6, 2.6), (1060 / 2.6) / 26);
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
  // zoom 1 contains: the whole 200 px canvas in the 200-tall sheet, top to bottom, nothing cut off (play test 1 item 9)
  assert.equal(t.scale, 1);
  assert.ok(t.ty === 0 && t.ty + 200 * t.scale <= 200 && t.tx === 100);
  const tall = transform(ix, v, 300, 900);
  assert.ok(tall.tx === 0 && tall.tx + 200 * tall.scale <= 300, "a tall sheet: the canvas fits its width");
  const far = pan(ix, v, 400, 200, 1e6, -1e6, 1000);
  assert.equal(far.zoom, ZOOM_MAX);
  // Zooming in goes to the player; out keeps the centre and stops at the whole province.
  const me = { x: 1.5, y: -1, heading: 90 };
  assert.deepEqual(toward(v, me, 1.5), { centreX: 1.5, centreY: -1, zoom: 1.5 });
  assert.deepEqual(toward({ centreX: 1.5, centreY: -1, zoom: 1.2 }, me, 1 / 1.5), { centreX: 1.5, centreY: -1, zoom: 1 });
  assert.deepEqual(toward(v, undefined, 2), { ...v, zoom: 2 });
  // The minimap (owner look 1): the player at the square's centre, 2 * REACH cells across, north up whatever the
  // heading; the arrow turns the shorter way.
  const dt = discTransform(ix, { x: 0, y: 0, heading: 0 }, 100);
  assert.equal(dt.scale, 100 / (2 * REACH * 32));
  const north = { x: 0, y: 2 };
  for (const heading of [0, 90, 225]) {
    const n = onDisc(ix, { x: 0, y: 0, heading }, 100, north)!;
    assert.ok(Math.abs(n[0] - 50) < 1e-9 && n[1] < 50, `north is up facing ${heading}`);
  }
  assert.ok(onDisc(ix, { x: 0, y: 0, heading: 0 }, 100, { x: REACH - 0.1, y: REACH - 0.1 }), "a corner is inside the square");
  assert.equal(onDisc(ix, { x: 0, y: 0, heading: 0 }, 100, { x: REACH + 1, y: 0 }), null, "past the edge");
  assert.equal(turnTo(359, 1), 361, "359 to 1 turns 2 degrees forward");
  assert.equal(turnTo(10, 350), -10, "10 to 350 turns 20 degrees back");
  const [px, py] = toPx(ix, far.centreX, far.centreY);
  assert.ok(px >= 0 && px <= 200 && py >= 0 && py <= 200);
  ok(panIntent(pan(ix, v, 400, 200, 30, 10, 1.5)), "pan");
  // Lettering: a city's small drawn label is covered by ours, a large one is left; a discovered place with no drawn
  // label is lettered beside it; an undiscovered non-city is never lettered.
  ix.places = { city: { city: true, label: [10, 10, 50, 20] }, hut: { city: false, label: null } };
  const t1 = { scale: 1, tx: 0, ty: 0 };
  assert.deepEqual(labelAt(ix, t1, "city", 0, 0, false, 20)?.cover, [10, 10, 40, 10]);
  assert.equal(labelAt(ix, { scale: 4, tx: 0, ty: 0 }, "city", 0, 0, false, 20), null);
  assert.equal(labelAt(ix, t1, "hut", 0, 0, false, 20), null);
  assert.ok(labelAt(ix, t1, "hut", 0, 0, true, 20)!.left > toPx(ix, 0, 0)[0]);
  // The paper fills the sheet: a view centred on a corner stops at the edge.
  const edge = transform(ix, { centreX: -2, centreY: 2, zoom: 4 }, 400, 200);
  assert.ok(edge.tx <= 0 && edge.tx >= 400 - 200 * edge.scale && edge.ty <= 0 && edge.ty >= 200 - 200 * edge.scale);
});

test("label collisions: by priority, a clashing label moves to a free spot or is dropped, none overlap", () => {
  // Blackrose and Lilmoth on top of each other: the first keeps its spot, the second moves clear of it.
  const boxes = [{ id: "blackrose", x: 100, y: 100, w: 120, h: 30 }, { id: "lilmoth", x: 110, y: 105, w: 80, h: 30 }];
  const spots = placeLabels(boxes, 400, 300);
  assert.deepEqual(spots.get("blackrose"), [0, 0]);
  const moved = spots.get("lilmoth")!;
  assert.ok(moved && (moved[0] !== 0 || moved[1] !== 0));
  const at = boxes.map((b) => ({ ...b, x: b.x + (spots.get(b.id)?.[0] ?? 0), y: b.y + (spots.get(b.id)?.[1] ?? 0) }));
  assert.ok(!hits(at[0], at[1]));
  // A place's pin is an obstacle: the label over it moves off it.
  const pin = { id: "", x: 100, y: 100, w: 20, h: 20 };
  const off = placeLabels([{ id: "claywater", x: 95, y: 95, w: 120, h: 30 }], 400, 300, 2, [pin]).get("claywater")!;
  assert.ok(off && !hits({ id: "c", x: 95 + off[0], y: 95 + off[1], w: 120, h: 30 }, pin));
  // Boxed in on a sheet too small for any candidate: dropped, never overlapping.
  const tight = placeLabels([{ id: "a", x: 0, y: 0, w: 100, h: 30 }, { id: "b", x: 0, y: 0, w: 100, h: 30 }], 100, 30);
  assert.equal(tight.get("b"), null);
  // A crowd: whatever is placed never overlaps.
  const crowd = Array.from({ length: 30 }, (_, i) => ({ id: `p${i}`, x: 50 + (i % 5) * 20, y: 50 + (i % 3) * 10, w: 90, h: 24 }));
  const s2 = placeLabels(crowd, 500, 400);
  const kept = crowd.filter((b) => s2.get(b.id)).map((b) => ({ ...b, x: b.x + s2.get(b.id)![0], y: b.y + s2.get(b.id)![1] }));
  for (let i = 0; i < kept.length; i++) for (let j = i + 1; j < kept.length; j++) assert.ok(!hits(kept[i], kept[j]), `${i}/${j}`);
  assert.ok(kept.length >= 3);
});

test("the HUD's bars glide like Skyrim's meter, the trail holds then follows a loss, vastei shimmers by the gain", () => {
  // A loss: the fill glides over the gap between pushes, the trail waits then follows; a rise carries both.
  assert.deepEqual(motion(80, 50), { fill: FILL_GLIDE, trail: TRAIL_FOLLOW });
  assert.deepEqual(motion(50, 55), { fill: FILL_GLIDE, trail: FILL_GLIDE });
  assert.deepEqual(motion(50, 52, 0.4), { fill: FILL_GLIDE, trail: null }, "a regen tick in the hold leaves the trail");
  assert.deepEqual(motion(undefined, 55), { fill: FILL_GLIDE, trail: FILL_GLIDE });
  assert.match(FILL_GLIDE, /0\.24s linear/, "longer than the 0.2 s push gap, so the glide never stops between pushes");
  // The rows render slim with no regeneration class; a push renders the meter's own widths.
  const h = (current: number): HudState["bars"] => [{ kind: "health", current, max: 100, shown: true }];
  assert.match(renderBars(h(30), { health: { fill: 30, trail: 80 } }), /class="trail" style="width:80\.0%"[^]*class="fill" style="width:30\.0%"/);
  assert.doesNotMatch(renderBars(h(40)), /regen/);
  assert.ok(isLow(h(25)) && !isLow(h(26)), "low at a quarter");
  assert.match(hud({ ...(fx("hud").states.lowHealth as { body: HudState }).body }), /class="hud low"/);
  // Vastei: no "+N"; the shimmer grows with the gain, faint for a few on a large purse.
  const small = shimmer(5, 1005), big = shimmer(800, 900);
  assert.ok(small >= 0.15 && small < 0.35 && big > 0.8 && big <= 1, `${small} ${big}`);
  assert.equal(shimmer(undefined, 10), 0);
  const play = (fx("hud").states.play as { body: HudState }).body;
  const up = hud({ ...play, vastei: { carried: 900, gained: 800 } });
  assert.ok(!/\+800/.test(up) && /data-glow="0\.\d+"/.test(up), "a shimmer, no number");
  assert.ok(up.indexOf("data-bars") < up.indexOf('class="vastei'), "vastei under the bars");
  // The minimap's arrow is lane 1.12-chart's shared drawing.
  const file = readFileSync(new URL("../core/player-marker.svg", import.meta.url), "utf8");
  for (const d of file.match(/ d="[^"]+"/g)!) assert.ok(ME.includes(d), d);
});

// 1.12 §6's rulings on the journal: four ribbons, a failed quest marked, the opened quest's latest direction before
// its dated entries, the search field carrying what was typed, and no statistics page or "show on map".
test("the journal: ribbons, grouping, directions first, search, no map or statistics", () => {
  const st = fx("journal").states as Record<string, { body: JournalState }>;
  const lf = journal(st.currentLf83.body);
  const dir = lf.indexOf('class="dir"'), first = lf.indexOf('class="entry');
  assert.ok(dir > 0 && first > dir, "the latest direction comes before the entries");
  const failed = journal(st.finishedFailed.body);
  assert.match(failed, /class="quest failed[^"]*"[\s\S]*?Failed/, "the failed quest is marked");
  assert.match(textOf(failed), /Failed\./, "its last entry says Failed");
  assert.match(journal(st.searchAll.body), /value="clay"/, "the field shows the search");
  assert.ok(textOf(journal(st.topics.body)).includes("Topics you hear"), "Topics is a placeholder");
  for (const [name, m] of Object.entries(st)) {
    const html = journal(m.body);
    assert.doesNotMatch(html, /show on map|statistic|marker/i, `${name}: no map link, no statistics`);
    for (const i of intentsIn(html)) ok(i, `${name}: intent`);
  }
  assert.deepEqual(searchIntent(st.currentLf83.body, "well"),
    { type: "journal.page", v: 2, body: { tab: "current", page: 0, quest: "quest.local.lf83", search: "well" } });
  assert.equal(turn(st.current.body, 1), null, "only the diary turns pages");
});

test("the dialogue window: frame style, Barter as a service, Goodbye", () => {
  const st = fx("dialogue").states as Record<string, { body: DialogueState }>;
  const html = dialogue(st.answer.body);
  assert.match(html, /class="dialogue frame"/);
  assert.doesNotMatch(html, /class="[^"]*\bpaper\b/, "no parchment");
  assert.ok(intentsIn(html).some((i) => JSON.stringify(i) === JSON.stringify(fx("dialogue").intents.barter)), "Barter sends dialogue.service");
  assert.ok(!dialogue(st.forced.body).includes("Barter"), "no Barter for a speaker without the service");
});

test("chart look 1: the seen land is a disc about each revealed cell; the pyramid level fits the zoom; the glide settles", () => {
  const cells: CellIndex["cells"] = {};
  for (let x = -2; x <= 2; x++) for (let y = -2; y <= 2; y++) cells[`${x},${y}`] = [100 + 32 * x, 100 - 32 * y, 32, 32];
  const ix: CellIndex = { size: 200, cells };
  // one cell stood in uncovers REVEAL cells round it (1.12's single cell was 7 px on the whole chart: never seen)
  assert.deepEqual(revealDiscs(ix, [{ x: 0, y: 0 }]), [[116, 116, (REVEAL + 0.5) * 32]]);
  assert.ok(REVEAL >= 3);
  // the level: the smallest whose pixels reach one per screen pixel, else the largest
  assert.equal(levelFor([1024, 2048, 4096], 4096, 0.22), 1024);
  assert.equal(levelFor([1024, 2048, 4096], 4096, 0.45), 2048);
  assert.equal(levelFor([1024, 2048, 4096], 4096, 8 * 0.22), 4096);
  // the tiles a view shows: the whole chart at scale 1 in its own size is every tile; a corner view is one
  assert.equal(visibleTiles(1024, 512, 200, { scale: 1, tx: 0, ty: 0 }, 200, 200).length, 4);
  assert.deepEqual(visibleTiles(1024, 512, 200, { scale: 4, tx: 0, ty: 0 }, 100, 100), [[0, 0]]);
  // the glide: part way after one frame, at the target after a while, never past it
  const a = { centreX: 0, centreY: 0, zoom: 1 }, b = { centreX: 10, centreY: -4, zoom: 4 };
  const one = glide(a, b, 16);
  assert.ok(one.centreX > 0 && one.centreX < 10 && one.zoom > 1 && one.zoom < 4);
  let v = a;
  for (let i = 0; i < 120; i++) v = glide(v, b, 16);
  assert.deepEqual(v, b);
  assert.ok(ZOOM_MAX <= 8, "past the largest render's pixels the chart goes soft");
});

test("our System pane lists settings, load and the two quits, never Quests; our wait window sends its hours", () => {
  for (const [name, m] of Object.entries(fx("system").states)) {
    if (m.type !== "system.state") continue;
    const html = system(m.body), t = textOf(html);
    for (const e of ["Settings", "Load", "Quit to the main menu", "Quit to the desktop"]) assert.ok(t.includes(e), `${name}: ${e}`);
    assert.ok(!/quest/i.test(t), `${name}: no Quests entry (quests live only in the journal)`);
    assert.equal(/data-key="load" disabled/.test(html), !m.body.canLoad, `${name}: Load off iff no save`);
  }
  for (const [name, m] of Object.entries(fx("wait").states)) {
    if (m.type !== "wait.state") continue;
    const t = textOf(wait(m.body, 3));
    assert.ok(t.includes(m.body.now) && t.includes(m.body.mode === "sleep" ? "Sleep 3 hours" : "Wait 3 hours"), name);
    assert.ok(intentsIn(wait(m.body, 3)).some((i) => JSON.stringify(i) === JSON.stringify({ type: "wait.pick", v: 1, body: { hours: 3 } })), name);
    assert.equal(waitClamp(0, m.body.max), 1);
    assert.equal(waitClamp(99, m.body.max), m.body.max);
    assert.ok(textOf(wait(m.body, 1)).includes("1 hour") && !textOf(wait(m.body, 1)).includes("1 hours"), name);
  }
});

// Owner 2026-11-03 (#37): the sketch is always visible. The mask applies to the `full` layer only, never to `sketch`.
test("chart compositing: the sketch is drawn whole and unmasked, the mask cuts only the detail", () => {
  assert.deepEqual(compositePlan(0), [{ layer: "sketch", masked: false }]);
  for (const n of [1, 10, 400]) {
    assert.deepEqual(compositePlan(n), [{ layer: "sketch", masked: false }, { layer: "full", masked: true }]);
  }
  for (const n of [0, 1, 10]) for (const s of compositePlan(n)) assert.equal(s.masked, s.layer === "full");
  assert.equal(compositePlan(0)[0].layer, "sketch");   // under the detail, never over it
});
