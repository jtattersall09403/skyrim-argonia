// Our magic pane (1.12, lane-1.12-magicpane), render only: Morrowind's spell window in the frame style, standing in
// for Wind UI's magic window (its five school headings are fixed in its closed DLL; Mysticism has none). The title bar
// names what is readied in each hand; the active effects run along the top; the list well holds Powers, then the
// spells under Morrowind's six schools with their cost (and chance where ArgoniaCore has one). A spell's name readies
// it in the right hand; its "L" readies it in the left. A power readies in the voice slot. ArgoniaCore groups, orders
// and equips (skse/core magic::pane_state); the view only draws and sends magic.equip.
import type { MagicGroup, MagicPower, MagicSpell, MagicState } from "../../schema/generated/messages.ts";
import { esc, intentButton } from "../core/html.ts";

type Hand = "left" | "right" | "voice";
export const equip = (spell: string, hand: Hand) =>
  ({ type: "magic.equip" as const, v: 1 as const, body: { spell, hand } });
export const close = () => ({ type: "view.close" as const, v: 1 as const, body: { view: "magic" as const } });

const figure = (s: MagicSpell) => (s.chance === undefined ? `${s.cost}` : `${s.cost}/${s.chance}`);

function spellRow(s: MagicSpell): string {
  const marks = s.right ? `<span class="hand" title="Right hand">R</span>` : "";  // the left hand's is its lit "L"
  const on = s.left || s.right ? " on" : "";
  return `<li class="row${on}">${intentButton(equip(s.id, "right"), "name",
    `<span class="n">${esc(s.name)}</span>${marks}<span class="cost">${figure(s)}</span>`,
    `data-key="r:${esc(s.id)}" aria-pressed="${s.right}" aria-label="${esc(s.name)}, ready in the right hand"`)}${
    intentButton(equip(s.id, "left"), `lh${s.left ? " on" : ""}`, "L",
      `data-key="l:${esc(s.id)}" data-aside aria-pressed="${s.left}" aria-label="${esc(s.name)}, ready in the left hand"`)}</li>`;
}

function powerRow(p: MagicPower): string {
  return `<li class="row power${p.readied ? " on" : ""}">${intentButton(equip(p.id, "voice"), "name",
    `<span class="n">${esc(p.name)}</span>${p.readied ? `<span class="hand" title="Readied">V</span>` : ""}`,
    `data-key="v:${esc(p.id)}" aria-pressed="${p.readied}"`)}</li>`;
}

function school(g: MagicGroup): string {
  const body = g.spells.length ? g.spells.map(spellRow).join("") : `<li class="none">None known</li>`;
  return `<li class="school ${g.school}"><h3 class="shead">${esc(g.name)}</h3><ul class="spells">${body}</ul></li>`;
}

// What each hand holds, for the title bar (Morrowind titles the window with the readied spell).
function readied(s: MagicState): string {
  const all = s.groups.flatMap((g) => g.spells);
  const left = all.find((x) => x.left)?.name, right = all.find((x) => x.right)?.name;
  const voice = s.powers.find((p) => p.readied)?.name;
  const part = (label: string, v: string | undefined) =>
    `<span class="slot"><span class="lab">${label}</span> ${v === undefined ? "<i>empty</i>" : esc(v)}</span>`;
  return `${part("Left", left)}${part("Right", right)}${voice === undefined ? "" : part("Power", voice)}`;
}

export function render(s: MagicState): string {
  const effects = s.effects.length
    ? s.effects.map((e) => `<li class="eff"><span class="en">${esc(e.name)}</span>${e.detail === undefined ? ""
      : ` <span class="ed">${esc(e.detail)}</span>`}</li>`).join("")
    : `<li class="eff none">No active effects</li>`;
  const powers = s.powers.length ? s.powers.map(powerRow).join("") : `<li class="none">None</li>`;
  const notice = s.notice === undefined ? "" : `<p class="notice" role="status">${esc(s.notice)}</p>`;
  return `<section class="window magic" aria-label="Magic">
  <header class="bar"><h1>Magic</h1><div class="readied">${readied(s)}</div>
    ${intentButton(close(), "close", "Close", `data-key="close"`)}</header>
  <ul class="effects" aria-label="Active effects">${effects}</ul>
  <div class="well scroll" data-list="spells">
    <h2 class="ghead">Powers</h2><ul class="powers">${powers}</ul>
    <div class="spellhead"><h2 class="ghead">Spells</h2><span class="colhead">Cost</span></div>
    <ul class="schools">${s.groups.map(school).join("")}</ul>
  </div>
  ${notice}
</section>`;
}
