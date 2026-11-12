"""python -m tools.places sources-mine [--only GROUP ...] [--force]

Mines candidate source places out of every plugin group we hold (GROUPS) with the C# extractor's `mine` mode into
out/newworld/sources/mined/<group>.jsonl, one row per candidate: its location record or map marker, cells,
interiors behind its doors, counts, people (enemies and residents), wet cells and culture or tileset tags. Each group
is keyed on its plugins' sha256 and the extractor's hash, so a rerun mines only what changed (decision 0037).
A plugin that is in none of the search directories is reported as not mined, never a stop.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from tools.places.bundle import REPO, sha256_file, stamp_key
from tools.places.extract import build_tool, find_plugin, search_dirs, tool_hash

OUT = REPO / "out" / "newworld" / "sources" / "mined"
VANILLA = ["Skyrim.esm", "Update.esm", "Dawnguard.esm", "HearthFires.esm", "Dragonborn.esm"]

# group: (plugins loaded in order, the winners last; the plugins whose places are mined; the mod row it is credited to)
GROUPS: dict[str, tuple[list[str], list[str], str]] = {
    "bmv": (["Black Marsh.esm", "Black Marsh North.esp"], ["Black Marsh.esm", "Black Marsh North.esp"], "bmv"),
    "kotm": (["King of the Murkmire.esp"], ["King of the Murkmire.esp"], "king-of-the-murkmire"),
    "skyrim": (VANILLA + ["Tropical Skyrim.esp"], VANILLA, "skyrim (Tropical Skyrim's winners)"),
    "htbm": (["Here There Be Monsters.esp"], ["Here There Be Monsters.esp"], "htbm"),
    "cipactli": (["Here There Be Monsters - Curse of Cipactli.esp"], ["Here There Be Monsters - Curse of Cipactli.esp"], "htbm-cipactli"),
    "xanmeer": (["XanmeerResources.esp"], ["XanmeerResources.esp"], "xanmeer-tileset"),
    "mudmother": (["ArgonianLakeHouse.esl"], ["ArgonianLakeHouse.esl"], "mud-mother-grove"),
    "ayleidres": (["CCAyliedRuinsResources.esp"], ["CCAyliedRuinsResources.esp"], "cc-ayleid-resources"),
    "histtree": (["Skyfall Sleeping Tree Overhaul.esp"], ["Skyfall Sleeping Tree Overhaul.esp"], "sleeping-hist-tree"),
    "depths": (["DepthsOfSkyrim.esp"], ["DepthsOfSkyrim.esp"], "depths-of-skyrim"),
    "sirenroot": (["evgSIRENROOT.esm"], ["evgSIRENROOT.esm"], "sirenroot"),
    "dunmersettle": (["dunmer settlements solstheim.esp"], ["dunmer settlements solstheim.esp"], "dunmer-settlements-solstheim"),
    "aho": (["Dwarfsphere.esp"], ["Dwarfsphere.esp"], "project-aho"),
    "solexpand": (["SolstheimExpand.esp"], ["SolstheimExpand.esp"], "solstheim-dunmer-additions"),
    "newzainab": (["CampNewZainab.esp"], ["CampNewZainab.esp"], "ashlander-camp-new-zainab"),
    "baanmalur": (["Journey to Baan Malur.esp"], ["Journey to Baan Malur.esp"], "journey-to-baan-malur"),
    "greyquarter": (["Grey_Quarter_Overhaul.esp"], ["Grey_Quarter_Overhaul.esp"], "grey-quarter-overhaul"),
    "dawnofskyrim": (["Dawn of Skyrim.esp"], ["Dawn of Skyrim.esp"], "dawn-of-skyrim"),
    "dosgq": (["DOS - Grey Quarter Overhaul Patch.esp"], ["DOS - Grey Quarter Overhaul Patch.esp"], "dawn-of-grey-quarter"),
    "cavesmw": (["CavesofMorrowind.esp"], ["CavesofMorrowind.esp"], "caves-of-morrowind"),
    "moonpath": (["moonpath.esp"], ["moonpath.esp"], "moonpath-to-elsweyr"),
    "wyrmstooth": (["Wyrmstooth.esp"], ["Wyrmstooth.esp"], "wyrmstooth"),
    "nyhus": (["Nyhus.esp"], ["Nyhus.esp"], "nyhus"),
    "bloodmoon": (["Forgotten Bloodmoon Dungeons.esp", "VendesMorrowindSolstheimDungeons.esp", "Bloodmoon Dungeons Restored - Fort Frostmoth Expansion.esp", "Berserkers N Fryse Hags.esp"], ["Forgotten Bloodmoon Dungeons.esp", "VendesMorrowindSolstheimDungeons.esp", "Bloodmoon Dungeons Restored - Fort Frostmoth Expansion.esp", "Berserkers N Fryse Hags.esp"], "bloodmoon-dungeons-restored"),
    "soldungeons": (["SolsthDungeonPack.esp"], ["SolsthDungeonPack.esp"], "solstheim-dungeonpack"),
    "tradingposts": (["Skyrim Trading Posts.esp"], ["Skyrim Trading Posts.esp"], "skyrim-trading-posts"),
    "northwatch": (["Northwatch Coast.esp"], ["Northwatch Coast.esp"], "northwatch-coast"),
    "exploreskyrim": (["ExploreSkyrim-ES.esp"], ["ExploreSkyrim-ES.esp"], "explore-skyrim"),
    "underwater": (["UWRL_UnderWaterSkyrimRiversAndLakes.esp"], ["UWRL_UnderWaterSkyrimRiversAndLakes.esp"], "underwater-skyrim-rivers-and-lakes"),
}


def status_path() -> Path:
    return OUT / "status.json"


def mine_group(name: str, dirs: list[str], force: bool) -> dict:
    load, mine, credit = GROUPS[name]
    try:
        inputs = {p: sha256_file(find_plugin(p, dirs)) for p in load}
    except FileNotFoundError as e:
        return {"group": name, "mined": False, "why": str(e), "credit": credit, "plugins": mine}
    key = stamp_key(inputs, tool_hash(), {"load": load, "mine": mine, "cluster": name != "skyrim"})
    out = OUT / f"{name}.jsonl"
    stamp = OUT / f"{name}.key"
    if out.exists() and stamp.exists() and stamp.read_text() == key and not force:
        rows = sum(1 for _ in out.open())
        return {"group": name, "mined": True, "rows": rows, "credit": credit, "plugins": mine, "key": key, "fresh": False}
    dll = build_tool()
    OUT.mkdir(parents=True, exist_ok=True)
    job = OUT / f".{name}.job.json"
    job.write_text(json.dumps({"plugins": load, "mine": mine, "search": dirs, "cluster": name != "skyrim"}))
    tmp = OUT / f".{name}.jsonl"
    env = dict(os.environ, DOTNET_ROOT=str(Path.home() / ".dotnet"))
    r = subprocess.run([str(Path.home() / ".dotnet" / "dotnet"), str(dll), "mine", str(job), str(tmp)], env=env,
                       capture_output=True, text=True)
    job.unlink()
    if r.returncode != 0:
        sys.stderr.write(r.stderr[-4000:])
        return {"group": name, "mined": False, "why": "the extractor failed", "credit": credit, "plugins": mine}
    missing = Path(str(tmp) + ".missing")
    miss = [m for m in missing.read_text().splitlines() if m] if missing.exists() else []
    missing.unlink(missing_ok=True)
    tmp.replace(out)
    stamp.write_text(key)
    rows = sum(1 for _ in out.open())
    print(f"{name}: {rows} candidates" + (f" (masters not found: {', '.join(miss)})" if miss else ""))
    return {"group": name, "mined": True, "rows": rows, "credit": credit, "plugins": mine, "key": key,
            "masters_missing": miss, "fresh": True}


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="python -m tools.places sources-mine")
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args(argv)
    dirs = search_dirs()
    OUT.mkdir(parents=True, exist_ok=True)
    st = json.loads(status_path().read_text()) if status_path().exists() else {}
    for name in GROUPS:
        if a.only and name not in a.only:
            continue
        st[name] = mine_group(name, dirs, a.force)
        if not st[name]["mined"]:
            print(f"{name}: NOT MINED: {st[name]['why']}")
        status_path().write_text(json.dumps(st, indent=1))
    return 0
