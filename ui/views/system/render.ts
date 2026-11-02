// Our System pane (1.12, lane 1.12-menus), render only: Esc and the pad's last pane open it in place of Dear Diary's
// System page, which listed Quests (quests live only in the journal, owner look 1). Four entries in the frame style:
// Settings and Load hand over to the engine's own pages, the two quits to the engine's own handlers (ArgoniaCore).
import type { SystemState } from "../../schema/generated/messages.ts";
import { intentButton } from "../core/html.ts";

type Action = "settings" | "load" | "quitToMainMenu" | "quitToDesktop";
export const pick = (action: Action) => ({ type: "system.pick" as const, v: 1 as const, body: { action } });
export const close = () => ({ type: "view.close" as const, v: 1 as const, body: { view: "system" as const } });

// Two groups under left-hand headings in the journal's heading style (owner play test 3, finding 8): the game's own
// pages, then leaving it.
const GROUPS: readonly [string, readonly [Action, string][]][] = [
  ["Game", [["settings", "Settings"], ["load", "Load"]]],
  ["Leave", [["quitToMainMenu", "Quit to the main menu"], ["quitToDesktop", "Quit to the desktop"]]],
];

export function render(s: SystemState): string {
  const groups = GROUPS.map(([head, entries]) => {
    const rows = entries.map(([a, label]) => {
      const off = a === "load" && !s.canLoad;
      return `<li>${intentButton(pick(a), `entry${off ? " off" : ""}`, label,
        `data-key="${a}"${off ? ' disabled aria-disabled="true"' : ""}`)}</li>`;
    }).join("");
    return `<li class="group"><h2 class="ghead">${head}</h2><ul class="entries">${rows}</ul></li>`;
  }).join("");
  return `<section class="window system" aria-label="System">
  <header class="bar"><h1>System</h1>${intentButton(close(), "close", "Close", `data-key="close"`)}</header>
  <ul class="sheet" data-list="entries">${groups}</ul>
</section>`;
}
