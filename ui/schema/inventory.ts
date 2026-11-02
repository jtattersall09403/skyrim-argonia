// Our inventory screen (1.12 round 4), standing in for SkyUI's and Wind UI's InventoryMenu. ArgoniaCore owns the
// carried items, their order and every figure; the view filters by category tab (a view-local choice, LB/RB), shows
// the focused item's detail and sends inventory.use and inventory.drop.
import { bool, enumDef, int, intent, list, num, oneOf, opt, push, ref, str, struct } from "./types.ts";

export const InventoryCategory = enumDef("InventoryCategory", "the category an item belongs to",
  ["weapons", "apparel", "potions", "scrolls", "food", "ingredients", "books", "keys", "misc"]);

export const InventoryItem = struct("InventoryItem", "One carried stack", {
  id: str("the stack's key: the item's form id, 8 hex digits, then # and the stack's index when the item is split"),
  name: str("the item's name as the game has it"),
  category: oneOf(InventoryCategory),
  count: int("how many in the stack", { min: 1 }),
  weight: num("the stack's weight, all of it", { min: 0 }),
  value: int("the stack's value in gold, all of it", { min: 0 }),
  equipped: bool("worn or readied now"),
  action: str("what the pad's A does to it, as the player reads it: Equip, Unequip, Use, Eat, Read, Drink"),
  detail: opt(str("one line of the item's figures or effect, as ArgoniaCore words them")),
});

export const inventoryState = push("inventory.state", 1, "The open inventory", {
  items: list(ref(InventoryItem), "every carried stack, in ArgoniaCore's order (equipped first within a category)"),
  carried: num("weight carried", { min: 0 }),
  capacity: num("the weight the player can carry before slowing", { min: 0 }),
  gold: int("gold carried", { min: 0 }),
  notice: opt(str("one line about the last action (a refusal), as ArgoniaCore words it")),
});

export const inventoryUse = intent("inventory.use", 1, "The player equipped or used a stack (the pad's A)", {
  item: str("the stack's key"),
});

export const inventoryDrop = intent("inventory.drop", 1, "The player dropped a stack", {
  item: str("the stack's key"),
});

export const messages = [inventoryState, inventoryUse, inventoryDrop];
