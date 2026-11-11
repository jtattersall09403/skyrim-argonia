"""Community Shaders' half of the new world's air: a low, warm height fog per weather, for the NewWorld profile only.

    python3 -m tools.newworld.atmosphere_cs write [--plugin out/newworld/plugin]   # the row's files into the manifest
    python3 -m tools.newworld.atmosphere_cs check [--plugin out/newworld/plugin]   # the rows below, PASS/FAIL
    python3 -m tools.newworld.atmosphere_cs current [--plugin out/newworld/plugin] # exit 1 when `write` would change the row

The fog is Community Shaders' Exponential Height Fog (the add-on of the same build as the Community Shaders the stack
lays, mods/dependencies.json row `cs-height-fog`, profile newworld). Each of our weathers gets a per-weather settings
file, `SKSE/Plugins/CommunityShaders/Weathers/0x<local form id>~ArgoniaNewWorld.esm.json` (Community Shaders 1.9.1:
WeatherManager reads `featureSettings.<feature>` from the file whose stem is Util::GetFormFileKey of the weather; a
feature block is used only with `"__enabled": true`; the keys are the names the feature registers, e.g. "Fog Density").

Per weather (atmosphere.py's spec, <plugin>/atmosphere.json):
- the vanilla fog is replaced by the height fog (`disableVanillaFog`): with the vanilla fog kept, Community Shaders'
  composite (ISSAOComposite.hlsl) paints every sky pixel with the weather's far fog colour at its fog max, the flat
  veil with no clouds; with it replaced, the sky takes only the height fog, which thins upward;
- density: 90 % fogged at the weather's own day fog far (the record's visibility for its class and band), times the
  class's strength (thick over the peat swamp and the green marsh, thin on the highland, the coasts and the islands)
  and the kind's (mist and steam thick, fair thinner, rain and storm left to their rain);
- the layer's floor (`Fog Height`) is the class's wet ground, measured on the terrain (75th percentile of the surface,
  water at 0, over its still and flowing water and its marsh habitats); a camera at or below the floor sees the full
  density, and above it the density halves every 500 units (falloff 2.0, the feature's documented maximum): it lies in the hollows and over the water and
  thins up the slopes;
- colour: the weather's own fog colour by the hour (`Original Fog Color Amount` 1), no added colour and no sky
  cubemap (their alphas 0), the sun's own colour scattered forward (anisotropy 0.6, humid haze), so it never greys;
- volumetric (the froxel fog, lit and shadowed: shafts through canopy) in the sunlit kinds (fair, cloudy, steam),
  out to 20,000 units, its albedo (stated in every weather) the weather's day fog colour.
The feature has no time-of-day input: the per-weather values hold at every hour.

Global (overrides, the NewWorld profile only, the same paths as the community-shaders row's so they win there):
the height fog on; a weather with no file (another worldspace's) takes global_fog(), vanilla clear weather's
visibility at sea level thinning upward; Community Shaders' volumetric lighting on outdoors (it sets the engine's
bEnableVolumetricLighting, so our weathers' volumetric lighting records draw). Indoors the feature is off
(SceneSettings/InteriorOnly), so each interior keeps its own vanilla cell fog.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
MANIFEST = REPO / "mods/dependencies.json"
ROW = "cs-height-fog"
ESM = "ArgoniaNewWorld.esm"
FEATURE = "ExponentialHeightFog"
CS = "SKSE/Plugins/CommunityShaders"
ADDON_INI = "Shaders/Features/ExponentialHeightFog.ini"
ADDON_VERSION = "1-3-2"   # CS 1.9.1's FEATURE_MINIMAL_VERSIONS entry (features/Exponential Height Fog/.../ExponentialHeightFog.ini)
FALLOFF = 2.0             # the feature's documented maximum: the thinnest layer it draws, halving every 500 units
OPACITY_AT_FAR = 0.9      # fogged at the weather's own day fog far
VOLUMETRIC_DISTANCE = 20000.0
GLOBAL_FAR = 80000.0      # vanilla SkyrimClear's day fog far (Update.esm, the load order's winner)
# Indoors (Community Shaders' SceneSettings, applied when the sky mode is not full): the feature off, so the shaders
# take their vanilla fog branch and each interior keeps its own cell fog. One setting a file, `_feature` naming it.
INTERIOR = "SKSE/Plugins/CommunityShaders/SceneSettings/InteriorOnly/Argonia_ExponentialHeightFog.json"
INTERIOR_OFF = {"_feature": "ExponentialHeightFog", "enabled": 0}
LOADED_LOG = "Finished loading per-weather settings. Total weathers: {}"   # WeatherManager.cpp, CommunityShaders.log
ANISOTROPY = 0.6
WET_PERCENTILE = 75
# The class's strength: thick in the peat swamp and the green marsh, where the owner asked for more; thin where the
# research has cleaner air (section 1.6, 1.7: the highland's crisp light above its valley fog, the islands' salt air)
CLASS_STRENGTH = {"blackwater-swamp": 1.4, "green-marsh": 1.4, "river-corridor": 1.2, "rainforest": 1.1,
                  "coast-south": 1.0, "coast-east": 0.7, "coast-west": 0.7, "island": 0.5, "highland": 0.5}
# The kind's: density factor, sunlight scattered in the fog, volumetric (sunlit kinds)
KIND = {"fair": (0.7, 1.0, True), "cloudy": (0.9, 0.8, True), "mist": (1.0, 0.4, False),
        "steam": (1.0, 1.0, True), "rain": (0.5, 0.2, False), "storm": (0.5, 0.2, False)}
# The ranges the feature registers (CS 1.9.1 ExponentialHeightFog.cpp RegisterWeatherVariables): name -> (min, max)
RANGES = {"Start Distance": (0.0, 100000.0), "Fog Height": (-22000.0, 22000.0), "Fog Height Falloff": (0.001, 2.0),
          "Original Fog Color Amount": (0.0, 1.0), "Fog Density": (0.0, 1.0),
          "Directional Inscattering Multiplier": (0.0, 10.0), "Sunlight Attenuation Amount": (0.0, 1.0),
          "Directional Inscattering Anisotropy": (-0.99, 0.99), "Volumetric View Distance": (1000.0, 200000.0),
          "Volumetric Start Distance": (0.0, 200000.0), "Volumetric Near Fade In Distance": (0.0, 20000.0),
          "Volumetric Extinction Scale": (0.0, 10.0), "Volumetric Scattering Distribution": (-0.9, 0.9),
          "Volumetric Directional Scattering Intensity": (0.0, 10.0), "Volumetric Sky Lighting Intensity": (0.0, 10.0),
          "Volumetric Local Light Scattering Intensity": (0.0, 100.0)}
COLOURS = ("Fog Inscattering Color", "Inscattering Cubemap Tint", "Volumetric Albedo", "Volumetric Emissive")
FLAGS = ("respectVanillaFogFade", "disableVanillaFog", "volumetricFogEnabled")
# The sky through the fog, camera at the layer's floor (the worst case): least transmittance allowed
SKY_MIN = {"zenith": 0.7, "fair_15deg": 0.8}


def weather_file(formid: int) -> str:
    """The per-weather file of a weather of ours: Util::GetFormFileKey is 0x<local form id, hex upper, no padding>~<the
    plugin that defines it>."""
    return f"{CS}/Weathers/0x{formid & 0xFFFFFF:X}~{ESM}.json"


def floors(plugin: Path, landcover: Path | None = None) -> dict:
    """Per atmosphere class: the fog's floor, the WET_PERCENTILE of the surface (ground, water at the grid's level) over
    its still and flowing water and its marsh habitats, rounded to 10 units; and the terrain build it was read on."""
    import numpy as np

    from tools.newworld import atmosphere
    from tools.newworld.world import mist
    lc = landcover or mist.LC
    man = json.loads((plugin / "land/manifest.json").read_text())
    leg = json.loads((lc / "legend.json").read_text())
    if leg["build_id"] != man["build_id"]:
        raise RuntimeError("landcover is another terrain build: rerun landcover")
    water = man["grid"].get("water", 0.0)
    hm = np.load(man["heightmap"], mmap_mode="r")
    reg, hab = np.load(lc / "region.npy", mmap_mode="r"), np.load(lc / "habitat.npy", mmap_mode="r")
    kind, flags = np.load(lc / "kind.npy", mmap_mode="r"), np.load(lc / "flags.npy", mmap_mode="r")
    habs, kinds, regs = leg["habitats"], leg["kinds"], leg["regions"]
    wet_h = [habs.index(h) for h in ("reed_marsh", "cypress_swamp", "drowned_forest", "open_still_water",
                                     "mangrove_fringe", "swamp_hummock") if h in habs]
    inland = [kinds.index(k) for k in (*mist.STILL, *mist.FLOWING) if k in kinds]
    rc = atmosphere.region_classes()
    out = {}
    for y0 in range(0, reg.shape[0], 512):   # in bands, to keep the memory small
        sl = slice(y0, y0 + 512)
        R, HB, K = np.asarray(reg[sl]), np.asarray(hab[sl]), np.asarray(kind[sl])
        FL = np.asarray(flags[sl])
        W, margin = (FL & 1) == 1, (FL & 4) == 4
        H = np.maximum(np.asarray(hm[sl, : reg.shape[1]], dtype=np.float32), water)
        wet = ~margin & ((W & np.isin(K, inland)) | (~W & np.isin(HB, wet_h)))
        for cid in sorted({c for c, _ in rc.values()}):
            ids = [regs.index(r) for r, (c, _) in rc.items() if c == cid and r in regs]
            out.setdefault(cid, []).append(H[wet & np.isin(R, ids)])
    res = {cid: int(round(float(np.percentile(np.concatenate(v), WET_PERCENTILE)) / 10) * 10) for cid, v in out.items()
           if sum(a.size for a in v)}
    return {"build_id": man["build_id"], "floors": res}


def albedo(rgb) -> list[float]:
    m = max(rgb) or 1
    return [round(c / m, 3) for c in rgb] + [1.0]


def weather_settings(w: dict, floor: float) -> dict:
    """One weather's Exponential Height Fog block."""
    cm = CLASS_STRENGTH[w["class"]]
    km, inscatter, vol = KIND[w["kind"]]
    far = w["set"]["FogDistanceDayFar"]
    # the shader's level ray: 2^(-d0 L ln 2) (its line integral's limit, ExponentialHeightFog.hlsli), d0 = density / 1000
    density = min(1.0, math.log2(1 / (1 - OPACITY_AT_FAR)) / math.log(2) * 1000 / far * cm * km)
    s = {"__enabled": True,
         "Fog Density": round(density, 4), "Fog Height": float(floor), "Fog Height Falloff": FALLOFF,
         "Directional Inscattering Multiplier": inscatter, "volumetricFogEnabled": vol,
         # the veil guard, also global: stated per weather so no other override can bring the vanilla fog back
         "disableVanillaFog": True, "Original Fog Color Amount": 1.0,
         "Fog Inscattering Color": [0.0, 0.0, 0.0, 0.0], "Inscattering Cubemap Tint": [1.0, 1.0, 1.0, 0.0],
         # in every weather, sunlit or not: a key a weather lacks blends to the global value through a transition
         "Volumetric Albedo": albedo(w["set"]["FogNearColor.Day"])}
    return s


def sky_transmittance(s: dict, elevation_deg: float, above_floor: float = 0.0) -> float:
    """The share of the sky's own colour left at an elevation, through the fog: the shader's line integral for a ray
    to the far plane, d0 2^(-f h) / (f sin e), taken as a power of 2 (d0 = density / 1000, f = falloff / 1000)."""
    d0, f = s["Fog Density"] * 1e-3, s["Fog Height Falloff"] * 1e-3
    return 2 ** (-(d0 * 2 ** (-f * max(above_floor, 0.0))) / (f * math.sin(math.radians(elevation_deg))))


def global_fog() -> dict:
    """The fog of a weather with no file of ours (other worldspaces, any weather not ours): the nearest the feature's
    formula comes to a plain distance fog without fogging the sky. A level-uniform fog (falloff toward 0) fogs every sky
    pixel, as the sky ray's integral d / (f sin e) grows without bound; so the density matches vanilla SkyrimClear's
    visibility (90 % at its 80,000-unit day fog far) along the floor at sea level (height 0), and the falloff is the
    least, in steps of 0.05, that leaves 0.8 of the sky at 15 degrees from that floor."""
    density = round(math.log2(1 / (1 - OPACITY_AT_FAR)) / math.log(2) * 1000 / GLOBAL_FAR, 4)
    falloff = next(x / 100 for x in range(5, 201, 5)
                   if sky_transmittance({"Fog Density": density, "Fog Height Falloff": x / 100}, 15) >= SKY_MIN["fair_15deg"])
    return {"Fog Density": density, "Fog Height Falloff": falloff, "Fog Height": 0.0}


def global_files() -> list[dict]:
    meta = {"modName": "Argonia (new world)", "version": "walk5", "enabled": True}
    g = global_fog()
    ehf = {"enabled": 1, "useDynamicCubemaps": 0, "disableVanillaFog": 1, "respectVanillaFogFade": 1,
           "originalFogColorAmount": 1.0, "fogInscatteringColor": [0.0, 0.0, 0.0, 0.0],
           "inscatteringTint": [1.0, 1.0, 1.0, 0.0], "fogHeight": g["Fog Height"],
           "fogHeightFalloff": g["Fog Height Falloff"], "fogDensity": g["Fog Density"], "startDistance": 0.0, "directionalInscatteringAnisotropy": ANISOTROPY, "directionalInscatteringMultiplier": 1.0,
           "sunlightAttenuationAmount": 1.0, "volumetricFogEnabled": 0, "volumetricFogDistance": VOLUMETRIC_DISTANCE,
           "volumetricFogExtinctionScale": 1.0, "volumetricDirectionalScatteringIntensity": 1.0,
           "volumetricSkyLightingIntensity": 0.5,
           "_metadata": {**meta, "description": "Exponential Height Fog on, replacing the vanilla fog (kept, it paints the "
                         "sky pixels with the far fog colour: a flat veil). Our weathers set their own low fog per "
                         "weather (Weathers/); any other weather takes a fog as thick as vanilla's clear weather at sea "
                         "level, thinning upward. Off indoors (SceneSettings/InteriorOnly). No sky cubemap and no added "
                         "colour: the fog takes the weather's own fog colour."}}
    vl = {"ExteriorEnabled": True, "ExteriorQuality": 1, "InteriorEnabled": True, "InteriorQuality": 1,
          "_metadata": {**meta, "description": "Volumetric lighting outdoors: it sets the engine's "
                        "bEnableVolumetricLighting, so our weathers' volumetric lighting records draw shafts through "
                        "the canopy and the mist. Medium quality."}}
    return [{"path": f"{CS}/Overrides/Argonia_ExponentialHeightFog.json", "text": json.dumps(ehf, indent=1) + "\n"},
            {"path": f"{CS}/Overrides/Argonia_VolumetricLighting.json", "text": json.dumps(vl, indent=1) + "\n"},
            {"path": INTERIOR, "text": json.dumps(INTERIOR_OFF) + "\n"}]


def generate(spec: dict, fl: dict) -> list[dict]:
    """The row's files, in path order: the two global overrides, then one file per weather of the spec."""
    files = global_files()
    for w in spec["weathers"]:
        doc = {"_argonia": {"weather": w["edid"], "class": w["class"], "band": w["band"], "kind": w["kind"]},
               "featureSettings": {FEATURE: weather_settings(w, fl["floors"][w["class"]])}}
        files.append({"path": weather_file(w["formid"]), "text": json.dumps(doc) + "\n"})   # one line: the manifest stays small
    return sorted(files, key=lambda f: f["path"])


def manifest_row(doc: dict) -> dict:
    hit = [m for m in doc["mods"] if m["id"] == ROW]
    if len(hit) != 1:
        raise SystemExit(f"mods/dependencies.json: {len(hit)} rows {ROW!r}")
    return hit[0]


def write(plugin: Path) -> int:
    spec = json.loads((plugin / "atmosphere.json").read_text())
    fl = floors(plugin)
    doc = json.loads(MANIFEST.read_text())
    row = manifest_row(doc)
    files = generate(spec, fl)
    changed = row.get("files") != files
    row["files"] = files
    if changed:
        MANIFEST.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
    print(f"atmosphere_cs: {len(parse_weathers({f['path']: f['text'] for f in files}))} weather files, floors {fl['floors']} (terrain {fl['build_id']}); "
          f"{'written' if changed else 'unchanged'}", file=sys.stderr)
    return 0


# ---- the read-back --------------------------------------------------------------------------------------------------

def in_range(name: str, v) -> bool:
    if name in RANGES:
        lo, hi = RANGES[name]
        return isinstance(v, (int, float)) and not isinstance(v, bool) and lo <= v <= hi
    if name in COLOURS:
        return isinstance(v, list) and len(v) == 4 and all(isinstance(x, (int, float)) and x >= 0 for x in v)
    return name in FLAGS + ("__enabled",) and isinstance(v, bool)


def parse_weathers(files: dict[str, str]) -> dict[str, dict]:
    """{path: the whole file} of the per-weather files among `files` (path -> text)."""
    return {p: json.loads(t) for p, t in files.items() if p.lower().startswith(f"{CS}/Weathers/".lower())}


def esm_weathers(st: dict) -> dict[str, str]:
    """{the per-weather file's path, lower case: the weather's editor id} for each of our weathers in the ESM read back
    (`atmosphere.readback`): the editor id and local form id as the game loads them."""
    return {weather_file(int(r["FormKey"].split(":")[0], 16) & 0xFFFFFF).lower(): r["EditorID"]
            for r in st[ESM]["WTHR"] if (r.get("EditorID") or "").startswith("ANW_W_")}


def file_rows(want: dict[str, str], files: dict[str, str]) -> list[tuple[str, object, bool, str]]:
    """Rows over the row's files (path -> text) against the weathers of the ESM (path, lower case -> editor id): one
    file per weather, naming it, parsed back, in the feature's ranges; the veil guard; the interior switch; the sky."""
    rows = []
    docs = {p.lower(): d for p, d in parse_weathers(files).items()}
    got = {p: d["featureSettings"][FEATURE] for p, d in docs.items()}
    meta = {p: d.get("_argonia", {}) for p, d in docs.items()}
    miss, extra = sorted(set(want) - set(got)), sorted(set(got) - set(want))
    rows.append(("one height-fog file per weather of the ESM, at its form id, parsed back", f"{len(set(want) & set(got))}/{len(want)}",
                 not miss and not extra and bool(want), (f"missing {miss[:2]} " if miss else "") + (f"extra {extra[:2]}" if extra else "")))
    named = [p for p in set(want) & set(got) if meta[p].get("weather") != want[p]]
    rows.append(("each file names the weather the ESM has at that form id", len(named), not named, ", ".join(named[:2])))
    bad = [(p, k, v) for p, s in got.items() for k, v in s.items() if not in_range(k, v)]
    rows.append(("every per-weather value inside the feature's registered range", len(bad), not bad,
                 "; ".join(f"{p.rsplit('/', 1)[-1]} {k}={v}" for p, k, v in bad[:3])))
    off = [p for p, s in got.items() if s.get("__enabled") is not True]
    rows.append(("every per-weather block enabled (__enabled)", len(off), not off, ", ".join(off[:3])))
    veil = [p for p, s in got.items() if s.get("disableVanillaFog") is not True or s.get("Original Fog Color Amount") != 1.0
            or s.get("Fog Inscattering Color", [0, 0, 0, 0])[3] != 0 or s.get("Inscattering Cubemap Tint", [0, 0, 0, 0])[3] != 0]
    rows.append(("veil guard: vanilla fog replaced, colour the weather's own (no added colour, no sky cubemap)", len(veil),
                 not veil, ", ".join(veil[:3])))
    noalb = [p for p, s in got.items() if "Volumetric Albedo" not in s]
    rows.append(("every weather states its volumetric albedo (no blend to white in a transition)", len(noalb), not noalb,
                 ", ".join(noalb[:2])))
    inner = json.loads(files.get(INTERIOR, "{}"))
    keys = [k for k in inner if not k.startswith("_")]
    rows.append(("indoors the height fog is off (SceneSettings/InteriorOnly: one setting, enabled 0)", inner or "missing",
                 inner.get("_feature") == FEATURE and keys == ["enabled"] and inner["enabled"] == 0, ""))
    zen = {p: sky_transmittance(s, 90) for p, s in got.items()}
    fair = {p: sky_transmittance(s, 15) for p, s in got.items() if meta[p].get("kind") in ("fair", "cloudy")}
    zmin, fmin = min(zen.values(), default=0), min(fair.values(), default=0)
    rows.append((f"sky at the zenith through the fog, every weather, >= {SKY_MIN['zenith']}", round(zmin, 3),
                 zmin >= SKY_MIN["zenith"], min(zen, key=zen.get, default="").rsplit("/", 1)[-1]))
    rows.append((f"sky at 15 deg in fair and cloudy weather, >= {SKY_MIN['fair_15deg']}", round(fmin, 3),
                 fmin >= SKY_MIN["fair_15deg"], min(fair, key=fair.get, default="").rsplit("/", 1)[-1]))
    by, kd = {}, {}
    for p, s in got.items():
        by.setdefault(meta[p].get("class"), []).append(s["Fog Density"])
        if meta[p].get("class") == "green-marsh":
            kd.setdefault(meta[p].get("kind"), []).append(s["Fog Density"])
    mean = {c: sum(v) / len(v) for c, v in by.items()}
    thick = min((mean[c] for c in ("blackwater-swamp", "green-marsh") if c in mean), default=0)
    thin = max((mean[c] for c in ("highland", "island", "coast-east", "coast-west") if c in mean), default=1)
    rows.append(("peat swamp and green marsh fog thicker than highland, coasts and islands (mean density)",
                 f"{thick:.3f} > {thin:.3f}", thick > thin, ""))
    kmean = {k: sum(v) / len(v) for k, v in kd.items()}
    ok = bool(kmean) and min(kmean.get("mist", 0), kmean.get("steam", 0)) > max(kmean.get("fair", 1), kmean.get("cloudy", 1))
    rows.append(("mist and steam weathers thicker than fair and cloudy (green marsh)",
                 {k: round(v, 3) for k, v in sorted(kmean.items())}, ok, ""))
    return rows


def sha_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def stack_rows(stack: Path, want: dict[str, str], files: dict[str, str]) -> list[tuple[str, object, bool, str]]:
    """Rows over the staged stack: the add-on and the files in the NewWorld profile only, the laid bytes the row's,
    the overrides winning there."""
    rows = []
    rec = {p: stack / f for p, f in (("NewWorld", "installed-NewWorld.json"), ("Argonia", "installed.json"))}
    if not all(f.exists() for f in rec.values()):
        return [("height fog staged (installed records)", "missing", False, f"no {', '.join(str(f) for f in rec.values() if not f.exists())}: stack.py stage")]
    nw, ar = (json.loads(rec[p].read_text())["files"] for p in ("NewWorld", "Argonia"))

    def key(p: str) -> str:
        return p.replace("/", "\\").lower()
    ini = key(ADDON_INI)
    rows.append(("height-fog add-on laid in NewWorld, by its row", nw.get(ini, ["-"])[0], nw.get(ini, ["-"])[0] == ROW, ""))
    ours_ar = sorted(k for k, v in ar.items() if v[0] == ROW)
    rows.append(("Argonia profile lays none of the height-fog row's files", len(ours_ar), not ours_ar, ", ".join(ours_ar[:3])))
    laid = {k for k, v in nw.items() if k.startswith(key(f"{CS}/Weathers/")) and v[0] == ROW}
    wk = {key(p) for p in want}
    rows.append(("a per-weather file laid in NewWorld for every weather of the ESM, no other", f"{len(wk & laid)}/{len(wk)}",
                 laid == wk and bool(wk), f"{len(wk - laid)} missing, {len(laid - wk)} extra" if laid != wk else ""))
    stale = []
    for p, t in files.items():
        disk = stack / "MO2/mods" / ROW / p
        h = sha_text(t)
        if nw.get(key(p), ["-", ""])[1] != h or not disk.exists() or hashlib.sha256(disk.read_bytes()).hexdigest() != h:
            stale.append(p)
    rows.append(("every file of the row laid with the generated bytes (record and staged file sha256)",
                 f"{len(files) - len(stale)}/{len(files)}", not stale and bool(files), ", ".join(stale[:2])))
    for name in ("Overrides/Argonia_ExponentialHeightFog.json", "Overrides/Argonia_VolumetricLighting.json"):
        k = key(f"{CS}/{name}")
        rows.append((f"{name}: NewWorld's from the height-fog row, Argonia's from community-shaders",
                     f"{nw.get(k, ['-'])[0]} / {ar.get(k, ['-'])[0]}",
                     nw.get(k, ["-"])[0] == ROW and ar.get(k, ["-"])[0] == "community-shaders", ""))
    rows.append(("the interior switch laid in NewWorld by the height-fog row", nw.get(key(INTERIOR), ["-"])[0],
                 nw.get(key(INTERIOR), ["-"])[0] == ROW, ""))
    staged = stack / "MO2/mods" / ROW / ADDON_INI
    ver = ""
    if staged.exists():
        for ln in staged.read_text(errors="replace").splitlines():
            if ln.strip().lower().startswith("version"):
                ver = ln.split("=", 1)[1].strip()
    rows.append((f"add-on version is the one Community Shaders 1.9.1 requires ({ADDON_VERSION})", ver or "-", ver == ADDON_VERSION, str(staged) if not ver else ""))
    return rows


def readback(plugin: Path) -> dict:
    """The ESM's atmosphere records read back (atmosphere.readback), reusing its file when newer than the ESM."""
    from tools.newworld import atmosphere
    f, esm = plugin / "atmosphere-readback.json", plugin / ESM
    if f.exists() and esm.exists() and f.stat().st_mtime > esm.stat().st_mtime:
        return json.loads(f.read_text())
    return atmosphere.readback(plugin)[0]


def rows(plugin: Path, stack: Path | None = None) -> list[tuple[str, object, bool, str]]:
    """The verifier's rows: the weathers the built ESM holds, the manifest row's files read back against them, the
    row as the generator's output, the stack."""
    spec = json.loads((plugin / "atmosphere.json").read_text())
    row = manifest_row(json.loads(MANIFEST.read_text()))
    files = {f["path"]: f["text"] for f in row.get("files", [])}
    try:
        want = esm_weathers(readback(plugin))
    except Exception as e:  # noqa: BLE001 - a row that cannot be measured is a FAIL naming why
        return [("our weathers read back from the ESM", "unmeasured", False, f"{type(e).__name__}: {str(e)[:200]}")]
    out = file_rows(want, files)
    try:
        fresh = generate(spec, floors(plugin))
        same = fresh == row.get("files")
        out.append(("the manifest row's files are the generator's for this spec and terrain", same, same,
                    "" if same else "run python3 -m tools.newworld.atmosphere_cs write, then stack.py stage"))
    except (OSError, RuntimeError, KeyError) as e:
        out.append(("the manifest row's files are the generator's for this spec and terrain", "unmeasured", False, str(e)[:200]))
    if stack is not None:
        out += stack_rows(stack, want, files)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("cmd", choices=("write", "check", "current"))
    ap.add_argument("--plugin", type=Path, default=REPO / "out/newworld/plugin")
    ap.add_argument("--stack", type=Path, default=Path.home() / ".argonia/stack")
    a = ap.parse_args(argv)
    if a.cmd == "write":
        return write(a.plugin)
    if a.cmd == "current":
        same = manifest_row(json.loads(MANIFEST.read_text())).get("files") == generate(
            json.loads((a.plugin / "atmosphere.json").read_text()), floors(a.plugin))
        print("atmosphere_cs: the row's files are " + ("the generator's for this spec and terrain" if same else "not the generator's: run write, then stack.py stage"))
        return 0 if same else 1
    bad = 0
    for req, v, ok, det in rows(a.plugin, a.stack):
        print(f"{'PASS' if ok else 'FAIL'}  {req}: {v}" + (f"  ({det})" if det else ""))
        bad += not ok
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
