"""Ecology census (nw-03b): what creatures, leveled lists and harvestables the plugins of the new world hold.

Reads each plugin's own records with tools/argonia_world/esm.py and writes out/newworld/ecology/census.json (never
git): per plugin the creature NPC_ records (a race that is neither playable nor carries ActorTypeNPC), the races
used, the LVLN lists, the FLOR with an ingredient (PFIG), the INGR, and in the Black Marsh and King of the Murkmire
plugins the humanoid hostile candidates (bandit-like editor ids, with their factions). It also counts how many of
the flora build's bases carry an ingredient and how many placed refs use them.

    python -m tools.newworld.ecology.census
"""
from __future__ import annotations

import json
import os
import re
import struct
from collections import Counter
from pathlib import Path

from tools.argonia_world.esm import Plugin

DATA = Path(os.environ.get("ARGONIA_GAME_ROOT", Path.home() / "games/skyrimse")) / "Data"
MO2 = Path(os.environ.get("ARGONIA_STACK") or Path.home() / ".argonia/stack") / "MO2/mods"


def plugin_path(name: str) -> Path:
    """A plugin in the game's Data folder, else in the first MO2 mod folder that holds it."""
    for d in [DATA, *sorted(MO2.iterdir())]:
        if (d / name).exists():
            return d / name
    raise FileNotFoundError(name)

PLUGINS = ["Skyrim.esm", "Dawnguard.esm", "Dragonborn.esm", "ccBGSSSE001-Fish.esm", "Black Marsh.esm",
           "Black Marsh North.esp", "Here There Be Monsters.esp", "Here There Be Monsters - Curse of Cipactli.esp",
           "King of the Murkmire.esp", "Tropical Skyrim.esp", "Tropical Skyrim -- Birds.esp"]
HUMAN_SOURCES = {"Black Marsh.esm", "Black Marsh North.esp", "King of the Murkmire.esp"}
HOSTILE = re.compile(r"bandit|raider|slaver|pirate|thief|outlaw|brigand|marauder|cultist|necromancer|warlock|mage|"
                     r"poacher|smuggler|assassin|cutthroat|reaver|corsair", re.I)
SIGS = {"NPC_", "RACE", "LVLN", "FLOR", "INGR", "KYWD", "FACT"}
OUT = Path("out/newworld/ecology/census.json")
FLORA = Path("out/newworld/plugin/refs/flora")
LVLN_FLAGS = {1: "calc_all_levels_lte_pc", 2: "calc_each_item", 4: "use_all", 8: "special_loot"}


def _u(d: bytes | None, fmt: str, off: int = 0):
    return struct.unpack_from(fmt, d, off)[0] if d and len(d) >= off + struct.calcsize(fmt) else None


def _race_info(r, kyw: dict[str, str]) -> dict:
    flags = _u(r.sub("DATA"), "<I", 32)
    kw = r.sub("KWDA") or b""
    kws = {kyw.get(r.plugin.form_key(v), "") for (v,) in struct.iter_unpack("<I", kw[:len(kw) // 4 * 4])}
    playable = bool(flags and flags & 1)
    return {"key": r.key, "edid": r.edid, "name": r.name, "playable": playable,
            "creature": not playable and "ActorTypeNPC" not in kws,
            "actor_types": sorted(k for k in kws if k.startswith("ActorType"))}


def read_plugin(name: str, edids: dict[str, str], strings: dict[str, str]) -> dict:
    p = Plugin.read(plugin_path(name), SIGS)
    own = [r for r in p.records() if r.own]
    kyw = {r.key: r.edid for r in p.records("KYWD")}
    kyw.update({k: v for k, v in edids.items() if k not in kyw})
    races = {r.key: _race_info(r, kyw) for r in p.records("RACE")}
    facts = {r.key: r.edid for r in p.records("FACT")}
    for r in p.records():
        if r.edid:
            edids[r.key] = r.edid
    out = {"npcs": [], "races_defined": [v for r in own if (v := races.get(r.key)) and r.sig == "RACE"],
           "lvln": [], "flor": [], "ingr": [], "hostile_humanoids": []}
    used: Counter = Counter()
    for r in p.records("NPC_"):
        if not r.own:
            continue
        acbs, race = r.sub("ACBS"), r.ref("RNAM")
        fl = _u(acbs, "<I", 0) or 0
        info = races.get(race or "", {"edid": strings.get(race or "", race), "creature": None})
        npc = {"key": r.key, "edid": r.edid, "name": r.name, "race": race, "race_edid": info.get("edid"),
               "creature": info.get("creature"), "level": _u(acbs, "<H", 8), "level_mult": bool(fl & 0x80),
               "template": r.ref("TPLT"),
               "factions": [p.form_key(v) for v in (struct.unpack_from("<I", d)[0] for d in r.all("SNAM")) if v]}
        npc["factions"] = [facts.get(f, f) for f in npc["factions"]]
        if npc["creature"]:
            out["npcs"].append(npc)
            used[race] += 1
        elif name in HUMAN_SOURCES and HOSTILE.search((npc["edid"] or "") + " " + " ".join(map(str, npc["factions"]))):
            out["hostile_humanoids"].append(npc)
    out["races_used"] = [{"race": k, "edid": (races.get(k) or {}).get("edid") or edids.get(k), "npcs": n}
                         for k, n in used.most_common()]
    for r in p.records("LVLN"):
        if r.own:
            ents = [{"ref": p.form_key(v), "level": lv, "count": c} for lv, v, c in
                    (struct.unpack_from("<HxxIHxx", d) for d in r.all("LVLO") if len(d) >= 12)]
            f = _u(r.sub("LVLF"), "<B") or 0
            out["lvln"].append({"key": r.key, "edid": r.edid, "chance_none": _u(r.sub("LVLD"), "<B"),
                                "flags": [v for k, v in LVLN_FLAGS.items() if f & k], "entries": ents})
    for r in p.records("INGR"):
        if r.own:
            out["ingr"].append({"key": r.key, "edid": r.edid, "name": r.name})
    for r in p.records("FLOR"):
        if r.own:
            out["flor"].append({"key": r.key, "edid": r.edid, "name": r.name, "ingredient": r.ref("PFIG")})
    return out


def harvestables(flor_by_key: dict[str, str | None]) -> dict:
    """Flora bases of the build that carry an ingredient, and how many placed refs use them."""
    try:
        bases = json.loads((FLORA / "bases.json").read_text())["bases"]
    except OSError:
        return {"built": False}
    withing = {b["key"]: flor_by_key.get(b["key"]) for b in bases if b["sig"] == "FLOR" and flor_by_key.get(b["key"])}
    uses: Counter = Counter()
    for f in FLORA.glob("cy*.jsonl"):
        for line in f.open():
            k = json.loads(line).get("key")
            if k in withing:
                uses[k] += 1
    return {"built": True, "flor_bases": sum(b["sig"] == "FLOR" for b in bases), "with_ingredient": len(withing),
            "refs_using": sum(uses.values()),
            "by_base": [{"key": k, "edid": next(b["edid"] for b in bases if b["key"] == k), "ingredient": withing[k],
                         "refs": uses[k]} for k in sorted(withing, key=lambda k: -uses[k])]}


def main() -> None:
    edids: dict[str, str] = {}
    strings: dict[str, str] = {}
    res = {}
    for n in PLUGINS:
        try:
            res[n] = read_plugin(n, edids, strings)
        except FileNotFoundError:
            res[n] = {"missing": True}
    flor = {f["key"]: f["ingredient"] for d in res.values() for f in d.get("flor", [])}
    for d in res.values():
        for f in d.get("flor", []):
            f["ingredient_edid"] = edids.get(f["ingredient"]) if f["ingredient"] else None
    harv = harvestables({k.split(":")[0] + ":" + k.split(":")[1]: v for k, v in flor.items()})
    for b in harv.get("by_base", []):
        b["ingredient_edid"] = edids.get(b["ingredient"])
    try:
        deps = json.loads(Path("mods/dependencies.json").read_text())
    except OSError:
        deps = {}
    asset_only: list[str] = []

    def walk(o):
        if isinstance(o, dict):
            if o.get("asset_only"):
                asset_only.extend(o.get("plugins") or [])
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(deps)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"plugins": res, "harvestables_in_build": harv,
                               "asset_only": [p for p in PLUGINS if p in asset_only]}, indent=1))
    print(f"{'plugin':48} {'npc':>5} {'races':>5} {'lvln':>5} {'flor+ing':>8} {'ingr':>5} {'hostile':>7}")
    for n, d in res.items():
        if d.get("missing"):
            print(f"{n:48} missing")
            continue
        print(f"{n:48} {len(d['npcs']):5} {len(d['races_used']):5} {len(d['lvln']):5} "
              f"{sum(bool(f['ingredient']) for f in d['flor']):8} {len(d['ingr']):5} {len(d['hostile_humanoids']):7}")
    print("asset_only:", ", ".join(p for p in PLUGINS if p in asset_only))
    print("build harvestables:", {k: v for k, v in harv.items() if k != "by_base"})
    for b in harv.get("by_base", [])[:10]:
        print("  ", b)


if __name__ == "__main__":
    main()
