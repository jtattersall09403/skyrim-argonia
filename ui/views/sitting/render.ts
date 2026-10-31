// The level sitting (1.5, 2.8 §a), render only: the rest's one page where carried vastei buys attribute points. Every
// number comes from the push (ArgoniaCore prices each point and gives the refusal); the view computes no price and
// no rule. A Buy is a sitting.buy intent; Rise (and Escape, the pad's B) is sitting.done, so closing is rising.
import type { SittingAttribute, SittingRefusal, SittingState } from "../../schema/generated/messages.ts";
import { esc, intentButton } from "../core/html.ts";

export const done = () => ({ type: "sitting.done" as const, v: 1 as const, body: {} });
const buy = (a: SittingAttribute["id"]) => ({ type: "sitting.buy" as const, v: 1 as const, body: { attribute: a } });

export const REFUSAL: Record<SittingRefusal, string> = {
  tooDear: "Not enough vastei",
  atCapThisSitting: "No more at this sitting",
  atPurchaseCap: "At its height",
  noPendingLevel: "No level to take",
};

// Whole numbers read plainly; a fraction keeps one place.
const fmt = (n: number): string => (Number.isInteger(n) ? String(n) : n.toFixed(1));

function pips(a: SittingAttribute): string {
  const dots = Array.from({ length: a.cap }, (_, i) => `<i class="${i < a.bought ? "on" : ""}"></i>`).join("");
  return `<span class="tally"><span class="pips" aria-hidden="true">${dots}</span><span class="count">+${a.bought} / ${a.cap}</span></span>`;
}

function row(a: SittingAttribute): string {
  const why = a.refusal !== undefined
    ? `<span class="why">${esc(REFUSAL[a.refusal])}</span>`
    : `<span class="why"></span>`;
  const control = a.refusal !== undefined
    ? `<button type="button" class="buy" disabled data-key="buy:${a.id}">Buy</button>`
    : intentButton(buy(a.id), "buy", "Buy", `data-key="buy:${a.id}"`);
  return `<li class="attr ${a.refusal ?? "open"}" data-attr="${a.id}">
    <span class="name">${esc(a.name)}</span><span class="value">${a.value}</span>${pips(a)}
    <span class="cost">${fmt(a.cost)}</span>${why}${control}</li>`;
}

export function render(s: SittingState): string {
  const notice = s.notice !== undefined ? `<p class="notice" role="status">${esc(s.notice)}</p>` : "";
  const later = s.pendingAfter > 0 ? `<span class="later">${s.pendingAfter} more level to take later</span>` : "";
  return `<section class="sitting paper" aria-label="Level sitting">
  <header class="head"><h1>Level ${s.level}</h1><span class="vastei">Vastei carried <b>${fmt(s.vastei)}</b></span>${later}</header>
  <div class="cols"><span>Attribute</span><span>Now</span><span>This sitting</span><span>Cost</span><span></span><span></span></div>
  <ul class="attrs">${s.attributes.map(row).join("")}</ul>
  <div class="base"><p class="pool">Health <b>${fmt(s.health.before)}</b> <span class="arrow">&rarr;</span> <b>${fmt(s.health.after)}</b></p>
  ${notice}
  <span class="rise-slot">${intentButton(done(), "rise", "Rise", `data-key="rise"`)}</span></div>
</section>`;
}
