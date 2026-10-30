// The dialogue window (1.2 §b), render only: Morrowind's layout in our paper. The speaker's name heads the window;
// the conversation scrolls on the left with hyperlinked keywords; on the right, disposition as Morrowind shows it
// (a bar and its number), the persuasion button, the growing topic list and Goodbye.
import type { DialogueState, TextRun } from "../../schema/generated/messages.ts";
import { esc, intentButton } from "../core/html.ts";

export interface DialogueUi { persuading: boolean }

const runsHtml = (runs: TextRun[]): string =>
  runs.map((r) => r.topic === undefined
    ? esc(r.text)
    : intentButton({ type: "dialogue.keyword", v: 1, body: { topic: r.topic } }, "kw", esc(r.text))).join("");

function entries(s: DialogueState): string {
  return s.entries.map((e, i) => {
    const head = e.heading !== undefined ? `<h2 class="asked">${esc(e.heading)}</h2>` : "";
    const last = i === s.entries.length - 1 ? " last" : "";
    return `<div class="entry ${e.kind}${last}">${head}<p>${runsHtml(e.runs)}</p></div>`;
  }).join("");
}

function persuasionPanel(s: DialogueState): string {
  const opts = s.persuasion.options.map((o) => {
    const cost = o.cost !== undefined ? `<span class="cost">${o.cost} gold</span>` : "";
    return intentButton({ type: "dialogue.persuade", v: 1, body: { option: o.id } }, "opt",
      `<span>${esc(o.label)}</span>${cost}`, `data-key="persuade:${esc(o.id)}"${o.enabled ? "" : " disabled"}`);
  }).join("");
  return `<div class="persuade paper" role="dialog" aria-label="Persuasion">
    <h2>Persuasion</h2><div class="opts">${opts}</div>
    <button type="button" class="back-btn" data-ui="persuade-close" data-key="persuade:close">Back</button></div>`;
}

export function render(s: DialogueState, ui: DialogueUi = { persuading: false }): string {
  const d = s.disposition;
  const topics = s.topics.map((t) =>
    `<li>${intentButton({ type: "dialogue.topic", v: 1, body: { topic: t.id } }, "topic", esc(t.label),
      `data-key="topic:${esc(t.id)}"`)}</li>`).join("");
  const persuade = s.persuasion.available
    ? `<button type="button" class="special" data-ui="persuade-open" data-key="persuade">Persuasion</button>` : "";
  const goodbye = s.canLeave
    ? intentButton({ type: "dialogue.goodbye", v: 1, body: {} }, "goodbye", "Goodbye", `data-key="goodbye"`) : "";
  return `<section class="dialogue paper" data-band="${d.band}" aria-label="${esc(s.speaker.name)}">
  <header class="title"><h1>${esc(s.speaker.name)}</h1></header>
  <div class="cols">
    <div class="talk scroll" data-scroll="talk">${entries(s)}</div>
    <aside class="side">
      <div class="disp" title="Disposition">
        <div class="disp-bar"><div class="disp-fill" style="width:${d.value}%"></div>
          <span class="disp-text">Disposition ${d.value}</span></div>
      </div>
      ${persuade}
      <ul class="topics scroll" data-list="topics">${topics}</ul>
      ${goodbye}
    </aside>
  </div>
  ${ui.persuading && s.persuasion.available ? persuasionPanel(s) : ""}
</section>`;
}

// Escape and the pad's B: the window closes (view.close) unless the conversation is forced.
export const backIntent = (s: DialogueState) =>
  s.canLeave ? { type: "view.close" as const, v: 1 as const, body: { view: "dialogue" as const } } : null;
