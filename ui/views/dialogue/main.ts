// The dialogue window in the browser: one innerHTML per dialogue.state; the conversation scrolls to the newest entry.
import type { DialogueState } from "../../schema/generated/messages.ts";
import { send, start } from "../core/bridge.ts";
import { backIntent, render, type DialogueUi } from "./render.ts";

const root = document.getElementById("view")!;
let state: DialogueState | null = null;
const ui: DialogueUi = { persuading: false, filter: "" };

function draw(keepScroll: boolean): void {
  if (!state) return;
  const list = root.querySelector<HTMLElement>("[data-list=topics]");
  const top = list?.scrollTop ?? 0;
  root.innerHTML = render(state, ui);
  const talk = root.querySelector<HTMLElement>("[data-scroll=talk]")!;
  talk.scrollTop = talk.scrollHeight;              // Morrowind: the newest answer in view
  const l2 = root.querySelector<HTMLElement>("[data-list=topics]");
  if (l2 && keepScroll) l2.scrollTop = top;        // the topic list keeps its place as it grows
  if (ui.persuading) root.querySelector<HTMLElement>(".persuade button:not([disabled])")?.focus();
}

start({
  accepts: ["dialogue.state"],
  render(m) {
    if (m.type !== "dialogue.state") return;
    const same = state?.speaker.id === m.body.speaker.id;
    state = m.body;
    if (!same || !m.body.persuasion.available) ui.persuading = false;
    if (!same) ui.filter = "";
    draw(same);
  },
  back() {
    if (ui.filter) { ui.filter = ""; draw(true); return; }
    if (ui.persuading) { ui.persuading = false; draw(true); root.querySelector<HTMLElement>("[data-key=persuade]")?.focus(); return; }
    const m = state && backIntent(state);
    if (m) send(m);
  },
  local(el) {
    if (el.dataset.ui === "persuade-open") { ui.persuading = true; draw(true); }
    if (el.dataset.ui === "persuade-close") { ui.persuading = false; draw(true); root.querySelector<HTMLElement>("[data-key=persuade]")?.focus(); }
  },
});

// Typing narrows the topic list: letters and digits add, Backspace takes one back, Escape (back) clears it.
document.addEventListener("keydown", (e) => {
  if (!state || ui.persuading || e.ctrlKey || e.altKey || e.metaKey) return;
  const f = ui.filter ?? "";
  if (e.key === "Backspace" && f) ui.filter = f.slice(0, -1);
  else if (/^[a-z0-9]$/i.test(e.key)) ui.filter = f + e.key;
  else return;
  e.preventDefault();
  draw(false);
  root.querySelector<HTMLElement>("[data-list=topics] button")?.focus({ preventScroll: true });
});
