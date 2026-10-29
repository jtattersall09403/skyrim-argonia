// L1: the generator (tools/schema_gen). The tree's twins are current; a stale or missing twin is named with its
// first differing line; a schema the twins cannot carry is refused at generation, not at run time.
import assert from "node:assert/strict";
import { cpSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";
import { bool, int, intent, list, opt, push, ref, str, struct } from "../../../ui/schema/types.ts";
import { emitFamilies } from "../families.ts";
import { render, ROOT, stale } from "../gen.ts";
import { build, SchemaError } from "../model.ts";
import { emitRouter } from "../router.ts";

test("the tree's twins are current", () => {
  assert.deepEqual(stale(render()), []);
});

test("a stale or missing twin is named", () => {
  const files = render();
  const tmp = mkdtempSync(join(tmpdir(), "schema-gen-"));
  try {
    for (const p of files.keys()) cpSync(join(ROOT, p), join(tmp, p), { recursive: true });
    assert.deepEqual(stale(files, tmp), []);
    const h = "skse/core/generated/argonia/core/messages.h";
    writeFileSync(join(tmp, h), files.get(h)!.replace("inline constexpr std::string_view kSchemaHash", "inline constexpr auto kSchemaHash"));
    rmSync(join(tmp, "ui/schema/generated/messages.ts"));
    const bad = stale(files, tmp);
    assert.equal(bad.length, 2);
    assert.match(bad[0], /messages\.h:\d+: stale\n {2}tree: inline constexpr auto kSchemaHash/);
    assert.equal(bad[1], "ui/schema/generated/messages.ts: missing");
  } finally {
    rmSync(tmp, { recursive: true, force: true });
  }
});

const refuses = (f: () => unknown, why: RegExp) => assert.throws(f, (e: unknown) => e instanceof SchemaError && why.test(e.message));

test("the model refuses what the twins cannot carry", () => {
  const a = push("a.state", 1, "", { x: str("") });
  refuses(() => build([a, push("a.state", 1, "", {})]), /declared twice/);
  refuses(() => build([push("a.state", 0, "", {})]), /version must be/);
  refuses(() => build([push("NoScreen", 1, "", {})]), /is not '<screen>.<name>'/);
  refuses(() => build([push("a.state", 1, "", { xs: list(opt(str(""))) })]), /opt is allowed only on a field/);
  refuses(() => build([push("a.state", 1, "", { Bad: str("") })]), /camelCase/);
  refuses(() => build([push("a.state", 1, "", { x: int("", { min: 0.5 }) })]), /safe integer/);
  const s1 = struct("Same", "", { a: bool("") }), s2 = struct("Same", "", { b: bool("") });
  refuses(() => build([push("a.state", 1, "", { p: ref(s1), q: ref(s2) })]), /two different types are named 'Same'/);
  refuses(() => build([push("a.state", 1, "", { aB: str(""), a_b: str("") })]), /camelCase|C\+\+ member/);
  assert.equal(build([a, intent("a.go", 1, "", {})]).structs.length, 2);
});

test("families.json and surfaces.json are checked", () => {
  const fam = (versions: unknown) => JSON.stringify({ families: [{ id: "ABCD", module: "m", versions }] });
  refuses(() => emitFamilies(fam([{ version: 2, layout: [] }])), /run 1, 2, 3/);
  refuses(() => emitFamilies(fam([{ version: 1, layout: [] }, { version: 2, layout: [] }])), /says whether it migrates/);
  refuses(() => emitFamilies(fam([{ version: 1, layout: [{ u32: "a", u8: "b" }] }])), /exactly one kind/);
  refuses(() => emitFamilies(fam([{ version: 1, layout: [{ list: "a", of: [{ u8: "b" }] }] }])), /needs a count/);
  refuses(() => emitFamilies(fam([{ version: 1, layout: [{ list: "a", count: 2, keyed: true, of: [{ f64: "b" }] }] }])),
    /first item is an integer/);
  const router = (surfaces: unknown[]) => JSON.stringify({ kinds: ["menu", "dialogue"], replacements: ["view", "suppressed"],
    hooks: [{ id: "h", mechanism: "m", chunk: "c" }, { id: "dialogueIntercept", mechanism: "m", chunk: "1.3 §b" }], surfaces });
  const dlg = { id: "dialogueMenu", kind: "dialogue", menu: "Dialogue Menu", replacement: "view", by: "dialogue", hook: "dialogueIntercept", chunk: "1.3 §b" };
  const inv = { id: "inv", kind: "menu", menu: "InventoryMenu", replacement: "suppressed", hook: "h", chunk: "c" };
  assert.match(emitRouter(router([dlg, inv])), /HookId::dialogueIntercept/);
  refuses(() => emitRouter(router([inv])), /hook dialogueIntercept carries no surface|dialogueIntercept/);
  refuses(() => emitRouter(router([dlg, { ...inv, hook: "nope" }])), /hook "nope" is not in hooks/);
  refuses(() => emitRouter(router([dlg, inv, { ...inv, id: "inv2" }])), /menu "InventoryMenu" has two rows/);
  refuses(() => emitRouter(router([{ ...dlg, by: "" }, inv])), /names its view/);
  refuses(() => emitRouter(router([dlg, inv, { ...inv, id: "inv" }])), /not a unique camelCase id/);
});
