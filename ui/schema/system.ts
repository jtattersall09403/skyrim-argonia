// Our System pane and our wait window (1.12, lane 1.12-menus; owner look 1): they stand in for Dear Diary's System page
// (Esc, the pad's last pane), which listed Quests, and its Sleep/Wait Menu (T, the pad's Select). The engine's menus
// stay open underneath with their movies hidden: ArgoniaCore drives them by their own handlers (the Journal Menu's
// QuitToMainMenu and QuitToDesktop, its Settings and Load pages; the Sleep/Wait Menu's OK), so nothing of the game's
// behaviour is rebuilt. The views only draw and send the player's pick.
import { bool, enumDef, int, intent, oneOf, push, str } from "./types.ts";

export const SystemAction = enumDef("SystemAction", "what the player picked on the System pane",
  ["settings", "load", "quitToMainMenu", "quitToDesktop"]);

export const systemState = push("system.state", 1, "The open System pane", {
  canLoad: bool("a save exists to load (the engine's Load entry is enabled)"),
});

export const systemPick = intent("system.pick", 1, "The player picked an entry on the System pane", {
  action: oneOf(SystemAction),
});

export const WaitMode = enumDef("WaitMode", "the engine's mode for the Sleep/Wait Menu", ["wait", "sleep"]);

export const waitState = push("wait.state", 1, "The open wait window", {
  mode: oneOf(WaitMode),
  now: str("the time of day and date as the player reads it (ArgoniaCore words it; views never format game dates)"),
  hours: int("the hours the window opens on", { min: 1, max: 24 }),
  max: int("the most hours one wait may take (Dear Diary's config cap, the engine's)", { min: 1, max: 24 }),
});

export const waitPick = intent("wait.pick", 1, "The player chose to wait or sleep this many hours", {
  hours: int("hours, within the window's max", { min: 1, max: 24 }),
});

export const messages = [systemState, systemPick, waitState, waitPick];
