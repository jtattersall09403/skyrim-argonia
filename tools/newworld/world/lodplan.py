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
    (",True"), and the writer sets "Has Tree LOD" on our STAT trees (a master's static tree on an override of ours).
    At most 256 billboards a world: past that the fewest-placed get none.
  - object LOD is drawn for a STAT with LOD models (its own <model>_lod*.nif or DynDOLOD Resources' meshes\\lod\\...,
    found where DynDOLOD looks); a large log, cliff or rock (over 1,500 units) without one may be drawn by a rule naming
    its full model ("Full", no decimation) at LOD4, and LOD8 for cliffs alone, only while every LOD block stays within
    BUDGET, the triangles Tamriel's own object LOD carries per block; past it the model gets none (we make no LOD
    meshes). Skyrim's own None families (RockL/M/S, rock piles) and rocks under 1,500 units get none.
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
BOULDER_MAGNITUDE = 1500.0  # a rock smaller than this gets no LOD (Skyrim gives its RockL/M/S none)
BILLBOARD_CAP = 256  # DynDOLOD: at most 256 billboards in one worldspace's tree LOD atlas
TREE_CLASSES = {"canopy_tree", "palm", "understorey", "water_plant", "seabed_plant"}
OBJECT_CLASSES = {"log", "boulder", "cliff", "road_boulder", "seabed_rock", "mushroom", "road_fence", "road_cairn",
                  "road_signpost"}
ROCK_CLASSES = {"boulder", "road_boulder", "seabed_rock"}
LOD8_CLASSES = {"cliff"}  # a full model also at LOD8: cliffs alone (DynDOLOD: LOD8/16 None for small objects)
# DynDOLOD's Medium preset rules that give a model family no LOD (Rules\DynDOLOD_SSE_Medium.ini, in its preset ini):
SKYRIM_NONE = ("\\rockl", "\\rockm", "\\rocks0", "\\rockpile", "\\icepile", "\\snowdrifts\\", "\\roadchunk", "\\hay\\")
# The triangles a full-model rule may add to one LOD block: the 90th percentile of what Tamriel's own object LOD
# carries per block (Skyrim - Meshes1.bsa, meshes\terrain\tamriel\objects: 517 LOD4 .bto p50 3,864, p90 9,327,
# max 18,141; 152 LOD8 .bto p50 6,156, p90 14,263), measured 2026-11-10.
BUDGET = {4: 9327, 8: 14263}


def initials(file: str) -> str:
    """ForeignCopy.Initials: 'King of the Murkmire.esp' -> 'KotM'."""
    return "".join(m[0] for m in re.findall(r"[A-Z][a-z]*|[a-z]+|[0-9]+", re.sub(r"\.[^.]+$", "", file)))


def our_edid(b: dict) -> str:
    return f"ANW_{initials(b['plugin'])}_{b['edid']}" if b["copied"] else b["edid"]


def refs_per_base(plugin: Path) -> tuple[collections.Counter, dict, dict]:
    """Refs per base, its placer class, and its refs per LOD block {level: Counter((bx, by))} (a level-L block holds
    L x L cells from a multiple of L, the .lod grid's)."""
    n, cls, blocks = collections.Counter(), {}, {}
    for f in glob.glob(str(plugin / "refs" / "flora" / "cy*.jsonl")):
        with open(f) as fh:
            for ln in fh:
                r = json.loads(ln)
                n[r["base"]] += 1
                cls.setdefault(r["base"], r.get("cls"))
                cx, cy = int(r["x"] // 4096), int(r["y"] // 4096)
                b = blocks.setdefault(r["base"], {4: collections.Counter(), 8: collections.Counter()})
                for lvl in (4, 8):
                    b[lvl][(cx // lvl, cy // lvl)] += 1
    return n, cls, blocks


def lod_model(model: str, read) -> str | None:
    """A LOD model of the same shape where DynDOLOD looks for one by name (dyndolod.info Mod-Authors: <model>_lod_0..3
    beside it or under meshes\\lod\\), found in the NewWorld profile; None when there is none."""
    m = model.replace("/", "\\").lower()
    stem = m[:-4] if m.endswith(".nif") else m
    rest = stem.split("\\", 1)[1] if "\\" in stem else stem
    for c in (f"{stem}_lod.nif", f"{stem}_lod_0.nif", f"lod\\{rest}_lod_0.nif", f"lod\\{rest}_lod.nif", f"lod\\{stem}_lod_0.nif"):
        if read(c) is not None:
            return c
    return None


def triangles(model: str, read) -> int | None:
    """The full model's drawn triangles (every shape not hidden), or None when it cannot be read."""
    from tools.places.assets import nifglb
    raw = read(model)
    if raw is None:
        return None
    try:
        return sum(s["tris"] for s in nifglb.dump(raw)["shapes"] if not s.get("hidden"))
    except Exception:  # noqa: BLE001 - a mesh nifdump cannot read is a model with no count
        return None


def resolver():
    """read(model path under meshes) -> bytes | None, as the NewWorld profile has it (tools/places/assets/resolve.py)."""
    from tools.places.assets import resolve
    r = resolve.default()
    return lambda p: r.read(resolve.norm(p, "meshes"))


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
        # ours carries the flag itself; a master's (Black Marsh.esm) gets an override of ours that carries it
        return "tree", "STAT tree at TexGen's size: Has Tree LOD set" + ("" if b["copied"] else " on our override") + ", billboard forced"
    if b["sig"] == "STAT" and any(s in "\\" + model for s in SKYRIM_NONE):
        return "none", "a model family Skyrim's own LOD rules give none (RockL/M/S, rock piles)"
    if b["sig"] == "STAT" and cls in ROCK_CLASSES and mag < BOULDER_MAGNITUDE:
        return "none", f"rock under {BOULDER_MAGNITUDE:.0f} units: no LOD, as Skyrim's RockL/M/S"
    if b["sig"] == "STAT" and mag >= MIN_MAGNITUDE and (cls in OBJECT_CLASSES or (cls in TREE_CLASSES and o[5] >= MIN_HEIGHT)):
        return "object", "large STAT without LOD models: full model rule at LOD4" + (" and LOD8" if cls in LOD8_CLASSES else "")
    if b["sig"] == "FLOR":
        return "none", "flora (harvestable plant): no LOD in Skyrim"
    if mag >= MIN_MAGNITUDE:
        return "none", f"low ({cls}, {o[5]:.0f} units high, under TexGen's {MIN_HEIGHT:.0f}): ground cover, no LOD in Skyrim"
    return "none", f"small ({cls}, bounds {mag:.0f} units): no LOD in Skyrim, drawn in the loaded cells"


def budget(rows: list[dict], blocks: dict, tris: dict) -> None:
    """Full-model rules within the per-block budget: models taken largest first; a model whose triangles times its
    refs would carry any LOD4 block (or, for an LOD8 rule, any LOD8 block) past BUDGET gets no LOD (we make no LOD
    meshes). A rule is per model (a mesh mask), so a model's bases are taken or refused together."""
    by_model: dict[str, list[dict]] = {}
    for r in rows:
        if r["mech"] == "object":
            by_model.setdefault(r["model"].lower(), []).append(r)
    load = {4: collections.Counter(), 8: collections.Counter()}
    for model, rs in sorted(by_model.items(), key=lambda kv: -max(r["magnitude"] for r in kv[1])):
        t = tris.get(model)
        add = {lvl: collections.Counter() for lvl in (4, 8)}
        for r in rs:
            for lvl in (4, 8) if r["lod8"] else (4,):
                for k, v in blocks[r["source"]][lvl].items():
                    add[lvl][k] += v * (t or 0)
        over = [(lvl, k, load[lvl][k] + v) for lvl in add for k, v in add[lvl].items() if load[lvl][k] + v > BUDGET[lvl]]
        if t is None or over:
            why = ("its full model cannot be read" if t is None else
                   f"its full model ({t} triangles) would carry LOD{over[0][0]} block {over[0][1]} to {over[0][2]} triangles, "
                   f"past Tamriel's {BUDGET[over[0][0]]}: no LOD (no LOD mesh of the shape exists, and we make none)")
            for r in rs:
                r["mech"], r["why"], r["lod8"] = "none", why, False
            continue
        for lvl in add:
            load[lvl].update(add[lvl])
    for r in rows:
        if r["mech"] == "object":
            r["block_peak"] = {lvl: max((load[lvl][k] for k in blocks[r["source"]][lvl]), default=0) for lvl in (4, 8)}


def build(plugin: Path, extra: Path | None = None, read=None) -> dict:
    bases = json.loads((plugin / "refs" / "flora" / "bases.json").read_text())
    n, cls, blocks = refs_per_base(plugin)
    own = own_lod_models(extra)
    read = read or resolver()
    rows, tris = [], {}
    for b in bases["bases"]:
        mech, why = classify(b, n[b["ref"]], cls.get(b["ref"]), own)
        o = b["obnd"]
        model = b["model"].replace("/", "\\").lower()
        lm = None
        if mech == "object":
            lm = lod_model(model, read)
            if lm:
                mech, why = "own", f"a LOD model of the same shape, {lm} (DynDOLOD's catch-all rule finds it)"
            elif model not in tris:
                tris[model] = triangles(model, read)
        rows.append({"edid": our_edid(b), "plugin": "ArgoniaNewWorld.esm" if b["copied"] else b["plugin"],
                     "key": None if b["copied"] else b["key"],  # a master's own form key; ours is read from the ESM
                     "source": b["ref"], "sig": b["sig"], "cls": cls.get(b["ref"]), "refs": n[b["ref"]],
                     "magnitude": round(math.dist(o[:3], o[3:])), "model": b["model"], "mech": mech, "why": why,
                     "triangles": tris.get(model), "lod_model": lm,
                     "lod8": mech == "object" and cls.get(b["ref"]) in LOD8_CLASSES})
    budget(rows, blocks, tris)
    trees = [r for r in rows if r["mech"] == "tree"]
    if len(trees) > BILLBOARD_CAP:  # the atlas holds 256: the most-placed keep theirs
        trees.sort(key=lambda r: -r["refs"])
        for r in trees[BILLBOARD_CAP:]:
            r["mech"], r["why"] = "none", f"past the {BILLBOARD_CAP}-billboard atlas (fewer refs than the {BILLBOARD_CAP} kept)"
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
