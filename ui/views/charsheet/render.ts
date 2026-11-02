// Our character sheet (1.12 round 4), render only: the StatsMenu's and Wind UI's stats page in the paper theme. The
// side column holds who the player is (name, race, level and its progress, the three pools, perk points); the three
// tabs (Attributes, Skills, Perks; LB/RB cycle them) hold one scrolling list each, every row a focusable button. A
// perk the player can take sends charsheet.perk; ArgoniaCore owns every figure and what is takeable.
import type { CharPerk, CharSkill, CharsheetState } from "../../schema/generated/messages.ts";
import { esc, intentButton } from "../core/html.ts";

export type Tab = "attributes" | "skills" | "perks";
export const TABS: readonly [Tab, string][] = [["attributes", "Attributes"], ["skills", "Skills"], ["perks", "Perks"]];
export const perk = (id: string) => ({ type: "charsheet.perk" as const, v: 1 as const, body: { perk: id } });
export const close = () => ({ type: "view.close" as const, v: 1 as const, body: { view: "charsheet" as const } });

export const step = (tab: Tab, by: 1 | -1): Tab =>
  TABS[(TABS.findIndex(([t]) => t === tab) + by + TABS.length) % TABS.length][0];

const fmt = (n: number): string => Math.round(n).toString();
const pct = (x: number): number => Math.round(Math.max(0, Math.min(1, x)) * 100);
const meter = (x: number, cls = "") => `<span class="meter ${cls}" aria-hidden="true"><i style="width:${pct(x)}%"></i></span>`;

const plain = (key: string, inner: string, label?: string, hint?: string) =>
  `<button type="button" class="name" data-key="${esc(key)}"${hint ? ` data-hint="${esc(hint)}"` : ""}${label ? ` aria-label="${esc(label)}"` : ""}>${inner}</button>`;

function skillRow(k: CharSkill): string {
  return `<li class="row">${plain("s:" + k.id, `<span class="n">${esc(k.name)}</span>${meter(k.progress, "use")}<span class="v">${k.value}</span>`,
    `${k.name} ${k.value}`, k.blurb)}</li>`;
}

function perkRow(p: CharPerk): string {
  const state = p.taken ? "Taken" : p.available ? "Take" : (p.need ?? "Locked");
  const inner = `<span class="n">${esc(p.name)}</span><span class="st">${esc(state)}</span><span class="d">${esc(p.description)}</span>`;
  const cls = `name perk${p.taken ? " taken" : ""}${!p.taken && !p.available ? " locked" : ""}`;
  const li = p.available && !p.taken
    ? intentButton(perk(p.id), cls, inner, `data-key="p:${esc(p.id)}" aria-label="${esc(p.name)}, take" data-hint="${esc(p.description)}"`)
    : `<button type="button" class="${cls}" data-key="p:${esc(p.id)}" data-hint="${esc(p.description)}" aria-label="${esc(p.name)}, ${esc(state)}">${inner}</button>`;
  return `<li class="row">${li}</li>`;
}

// Consecutive items under one heading, in the order given.
function grouped<T>(xs: T[], head: (x: T) => string, row: (x: T) => string): string {
  let out = "", last: string | undefined;
  for (const x of xs) {
    const h = head(x);
    if (h !== last) { out += `${last === undefined ? "" : "</ul></li>"}<li class="group"><h2 class="ghead">${esc(h)}</h2><ul class="rows">`; last = h; }
    out += row(x);
  }
  return out + (last === undefined ? "" : "</ul></li>");
}

export function list(s: CharsheetState, tab: Tab): string {
  if (tab === "attributes") {
    return `<ul class="well scroll" data-list="attributes"><li class="group"><h2 class="ghead">Attributes</h2><ul class="rows">${
      s.attributes.map((a) => `<li class="row">${plain("a:" + a.id, `<span class="n">${esc(a.name)}</span><span class="v">${a.value}</span>`, `${a.name} ${a.value}`, a.blurb)}</li>`).join("")}</ul></li></ul>`;
  }
  if (tab === "skills") {
    return `<ul class="well scroll" data-list="skills">${grouped(s.skills, (k) => k.group, skillRow)}</ul>`;
  }
  const name = (id: string) => s.skills.find((k) => k.id === id)?.name ?? id;
  const body = s.perks.length ? grouped(s.perks, (p) => name(p.skill), perkRow) : `<li class="none">No perks yet</li>`;
  return `<ul class="well scroll" data-list="perks">${body}</ul>`;
}

export function render(s: CharsheetState, tab: Tab = "attributes"): string {
  const tabs = TABS.map(([t, label]) =>
    `<button type="button" class="tab${t === tab ? " on" : ""}" data-ui="tab" data-tab="${t}" data-key="tab:${t}" aria-pressed="${t === tab}">${label}</button>`).join("");
  const pool = (label: string, now: number, max: number, cls: string) =>
    plain("pool:" + cls, `<span class="n">${label}</span>${meter(max > 0 ? now / max : 0, cls)}<span class="v">${fmt(now)}/${fmt(max)}</span>`,
      `${label} ${fmt(now)} of ${fmt(max)}`);
  const notice = s.notice === undefined ? "" : `<p class="notice" role="status">${esc(s.notice)}</p>`;
  return `<section class="window paper charsheet" aria-label="Character">
  <header class="bar"><h1>Character</h1>${intentButton(close(), "close", "Close", `data-key="close"`)}</header>
  <div class="tabrow"><span class="pad" aria-hidden="true">LB</span><nav class="tabs" aria-label="Pages">${tabs}</nav><span class="pad" aria-hidden="true">RB</span></div>
  <div class="body">
    <aside class="side" aria-label="Who">
      <h2 class="who">${esc(s.name)}</h2><p class="race">${esc(s.race)}</p>
      ${plain("level", `<span class="n">Level ${s.level}</span>${meter(s.progress, "lvl")}<span class="v">${pct(s.progress)}%</span>`, `Level ${s.level}, ${pct(s.progress)} percent to the next`)}
      ${pool("Health", s.health, s.healthMax, "health")}${pool("Magicka", s.magicka, s.magickaMax, "magicka")}${pool("Stamina", s.stamina, s.staminaMax, "stamina")}
      ${plain("points", `<span class="n">Perk points</span><span class="v">${s.perkPoints}</span>`, `Perk points ${s.perkPoints}`)}
    </aside>
    ${list(s, tab)}
  </div>
  <p class="hint" aria-live="polite"></p>
  <p class="legend" aria-hidden="true"><span><b>A</b> ${tab === "perks" ? "Take perk" : "Select"}</span><span><b>LB</b>/<b>RB</b> Page</span><span><b>B</b> Back</span></p>
  ${notice}
</section>`;
}
