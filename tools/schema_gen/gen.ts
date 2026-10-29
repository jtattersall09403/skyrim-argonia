// tools/schema_gen: the one generator of the seam's twins (1.1 §b-§d).
//   ui/schema/*.ts               -> skse/core/generated/argonia/core/messages.h, ui/schema/generated/messages.ts
//   skse/core/schema/families.json -> skse/core/generated/argonia/core/family_layouts.h
//   data/router/surfaces.json      -> skse/core/generated/argonia/core/router_table.h
// Usage: node --experimental-strip-types tools/schema_gen/gen.ts [--check]
// --check regenerates in memory and diffs against the tree: exit 1 naming each stale file and its first differing
// line (the gate's step in skse/check.sh).
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { messages } from "../../ui/schema/index.ts";
import { emitCpp } from "./emit_cpp.ts";
import { emitTs } from "./emit_ts.ts";
import { emitFamilies } from "./families.ts";
import { build } from "./model.ts";
import { emitRouter } from "./router.ts";

export const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..");
const GEN = "skse/core/generated/argonia/core";

// Every generated file, by its path from the repo root.
export function render(root: string = ROOT): Map<string, string> {
  const model = build(messages);
  const read = (p: string) => readFileSync(join(root, p), "utf8");
  return new Map([
    [`${GEN}/messages.h`, emitCpp(model)],
    ["ui/schema/generated/messages.ts", emitTs(model)],
    [`${GEN}/family_layouts.h`, emitFamilies(read("skse/core/schema/families.json"))],
    [`${GEN}/router_table.h`, emitRouter(read("data/router/surfaces.json"))],
  ]);
}

// One line per stale or missing file; empty when the tree is current.
export function stale(files: Map<string, string>, root: string = ROOT): string[] {
  const out: string[] = [];
  for (const [path, want] of files) {
    let have: string;
    try { have = readFileSync(join(root, path), "utf8"); } catch { out.push(`${path}: missing`); continue; }
    if (have === want) continue;
    const a = have.split("\n"), b = want.split("\n");
    let i = 0;
    while (i < a.length && i < b.length && a[i] === b[i]) ++i;
    out.push(`${path}:${i + 1}: stale\n  tree: ${a[i] ?? "<end>"}\n  want: ${b[i] ?? "<end>"}`);
  }
  return out;
}

function main(argv: string[]): number {
  const files = render();
  if (argv.includes("--check")) {
    const bad = stale(files);
    if (bad.length) {
      console.error(`schema twins are stale (run node --experimental-strip-types tools/schema_gen/gen.ts):\n${bad.join("\n")}`);
      return 1;
    }
    return 0;
  }
  for (const [path, text] of files) {
    mkdirSync(dirname(join(ROOT, path)), { recursive: true });
    writeFileSync(join(ROOT, path), text);
    console.log(`wrote ${path}`);
  }
  return 0;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) process.exitCode = main(process.argv.slice(2));
