// Our HUD (1.2 §d): souls-style bars that grow with stats, the sneak eye, the effect stack, the vastei plaque, the
// place banner, the prompt with input glyphs, notices. No compass and no marker, ever. Boss bars join in 2.7.
import { InputGlyph } from "./common.ts";
import { bool, enumDef, int, list, num, oneOf, opt, push, ref, str, struct } from "./types.ts";

export const BarKind = enumDef("BarKind", "a bar of the HUD", ["health", "stamina", "magicka", "breath", "climb"]);
export const EffectPolarity = enumDef("EffectPolarity", "how the stack colours an effect", ["boon", "bane"]);
export const NoticeKind = enumDef("NoticeKind", "what raised a notice", ["info", "journal", "discovery", "warning"]);

export const Bar = struct("Bar", "One bar; its drawn length grows with max", {
  kind: oneOf(BarKind),
  current: num("the current value", { min: 0 }),
  max: num("the maximum, which sets the bar's length", { min: 0 }),
  shown: bool("false hides the bar (breath above water, climb off a wall)"),
});

export const Sneak = struct("Sneak", "The sneak eye", {
  sneaking: bool("whether the eye shows"),
  eye: num("how open the eye is: 0 unseen, 1 detected", { min: 0, max: 1 }),
});

export const Effect = struct("Effect", "One entry of the effect stack", {
  id: str("the effect instance id"),
  label: str("the effect's name"),
  glyph: str("the symbol id (Fal-made status symbols, decision 0017 §5)"),
  polarity: oneOf(EffectPolarity),
  remaining: opt(num("seconds of game time left; absent for a constant effect", { min: 0 })),
});

export const Vastei = struct("Vastei", "The vastei plaque", {
  carried: int("vastei carried", { min: 0 }),
  gained: opt(int("a recent gain shown beside the plaque", { min: 0 })),
});

export const PlaceBanner = struct("PlaceBanner", "The banner shown on entering a place", {
  place: str("world db place.id"),
  name: str("the place's name"),
  region: opt(str("the region's name")),
  firstVisit: bool("true on discovery"),
});

export const Prompt = struct("Prompt", "The activation prompt", {
  verb: str("what activating does (Talk, Take, Open)"),
  target: str("what it is done to"),
  inputs: list(ref(InputGlyph), "the glyph per device"),
});

export const Notice = struct("Notice", "One line of the notice stack", {
  id: str("the notice id, so a view can fade it once"),
  kind: oneOf(NoticeKind),
  text: str("the line"),
});

export const hudState = push("hud.state", 1, "The whole HUD, sent on any change but the bars", {
  visible: bool("false while one of our views or a menu covers play"),
  bars: list(ref(Bar)),
  sneak: ref(Sneak),
  effects: list(ref(Effect), "the effect stack, newest first"),
  vastei: ref(Vastei),
  banner: opt(ref(PlaceBanner)),
  prompt: opt(ref(Prompt)),
  notices: list(ref(Notice), "newest last"),
});

export const hudBars = push("hud.bars", 1, "The bars alone, the HUD's frequent update", {
  bars: list(ref(Bar)),
});

export const messages = [hudState, hudBars];
