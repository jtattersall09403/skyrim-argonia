"""Which placed bases of the new world get LOD, and by which of Skyrim's mechanisms (nw-02 walk 5, item 4).

Skyrim draws three things beyond the loaded cells: terrain LOD, tree LOD (a billboard per tree base, drawn in the
.btt chunks) and object LOD (a base's own LOD models, merged into the .bto chunks). What gets which, measured on
DynDOLOD 3 Alpha-217 and its documentation (dyndolod.info Help/Tree-LOD, Help/TexGen-Configuration) and on the run
of 2026-11-09 (DynDOLOD_SSE_BillboardsUsed_ArgoniaBlackMarsh.txt, LODGen_SSE_Export_ArgoniaBlackMarsh.txt):
  - tree LOD is drawn for TREE bases, and STAT bases with the "Has Tree LOD" flag, that have a billboard; TexGen
    makes a billboard only for a base whose bounds reach MinTreeModelMagnitude 512 and MinTreeModelHeight 256
    (TexGen_SSE.ini) AND whose model path holds "tree". Most King of the Murkmire plants and every BM&V or KotM tree
    kept as a STAT failed one of those: 54 TREE bases (91,469 refs) and 50 STAT trees were listed ",False" or never
    considered. TexGen's override file DynDOLOD_SSE_TexGen_Billboards_<plugin>.txt forces a listed base's billboard
    (",True"), and the writer sets "Has Tree LOD" on our STAT trees.
  - object LOD is drawn for a STAT with LOD models (its own <model>_lod*.nif or DynDOLOD Resources' meshes\\lod\\...);
    a large rock, log or cliff without one is drawn by a DynDOLOD rule naming its full model ("Full") at LOD4 (and
    LOD8 when it is very large), the rule placed ahead of the preset's catch-all.
  - small things get no LOD in Skyrim (grass, ground cover, herbs, ferns, small rocks: DynDOLOD's Medium preset
    rules \\rockl, \\rockm, \\rockpile None): they are drawn only inside the loaded cells, fading by the ini's
    fLODFadeOutMultObjects; nothing here changes that.

    python -m tools.newworld.world.lodplan build [--plugin out/newworld/plugin]
        -> <plugin>/map/lodplan.json   per placed base: mechanism (tree, object, own, none) and why, with counts
    python -m tools.newworld.world.lodplan coverage <lod logs dir> [--plugin ...]
        the last DynDOLOD run's read-back: per base, what it actually got, against the plan (exit 1 on a large base
        planned for LOD that got none); writes <lod logs dir>/coverage.json

`ArgoniaPlugin nwmap apply` reads lodplan.json: sets the flag, writes the TexGen override file and the rules file
(both with the ESM's own form ids) beside the map files; lod.sh sends them and lod.ps1 lays them.
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import math
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
OWN_LOD = Path(__file__).with_name("lod_models.json")  # models DynDOLOD found LOD models for (measured, refreshed by coverage)
MIN_MAGNITUDE = 512.0  # TexGen_SSE.ini MinTreeModelMagnitude: bounds diagonal
MIN_HEIGHT = 256.0  # TexGen_SSE.ini MinTreeModelHeight: bounds Z2
LOD8_MAGNITUDE = 1500.0  # a full model also at LOD8: the very large (cliffs, fallen giants)
BILLBOARD_CAP = 256  # DynDOLOD: at most 256 billboards in one worldspace's tree LOD atlas
TREE_CLASSES = {"canopy_tree", "palm", "understorey", "water_plant", "seabed_plant"}
OBJECT_CLASSES = {"log", "boulder", "cliff", "road_rock_pile", "road_boulder", "seabed_rock", "mushroom", "road_fence",
                  "road_cairn", "road_signpost"}


def initials(file: str) -> str:
    """ForeignCopy.Initials: 'King of the Murkmire.esp' -> 'KotM'."""
    return "".join(m[0] for m in re.findall(r"[A-Z][a-z]*|[a-z]+|[0-9]+", re.sub(r"\.[^.]+$", "", file)))


def our_edid(b: dict) -> str:
    return f"ANW_{initials(b['plugin'])}_{b['edid']}" if b["copied"] else b["edid"]


def refs_per_base(plugin: Path) -> tuple[collections.Counter, dict]:
    n, cls = collections.Counter(), {}
    for f in glob.glob(str(plugin / "refs" / "flora" / "cy*.jsonl")):
        with open(f) as fh:
            for ln in fh:
                r = json.loads(ln)
                n[r["base"]] += 1
                cls.setdefault(r["base"], r.get("cls"))
    return n, cls


def own_lod_models(extra: Path | None = None) -> set[str]:
    have = {m.lower() for m in json.loads(OWN_LOD.read_text())["models"]}
    if extra and extra.exists():
        have |= {m.lower() for m in json.loads(extra.read_text()).get("own_lod_models", [])}
    return have


def classify(b: dict, refs: int, cls: str | None, own: set[str]) -> tuple[str, str]:
    o = b["obnd"]
    mag = math.dist(o[:3], o[3:])
    big = mag >= MIN_MAGNITUDE and o[5] >= MIN_HEIGHT
    model = b["model"].replace("/", "\\").lower()
    if not refs:
        return "none", "not placed"
    if model in own:
        return "own", "its own LOD models (DynDOLOD's catch-all rule)"
    if b["sig"] == "TREE" and big:
        return "tree", "TREE base at TexGen's size: billboard forced"
    if b["sig"] == "STAT" and cls in TREE_CLASSES and big:
        if b["copied"]:
            return "tree", "STAT tree at TexGen's size: Has Tree LOD set, billboard forced"
        # a master's STAT (Black Marsh.esm) cannot carry our flag: its full model below
    if b["sig"] == "STAT" and mag >= MIN_MAGNITUDE and (cls in OBJECT_CLASSES or (cls in TREE_CLASSES and o[5] >= MIN_HEIGHT)):
        return "object", "large STAT without LOD models: full model rule at LOD4" + (" and LOD8" if mag >= LOD8_MAGNITUDE else "")
    if b["sig"] == "FLOR":
        return "none", "flora (harvestable plant): no LOD in Skyrim"
    if mag >= MIN_MAGNITUDE:
        return "none", f"low ({cls}, {o[5]:.0f} units high, under TexGen's {MIN_HEIGHT:.0f}): ground cover, no LOD in Skyrim"
    return "none", f"small ({cls}, bounds {mag:.0f} units): no LOD in Skyrim, drawn in the loaded cells"


def build(plugin: Path, extra: Path | None = None) -> dict:
    bases = json.loads((plugin / "refs" / "flora" / "bases.json").read_text())
    n, cls = refs_per_base(plugin)
    own = own_lod_models(extra)
    rows = []
    for b in bases["bases"]:
        mech, why = classify(b, n[b["ref"]], cls.get(b["ref"]), own)
        o = b["obnd"]
        rows.append({"edid": our_edid(b), "plugin": "ArgoniaNewWorld.esm" if b["copied"] else b["plugin"],
                     "key": None if b["copied"] else b["key"],  # a master's own form key; ours is read from the ESM
                     "source": b["ref"], "sig": b["sig"], "cls": cls.get(b["ref"]), "refs": n[b["ref"]],
                     "magnitude": round(math.dist(o[:3], o[3:])), "model": b["model"], "mech": mech, "why": why,
                     "lod8": mech == "object" and math.dist(o[:3], o[3:]) >= LOD8_MAGNITUDE})
    trees = [r for r in rows if r["mech"] == "tree"]
    if len(trees) > BILLBOARD_CAP:  # keep the most-placed; the rest drawn as objects (full model)
        trees.sort(key=lambda r: -r["refs"] * r["magnitude"])
        for r in trees[BILLBOARD_CAP:]:
            r["mech"], r["why"] = "object", f"over the {BILLBOARD_CAP}-billboard atlas: full model rule at LOD4"
    tally = collections.defaultdict(lambda: [0, 0])
    for r in rows:
        tally[r["mech"]][0] += 1
        tally[r["mech"]][1] += r["refs"]
    doc = {"build_id": bases["build_id"], "bases_key": bases["key"],
           "counts": {k: {"bases": v[0], "refs": v[1]} for k, v in sorted(tally.items())}, "bases": rows}
    d = plugin / "map"
    d.mkdir(parents=True, exist_ok=True)
    (d / "lodplan.json").write_text(json.dumps(doc, indent=1))
    return doc


def read_back(logs: Path) -> tuple[dict, set[str], set[str]]:
    """The last DynDOLOD run: billboard found per base editor id, object-LOD base editor ids, and the full models
    whose LOD models it used (a model whose LOD rows name *_lod*.nif)."""
    bb = {}
    for ln in (logs / "DynDOLOD_SSE_BillboardsUsed_ArgoniaBlackMarsh.txt").read_text(errors="replace").splitlines():
        m = re.match(r"(\S+) \[(\w+):(\w+)\] Billboard (found|not found)", ln)
        if m:
            bb[m[1].lower()] = m[4] == "found"
    obj, own = set(), set()
    for ln in (logs / "LODGen_SSE_Export_ArgoniaBlackMarsh.txt").read_text(errors="replace").splitlines():
        p = ln.split("\t")
        if len(p) == 17:
            obj.add(p[9].lower())
            if any("_lod" in x.lower() for x in p[13:16]):
                own.add(re.sub(r"^meshes\\", "", p[12].lower()))
    return bb, obj, own


def coverage(plugin: Path, logs: Path) -> int:
    plan = json.loads((plugin / "map" / "lodplan.json").read_text())
    bb, obj, own = read_back(logs)
    got = collections.Counter()
    miss = []
    for r in plan["bases"]:
        e = r["edid"].lower()
        have = "tree" if bb.get(e) else ("object" if e in obj else "none")
        got[(r["mech"], have)] += r["refs"]
        if r["mech"] in ("tree", "object", "own") and have == "none" and r["refs"]:
            miss.append(f"{r['edid']} ({r['refs']} refs) planned {r['mech']}, got none")
    (logs / "coverage.json").write_text(json.dumps({"own_lod_models": sorted(own), "planned_vs_got_refs":
                                                    {f"{a}->{b}": v for (a, b), v in sorted(got.items())}, "missing": miss}, indent=1))
    for (a, b), v in sorted(got.items()):
        print(f"planned {a:6} got {b:6}: {v} refs")
    print(f"large bases planned for LOD that got none: {len(miss)}")
    for m in miss[:20]:
        print("  FAIL", m)
    return 1 if miss else 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=("build", "coverage"))
    ap.add_argument("logs", nargs="?")
    ap.add_argument("--plugin", default=str(REPO / "out/newworld/plugin"))
    ap.add_argument("--coverage", default=str(REPO / "out/newworld/lod/logs/coverage.json"),
                    help="the last run's read-back (own LOD models found), added to lod_models.json")
    a = ap.parse_args(argv)
    if a.cmd == "build":
        doc = build(Path(a.plugin), Path(a.coverage))
        print(json.dumps(doc["counts"]))
        return 0
    return coverage(Path(a.plugin), Path(a.logs))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
