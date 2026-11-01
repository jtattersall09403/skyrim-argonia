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

// The player's marker: ui/views/core/player-marker.svg (our gilt arrowhead in the likeness of Morrowind's, 1.12 look 1),
// inlined so the page needs no fetch; it points north and the view turns it to the heading.
export const PLAYER_SVG = `<svg aria-hidden="true" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"> <defs> <linearGradient id="pmL" x1="0" y1="0" x2="1" y2="1"> <stop offset="0" stop-color="#f6e2a0"/><stop offset="1" stop-color="#b8892f"/> </linearGradient> <linearGradient id="pmR" x1="1" y1="0" x2="0" y2="1"> <stop offset="0" stop-color="#a87a28"/><stop offset="1" stop-color="#5e4114"/> </linearGradient> </defs> <g stroke="#1d1308" stroke-width="1.6" stroke-linejoin="round"> <path d="M16 2 L27 28 L16 21 L5 28 Z" fill="#2a1c0a"/> </g> <path d="M16 3.6 L16 20.2 L6.6 26.2 Z" fill="url(#pmL)"/> <path d="M16 3.6 L25.4 26.2 L16 20.2 Z" fill="url(#pmR)"/> <path d="M16 3.6 L16 20.2" stroke="#fff3c4" stroke-width="0.6" opacity="0.7"/> </svg>`;

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
  return `<section class="chart frame" aria-label="Chart" data-title="Map" data-worldspace="${esc(s.worldspace)}" data-sketch="${esc(s.sketch)}">
  <div class="sheet paper"><canvas class="layers"></canvas><div class="labels">${labels}</div><div class="places">${places}${me}</div></div>
  <div class="controls">
    <button type="button" class="zoom" data-ui="zoom-in" data-key="zoom-in" aria-label="Zoom in">+</button>
    <button type="button" class="zoom" data-ui="zoom-out" data-key="zoom-out" aria-label="Zoom out">&minus;</button>
    ${intentButton({ type: "view.close", v: 1, body: { view: "chart" } }, "close", "Close", `data-key="close"`)}
  </div>
</section>`;
}
