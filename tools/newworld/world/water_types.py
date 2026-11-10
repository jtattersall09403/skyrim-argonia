"""The new world's water types: one WATR of our own per kind (and per flow heading for running water).

How Skyrim makes water read as its kind (measured, docs/research/nw-02-walk5-water.md):
- Colour and clarity are the record's shallow, deep and reflection colours, opacity and fog distances.
- A river reads as running one way through its three noise layers: each layer's wind direction is the bearing the
  ripples come FROM (compass degrees, 0 north, 90 east) and they drift toward that + 180 at the layer's wind speed
  (Skyrim.esm RiverWaterFlowNE: layers 233/267/252, current (2.54, 1.35) = heading 62; RiverWaterFlowNW: 141/106/177,
  current heading 316). The current (DNAM linear velocity, world x east / y north) pushes swimmers and floating things
  the same way. One record per cell (XCWT), so a cell's flow is one heading; vanilla's own per-cell flow textures
  (textures/water/<plugin>/flow.x.y.dds, Update.esm's RiverWaterFlow) are art we do not make.
- Still water: no current and layers that do not agree (MurkyWater 22/150/0, DefaultCreekWater 263/38/189) at low speed.

Each record is a copy of a vanilla record as the game has it (Update.esm's version), its textures and sounds kept, with
the values in `set` (colours as [r, g, b]); running kinds name the vanilla record their noise is rotated from and the
current's speed. The writer (ArgoniaPlugin WaterBlend.Records) rotates all three layers so the noise drifts toward the
cell's heading, and sets the current to that heading. Colours: the sea is Tropical Skyrim's DefaultWater (its
override of the vanilla sea), the river King of the Murkmire's BlackmarshRiverWaterFlow, the black swamp vanilla's
MurkyWater browned toward tea, the green marsh vanilla's DefaultMarshWater greened and made opaque, the pond and the
stream vanilla's DefaultCreekWater (pond greener and still, stream clearer); the estuary sits between river and sea.
"""
from __future__ import annotations

HEADINGS = 16                      # running water: flow headings in steps of 22.5 degrees
STEP = 360 / HEADINGS
RUNNING = ("river", "stream", "estuary")
STILL_SPREAD = {"NoiseLayerOneWindDirection": 270, "NoiseLayerTwoWindDirection": 30, "NoiseLayerThreeWindDirection": 150}
ZERO = {"LinearVelocity": [0, 0, 0]}

KINDS = {
    # warm tropical blue-green: Tropical Skyrim.esp's DefaultWater values on vanilla's sea
    "sea": {"copy": "Update.esm:DefaultWater", "edid": "ANW_Water_Sea", "set": {
        "ShallowColor": [81, 174, 165], "DeepColor": [28, 104, 140], "ReflectionColor": [103, 122, 117], "Opacity": 30,
        "FogAboveWaterAmount": 1.0, "FogAboveWaterDistanceNearPlane": -100.0, "FogAboveWaterDistanceFarPlane": 580.0,
        "WaterReflectivity": 0.5, "WaterFresnel": 0.05, "NoiseLayerOneUvScale": 1087.0,
        "NoiseLayerOneAmplitudeScale": 0.8043, "NoiseLayerOneWindSpeed": 0.017, **ZERO}},
    # dark tea-brown, opaque, dead still: vanilla's MurkyWater (BM&V's own world water), browned
    "blackwater-swamp": {"copy": "Update.esm:MurkyWater", "edid": "ANW_Water_BlackSwamp", "set": {
        "ShallowColor": [44, 30, 16], "DeepColor": [13, 9, 5], "ReflectionColor": [36, 34, 24], "Opacity": 95,
        "NoiseLayerOneWindSpeed": 0.006, "NoiseLayerTwoWindSpeed": 0.006, "NoiseLayerThreeWindSpeed": 0.006, **ZERO}},
    # opaque algae green, still: vanilla's DefaultMarshWater, greener and opaque, Tropical Skyrim's still marsh speeds
    "green-marsh": {"copy": "Update.esm:DefaultMarshWater", "edid": "ANW_Water_GreenMarsh", "set": {
        "ShallowColor": [56, 80, 30], "DeepColor": [18, 36, 10], "ReflectionColor": [86, 104, 64], "Opacity": 80,
        "FogAboveWaterDistanceFarPlane": 90.0, "WaterReflectivity": 0.6,
        "NoiseLayerOneWindSpeed": 0.007, "NoiseLayerTwoWindSpeed": 0.007, "NoiseLayerThreeWindSpeed": 0.007,
        **STILL_SPREAD, **ZERO}},
    # clear green, still: vanilla's DefaultCreekWater (no current), greener
    "pond": {"copy": "Update.esm:DefaultCreekWater", "edid": "ANW_Water_Pond", "set": {
        "ShallowColor": [58, 92, 50], "DeepColor": [24, 52, 20], "ReflectionColor": [70, 90, 70], "Opacity": 35,
        "NoiseLayerOneWindSpeed": 0.008, "NoiseLayerTwoWindSpeed": 0.01, "NoiseLayerThreeWindSpeed": 0.02, **ZERO}},
    # brown-green silty, visibly running: King of the Murkmire's BlackmarshRiverWaterFlow colours on vanilla's river
    "river": {"copy": "Update.esm:RiverWaterFlowNE", "edid": "ANW_RiverWaterFlow", "speed": 2.88, "set": {
        "ShallowColor": [112, 104, 44], "DeepColor": [56, 82, 48], "ReflectionColor": [92, 118, 72], "Opacity": 70}},
    # clearer and quicker: vanilla's creek noise, its speeds raised past the river's, the creek's clear colours
    "stream": {"copy": "Update.esm:CreekWaterFlowSE", "edid": "ANW_CreekWaterFlow", "speed": 3.2, "set": {
        "ShallowColor": [96, 104, 92], "DeepColor": [52, 56, 48], "ReflectionColor": [80, 96, 104], "Opacity": 15,
        "NoiseLayerOneWindSpeed": 0.12, "NoiseLayerTwoWindSpeed": 0.07, "NoiseLayerThreeWindSpeed": 0.4}},
    # silty green-brown meeting the sea, running slowly seaward where the channel graph gives a heading
    "estuary": {"copy": "Update.esm:RiverWaterFlowNE", "edid": "ANW_EstuaryWaterFlow", "speed": 1.0, "set": {
        "ShallowColor": [96, 138, 104], "DeepColor": [40, 96, 92], "ReflectionColor": [98, 124, 100], "Opacity": 50,
        "NoiseLayerOneWindSpeed": 0.036, "NoiseLayerTwoWindSpeed": 0.016, "NoiseLayerThreeWindSpeed": 0.12}},
}
# landcover kinds whose water is one of the still kinds above
KIND_WATR = {"ocean": "sea", "shallow-coast": "sea", "bay": "sea", "lake": "pond", "green-marsh": "green-marsh",
             "blackwater-swamp": "blackwater-swamp", "estuary": "estuary", "pond": "pond"}


def heading(deg: float) -> int:
    """The flow heading snapped to the nearest of HEADINGS steps (compass degrees toward)."""
    return int(round(deg / STEP) % HEADINGS * STEP)


def key_for(kind: str, flow_deg: float | None, still: str) -> str:
    """A water cell's type key: running kinds by their heading where the channel graph gives one in this cell
    ("river-045"); a river or stream that does not flow here takes the region's still water; the rest their kind."""
    if kind in ("river", "stream"):
        return f"{kind}-{heading(flow_deg):03d}" if flow_deg is not None else KIND_WATR[still]
    if kind == "estuary" and flow_deg is not None:
        return f"estuary-{heading(flow_deg):03d}"
    return KIND_WATR.get(kind, "sea")


def spec(key: str) -> dict:
    """The record a key stands for: {"copy", "edid", "set"} plus, for a heading, "heading" and "speed"."""
    kind, _, h = key.rpartition("-") if key.rsplit("-", 1)[-1].isdigit() else (key, "", "")
    k = KINDS[kind]
    out = {"copy": k["copy"], "edid": k["edid"], "set": dict(k["set"])}
    if h:
        out.update(edid=f"{k['edid']}_{h}", heading=round(int(h) / STEP) * STEP, speed=k["speed"])  # "022" is 22.5
    elif kind in RUNNING:  # an estuary with no heading here: still, its layers spread so it does not drift
        out["edid"] = "ANW_Water_Estuary"
        out["set"].update(ZERO | STILL_SPREAD)
    return out


def records(keys) -> dict:
    """Every record the cells use, by key; the sea always (the world's own water)."""
    return {k: spec(k) for k in sorted(set(keys) | {"sea"})}


LIMITS = [
    "One water type per cell (XCWT): a cell holding two kinds shows its dominant kind's water.",
    f"Running water flows one heading per cell, the channel's mean heading in that cell snapped to {HEADINGS} "
    "headings; where a river bends the heading steps from one cell to the next.",
    "Cells near a change of kind are our own blend records (ArgoniaPlugin WaterBlend.cs), graded across the seam "
    "only, so no cell edge (side or corner) steps more than 14 of 255 in any colour or in the opacity; a strong "
    "contrast grades over more cells; rivers and streams, one to three cells wide, keep their own motion but share "
    "their colour with their banks; cells away from a seam keep their kind's own record.",
    "No rapids, falls or ripple FX statics yet (placement step).",
]
