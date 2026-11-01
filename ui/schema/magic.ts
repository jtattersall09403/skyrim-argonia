// Our magic pane (1.12, owner 2026-10-31): Morrowind's spell list standing in for Wind UI's magic window, which cannot
// show a Mysticism heading. Powers first, then the spells under Morrowind's six schools in a fixed order, each with
// its magicka cost; the active effects below. ArgoniaCore groups and orders (skse/core magic::pane_state, the school
// from our data: mod_form, else the effect's Skyrim school); the view only draws and sends magic.equip.
import { bool, enumDef, int, intent, list, oneOf, opt, push, ref, str, struct } from "./types.ts";

// skse/core's SkillId names of the six schools, in Morrowind's order.
export const MagicSchool = enumDef("MagicSchool", "one of Morrowind's six schools of magic",
  ["alteration", "conjuration", "destruction", "illusion", "mysticism", "restoration"]);

export const Hand = enumDef("Hand", "where a readied spell or power goes", ["left", "right", "voice"]);

export const MagicSpell = struct("MagicSpell", "One spell the player knows", {
  id: str("the spell's form id, 8 hex digits"),
  name: str("the spell's name as the game has it (our restated name where mod_form gives one)"),
  cost: int("magicka to cast, the engine's figure for the player now", { min: 0 }),
  chance: opt(int("the chance to cast, percent; absent: Skyrim has none", { min: 0, max: 100 })),
  left: bool("readied in the left hand"),
  right: bool("readied in the right hand"),
});

export const MagicPower = struct("MagicPower", "A power or lesser power the player has", {
  id: str("the power's form id, 8 hex digits"),
  name: str("the power's name"),
  readied: bool("readied in the voice slot"),
});

export const MagicGroup = struct("MagicGroup", "One school's heading and its spells, by name", {
  school: oneOf(MagicSchool),
  name: str("the heading as the player reads it"),
  spells: list(ref(MagicSpell), "by name; empty when the player knows none of the school"),
});

export const MagicActive = struct("MagicActive", "An effect on the player now", {
  name: str("the effect's name"),
  detail: opt(str("its magnitude and time left, as ArgoniaCore words them")),
});

export const magicState = push("magic.state", 1, "The open magic pane", {
  powers: list(ref(MagicPower), "by name"),
  groups: list(ref(MagicGroup), "the six schools, always, in Morrowind's order"),
  effects: list(ref(MagicActive), "the active effects shown in the game's UI, by name"),
  notice: opt(str("one line about the last pick (a refusal), as ArgoniaCore words it")),
});

export const magicEquip = intent("magic.equip", 1, "The player readied a spell in a hand, or a power", {
  spell: str("the spell's or power's form id, 8 hex digits"),
  hand: oneOf(Hand),
});

export const messages = [magicState, magicEquip];
