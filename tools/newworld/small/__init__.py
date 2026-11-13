"""The small test world: one block of the real build, run through the rebuild's own stage code in minutes.

    tools/newworld/rebuild.sh small [plan|run] [--from <a tree's out/newworld>] [--to STAGE] [--force STAGE]
    tools/newworld/rebuild.sh small play        # the block's world file under the play machine's names

BLOCK is a 16 by 16 cell block of the real world, chosen to hold one of each thing a stage has a rule for (HOLDS).
`cut` crops what the stages read of the real build (the heightmap, the scope, the water classification) to the block
under out/newworld-small/; the stages after the terrain then run on it: the same commands, the same checks, each
tool's module paths under out/newworld pointed at out/newworld-small (`tool`). Nothing under out/newworld is
written: the run ends by proving it. Each stage keeps its stamp under out/newworld-small/rebuild/, as the rebuild's
stages do, so a stage whose inputs stand is not run again, and `rebuild.sh run` reads the stamps: a stale stage of
the real world whose code is not the code of its last green small run is refused (`unproven`).

`play` writes out/newworld-small/play/: the block's world file as ArgoniaSmallWorld.esm with the worldspace
ArgoniaSmallWorld, its .lod and its LOD plan files under that plugin's name, for `infra/gpu-box/lod.sh selftest`.

What the block cannot prove is the skill world-build's to say (section 5): memory and time at scale, the whole
province's connectivity, and every rule on ground the block does not hold.
"""
from __future__ import annotations

import builtins
import dataclasses
import hashlib
import importlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
REAL = REPO / "out" / "newworld"
REAL_DB = REPO / "newworld/story/data/db"
ROOT = REPO / "out" / "newworld-small"
PLUGIN = "out/newworld-small/plugin"
BLOCK = (4, -134, 16, 16)        # south-west cell x, y; cells east, cells north
# What the block was chosen to hold; `cut` and the `holds` check prove each on every run, so a world that changes
# under the block says so instead of testing less.
HOLDS = ("three regions (valley-of-storms, chixathe-mesa, arnesian-jungle) and the seams between them; still water "
         "(green marsh) beside flowing water (a river and streams, several headings); forest with TREE bases, static "
         "trees flagged for tree LOD and our copies of other plugins' trees (a billboard of their own); rocky upland with rule-matched "
         "rocks, cliffs with LOD models of their own and a cliff drawn from a derived LOD model; a road with its "
         "dressing and four junctions; the pad of a place at the water (Tenmal)")
# what the block's own LOD plan must hold of each mechanism (lodplan.json counts: bases), or the LOD selftest tests less
PLAN_HOLDS = {"tree": 50, "own": 5, "object": 3, "lodmodel": 1, "none": 50}
START_PLACE = "tenmal"           # the block's place: the start marker's anchor here (the world's own is far outside)
# what a tool holds of the whole province, set to the block's while it runs here: the start marker's place, and the
# walk checks' anchors (each a spot of the province: none lies in the block)
PATCHES = {"START_PLACE": START_PLACE, "WALK": []}
PLAY_ESM, PLAY_WORLD = "ArgoniaSmallWorld.esm", "ArgoniaSmallWorld"     # the world's name, letter for letter as long
REAL_ESM, REAL_WORLD = "ArgoniaNewWorld.esm", "ArgoniaBlackMarsh"
# the rebuild's stages that run on the block, and the read-back's groups that judge a block's file
STAGES = ("tools", "land", "landcover", "cells", "place", "edits", "paint", "mist", "navmesh", "map", "ecology", "dressing", "esm", "readback")
# the block's own edits of single placed things (the province's name cells the block does not hold): a file beside
# the block, absent until a test of the edits writes rows to it (`small tool tools.newworld.place edit ... --edits <it>`)
EDITS = "out/newworld-small/placed_edits.jsonl"
READBACK = "plugin,land,textures,water,refs,ecology,mist,navmesh,music,location"
# the read-back's rows that count the whole province, by the start of their requirement, each with why
READBACK_OFF = (
    ("water kinds against the accepted classification", "the province's accepted classification"),
    ("blackwater-swamp: its cells read as", "the block holds three cells of it"),
    ("low mist over", "a density over the province's marshes: the block holds a dozen marsh cells"),
    ("low mist graded", "a rank over the province's atmosphere classes"),
    ("stronger mist", "a share over the province's swamp and marsh"),
    ("NAVM on every non-margin land cell", "the navmesh keeps one cell inside the grid's edge: the province's margin, the block's own land"),
    ("settlement-pair paths", "counts the province's twenty pairs"),
)
# checks whose rows judge the whole province: named here, each with why, and left out of the block's run
NOT_ON_A_BLOCK = {
    "landings": "every place of the province has its landing: the block holds one place",
    "relief": "regions read apart across the province; the land reaches past the picture",
    "atmosphere": "the records' spec is the world's own: the block reads the real build's",
    "height-fog": "it stages the mod stack",
    "upload": "nothing of the block is kept in the bucket",
}
SAMPLES = 32


def _rb():
    from tools.newworld import rebuild
    return rebuild


def source(given: str | None = None) -> Path:
    """The real build to cut from: the one named, this tree's, or (in a worktree) the main tree's, read only."""
    if given:
        return Path(given).resolve()
    if (REAL / "terrain/build.json").exists():
        return REAL
    cd = subprocess.run(["git", "-C", str(REPO), "rev-parse", "--path-format=absolute", "--git-common-dir"],
                        capture_output=True, text=True).stdout.strip()
    return Path(cd).parent / "out" / "newworld"


def _atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(data)
    os.replace(tmp, path)


def in_block(cx: int, cy: int, block=BLOCK) -> bool:
    return block[0] <= cx < block[0] + block[2] and block[1] <= cy < block[1] + block[3]


def crop(build: dict, block=BLOCK) -> tuple[dict, slice, slice]:
    """The block's build.json and the heightmap's rows and columns it keeps (one frame: world units, the origin moved)."""
    cell = 4096
    ox, oy = block[0] * cell, (block[1] + block[3]) * cell      # the block's north-west corner
    step = build["sample_units"]
    c0, r0 = int((ox - build["origin_world_x"]) / step), int((build["origin_world_y"] - oy) / step)
    w, h = block[2] * SAMPLES + 1, block[3] * SAMPLES + 1
    if c0 < 0 or r0 < 0 or c0 + w > build["width"] or r0 + h > build["height"]:
        raise ValueError(f"block {block} lies outside build {build['id']}")
    out = dict(build, id=f"{build['id']}-small", width=w, height=h, origin_world_x=float(ox), origin_world_y=float(oy),
               files="out/newworld-small/terrain/", cut_from=build["id"], block=list(block))
    return out, slice(r0, r0 + h), slice(c0, c0 + w)


def cut(src: Path, dst: Path = ROOT, block=BLOCK) -> dict:
    """Crop what the stages after the terrain read of the real build to the block. Whole files are written, the
    record last: a stopped cut is cut again."""
    import numpy as np
    src, dst = Path(src), Path(dst)
    if dst.resolve() == src.resolve():
        raise ValueError("the small world is never cut into the build it is cut from")
    build = json.loads((src / "terrain/build.json").read_text())
    small, rows, cols = crop(build, block)
    h = np.ascontiguousarray(np.load(src / "terrain/heightmap.npy", mmap_mode="r")[rows, cols])
    (dst / "terrain").mkdir(parents=True, exist_ok=True)
    tmp = dst / "terrain/heightmap.tmp.npy"
    np.save(tmp, h)
    os.replace(tmp, dst / "terrain/heightmap.npy")
    small["sha256"] = hashlib.sha256((dst / "terrain/heightmap.npy").read_bytes()).hexdigest()
    _atomic(dst / "terrain/build.json", json.dumps(small, indent=1).encode())
    # by cell: the block's rows alone (the scope and its margin count map cells, two of the world's cells a side)
    for name in ("scope_cells.json", "margin_cells.json"):
        _atomic(dst / name, json.dumps([c for c in json.loads((src / name).read_text())
                                        if in_block(2 * c[0], 2 * c[1], block) and in_block(2 * c[0] + 1, 2 * c[1] + 1, block)]).encode())
    flow = [r for r in json.loads((src / "water_flow_cells.json").read_text()) if in_block(*r["cell"], block)]
    _atomic(dst / "water_flow_cells.json", json.dumps(flow).encode())
    # in the picture's own pixels, or the world's own tables: whole
    for name in ("cell_region.json", "water_classified.json", "water_classified.png", "terrain/places_terrain.json",
                 "research/flora_catalogue.json", "research/hollow_extra.json", "plugin/atmosphere.json"):
        (dst / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src / name, dst / (name + ".tmp"))
        os.replace(dst / (name + ".tmp"), dst / name)
    # the world's tables whole, but the places: the block's own alone (a stage that walks every place walks these)
    (dst / "db").mkdir(exist_ok=True)
    kept = []
    for t in sorted(REAL_DB.glob("*.jsonl")):
        text = t.read_text(encoding="utf-8")
        if t.name == "place.jsonl":
            rows = [ln for ln in text.splitlines() if ln.strip()]
            rows = [ln for ln in rows if in_block(int(json.loads(ln)["world_x"] // 4096), int(json.loads(ln)["world_y"] // 4096), block)]
            kept = [json.loads(ln)["id"] for ln in rows]
            text = "".join(ln + "\n" for ln in rows)
        _atomic(dst / "db" / t.name, text.encode("utf-8"))
    rec = {"block": list(block), "from": build["id"], "places": kept, "build": small["id"], "sha256": small["sha256"],
           "flow_cells": len(flow), "dry_share": round(float((h > build["water_level_units"]).mean()), 3)}
    _atomic(dst / "cut.json", json.dumps(rec, indent=1).encode())
    print(f"cut: block {block} of {build['id']} -> {dst} ({h.shape[1]} x {h.shape[0]} samples, "
          f"{rec['dry_share']:.0%} above the water, {len(flow)} cells with flow)")
    return rec


# ---- a stage tool on the block ------------------------------------------------------------------------------------

def reroot(root: Path = ROOT, real: Path = REAL, db: Path = REAL_DB) -> int:
    """Every path a loaded tool keeps under out/newworld, pointed at the same place under the small world; the
    world's tables at the small world's own (the block's places); the start place at the block's."""
    n = 0
    for name, mod in list(sys.modules.items()):
        if mod is None or not name.startswith("tools.") or name.startswith("tools.newworld.small"):
            continue
        for attr, v in PATCHES.items():
            if attr in vars(mod) and (attr != "WALK" or name == "tools.newworld.teleports"):
                setattr(mod, attr, v)
        for attr, v in list(vars(mod).items()):
            if not isinstance(v, Path):
                continue
            for old, new in ((real, root), (db, root / "db")):
                if v == old or old in v.parents:
                    setattr(mod, attr, new / v.relative_to(old))
                    n += 1
    return n


def hook(root: Path = ROOT) -> None:
    """Re-root after every import that loads a module: a tool's paths are the small world's before its code reads them."""
    plain = builtins.__import__

    def imp(name, *a, **k):
        before = len(sys.modules)
        m = plain(name, *a, **k)
        if len(sys.modules) != before:
            reroot(root)
        return m
    builtins.__import__ = imp


def tool(argv: list[str]) -> int:
    """Run one stage tool's `main` on the small world: `tool <module> [its arguments]`."""
    hook()
    name = argv[0]
    mod = importlib.import_module(name)
    if not hasattr(mod, "main"):
        mod = importlib.import_module(name + ".__main__")
    from tools.newworld import keyed
    if mod is keyed and len(argv) > 1 and argv[1] in keyed.TOOLS:
        for m in keyed.TOOLS[argv[1]][::2]:
            importlib.import_module(m)
    reroot()
    return int(mod.main(argv[1:]) or 0)


# ---- the world file's steps, as world.sh makes them, on the small plugin folder --------------------------------------

def _dotnet(*a: str, tee: Path | None = None, quiet: bool = False) -> int:
    rb = _rb()
    p = subprocess.run(["dotnet", str(REPO / "out/tools/ArgoniaPlugin/ArgoniaPlugin.dll"), *a], cwd=REPO, env=rb._env(),
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if not quiet:
        sys.stdout.write(p.stdout)
    if tee is not None:
        import re
        tee.write_text(re.sub(r"(?m)^( *(PASS|FAIL)) in [0-9.]+ s$", r"\1", p.stdout))
    return p.returncode


def esm(step: str, root: Path = ROOT) -> int:
    rb = _rb()
    plug = root / "plugin"
    file, man = plug / REAL_ESM, plug / "land/manifest.json"
    data = str(rb.GAME)
    if step == "write":
        rc = _dotnet("newworld", "write", str(man), data, str(file))
        if rc == 0:
            key = json.loads(man.read_text())["key"]
            _atomic(plug / "ArgoniaNewWorld.json", json.dumps({"key": f"{key}:small", "esm": str(file),
                                                                "bytes": file.stat().st_size}, indent=1).encode())
        return rc
    if step == "map":
        if _dotnet("nwmap", "check", str(file), str(plug / "map"), quiet=True) != 0:
            rc = _dotnet("nwmap", "apply", str(file), str(plug / "map"), data)
            if rc:
                return rc
        rc = _dotnet("nwmap", "check", str(file), str(plug / "map"), tee=plug / "map-check.txt")
        return rc or _apply_again(file, plug, data)
    if step == "check":
        return _dotnet("newworld", "check", str(file), str(man), data, tee=plug / "check.txt")
    raise ValueError(step)


def _apply_again(file: Path, plug: Path, data: str) -> int:
    """The map applied once more to a copy of the file writes the same bytes: the LOD's map step applies it again, and
    a file that moved would move every key and stamp read from it."""
    import hashlib
    import shutil
    import tempfile
    with tempfile.TemporaryDirectory(dir=plug.parent) as tmp:
        again, m = Path(tmp) / file.name, Path(tmp) / "map"
        shutil.copy(file, again)
        shutil.copytree(plug / "map", m)
        if _dotnet("nwmap", "apply", str(again), str(m), data, quiet=True) != 0:
            print("  FAIL the map could not be applied a second time")
            return 1
        same = hashlib.sha256(again.read_bytes()).digest() == hashlib.sha256(file.read_bytes()).digest()
    print("  the map applied again writes the same file: " + ("PASS" if same else "FAIL"))
    return 0 if same else 1


def readback(root: Path = ROOT) -> int:
    """The read-back's groups that judge a block's file, every row printed; red on a FAIL but for READBACK_OFF's rows."""
    out = root / "verify"
    for f in out.glob("report-only-*.json"):
        f.unlink()
    tool(["tools.newworld.verify", "--only", READBACK, "--plugin", str(root / "plugin"), "--out", str(out)])
    doc = json.loads(next(out.glob("report-only-*.json")).read_text())
    rows = doc["rows"] if isinstance(doc, dict) else doc
    off = [r for r in rows if any(r["requirement"].startswith(p) for p, _ in READBACK_OFF)]
    bad = [r for r in rows if r["result"] != "PASS" and r not in off]
    print(f"read-back on the block: {len(rows) - len(off)} rows judged, {len(bad)} FAIL; {len(off)} rows count the province and are not judged:")
    for p, why in READBACK_OFF:
        print(f"  not judged: {p} ... ({why})")
    for r in bad:
        print(f"  FAIL {r['area']}: {r['requirement']} = {r['value']} {r['detail']}"[:300])
    return 1 if bad or not rows else 0


def plan_holds(root: Path = ROOT) -> int:
    plan = json.loads((root / "plugin/map/lodplan.json").read_text())
    bad = 0
    lm = root / "lodmodels/manifest.json"
    built = len(json.loads(lm.read_text()).get("models") or {}) if lm.exists() else 0
    for mech, least in PLAN_HOLDS.items():
        n = (plan["counts"].get(mech) or {}).get("bases", 0)
        if mech == "lodmodel" and built < least:  # the block places no base whose LOD model builds: every built one
            least = built                         # must still reach the plan, and the floor returns with one
            print(f"  NOTE the block places {built} base(s) whose LOD model builds; the lodmodel floor is {least}")
        bad += n < least
        print(f"  {'PASS' if n >= least else 'FAIL'} the block's LOD plan holds {mech}: {n} bases (at least {least})")
    static = sum(b["mech"] == "tree" and b["sig"] == "STAT" for b in plan["bases"])
    print(f"  {'PASS' if static else 'FAIL'} the block's LOD plan holds static trees flagged for tree LOD: {static} bases")
    return 1 if bad or not static else 0


# ---- the stages ---------------------------------------------------------------------------------------------------

def _spec(s: str) -> str:
    return s.replace(f"src:{_rb().EDITS_FILE}", f"out:{EDITS[4:]}").replace("out:newworld/", "out:newworld-small/")


def stages(src: Path) -> tuple:
    """The rebuild's own stages for the block: the same reads, commands and checks, under out/newworld-small."""
    rb = _rb()
    me = (rb.PY, "-m", "tools.newworld.small")

    def cmd(c: tuple) -> tuple:
        if "world.sh" in c[0]:
            return (*me, "esm", c[1])
        c = tuple(a.replace(rb.PLUGIN, PLUGIN).replace(rb.EDITS_FILE, EDITS) if isinstance(a, str) else a for a in c)
        if c[:3] == me:
            return c
        if c[0] == rb.PY and c[1] == "-m":
            extra = ("--terrain", "out/newworld-small/terrain") if c[2:4] == ("tools.newworld.keyed", "land") else ()
            return (*me, "tool", *c[2:], *extra)
        return c

    out = [rb.Stage("cut", f"the block {BLOCK} cut from the real build",
                    cmds=((*me, "cut", "--from", str(src)),), checks=((*me, "holds", "--from", str(src)),),
                    reads=("src:tools/newworld/small/*.py", "src:newworld/story/data/db/*.jsonl", f"ext:{src}/terrain/build.json", f"ext:{src}/terrain/heightmap.npy",
                           f"ext:{src}/water_classified.json", f"ext:{src}/water_flow_cells.json", f"ext:{src}/cell_region.json",
                           f"ext:{src}/scope_cells.json", f"ext:{src}/plugin/atmosphere.json"),
                    writes=("out:newworld-small/terrain/build.json", "out:newworld-small/cut.json", "out:newworld-small/scope_cells.json",
                            "out:newworld-small/margin_cells.json", "out:newworld-small/water_flow_cells.json",
                            "out:newworld-small/cell_region.json", "out:newworld-small/water_classified.json",
                            "out:newworld-small/water_classified.png", "out:newworld-small/terrain/places_terrain.json",
                            "out:newworld-small/research/flora_catalogue.json", "out:newworld-small/research/hollow_extra.json",
                            "out:newworld-small/plugin/atmosphere.json", "db:*"),
                    gb=0.5, minutes=0.1)]
    for s in rb.STAGES:
        if s.name not in STAGES:
            continue
        checks = s.checks
        if s.name == "readback":
            checks = ((*me, "readback"),)
        cmds, reads = tuple(c for c in s.cmds if c != rb.NAVMESH_SAMPLE), s.reads   # the block is itself the fast test
        if s.name == "map":       # the teleports' check judges every place of the province; the plan is the LOD's
            checks = ((*me, "plan-holds"),)   # whole one here: the derived LOD models made, and the plan that names them
            lm = "out/newworld-small/lodmodels"
            cmds += ((rb.PY, "-m", "tools.newworld.world.lodmodels", "build", "--plugin", PLUGIN, "--out", lm),
                     (rb.PY, "-m", "tools.newworld.world.lodplan", "build", "--plugin", PLUGIN, "--lodmodels", f"{lm}/manifest.json"))
            reads += ("src:tools/newworld/world/lodmodels.py", "src:tools/newworld/niflod/niflod.cpp")
        out.append(dataclasses.replace(
            s, cmds=tuple(cmd(c) for c in cmds), checks=tuple(cmd(c) for c in checks),
            reads=tuple(_spec(r) for r in reads),
            check_reads=tuple(_spec(r) for r in s.check_reads), writes=tuple(_spec(w) for w in s.writes),
            agree=tuple((_spec(a), _spec(b), how) for a, b, how in s.agree),
            after=tuple(a for a in s.after if a in STAGES), proof=()))
    return tuple(out)


def tree(src: Path | None = None):
    rb = _rb()
    return rb.Tree(stages=stages(src or source()), state=ROOT / "rebuild", db=ROOT / "db")


def untouched(since: float, real: Path = REAL) -> list[str]:
    """Files under the real build written since `since`: none, or the small run broke its one rule."""
    hits = []
    if real.exists():
        for d, _, files in os.walk(real):
            for f in files:
                p = os.path.join(d, f)
                try:
                    if os.lstat(p).st_mtime > since:
                        hits.append(os.path.relpath(p, real))
                except OSError:
                    pass
    return hits


def run(src: Path, to: str | None = None, force: tuple = (), plan_only: bool = False) -> int:
    rb = _rb()
    t = tree(src)
    for n in (*force, *([to] if to else [])):
        if n not in t.by_name:
            print(f"no stage {n!r}; stages: {', '.join(rb.order(t.stages))}", file=sys.stderr)
            return 2
    t.fresh = not plan_only
    rows = rb.plan(t, force)
    rb.print_plan(rows)
    rb.edit_notes(rows, ROOT / "plugin", REPO / EDITS, REPO / "newworld/places")
    if plan_only:
        return 0
    todo = [r["stage"] for r in rows if r["state"] != "current"]
    if to:
        d, keep, stack = rb.deps(t.stages), set(), [to]
        while stack:
            n = stack.pop()
            if n not in keep:
                keep.add(n)
                stack += d[n]
        todo = [n for n in todo if n in keep]
    if not (src / "terrain/build.json").exists():
        print(f"no real build to cut from at {src} (--from <a tree's out/newworld>)", file=sys.stderr)
        return 2
    held = rb.take_lock(t.state / "run.pid")
    if held:
        print(held, file=sys.stderr)
        return 2
    t0 = time.time()
    try:
        done = rb.Run(t, todo, max(rb.mem_available_gb() - rb.RESERVE_GB, 1.0), past_checks=True).go(force) if todo else {}
    finally:
        (t.state / "run.pid").unlink(missing_ok=True)
        t.save_cache()
    red = [n for n, r in done.items() if r["result"] == "red"]
    ran = [n for n, r in done.items() if r["result"] == "green"]
    wrote = untouched(t0)
    print("summary (the small world)")
    print(f"  stages run: {len(ran)} of {len(t.stages)} ({', '.join(ran) or 'none'}) in {time.time() - t0:.0f} s; "
          f"current: {len(t.stages) - len(todo)}; red: {', '.join(red) or 'none'}")
    print(f"  out/newworld untouched: {'yes' if not wrote else 'NO: ' + ', '.join(wrote[:5])}")
    for name, why in NOT_ON_A_BLOCK.items():
        print(f"  not run on a block: {name} ({why})")
    return 1 if red or wrote else 0


# ---- what a full run asks of the small world ------------------------------------------------------------------------

def code_specs(s) -> list[str]:
    """What of a stage's reads is code, script, plan or settings: the tracked files under tools/ and infra/."""
    return [r for r in (*s.reads, *s.check_reads) if r.startswith(("src:tools/", "src:infra/"))]


def unproven(real_tree, stale: list, state: Path | None = None) -> list[str]:
    """For each stale stage of the real world with a twin on the block: why its code is not the code of its last
    green small run, or nothing. Keyed by file content, so a stage whose code stands is not asked to be proven again."""
    state = Path(state or real_tree.repo / "out/newworld-small/rebuild")
    out = []
    for s in stale:
        if s.name not in STAGES:
            continue
        specs = code_specs(s)
        if not specs:
            continue
        try:
            st = json.loads((state / f"{s.name}.json").read_text())
        except (OSError, ValueError):
            st = {}
        if not st.get("key"):
            out.append(f"{s.name}: no green small run")
            continue
        was = st.get("inputs") or {}
        ch = [r.split(":", 1)[1] for r in specs if was.get(r) != real_tree.digest(r)]
        if ch:
            out.append(f"{s.name}: changed since its green small run: {', '.join(ch[:3])}" + (f" and {len(ch) - 3} more" if len(ch) > 3 else ""))
    return out


def real_names(src: Path, dst: Path) -> int:
    """The play machine's listing and logs of the small world, under the names the stage tools read them by."""
    dst.mkdir(parents=True, exist_ok=True)
    n = 0
    for f in sorted(p for p in Path(src).iterdir() if p.is_file()):
        data = f.read_bytes()
        for a, b in ((PLAY_ESM, REAL_ESM), (PLAY_WORLD, REAL_WORLD)):
            for x, y in ((a, b), (a.lower(), b.lower())):
                data = data.replace(x.encode(), y.encode())
        (dst / f.name.replace(PLAY_WORLD, REAL_WORLD)).write_bytes(data)
        n += 1
    return n


# ---- the play machine's names -------------------------------------------------------------------------------------

def rename_world(data: bytes, old: str = REAL_WORLD, new: str = PLAY_WORLD) -> bytes:
    """The world file with its worldspace's editor id changed to one of the same length: one EDID subrecord, in place."""
    if len(old) != len(new):
        raise ValueError("the new name must be as long as the old one")
    needle = b"EDID" + (len(old) + 1).to_bytes(2, "little") + old.encode() + b"\0"
    at = data.find(needle)
    if at < 0 or data.find(needle, at + 1) >= 0 or data[at - 24:at - 20] != b"WRLD":
        raise ValueError(f"the file does not hold exactly one uncompressed WRLD named {old}")
    return data[:at] + needle.replace(old.encode(), new.encode()) + data[at + len(needle):]


def play(root: Path = ROOT) -> Path:
    """out/newworld-small/play/plugin: the block's world file, .lod and LOD plan files under the play machine's names."""
    plug, out = root / "plugin", root / "play/plugin"
    try:
        green = bool(json.loads((root / "rebuild/esm.json").read_text()).get("key"))
    except (OSError, ValueError):
        green = False
    if not green:
        raise SystemExit("play: the small world's file is not green: tools/newworld/rebuild.sh small")
    if out.exists():
        shutil.rmtree(out)
    (out / "map/LODSettings").mkdir(parents=True)
    _atomic(out / PLAY_ESM, rename_world((plug / REAL_ESM).read_bytes()))
    shutil.copyfile(plug / f"map/LODSettings/{REAL_WORLD}.lod", out / f"map/LODSettings/{PLAY_WORLD}.lod")
    old, new = REAL_ESM.replace(".", "").lower(), PLAY_ESM.replace(".", "").lower()
    n = 0
    for f in sorted((plug / "map").glob("DynDOLOD_SSE_*")):
        text = f.read_bytes().replace(REAL_ESM.encode(), PLAY_ESM.encode()).replace(REAL_ESM.lower().encode(), PLAY_ESM.lower().encode())
        (out / "map" / f.name.replace(old, new)).write_bytes(text)
        n += 1
    for name in ("map/lodplan.json", "map/map.json", "land/manifest.json"):
        (out / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(plug / name, out / name)
    print(f"play: {out / PLAY_ESM} (worldspace {PLAY_WORLD}), its .lod and {n} LOD plan files")
    return out
