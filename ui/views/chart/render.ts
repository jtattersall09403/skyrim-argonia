// The parchment chart's frame (1.2 §e, 1.12 §5), render only: our own window in the frame style (a dark pane with the
// gold-green trim round the parchment), the canvas the layers are drawn on, a marker for each discovered place (the
// push carries only those; its name shows on focus, hover or tap and is lettered beside it), the player's marker,
// and the zoom and close controls for touch. No quest or other markers, and no fast travel: a place is not a button
// that travels.
import type { ChartPlace, ChartState } from "../../schema/generated/messages.ts";
import { esc, intentButton } from "../core/html.ts";

// A place kind's glyph (tools/chart/render.py PIN; glyphs.json, the old map's own art); a kind with none is a landmark.
export const PIN: Record<string, string> = { settlement: "pin-settlement", ruin: "pin-ruin", lair: "pin-cave",
  sacred: "pin-shrine", transit: "pin-docks", works: "pin-mine", camp: "pin-camp", lone: "pin-farm",
  martial: "pin-fort", civic: "pin-landmark" };

export const pinSvg = (kind: string, paths: Record<string, string> = {}): string => {
  const d = paths[PIN[kind] ?? "pin-landmark"] ?? paths["pin-landmark"];
  return `<svg class="pin" viewBox="0 0 100 100" aria-hidden="true">${d ? `<path fill-rule="evenodd" d="${d}"/>`
    : `<circle cx="50" cy="50" r="30"/>`}</svg>`;
};

// The player's marker in our style: an ink arrowhead with a paper rim, pointing the way the player faces.
export const PLAYER_SVG = `<svg viewBox="-12 -12 24 24" aria-hidden="true"><circle r="10.5" class="me-ring"/>
  <path d="M0 -9 L6.5 7 L0 3.5 L-6.5 7Z" class="me-arrow"/></svg>`;

export function render(s: ChartState, cities: { id: string; name: string; x: number; y: number }[] = [],
  pins: Record<string, string> = {}): string {
  const all: (Pick<ChartPlace, "id" | "name" | "x" | "y"> & { discovered: boolean })[] =
    [...s.places.map((p) => ({ ...p, discovered: true })), ...cities.map((c) => ({ ...c, discovered: false }))];
  const labels = all.map((p) =>
    `<span class="label" hidden data-label="${esc(p.id)}" data-x="${p.x}" data-y="${p.y}" data-discovered="${p.discovered}">${esc(p.name)}</span>`).join("");
  const places = s.places.map((p) =>
    `<button type="button" class="place" data-nav data-key="place:${esc(p.id)}" data-place="${esc(p.id)}" data-kind="${esc(p.kind)}"
      data-x="${p.x}" data-y="${p.y}" aria-label="${esc(p.name)}">${pinSvg(p.kind, pins)}<span class="pname">${esc(p.name)}</span></button>`).join("");
  const me = s.player
    ? `<div class="me" data-player data-x="${s.player.x}" data-y="${s.player.y}" data-heading="${s.player.heading}" aria-label="You">${PLAYER_SVG}</div>` : "";
  return `<section class="chart frame" aria-label="Chart" data-worldspace="${esc(s.worldspace)}" data-sketch="${esc(s.sketch)}">
  <div class="sheet paper"><canvas class="layers"></canvas><div class="labels">${labels}</div><div class="places">${places}${me}</div></div>
  <div class="controls">
    <button type="button" class="zoom" data-ui="zoom-in" data-key="zoom-in" aria-label="Zoom in">+</button>
    <button type="button" class="zoom" data-ui="zoom-out" data-key="zoom-out" aria-label="Zoom out">&minus;</button>
    ${intentButton({ type: "view.close", v: 1, body: { view: "chart" } }, "close", "Close", `data-key="close"`)}
  </div>
</section>`;
}
