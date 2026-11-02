// Our character sheet (1.12 round 4), standing in for the StatsMenu and Wind UI's stats page. ArgoniaCore owns every
// figure and which perks can be taken (skse/core progression); the view draws three tabs and sends charsheet.perk.
import { bool, enumDef, int, intent, list, num, oneOf, opt, push, ref, str, struct } from "./types.ts";
import { AttributeId } from "./sitting.ts";

// skse/core's SkillId names, in its order.
export const SkillId = enumDef("SkillId", "one of Argonia's twenty-seven skills",
  ["acrobatics", "alchemy", "alteration", "athletics", "axe", "block", "blunt", "conjuration", "destruction", "enchant",
    "handToHand", "heavyArmor", "illusion", "lightArmor", "longBlade", "marksman", "mediumArmor", "mercantile",
    "mysticism", "restoration", "security", "shortBlade", "smithing", "sneak", "spear", "speechcraft", "unarmored"]);

export const CharAttribute = struct("CharAttribute", "One attribute", {
  id: oneOf(AttributeId),
  name: str("the attribute's name as the sheet shows it"),
  value: int("the attribute now", { min: 0 }),
  blurb: opt(str("one line on what it does, shown under the list when the row is focused")),
});

export const CharSkill = struct("CharSkill", "One skill", {
  id: oneOf(SkillId),
  name: str("the skill's name as the sheet shows it"),
  group: str("its class heading as the sheet shows it (armour, craft, magic, ...)"),
  value: int("the skill now", { min: 0 }),
  progress: num("use points toward the next rank, 0 to 1", { min: 0, max: 1 }),
  blurb: opt(str("one line on what it does, shown under the list when the row is focused")),
});

export const CharPerk = struct("CharPerk", "One perk in a skill's tree", {
  id: str("the perk's form id, 8 hex digits"),
  skill: oneOf(SkillId),
  name: str("the perk's name (our wording, perk_text)"),
  description: str("what it does, in our wording"),
  taken: bool("the player has it"),
  available: bool("the player can take it now"),
  need: opt(str("what is missing when it is not available, as ArgoniaCore words it")),
});

export const charsheetState = push("charsheet.state", 1, "The open character sheet", {
  name: str("the player's name"),
  race: str("the player's race as the game has it"),
  level: int("the character level", { min: 1 }),
  progress: num("progress to the next level, 0 to 1", { min: 0, max: 1 }),
  health: num("health now", { min: 0 }),
  healthMax: num("maximum health", { min: 0 }),
  magicka: num("magicka now", { min: 0 }),
  magickaMax: num("maximum magicka", { min: 0 }),
  stamina: num("stamina now", { min: 0 }),
  staminaMax: num("maximum stamina", { min: 0 }),
  perkPoints: int("perk points to spend", { min: 0 }),
  attributes: list(ref(CharAttribute), "the seven attributes, in the sheet's order"),
  skills: list(ref(CharSkill), "the twenty-seven skills, by class then name"),
  perks: list(ref(CharPerk), "every perk the player has or can see, by skill then tree order"),
  notice: opt(str("one line about the last pick (a refusal), as ArgoniaCore words it")),
});

export const charsheetPerk = intent("charsheet.perk", 1, "The player took a perk", {
  perk: str("the perk's form id, 8 hex digits"),
});

export const messages = [charsheetState, charsheetPerk];
