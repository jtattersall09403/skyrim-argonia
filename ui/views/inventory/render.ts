// Our inventory screen (1.12 round 4), render only: SkyUI's and Wind UI's InventoryMenu in the paper theme. Ten tabs
// (All, then the nine categories) cycle with LB/RB and are buttons too; the list well holds the stacks with count,
// weight and value, an equipped mark on worn ones; the detail panel names the focused stack and carries Use and Drop;
// the foot line is the carry weight and gold. ArgoniaCore owns the items and every figure (the pad's A sends
// inventory.use); the tab and the focused stack are the view's own.
import type { InventoryCategory, InventoryItem, InventoryState } from "../../schema/generated/messages.ts";
import { esc, intentButton } from "../core/html.ts";

export type Tab = "all" | InventoryCategory;
export const TABS: readonly [Tab, string][] = [
  ["all", "All"], ["weapons", "Weapons"], ["apparel", "Apparel"], ["potions", "Potions"], ["scrolls", "Scrolls"],
  ["food", "Food"], ["ingredients", "Ingredients"], ["books", "Books"], ["keys", "Keys"], ["misc", "Misc"],
];
export const use = (item: string) => ({ type: "inventory.use" as const, v: 1 as const, body: { item } });
export const drop = (item: string) => ({ type: "inventory.drop" as const, v: 1 as const, body: { item } });
export const close = () => ({ type: "view.close" as const, v: 1 as const, body: { view: "inventory" as const } });

export const step = (tab: Tab, by: 1 | -1): Tab =>
  TABS[(TABS.findIndex(([t]) => t === tab) + by + TABS.length) % TABS.length][0];

export const visible = (s: InventoryState, tab: Tab): InventoryItem[] =>
  s.items.filter((i) => tab === "all" || i.category === tab);

const fmt = (n: number): string => (Math.round(n * 10) / 10).toString();

function row(i: InventoryItem): string {
  const mark = i.equipped ? `<span class="eq" title="Equipped">E</span>` : `<span class="eq"></span>`;
  return `<li class="row${i.equipped ? " on" : ""}">${intentButton(use(i.id), "name",
    `<span class="ic" aria-hidden="true"></span>${mark}<span class="n">${esc(i.name)}</span><span class="c">${i.count > 1 ? i.count : ""}</span>` +
    `<span class="w">${fmt(i.weight)}</span><span class="v">${i.value}</span>`,
    `data-key="i:${esc(i.id)}" data-id="${esc(i.id)}" aria-label="${esc(i.name)}, ${esc(i.action)}"` +
    `${i.equipped ? ' aria-pressed="true"' : ""}`)}</li>`;
}

// The detail panel for one stack (or none): the text above, then the two buttons. The buttons stay in the DOM while
// focus moves between stacks (main.ts only repoints them), so a focus on one is never torn out from under the pad.
export function detailText(i: InventoryItem | undefined): string {
  if (i === undefined) return `<p class="none">Nothing to show</p>`;
  const cat = TABS.find(([t]) => t === i.category)![1];
  return `<h2 class="ghead">${esc(i.name)}</h2><p class="kind">${esc(cat)}${i.equipped ? " (equipped)" : ""}</p>
    <dl class="figs"><dt>Count</dt><dd>${i.count}</dd><dt>Weight</dt><dd>${fmt(i.weight)}</dd><dt>Value</dt><dd>${i.value}</dd></dl>
    ${i.detail === undefined ? "" : `<p class="info">${esc(i.detail)}</p>`}`;
}
export function detail(i: InventoryItem | undefined): string {
  const off = i === undefined ? " disabled" : "";
  const [u, d] = i === undefined ? ["Use", "Drop"] : [i.action, "Drop"];
  const btn = (m: ReturnType<typeof use> | undefined, label: string, key: string) => m
    ? intentButton(m, "act", esc(label), `data-key="${key}"`)
    : `<button type="button" class="act" data-key="${key}"${off}>${label}</button>`;
  return `<div class="dtext">${detailText(i)}</div><div class="acts">${btn(i && use(i.id), u, "use")}${btn(i && drop(i.id), d, "drop")}</div>`;
}

export function render(s: InventoryState, tab: Tab = "all", sel?: string): string {
  const items = visible(s, tab);
  const cur = items.find((i) => i.id === sel) ?? items[0];
  const tabs = TABS.map(([t, label]) => {
    const n = s.items.filter((i) => t === "all" || i.category === t).length;
    return `<button type="button" class="tab${t === tab ? " on" : ""}" data-ui="tab" data-tab="${t}" data-key="tab:${t}" ` +
      `aria-pressed="${t === tab}">${label}<span class="tn">${n}</span></button>`;
  }).join("");
  const list = items.length ? items.map(row).join("") : `<li class="none">Nothing carried here</li>`;
  const notice = s.notice === undefined ? "" : `<p class="notice" role="status">${esc(s.notice)}</p>`;
  return `<section class="window paper inventory" aria-label="Inventory">
  <header class="bar"><h1>Inventory</h1>${intentButton(close(), "close", "Close", `data-key="close"`)}</header>
  <div class="body">
    <div class="listcol"><div class="tabrow"><span class="pad" aria-hidden="true">LB</span><nav class="tabs" aria-label="Categories">${tabs}</nav><span class="pad" aria-hidden="true">RB</span></div>
      <div class="colheads"><span class="ic"></span><span class="eq"></span><span class="n">Name</span><span class="c">Qty</span><span class="w">Wt</span><span class="v">Value</span></div>
      <ul class="well scroll" data-list="items">${list}</ul></div>
    <aside class="detail" aria-label="Item" aria-live="polite">${detail(cur)}</aside>
  </div>
  ${notice}
  <footer class="foot"><span class="carry${s.carried > s.capacity ? " over" : ""}">Carry weight ${fmt(s.carried)} / ${fmt(s.capacity)}<span class="meter" aria-hidden="true"><i style="width:${s.capacity > 0 ? Math.min(100, Math.round(100 * s.carried / s.capacity)) : 0}%"></i></span></span><span class="gold">Gold ${s.gold}</span></footer>
  <p class="legend" aria-hidden="true"><span><b>A</b> ${cur ? esc(cur.action) : "Use"}</span><span><b>LB</b>/<b>RB</b> Category</span><span><b>B</b> Back</span></p>
</section>`;
}
