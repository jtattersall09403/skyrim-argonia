// Shapes more than one screen uses.
import { enumDef, int, list, num, oneOf, opt, ref, str, struct } from "./types.ts";

export const TextRun = struct("TextRun", "One run of display text; a run with a topic is a hyperlinked keyword span", {
  text: str("the run's text, as the record has it"),
  topic: opt(str("the topic id the keyword asks about (world db topic.id)")),
});

export const GameDate = struct("GameDate", "A date on the game calendar, with ArgoniaCore's rendering of it", {
  year: int("the era year"),
  month: int("1-based month", { min: 1, max: 12 }),
  day: int("1-based day of the month", { min: 1, max: 31 }),
  hour: num("hour of the day", { min: 0, max: 24 }),
  text: str("the date as the player reads it; views never format game dates"),
});

export const InputDevice = enumDef("InputDevice", "the device a glyph belongs to", ["keyboard", "gamepad", "touch"]);

export const InputGlyph = struct("InputGlyph", "The glyph for one input on one device", {
  device: oneOf(InputDevice),
  glyph: str("the glyph id in the symbol set (Skyrim's own, extracted at install, decision 0017 §5)"),
});

export const ViewId = enumDef("ViewId", "a view the player can close", ["dialogue", "journal", "chart"]);

export const runs = (doc: string) => list(ref(TextRun), doc);
