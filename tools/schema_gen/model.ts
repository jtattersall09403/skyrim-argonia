// The message schema as the emitters see it: every struct and enum reached from the messages, in dependency order,
// checked once. A schema the emitters cannot represent on both sides is refused here with a readable reason.
import type { EnumDef, MessageDef, StructDef, Ty } from "../../ui/schema/types.ts";

export interface Model {
  messages: readonly MessageDef[];
  structs: StructDef[];  // dependencies before dependants; message bodies included
  enums: EnumDef[];
  hash: string;          // FNV-1a 64 of the canonical schema; both twins carry it for the handshake
}

const CPP_WORDS = new Set(("alignas alignof and asm auto bool break case catch char class const constexpr continue " +
  "default delete do double else enum explicit export extern false float for friend goto if inline int long " +
  "mutable namespace new noexcept not nullptr operator or private protected public register return short signed " +
  "sizeof static struct switch template this throw true try typedef typename union unsigned using virtual void " +
  "volatile while xor").split(" "));

export const snake = (s: string): string => s.replace(/([a-z0-9])([A-Z])/g, "$1_$2").toLowerCase();
export const cppMember = (s: string): string => (CPP_WORDS.has(snake(s)) ? snake(s) + "_" : snake(s));
export const cppEnumerator = (s: string): string => (CPP_WORDS.has(s) ? s + "_" : s);

export class SchemaError extends Error {}

export function build(messages: readonly MessageDef[]): Model {
  const fail = (why: string): never => { throw new SchemaError(why); };
  const structs: StructDef[] = [];
  const enums: EnumDef[] = [];
  const byName = new Map<string, StructDef | EnumDef>();
  const claim = (name: string, def: StructDef | EnumDef) => {
    if (!/^[A-Z][A-Za-z0-9]*$/.test(name)) fail(`type name '${name}' is not PascalCase`);
    const had = byName.get(name);
    if (had && had !== def) fail(`two different types are named '${name}'`);
    byName.set(name, def);
    return !had;
  };
  const visiting = new Set<StructDef>();

  const walkTy = (ty: Ty, where: string, top: boolean): void => {
    switch (ty.kind) {
      case "enum": {
        if (claim(ty.def.name, ty.def)) {
          if (ty.def.values.length === 0) fail(`${ty.def.name}: an enum needs a value`);
          if (new Set(ty.def.values).size !== ty.def.values.length) fail(`${ty.def.name}: a value repeats`);
          for (const v of ty.def.values) if (!/^[a-z][A-Za-z0-9]*$/.test(v)) fail(`${ty.def.name}: '${v}' is not camelCase`);
          enums.push(ty.def);
        }
        return;
      }
      case "ref": walkStruct(ty.def); return;
      case "list": walkTy(ty.of, `${where}[]`, false); return;
      case "opt":
        if (!top) fail(`${where}: opt is allowed only on a field, not inside a list`);
        if (ty.of.kind === "opt") fail(`${where}: opt of opt`);
        walkTy(ty.of, where, false);
        return;
      case "int": case "num":
        if (ty.min !== undefined && ty.max !== undefined && ty.min > ty.max) fail(`${where}: min above max`);
        if (ty.kind === "int" && [ty.min, ty.max].some((b) => b !== undefined && !Number.isSafeInteger(b)))
          fail(`${where}: an int bound must be a safe integer`);
        return;
      default: return;
    }
  };

  function walkStruct(s: StructDef): void {
    if (byName.get(s.name) === s && !visiting.has(s)) return;  // already emitted
    if (visiting.has(s)) fail(`${s.name} contains itself`);
    claim(s.name, s);
    visiting.add(s);
    const members = new Set<string>();
    for (const [field, ty] of Object.entries(s.fields)) {
      if (!/^[a-z][A-Za-z0-9]*$/.test(field)) fail(`${s.name}.${field}: a field name is camelCase`);
      const m = cppMember(field);
      if (members.has(m)) fail(`${s.name}.${field}: two fields map to the C++ member '${m}'`);
      members.add(m);
      walkTy(ty, `${s.name}.${field}`, true);
    }
    visiting.delete(s);
    structs.push(s);
  }

  const types = new Set<string>();
  for (const m of messages) {
    if (!/^[a-z]+\.[a-z][A-Za-z0-9]*$/.test(m.type)) fail(`message type '${m.type}' is not '<screen>.<name>'`);
    if (types.has(m.type)) fail(`message type '${m.type}' is declared twice`);
    types.add(m.type);
    if (!Number.isInteger(m.version) || m.version < 1) fail(`${m.type}: version must be an integer >= 1`);
    walkStruct(m.body);
  }
  return { messages, structs, enums, hash: fnv1a64(canonical(messages)) };
}

// The schema's shape as one string: what changes the wire changes this, docs do not.
function canonical(messages: readonly MessageDef[]): string {
  const ty = (t: Ty): unknown => {
    switch (t.kind) {
      case "enum": return { enum: t.def.name, values: t.def.values };
      case "ref": return { ref: t.def.name, fields: fields(t.def) };
      case "list": case "opt": return { [t.kind]: ty(t.of) };
      case "int": case "num": return { [t.kind]: [t.min ?? null, t.max ?? null] };
      default: return t.kind;
    }
  };
  const fields = (s: StructDef) => Object.entries(s.fields).map(([k, t]) => [k, ty(t)]);
  return JSON.stringify(messages.map((m) => [m.type, m.version, m.dir, fields(m.body)]));
}

export function fnv1a64(s: string): string {
  let h = 0xcbf29ce484222325n;
  for (const b of new TextEncoder().encode(s)) h = ((h ^ BigInt(b)) * 0x100000001b3n) & 0xffffffffffffffffn;
  return h.toString(16).padStart(16, "0");
}
