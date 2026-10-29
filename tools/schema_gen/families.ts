// skse/core/schema/families.json -> generated/argonia/core/family_layouts.h: each co-save family's payload layout
// per version, as roundtrip::FamilySchema rows. Checked here: four-character ids, unique; versions 1..n in order;
// every older version says whether it migrates; items well formed.
import { SchemaError } from "./model.ts";

type Bound = number | string;
interface Raw { [k: string]: unknown }

const SCALARS = ["u8", "u32", "u64", "i32", "f64", "str"] as const;
const GROUPS = ["repeat", "list", "flag"] as const;

const fail = (why: string): never => { throw new SchemaError(`families.json: ${why}`); };
const bound = (b: Bound): string => (typeof b === "number" ? (Number.isInteger(b) ? `${b}.0` : String(b)) : `double(${b})`);
const count = (b: Bound): string => (typeof b === "number" ? String(b) : b);
const isBound = (b: unknown): b is Bound => typeof b === "number" || (typeof b === "string" && /^[\w:\s+\-*()]+$/.test(b));

function item(raw: Raw, where: string): string {
  const kinds = [...SCALARS, ...GROUPS].filter((k) => k in raw);
  if (kinds.length !== 1) fail(`${where}: an item names exactly one kind`);
  const kind = kinds[0], name = raw[kind];
  if (typeof name !== "string" || !/^[a-z][a-z0-9_]*$/.test(name)) fail(`${where}: the ${kind} needs a snake_case name`);
  const here = `${where}.${name}`;
  const allowed = new Set([kind, ...(kind === "str" ? [] : (SCALARS as readonly string[]).includes(kind) ? ["min", "max"] :
    kind === "flag" ? ["of"] : kind === "repeat" ? ["of", "count"] : ["of", "count", "keyed"])]);
  for (const k of Object.keys(raw)) if (!allowed.has(k)) fail(`${here}: '${k}' is not a key of a ${kind}`);
  for (const k of ["min", "max", "count"]) if (k in raw && !isBound(raw[k])) fail(`${here}: ${k} is a number or a C++ expression`);
  if ((SCALARS as readonly string[]).includes(kind)) {
    const args = [`"${name}"`];
    if ("min" in raw || "max" in raw) {
      const dflt: Record<string, [string, string]> = { u8: ["0", "255"], u32: ["0", "4294967295.0"], u64: ["0", "9007199254740991.0"],
        i32: ["-2147483648.0", "2147483647.0"], f64: ["-1e6", "1e6"] };
      args.push("min" in raw ? bound(raw.min as Bound) : dflt[kind][0], "max" in raw ? bound(raw.max as Bound) : dflt[kind][1]);
    }
    return `${kind}(${args.join(", ")})`;
  }
  const of = raw.of;
  if (!Array.isArray(of) || of.length === 0) fail(`${here}: 'of' lists at least one item`);
  const inner = `{${(of as Raw[]).map((x, i) => item(x, `${here}[${i}]`)).join(", ")}}`;
  if (kind === "flag") return `flag("${name}", ${inner})`;
  if (!("count" in raw)) fail(`${here}: a ${kind} needs a count`);
  if (kind === "repeat") return `repeat("${name}", ${count(raw.count as Bound)}, ${inner})`;
  if (raw.keyed !== undefined && typeof raw.keyed !== "boolean") fail(`${here}: keyed is true or false`);
  if (raw.keyed) {
    const first = (of as Raw[])[0];
    if (!["u8", "u32", "u64", "i32"].some((k) => k in first)) fail(`${here}: a keyed list's first item is an integer`);
  }
  return `list("${name}", ${count(raw.count as Bound)}, ${inner}${raw.keyed ? ", true" : ""})`;
}

export function emitFamilies(text: string): string {
  let doc: Raw;
  try { doc = JSON.parse(text) as Raw; } catch (e) { return fail(`not JSON: ${(e as Error).message}`); }
  const fams = doc.families;
  if (!Array.isArray(fams)) fail("'families' is a list");
  const ids = new Set<string>();
  const includes = new Set<string>();
  const rows: string[] = [];
  for (const f of fams as Raw[]) {
    const id = f.id;
    if (typeof id !== "string" || !/^[A-Z0-9]{4}$/.test(id)) fail(`family id ${JSON.stringify(id)} is not four capitals`);
    if (ids.has(id as string)) fail(`family ${id} is declared twice`);
    ids.add(id as string);
    for (const k of Object.keys(f)) if (!["id", "module", "include", "test", "versions"].includes(k)) fail(`${id}: unknown key '${k}'`);
    if (typeof f.module !== "string") fail(`${id}: module is a string`);
    if (f.include !== undefined) {
      if (typeof f.include !== "string" || !/^[\w/.]+\.h$/.test(f.include)) fail(`${id}: include is a header path`);
      includes.add(f.include as string);
    }
    const vs = f.versions;
    if (!Array.isArray(vs) || vs.length === 0) fail(`${id}: versions lists at least one`);
    const vrows = (vs as Raw[]).map((v, i) => {
      if (v.version !== i + 1) fail(`${id}: versions run 1, 2, 3 in order (found ${JSON.stringify(v.version)} at ${i})`);
      const last = i === (vs as Raw[]).length - 1;
      if (!last && typeof v.migrates !== "boolean") fail(`${id} v${v.version}: an older version says whether it migrates`);
      if (last && v.migrates !== undefined) fail(`${id} v${v.version}: the current version has no 'migrates'`);
      for (const k of Object.keys(v)) if (!["version", "migrates", "layout"].includes(k)) fail(`${id} v${v.version}: unknown key '${k}'`);
      if (!Array.isArray(v.layout)) fail(`${id} v${v.version}: layout is a list`);
      const layout = (v.layout as Raw[]).map((x, j) => item(x, `${id} v${v.version}[${j}]`));
      return `        {${v.version}, ${v.migrates === true}, {${layout.join(", ")}}},\n`;
    });
    rows.push(`    {cosave::fourcc("${id}"), "${f.module}", ${f.test === true}, {\n${vrows.join("")}    }},\n`);
  }
  let o = `// family_layouts.h: GENERATED by tools/schema_gen from skse/core/schema/families.json (1.1 §b). Do not edit:\n` +
    `// change the JSON and run \`node --experimental-strip-types tools/schema_gen/gen.ts\`; the gate refuses a stale file.\n` +
    `#pragma once\n#include "argonia/core/roundtrip.h"\n`;
  for (const inc of [...includes].sort()) o += `#include "${inc}"\n`;
  o += `\n#include <vector>\n\nnamespace argonia::core::gen {\n\n` +
    `// Every family's layouts, oldest version first.\ninline std::vector<roundtrip::FamilySchema> family_schemas() {\n` +
    `  using namespace roundtrip;\n  return {\n${rows.join("")}  };\n}\n\n}  // namespace argonia::core::gen\n`;
  return o;
}
