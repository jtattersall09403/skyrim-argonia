"""The new world's water types: one WATR of our own per kind (and per flow heading for running water), and per region
a variant of each kind that takes the region's water look.

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

A region's look (newworld/sources/identity/regions.json, water.look; LOOKS below) moves a kind's colours and opacity
toward the look's target by LOOK_FRACTION, so the region's water reads as its own colour while every cell still reads
as its own kind (water_check: nearer its own kind's record than any other kind's). Keys:
  "<kind>@<region>"              a still kind in a region ("pond@aphon-isle", "sea@padomaic-ocean")
  "<kind>-<heading>@<region>"    running water in a region ("river-045@nha-enasa")
The text before "@" is the plain key. A key is made only where the variant's values differ from the kind's own
record (`key_for`), and `records` always carries the plain record of every kind it uses (a kind's own look is the
plain record). Variant editor ids end "_R<slot>" (the region's slot in the identity sheet, never renumbered).
Form ids come from the form-id registry's "water" block by the key ("watr:<key>"): a new key takes the next id and
no existing id moves. The worldspace's water and LOD water are the plain "sea" record: the world-level sea stays
neutral; only sea cells may take "sea@<region>". Regions that look black or tea-brown read as those on their own
kinds (the tea-brown swamp, the black marsh) because the kind keeps most of its own colour.
"""
from __future__ import annotations

import json
from pathlib import Path

HEADINGS = 16                      # running water: flow headings in steps of 22.5 degrees
STEP = 360 / HEADINGS
RUNNING = ("river", "stream", "estuary")
IDENTITY = Path(__file__).resolve().parents[3] / "newworld/sources/identity/regions.json"
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

LOOK_FRACTION = 0.3   # how far a kind's colours and opacity move toward the region's look
MAX_SHIFT = 18        # of 255, the most any colour channel or the opacity moves: under half of water_check.MIN_PAIR (40,
                      # the nearest two kinds' own looks), so by the triangle inequality a variant is always nearer its
                      # own kind's record than any other kind's (water_check's "reads as own kind")
# the nine looks (identity regions.json water_looks): the water's target ShallowColor, DeepColor, ReflectionColor and
# Opacity, each from the region research's words ("water.words" of the region) set within Skyrim's own waters:
# MurkyWater (the dark opaque bog), DefaultMarshWater (opaque green), DefaultCreekWater (clear green-grey), Tropical
# Skyrim's DefaultWater (clear turquoise sea) and King of the Murkmire's BlackmarshRiverWaterFlow (brown-green silt).
LOOKS = {
    "black": {"ShallowColor": [22, 18, 12], "DeepColor": [6, 5, 4], "ReflectionColor": [28, 28, 22], "Opacity": 98},
    "tea-brown": {"ShallowColor": [58, 38, 18], "DeepColor": [18, 11, 5], "ReflectionColor": [44, 38, 26], "Opacity": 92},
    "silt-brown": {"ShallowColor": [112, 88, 52], "DeepColor": [62, 48, 28], "ReflectionColor": [96, 88, 64], "Opacity": 78},
    "algae-green": {"ShallowColor": [60, 96, 36], "DeepColor": [20, 44, 12], "ReflectionColor": [84, 108, 60], "Opacity": 82},
    "reed-green": {"ShallowColor": [70, 102, 56], "DeepColor": [28, 58, 26], "ReflectionColor": [76, 98, 72], "Opacity": 45},
    "pale-silt-grey": {"ShallowColor": [140, 136, 118], "DeepColor": [86, 86, 76], "ReflectionColor": [118, 122, 116], "Opacity": 62},
    "turquoise": {"ShallowColor": [90, 190, 178], "DeepColor": [30, 120, 150], "ReflectionColor": [108, 130, 126], "Opacity": 25},
    "sea-green-grey": {"ShallowColor": [84, 130, 122], "DeepColor": [40, 84, 100], "ReflectionColor": [106, 118, 116], "Opacity": 45},
    "slate-blue": {"ShallowColor": [70, 110, 140], "DeepColor": [28, 60, 90], "ReflectionColor": [100, 116, 126], "Opacity": 40},
}
_REGIONS: dict = {}


def regions() -> dict:
    """region id -> {"slot", "look"} from the identity sheets."""
    if not _REGIONS:
        for rid, r in json.loads(IDENTITY.read_text())["regions"].items():
            _REGIONS[rid] = {"slot": r["slot"], "look": r["water"]["look"]}
    return _REGIONS


def toward(set_: dict, look: str, f: float = LOOK_FRACTION) -> dict:
    """A kind's `set` with its three colours and opacity moved the fraction f toward the look's target, the largest
    channel step held to MAX_SHIFT."""
    t, out = LOOKS[look], dict(set_)
    far = max(abs(b - a) for m in ("ShallowColor", "DeepColor", "ReflectionColor") for a, b in zip(set_[m], t[m]))
    f = min(f, MAX_SHIFT / max(far, abs(t["Opacity"] - set_["Opacity"]), 1))
    for m in ("ShallowColor", "DeepColor", "ReflectionColor"):
        out[m] = [round(a + (b - a) * f) for a, b in zip(set_[m], t[m])]
    out["Opacity"] = round(set_["Opacity"] + (t["Opacity"] - set_["Opacity"]) * f)
    return out


# landcover kinds whose water is one of the still kinds above
KIND_WATR = {"ocean": "sea", "shallow-coast": "sea", "bay": "sea", "lake": "pond", "green-marsh": "green-marsh",
             "blackwater-swamp": "blackwater-swamp", "estuary": "estuary", "pond": "pond"}


def heading(deg: float) -> int:
    """The flow heading snapped to the nearest of HEADINGS steps (compass degrees toward)."""
    return int(round(deg / STEP) % HEADINGS * STEP)


def split(key: str) -> tuple[str, str, str]:
    """A key's (kind, heading, region): "river-045@nha-enasa" -> ("river", "045", "nha-enasa"); "" where absent."""
    base, _, region = key.partition("@")
    kind, _, h = base.rpartition("-") if base.rsplit("-", 1)[-1].isdigit() else (base, "", "")
    return kind, h, region


def plain_key(key: str) -> str:
    """The key without its region ("river-045@nha-enasa" -> "river-045")."""
    return key.partition("@")[0]


def key_for(kind: str, flow_deg: float | None, still: str, region: str | None = None) -> str:
    """A water cell's type key: running kinds by their heading where the channel graph gives one in this cell
    ("river-045"); a river or stream that does not flow here takes the region's still water; the rest their kind.
    In a region with a water look the key is the region's variant of that record ("pond@aphon-isle"), kept only
    where the variant differs from the kind's own record."""
    if kind in ("river", "stream"):
        key = f"{kind}-{heading(flow_deg):03d}" if flow_deg is not None else KIND_WATR[still]
    elif kind == "estuary" and flow_deg is not None:
        key = f"estuary-{heading(flow_deg):03d}"
    else:
        key = KIND_WATR.get(kind, "sea")
    return variant_key(key, region) if region else key


def variant_key(key: str, region: str) -> str:
    """The plain key's variant in the region, or the plain key where the region's look changes nothing."""
    r = regions().get(region)
    if r is None:
        return key
    kind = split(key)[0]
    return key if toward(KINDS[kind]["set"], r["look"]) == KINDS[kind]["set"] else f"{key}@{region}"


def spec(key: str) -> dict:
    """The record a key stands for: {"copy", "edid", "set"} plus, for a heading, "heading" and "speed"."""
    kind, h, region = split(key)
    k = KINDS[kind]
    out = {"copy": k["copy"], "edid": k["edid"], "set": dict(k["set"])}
    if h:
        out.update(edid=f"{k['edid']}_{h}", heading=round(int(h) / STEP) * STEP, speed=k["speed"])  # "022" is 22.5
    elif kind in RUNNING:  # an estuary with no heading here: still, its layers spread so it does not drift
        out["edid"] = "ANW_Water_Estuary"
        out["set"].update(ZERO | STILL_SPREAD)
    if region:
        r = regions()[region]
        out["set"] = toward(out["set"], r["look"])
        out["edid"] += f"_R{r['slot']:02d}"
        out["look"] = r["look"]
    return out


def records(keys) -> dict:
    """Every record the cells use, by key, with the plain record of each (a kind's own look); the sea always (the
    world's own water, neutral)."""
    keys = set(keys) | {"sea"}
    return {k: spec(k) for k in sorted(keys | {plain_key(k) for k in keys})}


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
