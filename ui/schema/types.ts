// The descriptor language of the message schema (1.1 §c; decision 0017 §3). Every message between ArgoniaCore and
// the views is declared once in ui/schema/*.ts with these builders; tools/schema_gen turns the declarations into the
// C++ twin (skse/core/generated/argonia/core/messages.h) and the TS types and validator (ui/schema/generated/).
// Plain TypeScript with erasable types only, so Node runs it with --experimental-strip-types and no build step.
//
// Wire form: {"type": "<screen>.<name>", "v": <version>, "body": {...}}. Every field is required unless `opt`;
// an absent optional is omitted, never null. A key not in the schema, a wrong type, a value outside its range or
// set, an unknown type or a version this build does not speak is refused at both ends with a readable path.

export interface EnumDef { readonly name: string; readonly doc: string; readonly values: readonly string[] }

export type Ty =
  | { readonly kind: "str"; readonly doc: string }
  | { readonly kind: "int"; readonly doc: string; readonly min?: number; readonly max?: number }
  | { readonly kind: "num"; readonly doc: string; readonly min?: number; readonly max?: number }
  | { readonly kind: "bool"; readonly doc: string }
  | { readonly kind: "enum"; readonly doc: string; readonly def: EnumDef }
  | { readonly kind: "list"; readonly doc: string; readonly of: Ty }
  | { readonly kind: "opt"; readonly doc: string; readonly of: Ty }
  | { readonly kind: "ref"; readonly doc: string; readonly def: StructDef };

export interface StructDef { readonly name: string; readonly doc: string; readonly fields: Readonly<Record<string, Ty>> }

export type Direction = "push" | "intent";

export interface MessageDef {
  readonly type: string;        // "<screen>.<name>", unique
  readonly version: number;     // >= 1; bumped on any change to the body's shape
  readonly dir: Direction;      // push: ArgoniaCore -> view (state); intent: view -> ArgoniaCore
  readonly doc: string;
  readonly body: StructDef;
}

interface Range { min?: number; max?: number }

export const str = (doc: string): Ty => ({ kind: "str", doc });
export const int = (doc: string, r: Range = {}): Ty => ({ kind: "int", doc, ...r });
export const num = (doc: string, r: Range = {}): Ty => ({ kind: "num", doc, ...r });
export const bool = (doc: string): Ty => ({ kind: "bool", doc });
export const oneOf = (def: EnumDef, doc: string = def.doc): Ty => ({ kind: "enum", doc, def });
export const list = (of: Ty, doc: string = of.doc): Ty => ({ kind: "list", doc, of });
export const opt = (of: Ty, doc: string = of.doc): Ty => ({ kind: "opt", doc, of });
export const ref = (def: StructDef, doc: string = def.doc): Ty => ({ kind: "ref", doc, def });

export const enumDef = (name: string, doc: string, values: readonly string[]): EnumDef => ({ name, doc, values });
export const struct = (name: string, doc: string, fields: Record<string, Ty>): StructDef => ({ name, doc, fields });

// "dialogue.state" -> "DialogueState"
export const pascal = (type: string): string =>
  type.split(/[.\-_]/).map((p) => p.charAt(0).toUpperCase() + p.slice(1)).join("");

const message = (dir: Direction) => (type: string, version: number, doc: string, fields: Record<string, Ty>): MessageDef =>
  ({ type, version, dir, doc, body: struct(pascal(type), doc, fields) });

export const push = message("push");
export const intent = message("intent");
