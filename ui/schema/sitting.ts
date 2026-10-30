// The level sitting (1.5, 2.8 §a; 76 §120.4): a rest consolidates one pending level and opens the sitting, where
// carried vastei buys attribute points at the formula cost, at most a cap per attribute per sitting. ArgoniaCore
// prices every point (skse/core/sitting); the view only shows the prices and sends the player's picks.
import { int, intent, list, num, oneOf, opt, push, ref, str, struct, enumDef } from "./types.ts";

// The names of skse/core's AttrId, in its order.
export const AttributeId = enumDef("AttributeId", "one of the seven attributes (Morrowind's, without Luck)",
  ["agility", "endurance", "intelligence", "personality", "speed", "strength", "willpower"]);

// skse/core/sitting's Refusal, camelCased.
export const SittingRefusal = enumDef("SittingRefusal", "why the next point of an attribute cannot be bought",
  ["noPendingLevel", "atCapThisSitting", "atPurchaseCap", "tooDear"]);

export const SittingAttribute = struct("SittingAttribute", "One attribute's row of the sitting", {
  id: oneOf(AttributeId),
  name: str("the attribute's name as the sheet shows it"),
  value: int("the attribute now, with this sitting's points", { min: 0 }),
  bought: int("points bought this sitting", { min: 0 }),
  cap: int("the most points one sitting may buy", { min: 0 }),
  cost: num("the vastei the next point costs (cost formula, ArgoniaCore's)", { min: 0 }),
  refusal: opt(oneOf(SittingRefusal, "why the next point cannot be bought; absent when it can")),
});

export const SittingPool = struct("SittingPool", "A pool the sitting recomputes", {
  before: num("the maximum when the sitting opened", { min: 0 }),
  after: num("the maximum with this sitting's points", { min: 0 }),
});

export const sittingState = push("sitting.state", 1, "The open sitting after each purchase", {
  level: int("the level this sitting takes", { min: 1 }),
  vastei: num("vastei carried, after this sitting's purchases", { min: 0 }),
  pendingAfter: int("pending levels left for later rests", { min: 0 }),
  attributes: list(ref(SittingAttribute), "the seven attributes, in the sheet's order"),
  health: ref(SittingPool),
  notice: opt(str("one line about the last pick (a refusal), as ArgoniaCore words it")),
});

export const sittingBuy = intent("sitting.buy", 1, "The player bought one point of an attribute", {
  attribute: oneOf(AttributeId),
});

export const sittingDone = intent("sitting.done", 1, "The player rose from the sitting; unspent vastei carries over", {});

export const messages = [sittingState, sittingBuy, sittingDone];
