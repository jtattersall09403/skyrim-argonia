// The parchment chart (1.2 §e, 1.12 §5): the sketch layer everywhere, the revealed layer only where the player has
// been, a marker for each place whose discovery has fired (none before), and the player's marker. No quest or other
// markers, and no fast travel from it. Positions are in exterior cell units; Skyrim units live only in the units module.
import { int, intent, list, num, opt, push, ref, str, struct } from "./types.ts";

export const CellKey = struct("CellKey", "One exterior cell of the worldspace grid", {
  x: int("cell grid x"),
  y: int("cell grid y"),
});

export const ChartPlace = struct("ChartPlace", "A discovered place: its map marker, whose discovery has fired", {
  id: str("the map marker reference's form id, 8 hex digits"),
  name: str("the name lettered on the chart (the marker's name)"),
  kind: str("the marker's glyph kind (settlement, ruin, lair, ...; core chart::marker_kind)"),
  x: num("position in cell units"),
  y: num("position in cell units"),
});

export const ChartPlayer = struct("ChartPlayer", "Where the player stands and faces, in the province", {
  x: num("position in cell units"),
  y: num("position in cell units"),
  heading: num("degrees clockwise from north", { min: 0, max: 360 }),
});

export const ChartView = struct("ChartView", "Where the chart is looking; kept by ArgoniaCore between openings", {
  centreX: num("centre in cell units"),
  centreY: num("centre in cell units"),
  zoom: num("scale factor, 1 the whole province", { min: 0.05, max: 64 }),
});

export const chartState = push("chart.state", 2, "The open chart", {
  worldspace: str("world db worldspace id"),
  sketch: str("the sketch layer image id the view loads"),
  revealed: list(ref(CellKey), "every cell the player has uncovered"),
  places: list(ref(ChartPlace), "the discovered places only"),
  player: opt(ref(ChartPlayer), "absent outside the province (an interior, another worldspace)"),
  view: ref(ChartView),
});

export const chartPan = intent("chart.pan", 1, "The chart was panned or zoomed", {
  view: ref(ChartView),
});

export const messages = [chartState, chartPan];
