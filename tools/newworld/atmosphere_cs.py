"""Community Shaders' half of the new world's air: a low, warm height fog per weather, for the NewWorld profile only.

    python3 -m tools.newworld.atmosphere_cs write [--plugin out/newworld/plugin]   # the row's files into the manifest
    python3 -m tools.newworld.atmosphere_cs check [--plugin out/newworld/plugin]   # the rows below, PASS/FAIL

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
  water at 0, over its still and flowing water and its marsh habitats); below the floor the fog is full, above it
  halves every 500 units (falloff 2.0, the feature's documented maximum): it lies in the hollows and over the water and
  thins up the slopes;
- colour: the weather's own fog colour by the hour (`Original Fog Color Amount` 1), no added colour and no sky
  cubemap (their alphas 0), the sun's own colour scattered forward (anisotropy 0.6, humid haze), so it never greys;
- volumetric (the froxel fog, lit and shadowed: shafts through canopy) in the sunlit kinds (fair, cloudy, steam),
  out to 20,000 units, its albedo the weather's day fog colour.
The feature has no time-of-day input: the per-weather values hold at every hour.

Global (overrides, the NewWorld profile only, the same paths as the community-shaders row's so they win there):
the height fog on with the feature's shipped values for any other weather; Community Shaders' volumetric lighting on
outdoors (it sets the engine's bEnableVolumetricLighting, so our weathers' volumetric lighting records draw).
"""
from __future__ import annotations

import argparse
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
EYE = 120.0               # units, the eye over the ground (1.7 m)
VOLUMETRIC_DISTANCE = 20000.0
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
         "Fog Inscattering Color": [0.0, 0.0, 0.0, 0.0], "Inscattering Cubemap Tint": [1.0, 1.0, 1.0, 0.0]}
    if vol:
        s["Volumetric Albedo"] = albedo(w["set"]["FogNearColor.Day"])
    return s


def sky_transmittance(s: dict, elevation_deg: float, above_floor: float = 0.0) -> float:
    """The share of the sky's own colour left at an elevation, through the fog: the shader's line integral for a ray
    to the far plane, d0 2^(-f h) / (f sin e), taken as a power of 2 (d0 = density / 1000, f = falloff / 1000)."""
    d0, f = s["Fog Density"] * 1e-3, s["Fog Height Falloff"] * 1e-3
    return 2 ** (-(d0 * 2 ** (-f * max(above_floor, 0.0))) / (f * math.sin(math.radians(elevation_deg))))


def global_files() -> list[dict]:
    meta = {"modName": "Argonia (new world)", "version": "walk5", "enabled": True}
    ehf = {"enabled": 1, "useDynamicCubemaps": 0, "disableVanillaFog": 1, "respectVanillaFogFade": 1,
           "originalFogColorAmount": 1.0, "fogInscatteringColor": [0.0, 0.0, 0.0, 0.0],
           "inscatteringTint": [1.0, 1.0, 1.0, 0.0], "fogHeight": 0.0, "fogHeightFalloff": 0.2, "fogDensity": 0.005,
           "startDistance": 0.0, "directionalInscatteringAnisotropy": ANISOTROPY, "directionalInscatteringMultiplier": 1.0,
           "sunlightAttenuationAmount": 1.0, "volumetricFogEnabled": 0, "volumetricFogDistance": VOLUMETRIC_DISTANCE,
           "volumetricFogExtinctionScale": 1.0, "volumetricDirectionalScatteringIntensity": 1.0,
           "volumetricSkyLightingIntensity": 0.5,
           "_metadata": {**meta, "description": "Exponential Height Fog on, replacing the vanilla fog (kept, it paints the "
                         "sky pixels with the far fog colour: a flat veil). Our weathers set their own low fog per "
                         "weather (Weathers/); any other weather takes the feature's shipped values. No sky cubemap and "
                         "no added colour: the fog takes the weather's own fog colour."}}
    vl = {"ExteriorEnabled": True, "ExteriorQuality": 1, "InteriorEnabled": True, "InteriorQuality": 1,
          "_metadata": {**meta, "description": "Volumetric lighting outdoors: it sets the engine's "
                        "bEnableVolumetricLighting, so our weathers' volumetric lighting records draw shafts through "
                        "the canopy and the mist. Medium quality."}}
    return [{"path": f"{CS}/Overrides/Argonia_ExponentialHeightFog.json", "text": json.dumps(ehf, indent=1) + "\n"},
            {"path": f"{CS}/Overrides/Argonia_VolumetricLighting.json", "text": json.dumps(vl, indent=1) + "\n"}]


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
    print(f"atmosphere_cs: {len(files) - 2} weather files, floors {fl['floors']} (terrain {fl['build_id']}); "
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
    """{path: the feature block} of the per-weather files among `files` (path -> text)."""
    out = {}
    for p, t in files.items():
        if p.lower().startswith(f"{CS}/Weathers/".lower()):
            out[p] = json.loads(t)["featureSettings"][FEATURE]
    return out


def file_rows(spec: dict, files: dict[str, str]) -> list[tuple[str, object, bool, str]]:
    """Rows over the row's files (path -> text): one per weather, parsed back, in the feature's ranges, the veil guard,
    the sky through the fog."""
    rows = []
    want = {weather_file(w["formid"]).lower(): w for w in spec["weathers"]}
    got = {p.lower(): s for p, s in parse_weathers(files).items()}
    miss, extra = sorted(set(want) - set(got)), sorted(set(got) - set(want))
    rows.append(("one height-fog file per weather of ours, parsed back", f"{len(set(want) & set(got))}/{len(want)}",
                 not miss and not extra and bool(want), (f"missing {miss[:2]} " if miss else "") + (f"extra {extra[:2]}" if extra else "")))
    bad = [(p, k, v) for p, s in got.items() for k, v in s.items() if not in_range(k, v)]
    rows.append(("every per-weather value inside the feature's registered range", len(bad), not bad,
                 "; ".join(f"{p.rsplit('/', 1)[-1]} {k}={v}" for p, k, v in bad[:3])))
    off = [p for p, s in got.items() if s.get("__enabled") is not True]
    rows.append(("every per-weather block enabled (__enabled)", len(off), not off, ", ".join(off[:3])))
    veil = [p for p, s in got.items() if s.get("disableVanillaFog") is not True or s.get("Original Fog Color Amount") != 1.0
            or s.get("Fog Inscattering Color", [0, 0, 0, 0])[3] != 0 or s.get("Inscattering Cubemap Tint", [0, 0, 0, 0])[3] != 0]
    rows.append(("veil guard: vanilla fog replaced, colour the weather's own (no added colour, no sky cubemap)", len(veil),
                 not veil, ", ".join(veil[:3])))
    zen = {p: sky_transmittance(s, 90) for p, s in got.items()}
    fair = {p: sky_transmittance(s, 15) for p, s in got.items() if want.get(p, {}).get("kind") in ("fair", "cloudy")}
    zmin, fmin = min(zen.values(), default=0), min(fair.values(), default=0)
    rows.append((f"sky at the zenith through the fog, every weather, >= {SKY_MIN['zenith']}", round(zmin, 3),
                 zmin >= SKY_MIN["zenith"], min(zen, key=zen.get, default="").rsplit("/", 1)[-1]))
    rows.append((f"sky at 15 deg in fair and cloudy weather, >= {SKY_MIN['fair_15deg']}", round(fmin, 3),
                 fmin >= SKY_MIN["fair_15deg"], min(fair, key=fair.get, default="").rsplit("/", 1)[-1]))
    by = {}
    for p, s in got.items():
        w = want.get(p)
        if w:
            by.setdefault(w["class"], []).append(s["Fog Density"])
    mean = {c: sum(v) / len(v) for c, v in by.items()}
    thick = min((mean[c] for c in ("blackwater-swamp", "green-marsh") if c in mean), default=0)
    thin = max((mean[c] for c in ("highland", "island", "coast-east", "coast-west") if c in mean), default=1)
    rows.append(("peat swamp and green marsh fog thicker than highland, coasts and islands (mean density)",
                 f"{thick:.3f} > {thin:.3f}", thick > thin, ""))
    kd = {}
    for p, s in got.items():
        w = want.get(p)
        if w and w["class"] == "green-marsh":
            kd.setdefault(w["kind"], []).append(s["Fog Density"])
    kmean = {k: sum(v) / len(v) for k, v in kd.items()}
    ok = bool(kmean) and min(kmean.get("mist", 0), kmean.get("steam", 0)) > max(kmean.get("fair", 1), kmean.get("cloudy", 1))
    rows.append(("mist and steam weathers thicker than fair and cloudy (green marsh)",
                 {k: round(v, 3) for k, v in sorted(kmean.items())}, ok, ""))
    return rows


def stack_rows(stack: Path, spec: dict) -> list[tuple[str, object, bool, str]]:
    """Rows over the staged stack: the add-on and the files in the NewWorld profile only; the overrides win there."""
    rows = []
    rec = {p: stack / f for p, f in (("NewWorld", "installed-NewWorld.json"), ("Argonia", "installed.json"))}
    if not all(f.exists() for f in rec.values()):
        return [("height fog staged (installed records)", "missing", False, f"no {', '.join(str(f) for f in rec.values() if not f.exists())}: stack.py stage")]
    nw, ar = (json.loads(rec[p].read_text())["files"] for p in ("NewWorld", "Argonia"))
    ini = ADDON_INI.replace("/", "\\").lower()
    rows.append(("height-fog add-on laid in NewWorld, by its row", nw.get(ini, ["-"])[0], nw.get(ini, ["-"])[0] == ROW, ""))
    ours_ar = sorted(k for k, v in ar.items() if v[0] == ROW)
    rows.append(("Argonia profile lays none of the height-fog row's files", len(ours_ar), not ours_ar, ", ".join(ours_ar[:3])))
    want = {weather_file(w["formid"]).replace("/", "\\").lower() for w in spec["weathers"]}
    laid = {k for k, v in nw.items() if k.startswith(f"{CS}/Weathers/".replace("/", "\\").lower()) and v[0] == ROW}
    rows.append(("a per-weather file laid in NewWorld for every weather of ours, no other", f"{len(want & laid)}/{len(want)}",
                 laid == want and bool(want), f"{len(want - laid)} missing, {len(laid - want)} extra" if laid != want else ""))
    for name in ("Argonia_ExponentialHeightFog.json", "Argonia_VolumetricLighting.json"):
        k = f"{CS}/Overrides/{name}".replace("/", "\\").lower()
        rows.append((f"{name}: NewWorld's from the height-fog row, Argonia's from community-shaders",
                     f"{nw.get(k, ['-'])[0]} / {ar.get(k, ['-'])[0]}",
                     nw.get(k, ["-"])[0] == ROW and ar.get(k, ["-"])[0] == "community-shaders", ""))
    staged = stack / "MO2/mods" / ROW / ADDON_INI
    ver = ""
    if staged.exists():
        for ln in staged.read_text(errors="replace").splitlines():
            if ln.strip().lower().startswith("version"):
                ver = ln.split("=", 1)[1].strip()
    rows.append((f"add-on version is the one Community Shaders 1.9.1 requires ({ADDON_VERSION})", ver or "-", ver == ADDON_VERSION, str(staged) if not ver else ""))
    return rows


def rows(plugin: Path, stack: Path | None = None) -> list[tuple[str, object, bool, str]]:
    """The verifier's rows: the manifest row is the generator's output for this spec, its files read back, the stack."""
    spec = json.loads((plugin / "atmosphere.json").read_text())
    row = manifest_row(json.loads(MANIFEST.read_text()))
    files = {f["path"]: f["text"] for f in row.get("files", [])}
    out = file_rows(spec, files)
    try:
        fresh = generate(spec, floors(plugin))
        same = fresh == row.get("files")
        out.append(("the manifest row's files are the generator's for this spec and terrain", same, same,
                    "" if same else "run python3 -m tools.newworld.atmosphere_cs write, then stack.py stage"))
    except (OSError, RuntimeError, KeyError) as e:
        out.append(("the manifest row's files are the generator's for this spec and terrain", "unmeasured", False, str(e)[:200]))
    if stack is not None:
        out += stack_rows(stack, spec)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("cmd", choices=("write", "check"))
    ap.add_argument("--plugin", type=Path, default=REPO / "out/newworld/plugin")
    ap.add_argument("--stack", type=Path, default=Path.home() / ".argonia/stack")
    a = ap.parse_args(argv)
    if a.cmd == "write":
        return write(a.plugin)
    bad = 0
    for req, v, ok, det in rows(a.plugin, a.stack):
        print(f"{'PASS' if ok else 'FAIL'}  {req}: {v}" + (f"  ({det})" if det else ""))
        bad += not ok
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
