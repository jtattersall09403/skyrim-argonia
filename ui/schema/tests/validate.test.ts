// L1/L2: the views' twin of the schema (1.1 §c). Every mock fixture of 1.2's four screens is accepted on its own
// side and refused on the other; a message not in the schema is refused with the same readable path the C++ twin
// gives (skse/core/tests/test_messages.cpp); encodeIntent refuses before anything leaves a view.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import {
  decodeIntent, decodePush, encodeIntent, encodePush, messageTable, schemaHash, validate,
  type IntentMessage, type PushMessage,
} from "../generated/messages.ts";

const root = new URL("../../../", import.meta.url);
const read = (p: string) => readFileSync(new URL(p, root), "utf8");
const screens = ["dialogue", "journal", "hud", "chart", "sitting"];

const refusal = (r: { ok: boolean; error?: string }): string => (r.ok ? "<accepted>" : (r as { error: string }).error);

test("every fixture is accepted on its side and refused on the other", () => {
  let n = 0;
  const seen = new Set<string>();
  for (const s of screens) {
    const fx = JSON.parse(read(`ui/fixtures/${s}.json`)) as { states: Record<string, unknown>; intents: Record<string, unknown> };
    for (const [name, m] of Object.entries(fx.states)) {
      const wire = JSON.stringify(m);
      assert.equal(refusal(decodePush(wire)), "<accepted>", `${s}.${name}`);
      assert.match(refusal(decodeIntent(wire)), /ArgoniaCore accepts intents only/);
      assert.ok(encodePush(m as PushMessage).ok);
      seen.add((m as { type: string }).type); ++n;
    }
    for (const [name, m] of Object.entries(fx.intents)) {
      const wire = JSON.stringify(m);
      assert.equal(refusal(decodeIntent(wire)), "<accepted>", `${s}.${name}`);
      assert.match(refusal(decodePush(wire)), /an intent is never pushed to a view/);
      const out = encodeIntent(m as IntentMessage);
      assert.ok(out.ok && JSON.stringify(JSON.parse(out.value)) === wire);
      seen.add((m as { type: string }).type); ++n;
    }
  }
  assert.ok(n >= 30);
  for (const m of messageTable) assert.ok(seen.has(m.type), `${m.type} has no fixture`);
});

test("a message not in the schema is refused with the C++ twin's words", () => {
  const cases: [string, string][] = [
    [`{"type":"dialogue.shout","v":1,"body":{}}`, "message type 'dialogue.shout' is not in the schema"],
    [`{"type":"dialogue.goodbye","v":2,"body":{}}`, "dialogue.goodbye version 2: this build speaks version 1"],
    [`{"type":"dialogue.goodbye","v":1,"body":{},"x":0}`, "message.x: not in the schema"],
    [`{"type":"dialogue.goodbye","body":{}}`, "message.v: missing"],
    [`{"type":"dialogue.goodbye","v":1,"body":{"now":true}}`, "dialogue.goodbye body.now: not in the schema"],
    [`{"type":"dialogue.topic","v":1,"body":{}}`, "dialogue.topic body.topic: missing"],
    [`{"type":"dialogue.topic","v":1,"body":{"topic":7}}`, "dialogue.topic body.topic: want a string"],
    [`{"type":"view.close","v":1,"body":{"view":"hud"}}`, "view.close body.view: 'hud' is not one of dialogue, journal, chart"],
    [`{"type":"journal.page","v":1,"body":{"tab":"entries","page":-1}}`, "journal.page body.page: -1 is outside 0.."],
    [`{"type":"journal.page","v":1,"body":{"tab":"entries","page":1.5}}`, "journal.page body.page: want a whole number"],
    [`{"type":"journal.page","v":1,"body":{"tab":"entries","page":1,"questFilter":null}}`, "journal.page body.questFilter: want a string"],
    [`{"type":"chart.pan","v":1,"body":{"view":{"centreX":0,"centreY":0,"zoom":0}}}`, "chart.pan body.view.zoom: 0 is outside 0.05..64"],
    [`{"type":"hud.bars","v":1,"body":{"bars":[{"kind":"health","current":1,"max":2}]}}`, "hud.bars body.bars[0].shown: missing"],
    [`[]`, "message: want an object"],
    [`{`, "message: JSON error"],
  ];
  for (const [wire, why] of cases) {
    const r = validateText(wire);
    assert.ok(r.includes(why), `${wire}\n  got: ${r}\n  want: ${why}`);
  }
});

function validateText(wire: string): string {
  try { return refusal(validate(JSON.parse(wire))); } catch { return refusal(decodePush(wire)); }
}

test("a view sends only what the schema holds", () => {
  assert.match(refusal(encodeIntent({ type: "view.close", v: 1, body: { view: "hud" } } as unknown as IntentMessage)),
    /'hud' is not one of/);
  assert.match(refusal(encodeIntent({ type: "hud.bars", v: 1, body: { bars: [] } } as unknown as IntentMessage)),
    /ArgoniaCore accepts intents only/);
  assert.match(refusal(encodeIntent({ type: "chart.pan", v: 1, body: { view: { centreX: NaN, centreY: 0, zoom: 1 } } })),
    /chart.pan body.view.centreX: want a number/);
  const page: IntentMessage = { type: "journal.page", v: 1, body: { tab: "quests", page: 2, questFilter: undefined } };
  const out = encodeIntent(page);
  assert.ok(out.ok);
  assert.equal(out.value, `{"type":"journal.page","v":1,"body":{"tab":"quests","page":2}}`);
});

test("both twins come from one schema", () => {
  const h = /kSchemaHash = "([0-9a-f]{16})"/.exec(read("skse/core/generated/argonia/core/messages.h"));
  assert.ok(h);
  assert.equal(h[1], schemaHash);
});
