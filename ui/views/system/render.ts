// Our System pane (1.12, lane 1.12-menus), render only: Esc and the pad's last pane open it in place of Dear Diary's
// System page, which listed Quests (quests live only in the journal, owner look 1). Four entries in the frame style:
// Settings and Load hand over to the engine's own pages, the two quits to the engine's own handlers (ArgoniaCore).
import type { SystemState } from "../../schema/generated/messages.ts";
import { intentButton } from "../core/html.ts";

type Action = "settings" | "load" | "quitToMainMenu" | "quitToDesktop";
export const pick = (action: Action) => ({ type: "system.pick" as const, v: 1 as const, body: { action } });
export const close = () => ({ type: "view.close" as const, v: 1 as const, body: { view: "system" as const } });

const ENTRIES: readonly [Action, string][] = [
  ["settings", "Settings"], ["load", "Load"], ["quitToMainMenu", "Quit to the main menu"],
  ["quitToDesktop", "Quit to the desktop"],
];

export function render(s: SystemState): string {
  const rows = ENTRIES.map(([a, label]) => {
    const off = a === "load" && !s.canLoad;
    return `<li>${intentButton(pick(a), `entry${off ? " off" : ""}`, label,
      `data-key="${a}"${off ? ' disabled aria-disabled="true"' : ""}`)}</li>`;
  }).join("");
  return `<section class="window system" aria-label="System">
  <header class="bar"><h1>System</h1>${intentButton(close(), "close", "Close", `data-key="close"`)}</header>
  <ul class="entries" data-list="entries">${rows}</ul>
</section>`;
}
