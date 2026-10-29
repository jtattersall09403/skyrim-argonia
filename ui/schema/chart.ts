// The parchment chart (1.2 §e): the sketch layer everywhere, the revealed layer only where the player has been, the
// places found. No player-position marker (C9). Positions are in exterior cell units; metres and Skyrim units live
// only in the units module.
import { bool, int, intent, list, num, push, ref, str, struct } from "./types.ts";

export const CellKey = struct("CellKey", "One exterior cell of the worldspace grid", {
  x: int("cell grid x"),
  y: int("cell grid y"),
});

export const ChartPlace = struct("ChartPlace", "A place drawn on the chart", {
  id: str("world db place.id"),
  name: str("the name lettered on the chart"),
  kind: str("world db place.classification_class (settlement, ruin, ...)"),
  x: num("position in cell units"),
  y: num("position in cell units"),
  discovered: bool("false for a sketch-layer place the player has not reached"),
});

export const ChartView = struct("ChartView", "Where the chart is looking; kept by ArgoniaCore between openings", {
  centreX: num("centre in cell units"),
  centreY: num("centre in cell units"),
  zoom: num("scale factor, 1 the whole province", { min: 0.05, max: 64 }),
});

export const chartState = push("chart.state", 1, "The open chart", {
  worldspace: str("world db worldspace id"),
  sketch: str("the sketch layer image id the view loads"),
  revealed: list(ref(CellKey), "every cell the player has uncovered"),
  places: list(ref(ChartPlace)),
  view: ref(ChartView),
});

export const chartPan = intent("chart.pan", 1, "The chart was panned or zoomed", {
  view: ref(ChartView),
});

export const messages = [chartState, chartPan];
