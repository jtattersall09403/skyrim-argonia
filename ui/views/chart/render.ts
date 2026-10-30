// The parchment chart's frame (1.2 §e), render only: the canvas the layers are drawn on, the discovered places as
// focusable marks (their names show on focus, hover or tap; the revealed layer letters them on the paper), and the
// zoom and close controls for touch. No player-position marker, ever (C9).
import type { ChartState } from "../../schema/generated/messages.ts";
import { esc, intentButton } from "../core/html.ts";

export function render(s: ChartState): string {
  const places = s.places.filter((p) => p.discovered).map((p) =>
    `<button type="button" class="place" data-nav data-key="place:${esc(p.id)}" data-place="${esc(p.id)}"
      data-x="${p.x}" data-y="${p.y}" aria-label="${esc(p.name)}"><span class="pname">${esc(p.name)}</span></button>`).join("");
  return `<section class="chart paper" aria-label="Chart" data-worldspace="${esc(s.worldspace)}" data-sketch="${esc(s.sketch)}">
  <div class="sheet"><canvas class="layers"></canvas><div class="places">${places}</div></div>
  <div class="controls">
    <button type="button" class="zoom" data-ui="zoom-in" data-key="zoom-in" aria-label="Zoom in">+</button>
    <button type="button" class="zoom" data-ui="zoom-out" data-key="zoom-out" aria-label="Zoom out">&minus;</button>
    ${intentButton({ type: "view.close", v: 1, body: { view: "chart" } }, "close", "Close", `data-key="close"`)}
  </div>
</section>`;
}
