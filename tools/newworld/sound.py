"""The regions' ambient sound (identity sheets' sound.day and sound.night): how Skyrim does it, measured, and each bed
of the sheets as real sound descriptors the load order holds. Records only, no audio files of ours.

    python3 -m tools.newworld.sound study   # newworld/sources/identity/sound_measured.json (Skyrim, Update, BM&V, Tropical, KotM)
    python3 -m tools.newworld.sound beds    # newworld/sources/identity/sound_beds.json from BEDS below and the study

How Skyrim does it (sound_measured.json): a region's Sounds data is a list of (sound descriptor, the weathers it plays in,
a chance) with a priority and, on the sets that must beat a neighbour, the Override flag. Every period of the day is in
the list: each descriptor carries its own GetCurrentTime window (a morning bird, a day bird, a night cricket), so a region
needs no day/night switch. A bed is a chance-1 loop (a wind bed, a night cricket loop); one-shots (birds, gusts) take a
chance of 0.03 to 0.1. Where a descriptor carries no hour (waves, a drizzle, our frogs), the sheet's day or night role gives
it one: our copy of the descriptor with the block test's hours (day: 6 <= hour < 20; night: hour < 6 or >= 20).
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
IDENT = REPO / "newworld/sources/identity"
MEASURED = IDENT / "sound_measured.json"
BEDS_FILE = IDENT / "sound_beds.json"
DATA = Path(os.environ.get("ARGONIA_GAME_ROOT", Path.home() / "games/skyrimse")) / "Data"
BIN = REPO / "out/tools/ArgoniaPlugin"
PLUGINS = ["Skyrim.esm", "Update.esm", "Black Marsh.esm", "Tropical Skyrim.esp", "Tropical Skyrim -- Birds.esp",
           "King of the Murkmire.esp"]
ALL = "Pleasant, Cloudy, Rainy, Snowy"
COPY_BASE = 0x80C00   # our time-gated descriptor copies: 0x80C00 .. 0x80FFF (atmosphere.py's id range)
COPY_LIMIT = 0x81000
M, T, F, K = "Skyrim.esm:", "Tropical Skyrim.esp:", "Tropical Skyrim -- Birds.esp:", "King of the Murkmire.esp:"

# bed -> parts. {"region": plugin:region edid, "prefix": descriptor edid prefix} takes every descriptor of that region
# whose editor id starts with the prefix, with the region's chance and weather flags (the evidence); {"sndr": ..., "chance":
# ..., "flags": ..., "why": ...} names one descriptor where no Skyrim region carries it.
BEDS = {
    "frog-chorus": [{"region": K + "ArgoniaMurkmireSouth", "prefix": "AMBrFrogsForestCypress"}],
    "cicadas": [{"region": M + "WeatherFallForest", "prefix": "AMBrInsectsForestFallCicadas1Morning"},
                {"region": M + "WeatherFallForest", "prefix": "AMBrInsectsForestFallCicadasBed1Morning"},
                {"region": M + "WeatherTundraMarsh", "prefix": "AMBrInsectsMarshCicadaSwell"}],
    "surf-gulls": [{"sndr": M + "AMBWaterCoastWavesLPSD", "chance": 1, "flags": ALL, "why": "Skyrim's coast waves loop, a chance-1 region loop as AMBrWindBedCoastLP in WeatherCoast"},
                   {"region": M + "WeatherCoast", "prefix": "AMBrWindCoastGust"},
                   {"sndr": F + "01BOSAudioSeagull", "chance": 0.05, "flags": ALL, "why": "Tropical Skyrim Birds' gull; one-shot at the chance of Skyrim's WeatherWinterhold day birds"}],
    "sea-swell": [{"sndr": M + "AMBWaterCoastWavesLPSD", "chance": 1, "flags": ALL, "why": "Skyrim's coast waves loop"},
                  {"sndr": M + "AMBWaterCoastWavesDistantLPSD", "chance": 1, "flags": ALL, "why": "Skyrim's distant coast waves loop"}],
    "reed-wind": [{"sndr": M + "AMBrWindBedMarshLP", "chance": 1, "flags": ALL, "why": "the marsh wind bed, a chance-1 loop as WeatherTundraMarsh's AMBrWindBedReachLP"},
                  {"region": M + "WeatherTundraMarsh", "prefix": "AMBrWindMarshGust"}],
    "rainforest-birds": [{"region": T + "WeatherTundraMarsh", "prefix": "AMBrJungleAmbience"},
                         {"region": M + "WeatherTundraMarsh", "prefix": "AMBrBirdsMarsh1Morning"},
                         {"region": M + "WeatherTundraMarsh", "prefix": "AMBrBirdsMarsh2Day"}],
    "deep-hush": [{"region": K + "ArgoniaMurkmireSouth", "prefix": "AMBrWindBedMarsh"},
                  {"region": M + "WeatherTundraMarshNoPrecip", "prefix": "AMBrInsectsMarshC0"}],
    "dusk-insects": [{"region": M + "WeatherFallForest", "prefix": "AMBrInsectsForestFallCicadas2Day"},
                     {"region": M + "WeatherFallForest", "prefix": "AMBrInsectsForestFallCicadasBed2Day"},
                     {"region": M + "WeatherReach", "prefix": "AMBrInsectsReach"}],
    "rain-drip": [{"sndr": M + "AMBWeatherRainDrizzleLP", "chance": 1, "flags": "Cloudy, Rainy", "why": "Skyrim's drizzle loop, only under cloud and rain"},
                  {"sndr": M + "AMBWaterDripsSplashLPSD", "chance": 0.05, "flags": ALL, "why": "Skyrim's dripping-water loop, sparse"}],
    "upland-wind": [{"region": M + "WeatherWinterhold", "prefix": "AMBrWindBedMountains"},
                    {"region": M + "WeatherWinterhold", "prefix": "AMBrWindMountainGust"}],
    "marsh-birds": [{"region": M + "WeatherTundraMarsh", "prefix": "AMBrBirdsMarsh1Morning"},
                    {"region": M + "WeatherTundraMarsh", "prefix": "AMBrBirdsMarsh2Day"},
                    {"region": M + "WeatherTundraMarsh", "prefix": "AMBrInsectsMarshCicadaSwell"}],
    "night-crickets": [{"region": M + "WeatherTundraMarsh", "prefix": "AMBrCricketsMarshNight"}],
    "fly-drone": [{"region": M + "WeatherVolcanicTundra", "prefix": "AMBrInsectsMarsh"},
                  {"region": M + "WeatherTundra", "prefix": "AMBrInsectsTundraDay"}],
    "owls": [{"region": M + "WeatherPineForest", "prefix": "AMBrBirdsForestPine3NightOwl"},
             {"region": M + "WeatherTundraMarsh", "prefix": "AMBrBirdsMarsh3Night"}],
}


def run_study(out: Path) -> dict:
    env = dict(os.environ, DOTNET_ROOT=str(Path.home() / ".dotnet"), DOTNET_CLI_TELEMETRY_OPTOUT="1", DOTNET_NOLOGO="1")
    env["PATH"] = f"{Path.home() / '.dotnet'}:{env['PATH']}"
    subprocess.run(["dotnet", "build", "-c", "Release", "-o", str(BIN), str(REPO / "tools/ArgoniaPlugin"), "-v", "q", "-nologo"],
                   check=True, env=env, capture_output=True)
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["dotnet", str(BIN / "ArgoniaPlugin.dll"), "sound", "study", str(out), str(DATA), *PLUGINS],
                   check=True, env=env, capture_output=True)
    return json.loads(out.read_text())


def hours(a: dict) -> str:
    """A descriptor's GetCurrentTime window as text (empty: no hour)."""
    return a["time"]


def measure(st: dict) -> dict:
    """The facts of Skyrim's way, from a study."""
    regs = st["regions"]
    by_plugin: dict[str, list] = {}
    for r in regs:
        by_plugin.setdefault(r["plugin"], []).append(r)
    ext = [r for r in regs if r["plugin"] == "Skyrim.esm" and not r["edid"].startswith(("AudioInt", "AudioMenu"))]
    desc = {v["edid"]: v for v in st["descriptors"].values()}
    allv = {a["edid"]: a for a in st["all"]}

    def timed(r):
        return [s for s in r["sounds"] if allv.get(s["sound"].split(":")[1], {}).get("time")]

    def entry(r):
        return {"region": r["edid"], "formkey": r["formkey"], "flags": r["flags"], "priority": r["priority"], "music": r["music"],
                "sounds": len(r["sounds"]), "with_an_hour": len(timed(r)),
                "chances": sorted({s["chance"] for s in r["sounds"]})}

    unused = [e for e in ("AMBWaterCoastWavesLPSD", "AMBWaterCoastWavesDistantLPSD", "AMBWeatherRainDrizzleLP", "AMBrFrogsForestPineNightLPSD")]
    used = {s["sound"].split(":")[1] for r in regs for s in r["sounds"]}
    return {
        "about": "Measured by `python -m tools.newworld.sound study` (ArgoniaPlugin `sound study`): every REGN with Sounds data in the load order.",
        "regions_with_sounds": {p: len(v) for p, v in by_plugin.items()},
        "skyrim_regions": {
            "count": len(regs and by_plugin.get("Skyrim.esm", [])),
            "region_flags": dict(Counter(r["flags"] for r in by_plugin["Skyrim.esm"])),
            "priority": dict(Counter(r["priority"] for r in by_plugin["Skyrim.esm"])),
            "entry_weather_flags": dict(Counter(s["flags"] for r in by_plugin["Skyrim.esm"] for s in r["sounds"])),
            "entries_per_region": [min(len(r["sounds"]) for r in ext), max(len(r["sounds"]) for r in ext)],
            "music_set": sum(1 for r in ext if r["music"]),
        },
        "descriptors": {
            "in_regions": len(st["descriptors"]),
            "with_a_GetCurrentTime_window": sum(1 for v in st["descriptors"].values() if allv.get(v["edid"], {}).get("time")),
            "loops": sum(1 for v in st["descriptors"].values() if v["loop"] == "Loop"),
            "chance_of_loops": sorted({s["chance"] for r in regs for s in r["sounds"] if desc.get(s["sound"].split(":")[1], {}).get("loop") == "Loop"})[-3:],
            "chance_of_one_shots": [min(s["chance"] for r in ext for s in r["sounds"] if desc.get(s["sound"].split(":")[1], {}).get("loop") == "None" and s["chance"] > 0),
                                    max(s["chance"] for r in ext for s in r["sounds"] if desc.get(s["sound"].split(":")[1], {}).get("loop") == "None")],
        },
        "day_and_night": "Every period's descriptors sit in one region list; each carries its own GetCurrentTime window (the marsh: "
                         "AMBrBirdsMarsh1Morning, 2Day, 3Night, AMBrCricketsMarshDay/Morning/Night, AMBrInsectsMarshCicadaSwell 11 to 19), "
                         "the region has no day/night switch.",
        "examples": [entry(r) for r in regs if r["plugin"] == "Skyrim.esm" and r["edid"] in
                     ("WeatherTundraMarsh", "WeatherCoast", "WeatherFallForest", "WeatherReach", "WeatherTundra", "WeatherPineForest")]
                    + [entry(r) for r in regs if r["plugin"] != "Skyrim.esm" and r["edid"] in ("WeatherTundraMarsh", "ArgoniaMurkmireSouth")],
        "not_in_any_region": [e for e in unused if e not in {u for u in used if u.startswith(e[:-2])} and not any(u.startswith(e) for u in used)],
        "coast": "WeatherCoast carries only AMBrWindBedCoastLP (chance 1) and the two AMBrWindCoastGust (0.1); the waves are sound markers in the world.",
        "needs_nothing_else": "Region sound data with its descriptors is the whole of Skyrim's exterior ambience; acoustic spaces (ASPC) belong to interiors "
                              "and to reverb areas, and sound markers place the waves, falls and rivers.",
        "kotm": "King of the Murkmire's regions run the same marsh lists at chances 0.0005 to 0.05 (ArgoniaMurkmireSouth, priority 50; "
                "ArgoniaMurkmireLilmoth priority 80) with its own AMBrFrogsForestCypress (7 one-shot frogs, no hour).",
        "tropical": "Tropical Skyrim's regions carry Skyrim's lists plus AMBrJungleAmbience (a loop, chance 0.09 to 0.14).",
    }


def expand(st: dict) -> dict:
    """BEDS over a study: each bed's entries as {sound, chance, flags, hours, source}."""
    regs = {f"{r['plugin']}:{r['edid']}": r for r in st["regions"]}
    allv = {(a["plugin"], a["edid"]): a for a in st["all"]}
    out = {}
    for bed, parts in BEDS.items():
        ents = []
        for p in parts:
            if "region" in p:
                r = regs[p["region"]]
                got = [s for s in r["sounds"] if s["sound"].split(":", 1)[1].startswith(p["prefix"])]
                if not got:
                    raise SystemExit(f"{bed}: {p['region']} has no sound {p['prefix']}*")
                for s in got:
                    ents.append({"sound": s["sound"], "chance": round(s["chance"], 4), "flags": s["flags"], "source": p["region"]})
            else:
                ents.append({"sound": p["sndr"], "chance": p["chance"], "flags": p["flags"], "source": p["why"]})
        for e in ents:
            plug, edid = e["sound"].split(":", 1)
            a = allv.get((plug, edid))
            if a is None:
                raise SystemExit(f"{bed}: {e['sound']} is not in {plug}")
            e["hours"] = hours(a)
        out[bed] = ents
    return out


def write_beds(st: dict) -> dict:
    """sound_beds.json: the beds, and the ids of our time-gated copies (kept once given, never renumbered)."""
    beds = expand(st)
    old = json.loads(BEDS_FILE.read_text()) if BEDS_FILE.exists() else {}
    ids = dict(old.get("copy_ids", {}))
    for bed, ents in sorted(beds.items()):
        for e in ents:
            if e["hours"]:
                continue
            for gate in ("day", "night"):
                key = f"{e['sound']}|{gate}"
                if key not in ids:
                    ids[key] = COPY_BASE + len(ids)
    if len(ids) > COPY_LIMIT - COPY_BASE:
        raise SystemExit("more sound copies than the id range holds")
    doc = {"about": "Each bed of the identity sheets (regions.json sound_beds) as the sound descriptors the load order holds, each entry "
                    "with the weathers it plays in, its chance and the region it is taken from (`python -m tools.newworld.sound beds`). An entry "
                    "with `hours` carries its own GetCurrentTime window; one without is copied by the spec for the sheet's day or night "
                    "(copy_ids: ids of those copies in 0x80C00..0x80FFF, kept once given).",
           "beds": beds, "copy_ids": ids}
    BEDS_FILE.write_text(json.dumps(doc, indent=1) + "\n")
    return doc


def load_beds() -> dict:
    return json.loads(BEDS_FILE.read_text())


def copy_edid(sound: str, gate: str) -> str:
    return f"ANW_Snd_{re.sub(r'[^A-Za-z0-9]', '', sound.split(':', 1)[1])}_{gate}"


def sound_spec(ident: dict, beds: dict | None = None) -> tuple[dict, list]:
    """(region -> entries, the copies): each region's day and night beds, an hourless descriptor replaced by our copy for
    the role it is in."""
    beds = beds or load_beds()
    copies, used, out = [], {}, {}
    for rid, row in ident.items():
        ents, seen = [], set()
        for gate in ("day", "night"):
            for e in beds["beds"][row["sound"][gate]]:
                sound = e["sound"]
                if not e["hours"]:
                    key = f"{sound}|{gate}"
                    used[key] = {"formid": beds["copy_ids"][key], "edid": copy_edid(sound, gate), "copy": sound, "gate": gate}
                    sound = "ANW:" + used[key]["edid"]
                if (sound, e["flags"]) not in seen:
                    seen.add((sound, e["flags"]))
                    ents.append({"sound": sound, "flags": e["flags"], "chance": e["chance"]})
        out[rid] = ents
    copies = sorted(used.values(), key=lambda c: c["formid"])
    return out, copies


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    scratch = REPO / "out/newworld/sound-study.json"
    if cmd == "study":
        MEASURED.write_text(json.dumps(measure(run_study(scratch)), indent=1) + "\n")
        print(f"wrote {MEASURED}", file=sys.stderr)
    elif cmd == "beds":
        st = json.loads(scratch.read_text()) if scratch.exists() else run_study(scratch)
        doc = write_beds(st)
        print(f"{len(doc['beds'])} beds, {len(doc['copy_ids'])} copies -> {BEDS_FILE}", file=sys.stderr)
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
