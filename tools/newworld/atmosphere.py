"""The new world's atmosphere (walk 5): the region atmosphere classes in the database, the weather, image space,
volumetric lighting and climate records they make, their read-back and a swatch sheet. The recipe is
docs/design/atmosphere.md; the research and every measured number docs/research/nw-02-walk5-atmosphere.md.

    python3 -m tools.newworld.atmosphere study  [--out out/atmosphere]          # measure Bethesda's, BM&V's, TS's and the build given by --old
    python3 -m tools.newworld.atmosphere spec   [--plugin out/newworld/plugin]  # <plugin>/atmosphere.json for the writer
    python3 -m tools.newworld.atmosphere check  [--plugin ...]                  # read the built ESM back against the spec
    python3 -m tools.newworld.atmosphere swatch [--plugin ...] [--out out/atmosphere]   # swatches.png

Sources: newworld/sources/atmosphere/classes.json (the classes, their research numbers, the kinds and families) and
regions.json (each region's class with its reason); `load(w)` puts them in the database (atmosphere_class,
region_atmosphere: the band measured from the region's province cells). The spec is built from the database and the
vanilla source records (read from Skyrim.esm and Update.esm through `ArgoniaPlugin atmos study`).

A colour slot keeps the source weather's luminance (Bethesda's level for that weather and hour) and takes the class's
hue: sunlight from the class's colour temperature, fog from its haze, ambient and the directional ambient sides from
its fill, the directional ambient from below from its ground, the sky from its sky colour. Fog distances are the
reference weather's (Skyrim's base set, classes.json reference_fog) times the class's visibility,
sqrt((1 - RH) / (1 - RH_ref)) / aerosol (hygroscopic growth of haze, gamma 0.5).
"""
from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "newworld/sources/atmosphere"
MEASURED = SRC / "measured.json"   # the reference measures (study()), kept as research numbers
DATA = Path(os.environ.get("ARGONIA_GAME_ROOT", Path.home() / "games/skyrimse")) / "Data"
BIN = REPO / "out/tools/ArgoniaPlugin"
TODS = ("Sunrise", "Day", "Sunset", "Night")
BANDS = ("north", "middle", "south")
# warm enough: tropical noon sun 5,000-6,000 K (research 1.1, 1.8); Skyrim's base set as BM&V lists it measures 7,446 K,
# sun warmth -0.09, far fog warmth -0.34
WARM_SUN_K, WARM_SUN_W, WARM_FOG_W = 6000, 0.05, -0.10
REGION_PRIORITY = 50     # NewWorldAtmosphere.cs RegionPriority: Skyrim's regional weather sets carry Override, 50 to 55
# fixed form ids (NewWorldAtmosphere.cs takes them from the spec): set s = class index * 3 + band index
BASE = {"IMGS": 0x80000, "VOLI": 0x80400, "WTHR": 0x80500, "CLMT": 0x80600}
# the regions' own sets (identity sheets): set s = the region's slot (newworld/sources/identity/regions.json); the class
# sets' ids above stay reserved and are no longer written
REGION_BASE = {"IMGS": 0x80800, "VOLI": 0x80A40, "WTHR": 0x80B00}
IDENTITY = REPO / "newworld/sources/identity/regions.json"
DAWN_MIX = 0.5   # dawn and dusk haze: half the class's, half the region's mood
SLOT_ROLE = {"SunlightColor": "sun", "EffectLightingColor": "sun", "FogNearColor": "haze", "FogFarColor": "far",
             "AmbientColor": "fill", "SkyUpperColor": "sky", "SkyLowerColor": "horizon", "HorizonColor": "horizon"}
DALC_SIDES = ("DirectionalXPlus", "DirectionalXMinus", "DirectionalYPlus", "DirectionalYMinus")


def load_sources() -> tuple[dict, dict]:
    return json.loads((SRC / "classes.json").read_text()), json.loads((SRC / "regions.json").read_text())


# ---- colour ------------------------------------------------------------------------------------------------------

def kelvin_rgb(k: float) -> list[int]:
    """sRGB of a black body at k kelvin (Tanner Helland's fit to the CIE 1964 data, 1000-40000 K)."""
    t = k / 100
    r = 255 if t <= 66 else 329.698727446 * (t - 60) ** -0.1332047592
    g = 99.4708025861 * math.log(t) - 161.1195681661 if t <= 66 else 288.1221695283 * (t - 60) ** -0.0755148492
    b = 255 if t >= 66 else 0 if t <= 19 else 138.5177312231 * math.log(t - 10) - 305.0447927307
    return [int(round(min(255, max(0, v)))) for v in (r, g, b)]


def lum(c) -> float:
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def recolour(src, target, gain: float = 1.0, strength: float = 1.0) -> list[int]:
    """The target's hue at the source's luminance times gain, mixed over the source by strength."""
    y, ty = lum(src) * gain, lum(target)
    t = [c * y / ty for c in target] if ty > 0 else [y, y, y]
    m = max(t)
    if m > 255:
        t = [c * 255 / m for c in t]
    return [int(round(min(255, max(0, s * (1 - strength) + c * strength)))) for s, c in zip(src, t)]


def mix(a, b, f: float) -> list[float]:
    return [x * (1 - f) + y * f for x, y in zip(a, b)]


def _lin(c: float) -> float:
    c /= 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def xyz(c) -> tuple[float, float, float]:
    r, g, b = (_lin(v) for v in c)
    return (0.4124 * r + 0.3576 * g + 0.1805 * b, 0.2126 * r + 0.7152 * g + 0.0722 * b, 0.0193 * r + 0.1192 * g + 0.9505 * b)


def lab(c) -> tuple[float, float, float]:
    X, Y, Z = xyz(c)
    f = [v ** (1 / 3) if v > 0.008856 else 7.787 * v + 16 / 116 for v in (X / 0.95047, Y, Z / 1.08883)]
    return 116 * f[1] - 16, 500 * (f[0] - f[1]), 200 * (f[1] - f[2])


def delta_e(a, b) -> float:
    return math.dist(lab(a), lab(b))


def cct(c) -> float:
    """Correlated colour temperature (McCamy) of an sRGB colour; meaningful for near-white light and fog."""
    X, Y, Z = xyz(c)
    s = X + Y + Z
    if s <= 0:
        return 0.0
    x, y = X / s, Y / s
    n = (x - 0.3320) / (0.1858 - y)
    return 449 * n ** 3 + 3525 * n ** 2 + 6823.3 * n + 5520.33


def warmth(c) -> float:
    """(R - B) / mean: + warm, - cool."""
    return (c[0] - c[2]) / max(1.0, sum(c) / 3)


# ---- the vanilla records -----------------------------------------------------------------------------------------

def run_study(plugins: list[Path], out: Path) -> dict:
    env = dict(os.environ, DOTNET_ROOT=str(Path.home() / ".dotnet"), DOTNET_CLI_TELEMETRY_OPTOUT="1", DOTNET_NOLOGO="1")
    env["PATH"] = f"{Path.home() / '.dotnet'}:{env['PATH']}"
    subprocess.run(["dotnet", "build", "-c", "Release", "-o", str(BIN), str(REPO / "tools/ArgoniaPlugin"), "-v", "q", "-nologo"],
                   check=True, env=env, capture_output=True)
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["dotnet", str(BIN / "ArgoniaPlugin.dll"), "atmos", "study", str(out), *map(str, plugins)],
                   check=True, env=env, capture_output=True)
    return json.loads(out.read_text())


class Records:
    """Load-order winners of a study's WTHR, IMGS, VOLI, CLMT and REGN, by form key and by editor id."""

    def __init__(self, study: dict, order: list[str]):
        self.win, self.src, self.edid = {}, {}, {}
        for p in order:
            for sig, recs in study.get(p, {}).items():
                for r in recs:
                    self.win[(sig, r["FormKey"])] = r
                    self.src[(sig, r["FormKey"])] = p
        for (sig, fk), r in self.win.items():
            if r.get("EditorID"):
                self.edid[(sig, r["EditorID"])] = fk

    def get(self, sig: str, key: str) -> dict:
        fk = key if ":" in key and key.split(":")[0].isalnum() and len(key.split(":")[0]) == 6 else self.edid[(sig, key.split(":")[-1])]
        return self.win[(sig, fk)]

    def winner_file(self, sig: str, r: dict) -> str:
        return self.src[(sig, r["FormKey"])]


VANILLA = ["Skyrim.esm", "Update.esm"]


# ---- the database ------------------------------------------------------------------------------------------------

def bands_of(cells) -> dict[str, tuple[str, float]]:
    """Each region's latitude band from its province (non-margin) cells: Morrowind cell y to the Skyrim cell row
    2y + 1, its mean against classes.json's thresholds."""
    cls, _ = load_sources()
    b = cls["bands"]
    acc: dict[str, list[float]] = {}
    for c in cells:
        if not c.margin:
            acc.setdefault(c.region_id, []).append(2 * c.y + 1)
    res = {}
    for rid, ys in acc.items():
        cy = sum(ys) / len(ys)
        band = "north" if cy > b["north"]["cy_above"] else "south" if cy < b["south"]["cy_below"] else "middle"
        res[rid] = (band, round(cy, 1))
    return res


def load(w) -> None:
    """newworld/sources/atmosphere -> atmosphere_class, region_atmosphere (called by build_db.build())."""
    cls, regs = load_sources()
    for cid, c in cls["classes"].items():
        w.insert("atmosphere_class", id=cid, name=c["name"], analogue=c["analogue"], weather_family=c["family"],
                 research_section=c["research"], sun_noon_k=c["sun_k"]["Day"], rh_afternoon=c["rh"], aerosol=c["aerosol"],
                 mist_density=c["mist"]["density"], mist_full_vis=c["mist"]["full_vis"])
    bands = bands_of(w.rows("cell"))
    aspects = {a.id for a in w.rows("note_aspect")}
    for rid, (cid, aspect, why) in sorted(regs["regions"].items()):
        if aspect not in aspects:
            raise ValueError(f"regions.json {rid}: aspect {aspect!r} is not a note_aspect")
        band, cy = bands[rid]
        w.insert("region_atmosphere", region_id=rid, atmosphere_class_id=cid, band=band, centroid_cell_y=cy,
                 note_aspect_id=aspect, why=why)


def region_classes(w=None) -> dict[str, tuple[str, str]]:
    """region id -> (class id, band), from the database."""
    if w is None:
        from tools.argonia_world import db
        w = db.open("newworld")
    return {r.region_id: (r.atmosphere_class_id, r.band) for r in w.rows("region_atmosphere")}


# ---- the spec ----------------------------------------------------------------------------------------------------

def camel(s: str) -> str:
    return "".join(p.capitalize() for p in s.replace("_", "-").split("-"))


def visibility(c: dict, band: dict, cls: dict) -> float:
    rh = min(0.97, c["rh"] + band["rh"])
    return math.sqrt((1 - rh) / (1 - cls["rh_reference"])) ** (2 * cls["gamma"]) / c["aerosol"]


def chances(c: dict, band: dict, kinds) -> dict[str, int]:
    raw = {k: max(1.0, c["chances"][k] + band["chances"].get(k, 0)) for k in kinds}
    tot = sum(raw.values())
    exact = {k: v * 100 / tot for k, v in raw.items()}
    out = {k: int(v) for k, v in exact.items()}
    for k in sorted(exact, key=lambda k: -(exact[k] - out[k]))[:100 - sum(out.values())]:
        out[k] += 1
    return out


def targets(c: dict, band: dict, tod: str) -> dict:
    sun = kelvin_rgb(c["sun_k"][tod] + band["sun_k"])
    haze, sky = c["haze"][tod], c["sky"][tod]
    return {"sun": sun, "haze": haze, "far": mix(haze, sky, 0.25), "fill": c["fill"][tod], "sky": sky,
            "horizon": mix(sky, haze, 0.6), "ground": c["ground"], "zenith": mix(sky, c["fill"][tod], 0.5),
            "tint": mix(sun, haze, 0.3)}


def with_identity(c: dict, idr: dict) -> dict:
    """The class's numbers with the region's identity over them: the day haze is the region's mood (dawn and dusk half
    way to it), the fill and sky lean to it; brightness scales the fog, ambient and sun gains; saturation the class's."""
    c = json.loads(json.dumps(c))
    li, haze = idr["light"], idr["light"]["haze"]
    c["haze"]["Day"] = haze
    for tod in ("Sunrise", "Sunset"):
        c["haze"][tod] = [round(v) for v in mix(c["haze"][tod], haze, DAWN_MIX)]
    c["fill"]["Day"] = [round(v) for v in mix(c["fill"]["Day"], haze, 0.5)]
    c["sky"]["Day"] = [round(v) for v in mix(c["sky"]["Day"], haze, 0.3)]
    c["gain"] = {k: v * li["brightness"] for k, v in c["gain"].items()}
    c["saturation"] = c["saturation"] * li["saturation"]
    c["night_gain"] = li["night"]
    c["chances"] = dict(idr["weather"]["chances"])
    return c


def extremes(rec: Records) -> dict:
    """Skyrim's own range over its regional weathers (the Skyrim* weathers its regions list, snow and blizzard left
    out): fog distances, each colour slot's luminance by hour, image space saturation. Ours are kept inside it."""
    ws = {}
    for (sig, _), r in rec.win.items():
        if sig == "REGN":
            for w in ((r.get("Weather") or {}).get("Weathers") or []):
                x = rec.win.get(("WTHR", w["Weather"]))
                e = (x or {}).get("EditorID") or ""
                if e.startswith("Skyrim") and "Snow" not in e and "Blizzard" not in e:
                    ws[e] = x
    if not ws:
        return {}
    out = {f: (min(w[f] for w in ws.values()), max(w[f] for w in ws.values())) for f in ("FogDistanceDayFar", "FogDistanceNightFar")}
    for slot in SLOT_ROLE:
        for tod in TODS:
            v = [lum(w[slot][tod]) for w in ws.values()]
            out[f"{slot}.{tod}"] = (min(v), max(v))
    sat = [rec.win[("IMGS", w["ImageSpaces"][t])]["Cinematic"]["Saturation"] for w in ws.values() for t in TODS
           if ("IMGS", w["ImageSpaces"][t]) in rec.win and rec.win[("IMGS", w["ImageSpaces"][t])].get("Cinematic")]
    out["Saturation"] = (min(sat), max(sat))
    return out


def clamp_lum(col: list[int], lo_hi) -> list[int]:
    if not lo_hi:
        return col
    y = lum(col)
    lo, hi = lo_hi
    if y <= 0 or lo <= y <= hi:
        return col
    f = (lo if y < lo else hi) / y
    return [int(round(min(255, max(0, v * f)))) for v in col]


def weather_set(cls: dict, cid: str, band_id: str, rec: Records, rid: str | None = None, idr: dict | None = None,
                lim: dict | None = None) -> dict:
    """The records of one set: 6 weathers, their 24 image spaces and 4 volumetric lightings. A region's own set (rid
    and its identity row idr) takes the region's light, sight and weather over its class (with_identity), its ids from
    the region's slot, its values held inside Skyrim's range (lim, extremes())."""
    c, band = cls["classes"][cid], cls["bands"][band_id]
    lim = lim or {}
    if idr is not None:
        c = with_identity(c, idr)
        s, base, name, vis = idr["slot"], REGION_BASE, camel(rid), idr["sight"]["visibility"]
    else:
        ci, bi = list(cls["classes"]).index(cid), BANDS.index(band_id)
        s, base, name, vis = ci * 3 + bi, BASE, f"{camel(cid)}_{band_id.capitalize()}", visibility(c, band, cls)
    night_gain = c.get("night_gain", 1.0)
    fam = cls["families"][c["family"]]
    out = {"weathers": [], "imagespaces": [], "volumetric": []}
    voli_src = rec.get("WTHR", fam["fair"].split(":")[1])["VolumetricLighting"]
    vl = {}
    for ti, tod in enumerate(TODS):
        src = rec.win[("VOLI", voli_src[tod])]
        t = targets(c, band, tod)
        col = [v / 255 for v in recolour([255, 255, 255], t["haze"], 1.0)]
        edid = f"ANW_VL_{name}_{tod}"
        out["volumetric"].append({"formid": base["VOLI"] + s * 4 + ti, "edid": edid, "copy": f"{rec.winner_file('VOLI', src)}:{src['EditorID']}",
                                  "set": {"CustomColorContribution": c["voli"]["colour_share"], "ColorR": round(col[0], 3),
                                          "ColorG": round(col[1], 3), "ColorB": round(col[2], 3),
                                          "DensityContribution": c["voli"]["density"]}})
        vl[tod] = edid
    for ki, kind in enumerate(cls["kinds"]):
        src = rec.get("WTHR", fam[kind].split(":")[1])
        st = cls["kind_strength"][kind]
        edid = f"ANW_W_{name}_{kind.capitalize()}"
        sets: dict = {}
        steam = kind == "steam"
        for tod in TODS:
            t = targets(c, band, tod)
            day = tod != "Night"
            for slot, role in SLOT_ROLE.items():
                gain = 1.0
                if role in ("haze", "far") and day:
                    gain = c["gain"]["fog"] * (1.1 if steam else 1.0)
                elif role == "fill":
                    gain = c["gain"]["ambient"]
                elif role == "sun" and day:
                    gain = c["gain"]["sun"]
                if not day:
                    gain *= night_gain
                strength = st * (c["sky_mix"] if role in ("sky", "horizon") else 1.0)
                sets[f"{slot}.{tod}"] = clamp_lum(recolour(src[slot][tod], t[role], gain, strength), lim.get(f"{slot}.{tod}"))
            d = src["DirectionalAmbientLightingColors"][tod]
            ng = 1.0 if day else night_gain
            for side in DALC_SIDES:
                sets[f"DirectionalAmbientLightingColors.{tod}.{side}"] = recolour(d[side], t["fill"], c["gain"]["ambient"] * ng, st)
            sets[f"DirectionalAmbientLightingColors.{tod}.DirectionalZPlus"] = recolour(d["DirectionalZPlus"], t["ground"], 1.0, st)
            sets[f"DirectionalAmbientLightingColors.{tod}.DirectionalZMinus"] = recolour(d["DirectionalZMinus"], t["zenith"], 1.0, st)
        ref = rec.get("WTHR", cls["reference_fog"][kind].split(":")[1])
        dfar = ref["FogDistanceDayFar"] * vis
        if steam:
            dfar *= c["steam_scale"]
        nfar = ref["FogDistanceNightFar"] * vis
        if "FogDistanceDayFar" in lim:  # inside Skyrim's own range of regional fog distances
            dfar = min(max(dfar, lim["FogDistanceDayFar"][0]), lim["FogDistanceDayFar"][1])
            nfar = min(max(nfar, lim["FogDistanceNightFar"][0]), lim["FogDistanceNightFar"][1])
        sets.update({"FogDistanceDayNear": 0.0, "FogDistanceDayFar": round(dfar), "FogDistanceNightFar": round(nfar)})
        if kind in ("fair", "cloudy"):  # the dawn mist: a dense Night slot lerped to Day across the sunrise window
            sets.update({"FogDistanceNightNear": 0.0, "FogDistanceNightFar": c["night_mist"]["far"],
                         "FogDistanceNightPower": 0.4, "FogDistanceNightMax": c["night_mist"]["max"]})
        ims = {}
        for ti, tod in enumerate(TODS):
            isrc = rec.win[("IMGS", src["ImageSpaces"][tod])]
            t = targets(c, band, tod)
            ie = f"ANW_IS_{name}_{kind.capitalize()}_{tod}"
            tint = recolour(isrc["Tint"]["Color"], t["tint"], 1.0, st)
            sat = isrc["Cinematic"]["Saturation"] * (1 + (c["saturation"] - 1) * st)
            if "Saturation" in lim:
                sat = min(max(sat, lim["Saturation"][0]), lim["Saturation"][1])
            out["imagespaces"].append({"formid": base["IMGS"] + s * 24 + ki * 4 + ti, "edid": ie,
                                       "copy": f"{rec.winner_file('IMGS', isrc)}:{isrc['EditorID']}",
                                       "set": {"Tint.Color": tint, "Cinematic.Saturation": round(sat, 4)}})
            ims[tod] = ie
        w = {"formid": base["WTHR"] + s * 8 + ki, "edid": edid, "kind": kind, "class": cid, "band": band_id, "region": rid,
             "copy": f"{rec.winner_file('WTHR', src)}:{src['EditorID']}", "set": sets, "imagespaces": ims}
        if kind not in ("rain", "storm"):
            w["volumetric"] = vl
        out["weathers"].append(w)
    return out


def build_spec(rec: Records, rc: dict[str, tuple[str, str]], ident: dict | None = None) -> dict:
    """Each region its own set (its class as the family, its identity sheet over it); the climate takes the default
    class's region set nearest the middle (classes.json climate.default_class)."""
    cls, _ = load_sources()
    ident = ident if ident is not None else json.loads(IDENTITY.read_text())["regions"]
    lim = extremes(rec)
    spec = {"weathers": [], "imagespaces": [], "volumetric": [], "regions": {}, "sets": {},
            "limits": {k: [round(v[0], 2), round(v[1], 2)] for k, v in lim.items()}}
    for rid, (cid, band) in sorted(rc.items(), key=lambda kv: ident[kv[0]]["slot"]):
        part = weather_set(cls, cid, band, rec, rid, ident[rid], lim)
        for k in ("weathers", "imagespaces", "volumetric"):
            spec[k] += part[k]
        ch = chances(with_identity(cls["classes"][cid], ident[rid]), {"chances": {}}, cls["kinds"])
        spec["sets"][rid] = [[w["edid"], ch[w["kind"]]] for w in part["weathers"]]
        spec["regions"][rid] = spec["sets"][rid]
    cl = cls["climate"]
    home = min((r for r, cb in rc.items() if cb == (cl["default_class"], cl["default_band"])), default=min(rc))
    spec["climate"] = {"formid": BASE["CLMT"], "edid": "ANW_Climate", "copy": "Black Marsh.esm:BlackMarshClimate",
                       "weathers": spec["sets"][home], "region": home,
                       **{k: cl[k] for k in ("sunrise_begin", "sunrise_end", "sunset_begin", "sunset_end")}}
    return spec


def spec(plugin: Path) -> dict:
    rec = Records(run_study([DATA / p for p in VANILLA], plugin / "atmosphere-sources.json"), VANILLA)
    sp = build_spec(rec, region_classes())
    (plugin / "atmosphere.json").write_text(json.dumps(sp, indent=0))
    print(f"atmosphere: {len(sp['weathers'])} weathers, {len(sp['imagespaces'])} image spaces, {len(sp['volumetric'])} "
          f"volumetric lightings, {len(sp['regions'])} regions -> {plugin / 'atmosphere.json'}", file=sys.stderr)
    return sp


# ---- measures (the research's numbers and the verifier's rows) ----------------------------------------------------

def mean_colour(pairs) -> list[float]:
    tot = sum(ch for _, ch in pairs) or 1
    return [sum(c[i] * ch for c, ch in pairs) / tot for i in range(3)]


def list_colour(rec: Records, weathers, slot: str, tod: str) -> list[float]:
    """A weather list's chance-weighted colour of one slot at one hour."""
    return mean_colour([(rec.get("WTHR", w)[slot][tod], ch) for w, ch in weathers])


def set_colours(rec: Records, spec_: dict) -> dict:
    """Per (class/band) set: its fair weather's and its list's colours at each hour."""
    res = {}
    for key, lst in spec_["sets"].items():
        fair = rec.get("WTHR", lst[0][0])
        res[key] = {"fair": {s: {t: fair[s][t] for t in TODS} for s in ("SkyUpperColor", "FogNearColor", "FogFarColor", "AmbientColor", "SunlightColor")},
                    "list": {s: {t: list_colour(rec, lst, s, t) for t in TODS} for s in ("FogNearColor", "FogFarColor", "AmbientColor", "SunlightColor")},
                    "day_far": fair["FogDistanceDayFar"]}
    return res


REFERENCES = {  # weather lists measured against: (name, plugin order, [(weather, chance)])
    "old build (ANW_BlackMarshClimate)": (["Skyrim.esm", "Update.esm", "ArgoniaNewWorld.esm"], "climate:ANW_BlackMarshClimate"),
    "BM&V (BlackMarshClimate)": (["Skyrim.esm", "Update.esm", "Black Marsh.esm", "Black Marsh North.esp"], "climate:BlackMarshClimate"),
    "Tropical Skyrim (its BM&V weathers)": (["Skyrim.esm", "Update.esm", "Tropical Skyrim.esp", "Black Marsh.esm", "Black Marsh North.esp"], "climate:BlackMarshClimate"),
    "Tropical Skyrim (its marsh, WeatherTundraMarsh)": (["Skyrim.esm", "Update.esm", "Tropical Skyrim.esp"], "region:WeatherTundraMarsh"),
    "Hjaalmarch (WeatherTundraMarsh)": (["Skyrim.esm", "Update.esm"], "region:WeatherTundraMarsh"),
    "the Rift (WeatherFallForest)": (["Skyrim.esm", "Update.esm"], "region:WeatherFallForest"),
    "the Reach (WeatherReach)": (["Skyrim.esm", "Update.esm"], "region:WeatherReach"),
    "the coast (WeatherCoast)": (["Skyrim.esm", "Update.esm"], "region:WeatherCoast"),
}


def reference_lists(study: dict) -> dict:
    res = {}
    for name, (order, what) in REFERENCES.items():
        if not all(p in study for p in order):
            continue
        rec = Records(study, order)
        kind, edid = what.split(":")
        r = rec.get("CLMT" if kind == "climate" else "REGN", edid)
        lst = r["WeatherTypes"] if kind == "climate" else r["Weather"]["Weathers"]
        pairs = [(w["Weather"], w["Chance"]) for w in lst if ("WTHR", w["Weather"]) in rec.win]
        res[name] = {"rec": rec, "list": pairs}
    return res


def summary(rec: Records, pairs) -> dict:
    out = {}
    for tod in ("Sunrise", "Day"):
        for slot in ("SunlightColor", "FogNearColor", "FogFarColor", "AmbientColor"):
            c = list_colour(rec, pairs, slot, tod)
            out[f"{slot}.{tod}"] = {"rgb": [round(v) for v in c], "warmth": round(warmth(c), 3), "cct": round(cct(c))}
    return out


def study(out: Path, old: Path | None = None) -> dict:
    """The research's measures: the reference weather lists' colours, warmth and colour temperature; Bethesda's
    regional distances (Hjaalmarch against the Rift, the Reach, the coast)."""
    plugins = [DATA / p for p in ("Skyrim.esm", "Update.esm", "Black Marsh.esm", "Tropical Skyrim.esp")]
    bmn = [p for p in (DATA / "Black Marsh North.esp", Path.home() / ".argonia/stack/MO2/mods/bmv/Black Marsh North.esp") if p.exists()]
    plugins += bmn[:1] + ([old] if old and old.exists() else [])
    st = run_study(plugins, out / "study.json")
    refs = reference_lists(st)
    res = {name: {"list": [[r["rec"].get("WTHR", w).get("EditorID"), ch] for w, ch in r["list"]], **summary(r["rec"], r["list"])}
           for name, r in refs.items()}
    regional = {}
    names = [n for n in res if n.startswith(("Hjaalmarch", "the "))]
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            regional[f"{a} / {b}"] = {f"{s}.{t}": round(delta_e(res[a][f"{s}.{t}"]["rgb"], res[b][f"{s}.{t}"]["rgb"]), 1)
                                      for s in ("FogNearColor", "FogFarColor", "AmbientColor", "SunlightColor") for t in ("Sunrise", "Day")}
    m = {"about": "Measured by `python -m tools.newworld.atmosphere study` (Skyrim.esm, Update.esm, Black Marsh.esm, Black Marsh "
              "North.esp, Tropical Skyrim.esp and the build given by --old): each reference weather list's chance-weighted colours at "
              "dawn and noon with warmth ((R-B)/mean) and colour temperature (McCamy), and the dE between Bethesda's regions. "
              "The verifier compares our records with these.", "references": res, "bethesda_regional_delta_e": regional}
    (out / "measure.json").write_text(json.dumps(m, indent=1))
    MEASURED.write_text(json.dumps(m, indent=1) + "\n")
    return m


MEASURE_SLOTS = ("FogNearColor", "FogFarColor", "AmbientColor", "SunlightColor")


def neighbour_distances(cols: dict, pairs) -> dict[str, float]:
    """Per pair of neighbouring regions (identity adjacency): the largest dE between their chance-weighted colours
    (MEASURE_SLOTS at dawn and noon): the measure Bethesda's regions are compared by (study())."""
    return {f"{a} vs {b}": max(delta_e(cols[a]["list"][s][t], cols[b]["list"][s][t]) for s in MEASURE_SLOTS for t in ("Sunrise", "Day"))
            for a, b in pairs if a in cols and b in cols}


def bethesda_floor() -> float:
    """The smallest of Bethesda's regional differences (Hjaalmarch, the Rift, the Reach, the coast), measured."""
    return min(max(v.values()) for v in json.loads(MEASURED.read_text())["bethesda_regional_delta_e"].values())


# ---- read-back -----------------------------------------------------------------------------------------------------

def readback(plugin: Path) -> tuple[dict, Records]:
    st = run_study([DATA / "Skyrim.esm", DATA / "Update.esm", plugin / "ArgoniaNewWorld.esm"], plugin / "atmosphere-readback.json")
    return st, Records(st, ["Skyrim.esm", "Update.esm", "ArgoniaNewWorld.esm"])


def get_path(r: dict, path: str):
    for p in path.split("."):
        r = r[p]
    return r


def rows(plugin: Path) -> list[tuple[str, object, bool, str]]:
    """The verifier's atmosphere rows: (requirement, value, ok, detail). Every value measured on the ESM read back."""
    sp = json.loads((plugin / "atmosphere.json").read_text())
    st, rec = readback(plugin)
    ours = st["ArgoniaNewWorld.esm"]
    out = []
    byid = {(sig, int(r["FormKey"].split(":")[0], 16)): r for sig in ("WTHR", "IMGS", "VOLI", "CLMT") for r in ours[sig]}
    edid_of = {r["FormKey"]: r.get("EditorID") for sig in ("WTHR", "IMGS", "VOLI") for r in ours[sig]}
    miss, wrong = [], []
    for sig, key in (("WTHR", "weathers"), ("IMGS", "imagespaces"), ("VOLI", "volumetric")):
        for e in sp[key]:
            r = byid.get((sig, e["formid"]))
            if r is None or r.get("EditorID") != e["edid"]:
                miss.append(e["edid"])
                continue
            for path, v in e["set"].items():
                got = get_path(r, path)
                if isinstance(v, list) and list(got) != v or not isinstance(v, list) and abs(float(got) - float(v)) > 1e-3 * max(1, abs(float(v))):
                    wrong.append(f"{e['edid']} {path} {got} != {v}")
            for field, links in (("ImageSpaces", e.get("imagespaces")), ("VolumetricLighting", e.get("volumetric"))):
                for tod, want in (links or {}).items():  # each hour's link names our record of that editor id
                    got = edid_of.get(r[field][tod]) if r.get(field) else None
                    if got != want:
                        wrong.append(f"{e['edid']} {field}.{tod} {got} != {want}")
    n = len(sp["weathers"]) + len(sp["imagespaces"]) + len(sp["volumetric"])
    out.append(("our weathers, image spaces and volumetric lightings at their form ids, every field as the spec",
                f"{n - len(miss)}/{n}, {len(wrong)} fields off", not miss and not wrong, "; ".join((miss + wrong)[:4])))
    clim = byid.get(("CLMT", sp["climate"]["formid"]))
    regs = {r["EditorID"]: r for r in ours["REGN"]}
    wn = {r["FormKey"]: r.get("EditorID") for r in ours["WTHR"]}
    bad, weak = [], []
    for rid, lst in sp["regions"].items():
        r = regs.get("ANW_Region_" + rid.replace("-", "_"))
        got = [[wn.get(w["Weather"]), w["Chance"]] for w in (r["Weather"]["Weathers"] if r else [])]
        if got != lst:
            bad.append(rid)
        wd = r["Weather"] if r else {}
        if "Override" not in str(wd.get("Flags", "")) or int(wd.get("Priority") or 0) < REGION_PRIORITY:
            weak.append(f"{rid} ({wd.get('Flags')}, {wd.get('Priority')})")
    out.append(("every region's weather list is its own set (read back)", f"{len(sp['regions']) - len(bad)}/{len(sp['regions'])}",
                not bad, f"e.g. {bad[:3]}"))
    out.append((f"every region's weather data overrides the climate (Override flag, priority at least {REGION_PRIORITY}, as Skyrim's "
                "regional sets: 50 to 55)", f"{len(sp['regions']) - len(weak)}/{len(sp['regions'])}", not weak, f"e.g. {weak[:3]}"))
    ws = ours["WRLD"][0] if ours["WRLD"] else {}
    c = sp["climate"]
    want = {"list": c["weathers"], "times": [c[k] for k in ("sunrise_begin", "sunrise_end", "sunset_begin", "sunset_end")]}
    got = {"list": [[wn.get(w["Weather"]), w["Chance"]] for w in clim["WeatherTypes"]] if clim else None,
           "times": [clim[k] for k in ("SunriseBegin", "SunriseEnd", "SunsetBegin", "SunsetEnd")] if clim else None}
    out.append(("the worldspace's climate is ANW_Climate with the spec's weather list and chances and its four sun times",
                f"{clim and clim['EditorID']} {got['times']}",
                bool(clim) and ws.get("Climate") == clim["FormKey"] and got == want, "" if got == want else f"read {got}, spec {want}"))
    # neighbouring regions are distinct, as much as Bethesda's own regions are from each other
    cols = set_colours(rec, sp)
    keys = sorted(cols)
    pairs = [p.split("|") for p in json.loads((IDENTITY.parent / "adjacency.json").read_text())["pairs"]]
    d = neighbour_distances(cols, pairs)
    worst = min(d.items(), key=lambda kv: kv[1])
    ref = bethesda_floor()
    out.append((f"neighbours are distinct: every two neighbouring regions differ at least as much as Bethesda's closest two regions "
                f"(dE {ref:.1f}; chance-weighted fog near, fog far, ambient, sunlight at dawn and noon)", round(worst[1], 1),
                worst[1] >= ref, f"closest {worst[0]}"))
    # warmth: fixed thresholds, set against Skyrim's base weathers as BM&V's climate lists them (measured.json)
    refs = json.loads(MEASURED.read_text())["references"]
    province = mean_colour([(cols[k]["list"]["SunlightColor"]["Day"], 1) for k in keys])
    fog = mean_colour([(cols[k]["list"]["FogFarColor"]["Day"], 1) for k in keys])
    detail = [f"{name}: sun {refs[name]['SunlightColor.Day']['cct']} K w {refs[name]['SunlightColor.Day']['warmth']:+.2f}, "
              f"fog {refs[name]['FogFarColor.Day']['cct']} K w {refs[name]['FogFarColor.Day']['warmth']:+.2f}"
              for name in ("BM&V (BlackMarshClimate)", "Tropical Skyrim (its BM&V weathers)") if name in refs]
    out.append((f"warm: noon sunlight at most {WARM_SUN_K} K with warmth at least {WARM_SUN_W:+.2f}, far fog warmth at least "
                f"{WARM_FOG_W:+.2f} (chance-weighted, mean of the sets)",
                f"sun {round(cct(province))} K w {warmth(province):+.2f}, fog {round(cct(fog))} K w {warmth(fog):+.2f}",
                cct(province) <= WARM_SUN_K and warmth(province) >= WARM_SUN_W and warmth(fog) >= WARM_FOG_W, "; ".join(detail)))
    return out


# ---- swatches ----------------------------------------------------------------------------------------------------

def swatch(plugin: Path, out: Path) -> Path:
    from PIL import Image, ImageDraw
    sp = json.loads((plugin / "atmosphere.json").read_text())
    rd = plugin / "atmosphere-readback.json"
    st = json.loads(rd.read_text()) if rd.exists() else readback(plugin)[0]
    rec = Records(st, ["Skyrim.esm", "Update.esm", "ArgoniaNewWorld.esm"])
    rows_ = [(k, rec.get("WTHR", lst[0][0])) for k, lst in sp["sets"].items()]
    ref = Path(os.environ.get("NW_ATMOS_STUDY", REPO / "out/atmosphere")) / "study.json"
    if ref.exists():
        s = json.loads(ref.read_text())
        for name, order, w in (("BM&V: SkyrimFog (45 %)", ["Skyrim.esm", "Update.esm"], "SkyrimFog"),
                               ("BM&V: SkyrimClear", ["Skyrim.esm", "Update.esm"], "SkyrimClear"),
                               ("Tropical Skyrim: SkyrimFog", ["Skyrim.esm", "Update.esm", "Tropical Skyrim.esp"], "SkyrimFog")):
            if all(p in s for p in order):
                try:
                    rows_.append((name, Records(s, order).get("WTHR", w)))
                except KeyError:
                    pass
    slots = ("SkyUpperColor", "HorizonColor", "FogNearColor", "FogFarColor", "AmbientColor", "SunlightColor")
    sw, gap, lw, rh = 22, 10, 300, 30
    W = lw + len(TODS) * (len(slots) * sw + gap)
    img = Image.new("RGB", (W, 40 + rh * len(rows_)), (24, 24, 24))
    dr = ImageDraw.Draw(img)
    for ti, tod in enumerate(TODS):
        dr.text((lw + ti * (len(slots) * sw + gap), 6), {"Sunrise": "dawn", "Day": "noon", "Sunset": "dusk", "Night": "night"}[tod], fill=(230, 230, 230))
    dr.text((4, 6), "fair weather: sky, horizon, fog near, fog far, ambient, sun", fill=(200, 200, 200))
    for ri, (name, w) in enumerate(rows_):
        y = 30 + ri * rh
        dr.text((4, y + 8), name, fill=(230, 230, 230))
        for ti, tod in enumerate(TODS):
            for si, s in enumerate(slots):
                x = lw + ti * (len(slots) * sw + gap) + si * sw
                dr.rectangle([x, y, x + sw - 2, y + rh - 4], fill=tuple(int(v) for v in w[s][tod]))
    out.mkdir(parents=True, exist_ok=True)
    p = out / "swatches.png"
    img.save(p)
    return p


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("cmd", choices=("study", "spec", "check", "swatch"))
    ap.add_argument("--plugin", type=Path, default=REPO / "out/newworld/plugin")
    ap.add_argument("--out", type=Path, default=REPO / "out/atmosphere")
    ap.add_argument("--old", type=Path, default=REPO / "out/newworld/plugin/ArgoniaNewWorld.esm", help="the build to compare against")
    a = ap.parse_args(argv)
    if a.cmd == "study":
        a.out.mkdir(parents=True, exist_ok=True)
        print(json.dumps(study(a.out, a.old), indent=1))
    elif a.cmd == "spec":
        spec(a.plugin)
    elif a.cmd == "check":
        bad = 0
        for req, v, ok, d in rows(a.plugin):
            print(f"{'PASS' if ok else 'FAIL'}  {req}: {v}  {d}")
            bad += not ok
        return 1 if bad else 0
    else:
        print(swatch(a.plugin, a.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
