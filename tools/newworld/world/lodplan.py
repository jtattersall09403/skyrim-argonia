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
    BUDGET, the triangles Tamriel's own object LOD carries per block; past it the model is heavy: it gets a derived
    LOD model (lodmodels.py: <model>_lod_0.nif, drawn at LOD4 by a rule naming it) with a triangle target that
    keeps every block within BUDGET, and none when no such model could be made. Skyrim's own None families
    (RockL/M/S, rock piles) and rocks under 1,500 units get none.
  - small things get no LOD in Skyrim (grass, ground cover, herbs, ferns, small rocks: DynDOLOD's Medium preset
    rules \\rockl, \\rockm, \\rockpile None): they are drawn only inside the loaded cells, fading by the ini's
    fLODFadeOutMultObjects; nothing here changes that.

    python -m tools.newworld.world.lodplan build [--plugin out/newworld/plugin] [--lodmodels <manifest.json>]
        -> <plugin>/map/lodplan.json   per placed base: mechanism (tree, object, lodmodel, own, none) and why, with
           counts, and "lod_targets": the triangle target of each heavy model's LOD model (lodmodels.py reads it;
           a model the manifest holds at its target is planned "lodmodel")
    python -m tools.newworld.world.lodplan preflight [--plugin ...] [--lodmodels ...]
        before a LOD run: the plan against the world's build, the plan files and the profile; a FAULT line each
    python -m tools.newworld.world.lodplan coverage <lod logs dir> [--plugin ...]
        the last DynDOLOD run's read-back: per base, what it actually got, against the plan (exit 1 on a large base
        planned for LOD that got none, or a rule that matched nothing); writes <lod logs dir>/coverage.json

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
OWN_LOD = Path(__file__).with_name("lod_models.json")  # models DynDOLOD found LOD models for (measured; coverage names any it lacks)
# A derived LOD model's triangles: the share of the full model's that Skyrim's own level-0 LOD models keep (median
# of the pairs in Skyrim - Meshes, 2026-11-11: 0.137; their triangles 123 to 741), never under LOD_MIN.
LOD_RATIO, LOD_MIN, LOD_MAX = 0.137, 12, 741
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


def own_lod_models() -> set[str]:
    return {m.lower() for m in json.loads(OWN_LOD.read_text())["models"]}


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


def budget(rows: list[dict], blocks: dict, tris: dict) -> dict:
    """Full-model rules within the per-block budget: models taken largest first; a model whose triangles times its
    refs would carry any LOD4 block (or, for an LOD8 rule, any LOD8 block) past BUDGET is heavy and gets no rule.
    A rule is per model (a mesh mask), so a model's bases are taken or refused together. Returns the triangles the
    accepted rules put in each block, {level: Counter}."""
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
                   f"past Tamriel's {BUDGET[over[0][0]]}: no LOD without a LOD model of the shape")
            for r in rs:
                r["mech"], r["why"], r["lod8"], r["heavy"] = "none", why, False, t is not None
            continue
        for lvl in add:
            load[lvl].update(add[lvl])
    for r in rows:
        if r["mech"] == "object":
            r["block_peak"] = {lvl: max((load[lvl][k] for k in blocks[r["source"]][lvl]), default=0) for lvl in (4, 8)}
    return load


def lod_targets(rows: list[dict], blocks: dict, load: dict) -> dict[str, int]:
    """The triangle target of each heavy model's LOD model: Skyrim's own share of the full model (LOD_RATIO, at most
    LOD_MAX), lowered where the model's refs are dense so that every LOD4 block stays within BUDGET beside the
    full-model rules; a model that would need fewer than LOD_MIN triangles gets no target (and so no LOD)."""
    refs: dict[str, collections.Counter] = {}
    t0: dict[str, int] = {}
    for r in rows:
        if r.get("heavy"):
            m = r["model"].replace("/", "\\").lower()
            refs.setdefault(m, collections.Counter()).update(blocks[r["source"]][4])
            t0[m] = max(LOD_MIN, min(LOD_MAX, round(r["triangles"] * LOD_RATIO), r["triangles"]))
    want = collections.Counter()
    for m, c in refs.items():
        for k, v in c.items():
            want[k] += v * t0[m]
    factor = {m: 1.0 for m in refs}
    for k, v in want.items():
        room = BUDGET[4] - load[4][k]
        if v > room:
            for m, c in refs.items():
                if k in c:
                    factor[m] = min(factor[m], max(room, 0) / v)
    out = {m: int(t0[m] * factor[m]) for m in refs}
    return {m: t for m, t in sorted(out.items()) if t >= LOD_MIN}


def build_rows(plugin: Path, read=None, lodmodels: Path | None = None) -> list[dict]:
    return _plan(plugin, read, lodmodels)[0]


def build(plugin: Path, read=None, lodmodels: Path | None = None) -> dict:
    rows, targets, bases = _plan(plugin, read, lodmodels)
    tally = collections.defaultdict(lambda: [0, 0])
    for r in rows:
        tally[r["mech"]][0] += 1
        tally[r["mech"]][1] += r["refs"]
    doc = {"build_id": bases["build_id"], "bases_key": bases["key"],
           "counts": {k: {"bases": v[0], "refs": v[1]} for k, v in sorted(tally.items())}, "lod_targets": targets,
           "bases": rows}
    d = plugin / "map"
    d.mkdir(parents=True, exist_ok=True)
    (d / "lodplan.json").write_text(json.dumps(doc, indent=1))
    return doc


def _plan(plugin: Path, read=None, lodmodels: Path | None = None) -> tuple[list[dict], dict, dict]:
    bases = json.loads((plugin / "refs" / "flora" / "bases.json").read_text())
    n, cls, blocks = refs_per_base(plugin)
    own = own_lod_models()
    lodmodels = lodmodels or plugin.parent / "lodmodels" / "manifest.json"
    read = read or resolver()
    rows, tris = [], {}
    for b in bases["bases"]:
        # a base with a texture repair is placed as our copy of it (NewWorld.cs forces the copy to carry the repair),
        # so the flag and the billboard belong to that copy, never to the master's record
        b = {**b, "copied": b["copied"] or bool(b.get("alt_textures"))}
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
    load = budget(rows, blocks, tris)
    targets = lod_targets(rows, blocks, load)
    made = json.loads(lodmodels.read_text())["models"] if lodmodels.exists() else {}
    for r in rows:
        m = r["model"].replace("/", "\\").lower()
        if not r.get("heavy"):
            continue
        if m not in targets:
            r["why"] += f"; its refs are too dense for a LOD model of {LOD_MIN} triangles or more"
        elif m in made and made[m]["target"] == targets[m] and made[m]["triangles"] <= targets[m]:
            r["mech"], r["lod_model"], r["lod_triangles"] = "lodmodel", made[m]["lod"], made[m]["triangles"]
            r["why"] = (f"heavy full model ({r['triangles']} triangles): its derived LOD model {made[m]['lod']} "
                        f"({made[m]['triangles']} triangles) at LOD4, by a rule naming it")
            for k, v in blocks[r["source"]][4].items():
                load[4][k] += v * made[m]["triangles"]
        else:
            r["why"] += f"; a LOD model of {targets[m]} triangles is owed (lodmodels.py build)"
    for r in rows:
        if r["mech"] == "lodmodel":
            r["block_peak"] = {4: max((load[4][k] for k in blocks[r["source"]][4]), default=0)}
            if r["block_peak"][4] > BUDGET[4]:
                raise ValueError(f"{r['edid']}: LOD4 block at {r['block_peak'][4]} triangles with its LOD model, past {BUDGET[4]}")
    trees = [r for r in rows if r["mech"] == "tree"]
    if len(trees) > BILLBOARD_CAP:  # the atlas holds 256: the most-placed keep theirs
        trees.sort(key=lambda r: -r["refs"])
        for r in trees[BILLBOARD_CAP:]:
            r["mech"], r["why"] = "none", f"past the {BILLBOARD_CAP}-billboard atlas (fewer refs than the {BILLBOARD_CAP} kept)"
    return rows, targets, bases


def read_back(logs: Path) -> tuple[dict, dict, set[str]]:
    """The last DynDOLOD run: billboard found per base editor id, the LOD4 model of each object-LOD base editor id,
    and the full models whose LOD models it used (a model whose LOD rows name *_lod*.nif)."""
    bb = {}
    for ln in (logs / "DynDOLOD_SSE_BillboardsUsed_ArgoniaBlackMarsh.txt").read_text(errors="replace").splitlines():
        m = re.match(r"(\S+) \[(\w+):(\w+)\] Billboard (found|not found)", ln)
        if m:
            bb[m[1].lower()] = m[4] == "found"
    obj, own = {}, set()
    for ln in (logs / "LODGen_SSE_Export_ArgoniaBlackMarsh.txt").read_text(errors="replace").splitlines():
        p = ln.split("\t")
        if len(p) == 17:
            obj.setdefault(p[9].lower(), re.sub(r"^meshes\\", "", p[13].lower()))
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
        if r["mech"] in ("tree", "object", "lodmodel", "own") and have == "none" and r["refs"]:
            miss.append(f"{r['edid']} ({r['refs']} refs) planned {r['mech']}, got none")
        elif r["mech"] == "tree" and have != "tree":
            miss.append(f"{r['edid']} ({r['refs']} refs) planned a tree billboard, got {have}")
        elif r["mech"] == "lodmodel" and obj.get(e) != r["lod_model"].lower():
            miss.append(f"{r['edid']} ({r['refs']} refs) planned its LOD model {r['lod_model']}, drawn from {obj.get(e)}")
    # every rule of ours matched references: each model a rule names is the LOD4 model of some base
    rules = collections.Counter()
    for r in plan["bases"]:
        if r["mech"] in ("object", "lodmodel"):
            rules[r["model"].replace("/", "\\").lower()] += r["edid"].lower() in obj
    dead = sorted(m for m, v in rules.items() if not v)
    unlisted = sorted(own - own_lod_models() - {r["model"].replace("/", "\\").lower() for r in plan["bases"] if r["mech"] == "lodmodel"})
    (logs / "coverage.json").write_text(json.dumps({"own_lod_models": sorted(own), "planned_vs_got_refs":
                                                    {f"{a}->{b}": v for (a, b), v in sorted(got.items())}, "missing": miss,
                                                    "rules": len(rules), "rules_without_refs": dead,
                                                    "own_lod_models_not_listed": unlisted}, indent=1))
    for (a, b), v in sorted(got.items()):
        print(f"planned {a:8} got {b:6}: {v} refs")
    print(f"billboards: {sum(1 for r in plan['bases'] if r['mech'] == 'tree' and bb.get(r['edid'].lower()))} of "
          f"{sum(1 for r in plan['bases'] if r['mech'] == 'tree')} planned; rules that matched references: {len(rules) - len(dead)} of {len(rules)}")
    for m in dead:
        print("  FAIL rule matched no reference:", m)
    for m in unlisted:  # drawn from LOD models of its own, better than the plan's full model: the list is owed the row
        print(f"  note: DynDOLOD found LOD models of {m}; add it to {OWN_LOD.name}")
    print(f"large bases planned for LOD that got none: {len(miss)}")
    for m in miss[:40]:
        print("  FAIL", m)
    return 1 if miss or dead else 0


def preflight(plugin: Path, lodmodels: Path, read=None) -> int:
    """Before a LOD run: the plan is this world build's, the plan files hold what it plans, every planned model (and
    LOD model) is there to be read. One FAULT line per fault; exit 1 on any."""
    faults = []
    m = plugin / "map"
    plan = json.loads((m / "lodplan.json").read_text())
    for name, f in (("land", plugin / "land" / "manifest.json"), ("bases", plugin / "refs" / "flora" / "bases.json")):
        bid = json.loads(f.read_text())["build_id"]
        if bid != plan["build_id"]:
            faults.append(f"lodplan.json is of build {plan['build_id']}, the {name} of {bid} (lod.sh map)")
    if json.dumps(build_rows(plugin, read, lodmodels), sort_keys=True) != json.dumps(plan["bases"], sort_keys=True):
        faults.append("lodplan.json is not what the plan builds to now (refs, bases or LOD models changed: lod.sh map)")
    rows = plan["bases"]
    trees = [r for r in rows if r["mech"] == "tree"]
    bill = [ln for f in m.glob("DynDOLOD_SSE_TexGen_Billboards_*.txt") for ln in f.read_text().splitlines() if ln.strip()]
    if len(bill) != len(trees) or {ln.rsplit(";", 1)[1].split(",")[0] for ln in bill} != {r["edid"] for r in trees}:
        faults.append(f"the billboard files list {len(bill)} bases, the plan {len(trees)} trees (lod.sh map)")
    if len(trees) > BILLBOARD_CAP:
        faults.append(f"{len(trees)} billboards planned, over the atlas's {BILLBOARD_CAP}")
    ini = m / "DynDOLOD_SSE_argonianewworldesm.ini"
    rules = [ln.split("=", 1)[1] for ln in ini.read_text().splitlines() if ln.startswith("LODGen")] if ini.exists() else []
    want = {r["model"].replace("/", "\\").lower(): r for r in rows if r["mech"] in ("object", "lodmodel")}
    if {x.split(",")[0] for x in rules} != set(want):
        faults.append(f"the rule file names {len(rules)} models, the plan {len(want)} (lod.sh map)")
    for x in rules:
        r = want.get(x.split(",")[0])
        if r and (x.split(",")[1] == "Level0") != (r["mech"] == "lodmodel"):
            faults.append(f"the rule of {x.split(',')[0]} does not draw what the plan says ({r['mech']})")
    read = read or resolver()
    made = json.loads(lodmodels.read_text())["models"] if lodmodels.exists() else {}
    names = collections.defaultdict(set)
    for r in rows:
        if r["refs"]:
            names[r["model"].replace("/", "\\").lower().rsplit("\\", 1)[-1]].add(r["model"].replace("/", "\\").lower())
    for r in rows:
        if r["mech"] in ("tree", "object", "lodmodel", "own") and read(r["model"]) is None:
            faults.append(f"{r['edid']}: its model {r['model']} is not in the profile")
        if r["mech"] == "lodmodel":
            k = r["model"].replace("/", "\\").lower()
            f = lodmodels.parent / "meshes" / Path(*r["lod_model"].split("\\"))
            if k not in made or not f.exists():
                faults.append(f"{r['edid']}: its LOD model {r['lod_model']} is not built (lod.sh models)")
            if len(names[k.rsplit("\\", 1)[-1]]) > 1:  # DynDOLOD pairs a LOD model with a full model by file name
                faults.append(f"{r['edid']}: another placed model shares the file name of {k}; its LOD model would serve both")
    for f in faults:
        print("FAULT", f)
    print(f"plan: {len(trees)} billboards, {len(rules)} rules ({sum(1 for r in want.values() if r['mech'] == 'lodmodel')} LOD models), "
          f"{sum(1 for r in rows if r['mech'] == 'own')} bases with LOD models of their own; {len(faults)} faults")
    return 1 if faults else 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=("build", "coverage", "preflight"))
    ap.add_argument("logs", nargs="?")
    ap.add_argument("--plugin", default=str(REPO / "out/newworld/plugin"))
    ap.add_argument("--lodmodels", default=None, help="the derived LOD models' manifest (default: beside the plugin folder)")
    a = ap.parse_args(argv)
    lm = Path(a.lodmodels) if a.lodmodels else Path(a.plugin).parent / "lodmodels" / "manifest.json"
    if a.cmd == "build":
        doc = build(Path(a.plugin), lodmodels=lm)
        print(json.dumps(doc["counts"]))
        return 0
    if a.cmd == "preflight":
        return preflight(Path(a.plugin), lm)
    return coverage(Path(a.plugin), Path(a.logs))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
