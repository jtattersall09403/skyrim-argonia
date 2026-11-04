#!/usr/bin/env python3
"""The record pipeline end to end (0.4 §a): `make plugin` and the gate's `plugin` part.

    pipeline.py plugin   scan the masters, index the pieces, write the intermediate JSON, generate Argonia.esm
                         (out/), serialise it with Spriggit into plugin/Argonia/; build the generated ground,
                         out/ArgoniaWorld.esm (decision 0031: never serialised; the terrain is rebuilt only when its
                         code or inputs change) and print its sha256
    pipeline.py ids      `plugin` without rebuilding out/ArgoniaWorld.esm (built only when missing): Argonia.esm, its
                         YAML and the FormIDs it allocates, over the master already there
    pipeline.py vegetation  (2.W4 §a and 1.15 §g's creatures; `plugin` and the gate's sample build already include it) out/ArgoniaWorld.esm with the province's vegetation REFRs spliced in
                         (tools/argonia_world/vegetation; its L1 checks and the spliced plugin's read-back)
    pipeline.py navmesh  the province's navmesh (tools/navmesh), then out/ArgoniaWorld.esm with its NAVM and NAVI
    pipeline.py plugin --plan  (`make plugin PLAN=1`) build nothing: print each stage's key and run/skip
    pipeline.py check    the FormID table append-only; every design piece resolved; regenerate twice into
                         out/check/{a,b}: identical ESM bytes and YAML trees, and equal to the committed
                         plugin/Argonia/ (else: run `make plugin`); the Spriggit round trip: plugin/Argonia/
                         and the generated ESM, both in canonical record order, are byte-identical;
                         ArgoniaWorld.esm's fixed cell sample rebuilt and its sha256 equal to the committed manifest;
                         the navmesh job on four cells: L1 green, its sha256 equal to tools/navmesh/sample-manifest.json

Spriggit's deserialiser writes a group's records in directory-listing order, which is the filesystem's and not
the content's; `canon` puts every group in the raw-FormID order the generator writes, so the round trip
compares content. Game data: $ARGONIA_GAME_ROOT/Data, else ~/games/skyrimse/Data (read-only, never in git).
"""
from __future__ import annotations

import filecmp
import json
import os
import shutil
import re
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "out"
YAML = ROOT / "plugin" / "Argonia"
PROJ = ROOT / "tools" / "ArgoniaGen"
GEN = PROJ / "bin" / "Release" / "net10.0" / "ArgoniaGen"
SPRIGGIT = ("-p", "Spriggit.Yaml", "-v", "0.41.0")  # pinned in infra/build-vm/toolchain.lock
HOME = Path.home()
ENV = dict(os.environ, DOTNET_ROOT=str(HOME / ".dotnet"), DOTNET_CLI_TELEMETRY_OPTOUT="1", DOTNET_NOLOGO="1",
           DOTNET_gcServer="0", DOTNET_GCHeapHardLimit="0xC0000000",  # workstation GC, 3 GB heap (memory guidance)
           PATH=f"{HOME / '.dotnet'}:{HOME / '.local/bin'}:{os.environ.get('PATH', '')}")
CAP = ["systemd-run", "--user", "--scope", "-q", "-p", "MemoryMax=3G"] if shutil.which("systemd-run") else []


# --- stages: each keyed by the inputs it reads (decision 0037), timed, and planned without running -----------------
STAGE_DIR = OUT / "stages"
TIMES: list[tuple[str, str, float, str]] = []  # (stage, run|skip, seconds, key12)


class stage:
    """`with stage(name, key) as st:` times a stage and records run/skip; st.run is False when `key` equals the key the
    stage last finished with (out/stages/<name>.key) and `outputs` all exist; key None always runs, never stored."""

    def __init__(self, name: str, key: str | None, *outputs: Path, force: bool = False):
        self.name, self.key, self.outputs = name, key, outputs
        f = STAGE_DIR / f"{name}.key"
        self.run = force or key is None or not (f.exists() and f.read_text() == key and all(o.exists() for o in outputs))

    def __enter__(self):
        import time
        self.t0 = time.monotonic()
        return self

    def __exit__(self, et, *_):
        import time
        dt = time.monotonic() - self.t0
        if et is None:
            if self.run and self.key is not None:
                STAGE_DIR.mkdir(parents=True, exist_ok=True)
                f = STAGE_DIR / f"{self.name}.key"  # atomic: an interrupt leaves the old key or the new, never half
                tmp = f.with_name(f"{f.name}.tmp-{os.getpid()}")
                tmp.write_text(self.key)
                tmp.replace(f)
            TIMES.append((self.name, "run" if self.run else "skip", dt, (self.key or "-")[:12]))
            print(f"plugin: stage {self.name:<11} {'run ' if self.run else 'skip'} {dt:8.1f} s  key {(self.key or '-')[:12]}",
                  flush=True)
        return False


def _stamp_holds(f: Path, key: str) -> bool:
    return f.exists() and f.read_text() == key


def stage_known(name: str, key: str | None, *outputs: Path) -> str:
    """The plan's verdict for a stage: run or skip, as `stage` would decide it."""
    return "run" if stage(name, key, *outputs).run else "skip"


def _files_key(*parts, files=(), tables=()) -> str:
    """A key over strings, file bytes (missing files by name) and world-db tables (their jsonl bytes, named by db.py)."""
    import hashlib
    h = hashlib.sha256()
    for x in parts:
        h.update(str(x).encode() + b"\0")
    for f in files:
        f = Path(f)
        h.update(f.name.encode() + (f.read_bytes() if f.is_file() else b"-") + b"\0")
    if tables:
        sys.path.insert(0, str(ROOT))
        from tools.argonia_world import db
        for t in tables:
            f = db.WORLD_ROOT / db.DB_DIR / f"{t}.jsonl"
            h.update(t.encode() + (f.read_bytes() if f.exists() else b"") + b"\0")
    return h.hexdigest()


def _stat_key(*files) -> str:
    """Large inputs (the binary, the masters) by size and time."""
    return ";".join(f"{Path(f).name}:{Path(f).stat().st_size}:{int(Path(f).stat().st_mtime)}" if Path(f).exists()
                    else Path(f).name for f in files)


def _gen_key() -> str:
    """The generator: its sources and project, what `dotnet build` compiles (not the binary: every build_tool
    rewrites its time, which moved the key with no input changed, 2026-11-04)."""
    return _files_key(files=sorted(PROJ.glob("*.cs")) + [PROJ / "ArgoniaGen.csproj"])


_MEMO: dict = {}


def _memo(f):
    """A stamp computed once per process (the nested stamps re-read the same tables: 79 s to 29 s for the plan);
    the inputs do not move inside one build. `_MEMO.clear()` forgets."""
    import functools

    @functools.wraps(f)
    def g(*a, **k):
        key = (f.__name__, a, tuple(sorted(k.items())))
        if key not in _MEMO:
            _MEMO[key] = f(*a, **k)
        return _MEMO[key]
    return g


def data_dir() -> Path:
    root = os.environ.get("ARGONIA_GAME_ROOT")
    d = Path(root) / "Data" if root else HOME / "games" / "skyrimse" / "Data"
    if not (d / "Skyrim.esm").exists():
        raise SystemExit(f"plugin: no Skyrim.esm under {d} (set ARGONIA_GAME_ROOT)")
    return d


def run(*cmd, capped=False, quiet=True):
    full = (CAP if capped else []) + [str(c) for c in cmd]
    r = subprocess.run(full, cwd=ROOT, env=ENV, capture_output=quiet, text=True, check=False)
    if r.returncode != 0:
        tail = ((r.stdout or "") + (r.stderr or ""))[-3000:] if quiet else ""
        raise SystemExit(f"plugin: failed: {' '.join(map(str, cmd))}\n{tail}")
    return r.stdout or ""


def build_tool():
    run("dotnet", "build", PROJ, "-c", "Release", "-nologo", "-v", "q", capped=True)


def scans(data: Path):
    """The vanilla scan and the piece index, remade only when the load order or a plugin changed."""
    sys.path.insert(0, str(ROOT))
    from tools.argonia_world.intermediate import load_order
    order = load_order(data)
    files = [data / p for p in order] + sorted(data.glob("*.bsa")) \
        + sorted((data / "argonia-mesh-lists").glob("*.txt")) + [GEN.with_suffix(".dll")]
    stamp = json.dumps([[f.name, f.stat().st_size, int(f.stat().st_mtime)] for f in files])
    sf = OUT / "scan.stamp"
    if sf.exists() and sf.read_text() == stamp and all((OUT / f).exists() for f in ("vanilla-scan.json", "pieces-index.json", "ltex-scan.json")):
        return
    plugins = ",".join(order)
    run(GEN, "quests", "--data", data, "--plugins", plugins, "--out", OUT / "vanilla-scan.json", capped=True)
    run(GEN, "index", "--data", data, "--plugins", plugins, "--out", OUT / "pieces-index.json", capped=True)
    run(GEN, "ltex", "--data", data, "--plugins", plugins, "--out", OUT / "ltex-scan.json", capped=True)
    sf.write_text(stamp)


NAV_PROVINCE = OUT / "navmesh" / "province"  # `make navmesh`'s build, which out/ArgoniaWorld.esm carries


def generate(data: Path, into: Path, frozen: bool, keyed: bool = False) -> tuple[Path, Path]:
    """intermediate -> ESM -> YAML, all under `into`; returns (esm, yaml dir). One province build at a time on
    the build VM (tools/argonia_world/province_lock.py)."""
    from tools.argonia_world.province_lock import province_lock
    with province_lock("plugin generate"):
        return _generate(data, into, frozen, keyed)


def _generate(data: Path, into: Path, frozen: bool, keyed: bool = False) -> tuple[Path, Path]:
    """keyed (`make plugin`): the records stage times itself, and the YAML is reserialised only when the ESM's bytes
    changed (the key is its sha256)."""
    into.mkdir(parents=True, exist_ok=True)
    inter, esm, yaml = into / "argonia.json", into / "Argonia.esm", into / "yaml"
    with stage("records", None):
        _records(data, inter, esm, frozen)
    with stage("yaml", sha256(esm) if keyed else None, yaml) as st:
        if st.run:
            shutil.rmtree(yaml, ignore_errors=True)
            run("spriggit", "serialize", "-i", esm, "-o", yaml, "-g", "SkyrimSE", *SPRIGGIT, capped=True)
    return esm, yaml


def _records(data: Path, inter: Path, esm: Path, frozen: bool) -> None:
    into = inter.parent
    run(sys.executable, "-m", "tools.argonia_world.intermediate", "--data", data, "--out", inter,
        "--frozen", "1" if frozen else "0")
    # Load doors on the navmesh (tools/navmesh/doors.py): the door cells' NAVMs with their door triangles, from the
    # province navmesh out/ArgoniaWorld.esm carries, for PlaceCells to write as overrides in Argonia.esm.
    ENV.pop("ARGONIA_NAV_DOORS", None)
    if (NAV_PROVINCE / "build.json").exists():
        run(sys.executable, "-m", "tools.navmesh", "doors", "overlay", "--nav", NAV_PROVINCE, "--intermediate", inter,
            "--out", into / "doors.json")
        ENV["ARGONIA_NAV_DOORS"] = str(into / "doors.json")
    else:
        print("plugin: WARNING no province navmesh (out/navmesh/province): Argonia.esm has no door triangles")
    run(GEN, "generate", "--in", inter, "--data", data, "--out", esm, capped=True)


# --- canonical record order -------------------------------------------------------------------------------
def canon(data: bytes) -> bytes:
    """The plugin with every group's entries in raw-FormID order; a record keeps its child group after it."""
    def entries(i: int, end: int) -> list[tuple[tuple, bytes]]:
        out = []
        while i < end:
            sig = data[i:i + 4]
            size = struct.unpack_from("<I", data, i + 4)[0]
            if sig == b"GRUP":
                body = b"".join(b for _, b in sorted(entries(i + 24, i + size)))
                blob = data[i:i + 4] + struct.pack("<I", 24 + len(body)) + data[i + 8:i + 24] + body
                gtype = struct.unpack_from("<i", data, i + 12)[0]
                if out and gtype in (1, 6, 7) and out[-1][0][0] == 0:  # a record's children follow it
                    k, b = out.pop()
                    out.append((k, b + blob))
                else:
                    label = data[i + 8:i + 12]
                    out.append(((1, gtype, label), blob))
                i += size
            else:
                fid = struct.unpack_from("<I", data, i + 12)[0]
                out.append(((0, fid), data[i:i + 24 + size]))
                i += 24 + size
        return out
    head = 24 + struct.unpack_from("<I", data, 4)[0]  # TES4 stays first
    top = entries(head, len(data))  # top groups keep their order (the game's group order)
    return data[:head] + b"".join(b for _, b in top)


def trees_equal(a: Path, b: Path) -> list[str]:
    fa = {p.relative_to(a).as_posix() for p in a.rglob("*") if p.is_file()}
    fb = {p.relative_to(b).as_posix() for p in b.rglob("*") if p.is_file()}
    diff = sorted(fa ^ fb)
    diff += sorted(f for f in fa & fb if not filecmp.cmp(a / f, b / f, shallow=False))
    return diff


# --- ArgoniaWorld.esm, the generated ground (decision 0031) ----------------------------------------------------
TERRAIN = ROOT / "tools" / "argonia_world" / "terrain"
WORLD_ESM = "ArgoniaWorld.esm"
# The world step holds every LAND, the water steps and the province NAVM in Mutagen's worldspace before the write:
# measured 2026-11-01 on the whole province (15,876 cells, navmesh in) 2.82 GB peak RSS in 2:05 (lane-1.15-pipeline);
# the old 1.5 GB heap limit was the "Out of memory". 4 GB heap under a 5 GB scope: about 1.8x headroom on the 15 GB VM.
WORLD_ENV = {"DOTNET_GCHeapHardLimit": "0x100000000", "DOTNET_GCConserveMemory": "9"}
WORLD_CAP = [*CAP[:-1], "MemoryMax=5G"] if CAP else []


@_memo
def _terrain_stamp(ground: bool = True) -> str:
    """The terrain's code, the world tables it reads and its inputs (by size and time): a change rebuilds.
    ground=False: the same without the generated ground's stamp, the land rows' shared key (row_key adds each row's
    window of the ground itself, so an edit in one region rebuilds only the rows it reaches)."""
    import hashlib
    sys.path.insert(0, str(ROOT))
    from tools.argonia_world import db
    from tools.argonia_world.terrain import vault
    from tools.argonia_world.terrain.landcover import table
    h = hashlib.sha256(repr(sorted(table(db.open()).items())).encode())
    for f in sorted(TERRAIN / n for n in ("__main__.py", "build.py", "grid.py", "landcover.py", "material.py", "png.py",
                                          "place_ground.py", "quantize.py", "world.py")):  # what the cell lines depend on
        h.update(f.name.encode() + f.read_bytes())
    roads = ROOT / "tools" / "argonia_world" / "routes" / "paint.py"  # 2.W3's road paint and the rows it reads
    h.update(roads.read_bytes() + repr(db.open().values(
        "SELECT group_concat(v, ';') FROM (SELECT route_id || surface_cover || flat_width_m || x_m || y_m v "
        "FROM road JOIN road_point USING (route_id) ORDER BY route_id, ord)")).encode())
    for n in sorted(vault.FILES):
        f = vault.data_dir() / n
        h.update(f"{n}:{f.stat().st_size}:{int(f.stat().st_mtime)}".encode() if f.exists() else n.encode())
    from tools.argonia_world.terrain import water_regrade
    h.update(water_regrade.stamp().encode())  # 2.W2's border regrade (rows in the world db)
    from tools.argonia_world.terrain import place_ground
    h.update(place_ground.stamp().encode())  # 0.4 §d: the built places' ground edits (build_ground rows)
    from tools.argonia_world.terrain import patches
    if ground:  # the places' pads and bowls (terrain_patch rows with a kind): in the stage's stamp, but not in the
        # rows' shared key, where row_key already hashes the patches reaching each row (patches.key): a pad edit
        # rebuilt all 262 rows (16 s each, 1508 s on 4 CPUs), now only the rows within its reach
        h.update(patches.stamp().encode())
        h.update(_ground_stamp().encode())  # 1.15: the generated ground the cells are built from
    h.update(_cover_key("terrain").encode())
    return h.hexdigest()


# every table generate.py and its helpers (water_field, cellwater, routes.shape/build/paint) read: the hydrology and
# route rows were missing (lane 1.15-r6-road-course, 2026-11-04 20:1x: the ground stood stale from 11-03 02:26 while
# `--plan` said skip, and lacked the r6 road shaping: 191,368 shaped samples against 246,222 fresh)
GROUND_TABLES = ("cell_water", "water_step", "region_relief", "land_region", "cell_region_run", "road", "road_point",
                 "route", "route_edge", "route_node", "travel_station", "hydrology_body", "hydrology_reach",
                 "hydrology_reach_point", "place", "place_terrain_requests")


@_memo
def _ground_stamp() -> str:
    """1.15's generated ground (terrain/generate.py): its code, the rows it reads and the prior's file."""
    import hashlib
    from tools.argonia_world import db
    h = hashlib.sha256()
    # the code: generate.py and every module it runs (water_field, cellwater, grid, routes.shape and its helpers)
    for f in sorted([*TERRAIN.glob("*.py"), TERRAIN.parent / "routes" / "shape.py"]):  # the import walk (_cover_key) adds the rest; routes/census.py and infra.py are not the ground's
        h.update(f.name.encode() + f.read_bytes())
    for t in GROUND_TABLES:
        f = db.WORLD_ROOT / db.DB_DIR / f"{t}.jsonl"  # the jsonl bytes, named by db.py
        h.update(t.encode() + (f.read_bytes() if f.exists() else b""))
    from tools.argonia_world.terrain.grid import data_root
    a = data_root() / "terrain" / "apron-source-near.npy"
    h.update(f"{a.stat().st_size}:{int(a.stat().st_mtime)}".encode() if a.exists() else b"no-apron")
    h.update(_cover_key("ground").encode())
    return h.hexdigest()


def ground() -> Path:
    """The terrain stage's first step: `terrain generate` (out/terrain/ground-f32.npy, role, cliff, entrance sites
    and the entrance_site rows) whenever its stamp is stale; the cell build reads that ground (grid.Sources)."""
    from tools.argonia_world.terrain.grid import generated_ground
    g = generated_ground()
    stamp = g.with_name("ground.stamp")
    now = _ground_stamp()
    if not (g.exists() and stamp.exists() and stamp.read_text() == now):
        run(sys.executable, "-m", "tools.argonia_world.terrain", "generate")  # its peak passes the 3 GB cap
        stamp.write_text(_ground_stamp())  # the rows generate wrote (entrance_site) are not in the stamp's tables
    return freeze_ground(g, _terrain_stamp()[:12])


FROZEN_FILES = ("ground-f32.npy", "cliff-u8.npy", "role-u8.npy", "entrance-sites.json", "generate.json")
FROZEN_KEEP = 2


def freeze_ground(g: Path, stamp12: str, keep: int = FROZEN_KEEP) -> Path:
    """Copy the ground this run decided to build from (and its cliff mask, roles, entrance sites and generate.json) to
    <terrain>/build/<stamp12>/ and return that ground-f32.npy: the land, vegetation and creature stages read the copy,
    so another tree's `terrain generate` over the shared out/terrain cannot change a build in progress. Derived
    output (out/ is ignored); copies older than the newest `keep` are deleted."""
    base = g.parent / "build"
    dest = base / stamp12
    tmp = base / f"{stamp12}.tmp-{os.getpid()}"
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)
    try:
        for n in FROZEN_FILES:
            if (g.parent / n).exists():
                shutil.copyfile(g.parent / n, tmp / n)
        shutil.rmtree(dest, ignore_errors=True)
        tmp.replace(dest)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    os.utime(dest)
    for old in sorted((d for d in base.iterdir() if d.is_dir() and ".tmp-" not in d.name),
                      key=lambda d: d.stat().st_mtime, reverse=True)[keep:]:
        shutil.rmtree(old, ignore_errors=True)
    return dest / g.name


WATER = ROOT / "tools" / "argonia_world" / "water"
WATER_OUT = OUT / "water"


@_memo
def _water_stamp() -> str:
    """The water plan's code (and the terrain's, whose ground it stands on), the hydrology and water tables, the
    frozen inputs: a change replans."""
    import hashlib
    h = hashlib.sha256(_terrain_stamp().encode())  # first: it puts the repo on sys.path
    from tools.argonia_world import db
    w = db.open()
    for f in sorted(WATER.glob("*.py")):
        h.update(f.name.encode() + f.read_bytes())
    for t in sorted(n for n in w.values("SELECT name FROM sqlite_master WHERE type = 'table'")
                    if n.startswith(("hydrology_", "water_", "cell_water"))):
        h.update(t.encode() + repr([tuple(r) for r in w.query(f'SELECT * FROM "{t}"')]).encode())
    for f in (OUT / "pieces-index.json",):
        h.update(f.read_bytes() if f.exists() else b"-")
    h.update(_cover_key("water").encode())
    return h.hexdigest()


def water(into: Path, sample: bool) -> Path:
    """The water stream (out/water: the solve's cell_water and water_step as XCLW/XCWT and step pieces, re-emitted
    only when its stamp changes; `water check` proves the solve is current), and for the sample its cells only."""
    WATER_OUT.mkdir(parents=True, exist_ok=True)
    stamp = WATER_OUT / "water.stamp"
    now = _water_stamp()
    if not (stamp.exists() and stamp.read_text() == now and (WATER_OUT / "cells.jsonl").exists()):
        # emit first: the check's placement rules judge the emitted stream (a check before the emit judged round 3's
        # pieces and types and failed round 4's first build, 2026-11-03 00:11)
        run(sys.executable, "-m", "tools.argonia_world.water", "emit", "--out", WATER_OUT, capped=True)
        run(sys.executable, "-m", "tools.argonia_world.water", "check", capped=True)
        stamp.write_text(now)
    if not sample:
        return WATER_OUT
    from tools.argonia_world.terrain.world import SAMPLE
    d = into / "water"
    d.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(WATER_OUT / "records.json", d / "records.json")
    keep = []
    for line in (WATER_OUT / "cells.jsonl").read_text().splitlines():
        c = json.loads(line)
        if any(x0 <= c["x"] <= x1 and y0 <= c["y"] <= y1 for x0, y0, x1, y1 in SAMPLE):
            keep.append(line + "\n")
    (d / "cells.jsonl").write_text("".join(keep))
    return d


VEG = ROOT / "tools" / "argonia_world" / "vegetation"
VEG_TABLES = ("land_region_object", "object_form", "vegetation_form", "vegetation_region_budget", "cell_region_run",
              "build_ref", "build_cell", "road", "road_point")


@_memo
def _veg_stamp() -> str:
    """The placement's code, the water plan's stamp (the ground and water it stands on), the navmesh inputs it
    reuses and the tables it reads: a change replaces."""
    import hashlib
    h = hashlib.sha256(_water_stamp().encode())
    from tools.argonia_world import db
    w = db.open()
    for f in sorted(VEG.glob("*.py")) + [ROOT / "tools" / "navmesh" / "inputs.py",
                                         ROOT / "tools" / "argonia_world" / "routes" / "paint.py"]:
        h.update(f.name.encode() + f.read_bytes())
    for t in VEG_TABLES:
        h.update(t.encode() + repr([tuple(r) for r in w.query(f'SELECT * FROM "{t}"')]).encode())
    h.update((WATER_OUT / "cells.jsonl").read_bytes())
    h.update(_cover_key("vegetation").encode())
    return h.hexdigest()


def vegetation(into: Path, sample: bool, frozen: Path | None = None) -> Path:
    """The province's vegetation (2.W4 §a: our placement from the region rules) with its L1 checks against the
    LAND under `into`: the sample's cells for the gate, else every cell (re-placed only when its stamp changes)."""
    d = into / "vegetation"
    stamp = d / "veg.stamp"
    now = None if sample else _veg_stamp()
    if sample or not (stamp.exists() and stamp.read_text() == now):
        stamp.unlink(missing_ok=True)
        run(sys.executable, "-m", "tools.argonia_world.vegetation", "build", "--out", d, "--water",
            WATER_OUT / "cells.jsonl", "--land", into / "land", *(["--sample"] if sample else []),
            *(["--ground", frozen] if frozen else []), capped=True)
        if now:
            stamp.write_text(now)
    return d


def _shared_tree(into: Path) -> Path | None:
    """The other tree whose out/ `into` really is, when this process runs in a worktree whose out/terrain links to it."""
    top = Path(subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=ROOT, capture_output=True, text=True,
                              check=False).stdout.strip() or ROOT).resolve()
    real = into.resolve()
    return real.parents[1] if real != into and not real.is_relative_to(top) else None


def _refuse_shared_rebuild(into: Path) -> None:
    """A worktree's out/terrain is the main tree's: a stale land stamp there is rebuilt in the main tree, never from
    here (four whole-province lands were emptied that way); ARGONIA_REBUILD_LAND=1 overrides."""
    if os.environ.get("ARGONIA_REBUILD_LAND") != "1" and _shared_tree(into):
        print("land is stale: run make plugin in the main tree", file=sys.stderr)
        raise SystemExit(2)


def world(data: Path, into: Path, sample: bool, nav: Path | None = None, veg: bool = True) -> Path:
    """terrain cells -> world.json -> ArgoniaWorld.esm under `into`; the full grid's cells are reused while the
    stamp holds. `nav`: a built navmesh (tools/navmesh) whose NAVM and NAVI go in too (`make navmesh`)."""
    into.mkdir(parents=True, exist_ok=True)
    with stage("ground", None if sample else _ground_stamp()) as st:
        st.run = not _stamp_holds(OUT / "terrain" / "ground.stamp", _ground_stamp())
        if st.run and not sample:
            _refuse_shared_rebuild(into)  # before the 140 s generate, not after it (r6-chain16, 20:1x: generated, then refused)
        frozen = ground()
    stamp = into / "terrain.stamp"
    now = _terrain_stamp()
    with stage("terrain", None if sample else now) as st:
        if sample or not (stamp.exists() and stamp.read_text() == now and (into / "land").is_dir()):
            if not sample:
                _refuse_shared_rebuild(into)
            run(sys.executable, "-m", "tools.argonia_world.terrain", "build", "--out", into, "--ground", frozen,
                "--stamp", now, *(["--sample"] if sample else ["--row-base", _terrain_stamp(ground=False)]), capped=True)
            if not sample:
                stamp.write_text(now)
        else:
            st.run = False
    with stage("world-json", None):  # cheap; its bytes key the ESM write (it reads the regions, creatures, rocks)
        run(sys.executable, "-m", "tools.argonia_world.terrain", "world", "--out", into,
            "--ground", frozen)
    with stage("water", None if sample else _water_stamp()) as st:
        st.run = not _stamp_holds(WATER_OUT / "water.stamp", _water_stamp())
        wdir = water(into, sample)
    esm = into / "esm" / WORLD_ESM
    esm.parent.mkdir(parents=True, exist_ok=True)
    final = esm.with_suffix(".final.esm")  # the last finished world (written, spliced) whose key esm-write.. holds
    wkey = None if sample else _world_key(data, into, wdir, nav, veg)
    with stage("world-esm", wkey, final) as st:
        if not st.run:
            shutil.copyfile(final, esm)
            return esm
        _world_esm(data, into, wdir, nav, esm, veg, sample, frozen)
        if not sample:
            shutil.copyfile(esm, final)
    return esm


def _world_key(data: Path, into: Path, wdir: Path, nav: Path | None, veg: bool) -> str:
    """ArgoniaWorld.esm's inputs: world.json, the land rows' stamp, the water stream, the navmesh build, the generator,
    the masters, and (with veg) the vegetation's and creatures' keys; equal keys write equal bytes."""
    return _files_key(_terrain_stamp(), _gen_key(), _stat_key(*sorted(data.glob("*.es[mp]"))), veg,
                      _veg_stamp() + _creature_key() if veg else "",
                      files=[into / "world.json", wdir / "cells.jsonl", wdir / "records.json",
                             *([nav / "build.json", nav / "terrain.stamp"] if nav else [])])


CREATURE_TABLES = ("build_cell", "build_person", "build_ref", "cell_region_run", "creature", "creature_band",
                   "creature_form", "creature_list", "creature_list_entry", "creature_region_class",
                   "creature_spawn_rule", "danger_band_combat", "danger_band_level", "encounter_zone", "land_region",
                   "land_region_weather", "layout", "npc", "npc_statblock", "place", "place_no_spawn", "socket")


@_memo
def _creature_key() -> str:
    """The spawn placement's code and the tables it reads (grep FROM in tools/argonia_world/creatures) over the
    vegetation it stands beside (whose stamp carries the ground and water)."""
    cr = ROOT / "tools" / "argonia_world" / "creatures"
    return _files_key(_veg_stamp(), files=sorted(cr.glob("*.py")) + [ROOT / "tools/argonia_world/regions/api.py"],
                      tables=CREATURE_TABLES) + _cover_key("creatures")


# The stamps' cover (lane 1.15-r6-stamp-walk, owner #42): a stamp that hashed a hand list of modules and tables
# went stale when road shaping was added to generate.py's imports and never to the list (the ground stood stale
# from 11-03 02:26 while `--plan` said skip). Each stage now also hashes the modules its entry imports (an AST walk
# within WALK_ROOTS, recursive, function-level imports included) and the tables named after FROM/JOIN in them.
WALK_ROOTS = ("tools/argonia_world", "tools/ArgoniaGen")
STAGE_ENTRY = {"ground": "tools.argonia_world.terrain.generate", "terrain": "tools.argonia_world.terrain.__main__",
               "water": "tools.argonia_world.water.__main__", "vegetation": "tools.argonia_world.vegetation.__main__",
               "creatures": "tools.argonia_world.creatures.__main__"}
# A top-level tools/argonia_world module the walk reaches is hashed but not descended: their function-level imports
# fan out to every generator (db's `check` imports checks.py; patches -> place_build -> intermediate -> quest_gen), so
# a descent covered 87 of the tree's modules for the ground; the stage packages (terrain, routes, water, ...) are
# walked through, which is where the incident's import (generate -> routes.shape) lay.


def _leaf(mod: str) -> bool:
    return mod.startswith("tools.argonia_world.") and mod.count(".") == 2
_SQL_NAME = re.compile(r'\b(?:FROM|JOIN)\s+"?([a-z_][a-z0-9_]*)')


def _mod_file(mod: str, root: Path = ROOT) -> Path | None:
    p = root.joinpath(*mod.split("."))
    for f in (p.with_suffix(".py"), p / "__init__.py"):
        if f.is_file() and any(str(f.relative_to(root)).startswith(r + "/") for r in WALK_ROOTS):
            return f
    return None


def walk_imports(entry: str, root: Path = ROOT) -> list[Path]:
    """Every module file the entry module imports, recursively (static: the AST's import lines, at any depth),
    within WALK_ROOTS, with the packages' __init__ files the imports run."""
    import ast
    seen: dict[Path, None] = {}
    todo = [entry]
    while todo:
        mod = todo.pop()
        f = _mod_file(mod, root)
        if f is None or f in seen:
            continue
        seen[f] = None
        if _leaf(mod):
            continue
        parts = mod.split(".")
        todo += [".".join(parts[:i]) for i in range(1, len(parts))]  # the packages above run their __init__
        pkg = parts if f.name == "__init__.py" else parts[:-1]
        for n in ast.walk(ast.parse(f.read_text(), str(f))):
            if isinstance(n, ast.Import):
                todo += [a.name for a in n.names]
            elif isinstance(n, ast.ImportFrom):
                base = ".".join(pkg[:len(pkg) - n.level + 1] + ([n.module] if n.module else [])) if n.level \
                    else (n.module or "")
                todo += [base, *(f"{base}.{a.name}" for a in n.names)]  # `from pkg import mod` names a module
    return sorted(seen)


def sql_tables(files, root: Path = ROOT) -> list[str]:
    """The world tables named after FROM or JOIN in the files' source, those the schema declares (db.SCHEMA)."""
    sys.path.insert(0, str(ROOT))
    from tools.argonia_world import db
    schema = set(re.findall(r"CREATE TABLE (?:IF NOT EXISTS )?\"?(\w+)", (root / db.SCHEMA).read_text()))
    return sorted({t for f in files for t in _SQL_NAME.findall(Path(f).read_text())} & schema)


def _hand(name: str) -> tuple[list[Path], tuple[str, ...]]:
    """The hand lists each stamp kept before the walk (still hashed: the union)."""
    rt = ROOT / "tools" / "argonia_world"
    return {"ground": ([*TERRAIN.glob("*.py"), rt / "routes" / "shape.py"], GROUND_TABLES),
            "terrain": ([TERRAIN / n for n in ("__main__.py", "build.py", "grid.py", "landcover.py", "material.py",
                                                "png.py", "place_ground.py", "quantize.py", "world.py")]
                        + [rt / "routes" / "paint.py"], ("road", "road_point")),
            "water": ([*WATER.glob("*.py")], ()),
            "vegetation": ([*VEG.glob("*.py"), ROOT / "tools/navmesh/inputs.py", rt / "routes/paint.py"], VEG_TABLES),
            "creatures": ([*(rt / "creatures").glob("*.py"), rt / "regions/api.py"], CREATURE_TABLES)}[name]


@_memo
def stage_cover(name: str) -> tuple[tuple[Path, ...], tuple[str, ...]]:
    """A stage's files and tables: the hand list unioned with the entry's import walk and its FROM/JOIN names."""
    files, tables = _hand(name)
    walked = walk_imports(STAGE_ENTRY[name])
    return tuple(sorted(set(files) | set(walked))), tuple(sorted(set(tables) | set(sql_tables(walked))))


def _cover_key(name: str) -> str:
    files, tables = stage_cover(name)
    return _files_key(name, *(str(f.relative_to(ROOT)) for f in files), files=files, tables=tables)


def stamps() -> int:
    """`pipeline.py stamps` (and `plugin --plan --verbose`): what each stage's stamp covers."""
    for name in STAGE_ENTRY:
        files, tables = stage_cover(name)
        print(f"stamp {name}: {len(files)} files, {len(tables)} tables (entry {STAGE_ENTRY[name]})")
        print("  files: " + " ".join(str(f.relative_to(ROOT)) for f in files))
        print("  tables: " + " ".join(tables))
    return 0


def _world_esm(data, into, wdir, nav, esm, veg, sample, frozen) -> None:
    full = WORLD_CAP + [str(GEN), "world", "--in", str(into / "world.json"), "--land", str(into / "land"),
                                   "--data", str(data), "--out", str(esm), "--water", str(wdir),
                                   *(["--navmesh", str(nav)] if nav else [])]
    with stage("esm-write", None):
        r = subprocess.run(full, cwd=ROOT, env=dict(ENV, **WORLD_ENV), capture_output=True, text=True, check=False)
    if r.returncode:
        raise SystemExit(f"plugin: ArgoniaWorld.esm failed\n{(r.stdout + r.stderr)[-3000:]}")
    if veg:  # 2.W4 §a, part of the build (the sample too: the gate's vegcheck): the REFRs spliced into each cell (VegetationRecords.cs)
        with stage("vegetation", None if sample else _veg_stamp()) as st:
            st.run = sample or not _stamp_holds(into / "vegetation" / "veg.stamp", _veg_stamp())
            vdir = vegetation(into, sample, frozen)
        tmp = esm.with_suffix(".veg.esm")
        run(*(CAP if CAP else []), GEN, "vegetation", "--in", esm, "--veg", vdir, "--out", tmp)
        tmp.replace(esm)
        print(run(sys.executable, "-m", "tools.argonia_world.vegetation", "readback", "--out", vdir, "--esm", esm,
                  "--gen", GEN).strip())
        print(run(sys.executable, "-m", "tools.argonia_world.vegetation", "textures", "overrides", "--esm", esm).strip())
    if veg:  # 1.15 §g, with the vegetation (both place on every cell): the spawn ACHRs and dens (CreatureRecords.cs)
        cdir = into / "creatures"
        with stage("creatures", None if sample else _creature_key(), cdir) as st:
            if st.run:
                run(sys.executable, "-m", "tools.argonia_world.creatures", "build", "--out", cdir, "--veg", vdir,
                    "--ground", frozen, *(["--sample"] if sample else []), capped=True)
        tmp = esm.with_suffix(".cr.esm")
        run(*(CAP if CAP else []), GEN, "creatures", "--in", esm, "--refs", cdir, "--out", tmp)
        tmp.replace(esm)
        print(run(sys.executable, "-m", "tools.argonia_world.creatures", "readback", "--out", cdir, "--esm", esm,
                  "--gen", GEN).strip())


def sha256(p: Path) -> str:
    import hashlib
    return hashlib.sha256(p.read_bytes()).hexdigest()


def master_world(data: Path, rebuild: bool) -> None:
    """out/ArgoniaWorld.esm, the master the place layers' cell overrides copy (PlaceCells.cs reads it from
    $ARGONIA_WORLD_ESM): rebuilt by `make plugin` (the terrain is reused while its stamp holds), built by the gate
    only when missing."""
    target = OUT / WORLD_ESM
    if rebuild or not target.exists():
        wesm = world(data, OUT / "terrain", sample=False, nav=province_navmesh())
        shutil.copyfile(wesm, target)
        print(f"plugin: out/{WORLD_ESM} ({wesm.stat().st_size} bytes) sha256 {sha256(wesm)}")
    ENV["ARGONIA_WORLD_ESM"] = str(target)


PLUGIN_STAMP = OUT / "plugin.stamp"
# What `plugin` reads (found from generate/world/scans): the world db and schema, the Spriggit YAML, data/, the
# generator's sources and the world/navmesh tooling; the binary, the province navmesh's build record, the terrain
# vault's inputs and the game's plugins/archives are folded in by size and time (too big to read).
HASH_DIRS = ("world", "plugin", "data", "tools/ArgoniaGen", "tools/argonia_world", "tools/navmesh")
HASH_SKIP = {"bin", "obj", "__pycache__", ".pytest_cache"}


def input_hash(data: Path | None = None) -> str:
    import hashlib
    h = hashlib.sha256()
    for d in HASH_DIRS:
        for dp, dn, fn in os.walk(ROOT / d):
            dn[:] = sorted(x for x in dn if x not in HASH_SKIP)
            for f in sorted(fn):
                if not f.endswith((".pyc", ".log")):
                    p = Path(dp) / f
                    h.update(str(p.relative_to(ROOT)).encode() + b"\0" + p.read_bytes() + b"\0")
    extra = [NAV_PROVINCE / "build.json"]  # the generator by its sources (tools/ArgoniaGen above), not its binary's time
    sys.path.insert(0, str(ROOT))
    from tools.argonia_world.terrain import vault
    extra += [vault.data_dir() / n for n in sorted(vault.FILES)]
    if data is not None:
        extra += sorted(data.glob("*.es[mpl]")) + sorted(data.glob("*.bsa"))
    for f in extra:
        st = f.stat() if f.exists() else None
        h.update(f"{f.name}:{st.st_size}:{int(st.st_mtime)}".encode() if st else f.name.encode())
    return h.hexdigest()


def skip_plugin(now: str, stamp: str | None, esms_exist: bool) -> bool:
    """The skip decision: the inputs hash to what the last successful build wrote, and both ESMs are there."""
    return esms_exist and stamp is not None and stamp.strip() == now


def plan() -> int:
    """`make plugin PLAN=1`: every stage's key against the key it last finished with; nothing is built. world-json,
    esm-write and records are unkeyed (cheap or keyed through world-esm); world-esm's key needs world.json, so the
    plan reads the one the last build left."""
    data = data_dir()
    sys.path.insert(0, str(ROOT))
    t = OUT / "terrain"
    nav = NAV_PROVINCE if (NAV_PROVINCE / "build.json").exists() else None
    own = [("ground", _ground_stamp(), t / "ground.stamp"), ("terrain", _terrain_stamp(), t / "terrain.stamp"),
           ("water", _water_stamp(), WATER_OUT / "water.stamp"),
           ("vegetation", _veg_stamp(), t / "vegetation" / "veg.stamp")]
    for name, key, f in own:  # these keep their own stamps (the cell rows and vegetation bands key per row inside)
        print(f"plan: {name:<11} {'skip' if _stamp_holds(f, key) else 'run '}  key {key[:12]}")
    for name, key, outs in (("creatures", _creature_key(), (t / "creatures",)),
                            ("world-esm", _world_key(data, t, WATER_OUT, nav, True),
                             (t / "esm" / f"{Path(WORLD_ESM).stem}.final.esm",))):
        print(f"plan: {name:<11} {stage_known(name, key, *outs)}  key {key[:12]}")
    if "--verbose" in sys.argv:
        stamps()
    for name in ("world-json", "esm-write", "records"):
        print(f"plan: {name:<11} run   (unkeyed: {'cheap' if name != 'esm-write' else 'runs when world-esm runs'})")
    y = OUT / "build" / "Argonia.esm"
    print(f"plan: {'yaml':<11} run when records' Argonia.esm sha256 differs from {(STAGE_DIR / 'yaml.key').read_text()[:12] if (STAGE_DIR / 'yaml.key').exists() else '-'}"
          f" (last {sha256(y)[:12] if y.exists() else '-'})")
    now = input_hash(data)
    st = PLUGIN_STAMP.read_text() if PLUGIN_STAMP.exists() else None
    print(f"plan: whole build {'skip' if skip_plugin(now, st, (OUT / 'Argonia.esm').exists() and (OUT / WORLD_ESM).exists()) else 'run'}  key {now[:12]}")
    return 0


def times_table() -> str:
    tot = sum(t for _, _, t, _ in TIMES)
    return "\n".join([f"plugin: times {n:<11} {r:<4} {t:8.1f} s  {k}" for n, r, t, k in TIMES] + [f"plugin: times total {tot:.1f} s"])


def plugin(force: bool = False, world: bool = True) -> int:
    """`world=False` (`pipeline.py ids`, `make plugin-ids`): Argonia.esm and its new FormIDs over the existing
    out/ArgoniaWorld.esm (built when missing), without the whole-province world build; the stamp is left unwritten."""
    data = data_dir()
    if not force and world:
        now = input_hash(data)
        stamp = PLUGIN_STAMP.read_text() if PLUGIN_STAMP.exists() else None
        if skip_plugin(now, stamp, (OUT / "Argonia.esm").exists() and (OUT / WORLD_ESM).exists()):
            print(f"plugin: unchanged ({now[:16]})")
            return 0
    PLUGIN_STAMP.unlink(missing_ok=True)
    TIMES.clear()
    with stage("tool", None):
        build_tool()
    with stage("scans", None):
        scans(data)
    master_world(data, rebuild=world)  # first: Argonia.esm's place cells override its cells
    esm, yaml = generate(data, OUT / "build", frozen=False, keyed=True)
    shutil.copyfile(esm, OUT / "Argonia.esm")
    with stage("yaml-copy", sha256(esm), YAML) as st:
        if st.run:
            shutil.rmtree(YAML, ignore_errors=True)
            shutil.copytree(yaml, YAML)
    with stage("round-trip", sha256(esm), OUT / "build" / "roundtrip.esm") as st:
        if st.run:  # plugin-check's round trip, here once per new Argonia.esm
            rt = OUT / "build" / "roundtrip.esm"
            run("spriggit", "deserialize", "-i", YAML, "-o", rt, *SPRIGGIT, capped=True)
            if canon(rt.read_bytes()) != canon(esm.read_bytes()):
                rt.unlink()
                raise SystemExit("plugin: round trip: plugin/Argonia/ deserialised is not byte-identical to Argonia.esm")
    print(times_table())
    from tools.argonia_world import forms_table; forms_table.write()  # the allocator may have added rows (1.1)
    n = sum(1 for _ in YAML.rglob("*.yaml"))
    print(f"plugin: out/Argonia.esm ({esm.stat().st_size} bytes), {n} YAML files in plugin/Argonia/")
    if world:
        PLUGIN_STAMP.write_text(input_hash(data))  # after success, over the tree the build left (the allocator's rows included)
    return 0


def check() -> int:
    root = os.environ.get("ARGONIA_GAME_ROOT")
    d = Path(root) / "Data" if root else HOME / "games" / "skyrimse" / "Data"
    if not (d / "Skyrim.esm").exists():
        print(f"plugin: SKIPPED, no Skyrim.esm under {d}: the build VM runs this part (the masters never enter git)")
        return 0
    data = data_dir()
    errs: list[str] = []
    r = subprocess.run([sys.executable, "-m", "tools.argonia_world.formids", "check"], cwd=ROOT, check=False, capture_output=True, text=True)
    if r.returncode:
        errs.append("formids: " + r.stdout.strip())
    build_tool()
    scans(data)
    master_world(data, rebuild=False)
    a_esm, a_yaml = generate(data, OUT / "check" / "a", frozen=True)
    built = sorted({r["layer"].split(":", 1)[1] for r in json.loads((OUT / "check" / "a" / "argonia.json").read_text())["records"]
                    if r.get("layer", "").startswith("place:")})
    r = subprocess.run([sys.executable, "-m", "tools.argonia_world.pieces", "check", "--places", ",".join(built)],
                       cwd=ROOT, check=False, capture_output=True, text=True)
    if r.returncode:
        errs.append("pieces: " + r.stdout.strip())
    errs += links(data, a_esm.parent)
    if (NAV_PROVINCE / "build.json").exists():  # L1: every built load door has its door triangle on both sides
        r = subprocess.run([sys.executable, "-m", "tools.navmesh", "doors", "check", "--nav", str(NAV_PROVINCE),
                            "--intermediate", str(a_esm.parent / "argonia.json"), "--esm", str(a_esm), "--data", str(data)],
                           cwd=ROOT, check=False, capture_output=True, text=True)
        if r.returncode:
            errs.append(f"navmesh doors: red\n{(r.stdout + r.stderr)[-1500:]}")
    b_esm, b_yaml = generate(data, OUT / "check" / "b", frozen=True)
    if a_esm.read_bytes() != b_esm.read_bytes():
        errs.append("regenerate: the two ESMs differ")
    if d := trees_equal(a_yaml, b_yaml):
        errs.append(f"regenerate: the two YAML trees differ in {len(d)} files, first {d[:3]}")
    if not YAML.exists():
        errs.append("plugin/Argonia/ missing: run `make plugin`")
    elif d := trees_equal(a_yaml, YAML):
        errs.append(f"plugin/Argonia/ is stale in {len(d)} files (first {d[:3]}): run `make plugin` and commit")
    else:
        rt = OUT / "check" / "roundtrip.esm"
        run("spriggit", "deserialize", "-i", YAML, "-o", rt, *SPRIGGIT, capped=True)
        if canon(rt.read_bytes()) != canon(a_esm.read_bytes()):
            errs.append("round trip: plugin/Argonia/ deserialised is not byte-identical to the generated ESM")
    from tools.argonia_world import db
    from tools.argonia_world.terrain import grass
    recs = json.loads((OUT / "check" / "a" / "argonia.json").read_text())["records"]
    from tools.argonia_world.intermediate import loading_screen_errors
    errs += [f"loading screens: {e}" for e in loading_screen_errors(json.loads((OUT / "vanilla-scan.json").read_text()), recs)]
    errs += [f"grass: {e}" for e in grass.check(grass.load_scan(OUT / "ltex-scan.json"), db.open(), recs)]
    try:
        got = sha256(world(data, OUT / "check" / "world", sample=True))
        want = json.loads((TERRAIN / "sample-manifest.json").read_text())["sha256"]
        if got != want:
            errs.append(f"{WORLD_ESM}: the fixed cell sample hashes {got[:12]}, the manifest says {want[:12]} "
                        "(a deliberate change: update tools/argonia_world/terrain/sample-manifest.json)")
    except SystemExit as e:
        errs.append(str(e))
    errs += navmesh_sample()
    for e in errs:
        print(f"plugin: {e}")
    if not errs:
        print("plugin: regenerate twice identical; plugin/Argonia/ current; Spriggit round trip byte-identical; "
              f"{WORLD_ESM} sample hash as the manifest")
    return 1 if errs else 0


# --- the game's load order (game-6: an empty MUSC and an unhoisted master crashed coc ARG_HoldingCell) ------------
PROFILE_PLUGINS = HOME / ".argonia" / "stack" / "MO2" / "profiles" / "Argonia" / "plugins.txt"  # infra/gpu-box/stack.py


def links(data: Path, ours: Path) -> list[str]:
    """ArgoniaGen links: every FormLink in Argonia.esm (from `ours`) and ArgoniaWorld.esm resolved, every master
    loaded before its plugin, every master's masters listed, every MUSC with a track, in the order the game is given:
    the laid vanilla plugins, the staged profile's plugins.txt, then ours (bridge.ps1 prepare)."""
    if not PROFILE_PLUGINS.exists():
        print(f"plugin: links SKIPPED, no staged profile at {PROFILE_PLUGINS} (infra/gpu-box/stack.py stage)")
        return []
    vanilla = [n for n in (ROOT / "infra" / "gpu-box" / "vanilla-data-files.txt").read_text().split()
               if n.lower().endswith((".esm", ".esp", ".esl"))]
    order = OUT / "check" / "load-order.txt"
    order.write_text("\n".join(vanilla + PROFILE_PLUGINS.read_text().splitlines() + [WORLD_ESM, "Argonia.esm"]) + "\n")
    r = subprocess.run([str(GEN), "links", "--data", str(data), "--order", str(order), "--ours", f"{ours},{OUT}"],
                       cwd=ROOT, env=ENV, capture_output=True, text=True, check=False)
    return [] if r.returncode == 0 else [f"links: red\n{(r.stdout + r.stderr)[-2500:]}"]


def province_navmesh() -> Path | None:
    """The last `make navmesh` build, which every ArgoniaWorld.esm carries (game-8: `make plugin` wrote the world
    without it, so the deployed province had no NAVM and no person could walk). Its stamp is the ground it was built
    on: a ground change since is reported (`make navmesh` rebuilds, about 26 min), never silently dropped."""
    nav = OUT / "navmesh" / "province"
    if not (nav / "build.json").exists():
        print("plugin: WARNING no province navmesh (out/navmesh/province): people cannot walk; run `make navmesh`")
        return None
    stamp = nav / "terrain.stamp"
    if not stamp.exists() or stamp.read_text() != _terrain_stamp():
        print("plugin: WARNING the province navmesh predates the current ground; `make navmesh` rebuilds it")
    return nav


# --- the navmesh (2.W4 §b): its own target, outside the gate but for a fixed sample's hash ---------------------------
NAV = ROOT / "tools" / "navmesh"
NAV_SAMPLE = (0, 0, 1, 1)  # four cells of the terrain sample (terrain/world.py SAMPLE)


def navmesh_sample() -> list[str]:
    """The navmesh job on NAV_SAMPLE: its L1 checks green and its records' sha256 as tools/navmesh/sample-manifest.json."""
    r = subprocess.run([sys.executable, "-m", "tools.navmesh", "build", "--cells", ",".join(map(str, NAV_SAMPLE)),
                        "--out", str(OUT / "check" / "navmesh")], cwd=ROOT, capture_output=True, text=True, check=False)
    if r.returncode:
        return [f"navmesh sample: red\n{(r.stdout + r.stderr)[-1500:]}"]
    got = json.loads((OUT / "check" / "navmesh" / "build.json").read_text())["sha256"]
    want = json.loads((NAV / "sample-manifest.json").read_text())["sha256"]
    return [] if got == want else [f"navmesh sample hashes {got[:12]}, the manifest says {want[:12]} (a deliberate "
                                   "change: update tools/navmesh/sample-manifest.json)"]


def navmesh() -> int:
    """`make navmesh`: the province's navmesh (tools/navmesh) on the current ground and water, then ArgoniaWorld.esm
    with it (out/ArgoniaWorld.esm, as `make plugin` writes it but with every NAVM and the NAVI)."""
    data = data_dir()
    build_tool()
    scans(data)
    water(OUT / "terrain", sample=False)
    nav = OUT / "navmesh" / "province"
    ground = _terrain_stamp()
    run(sys.executable, "-m", "tools.navmesh", "build", "--province", "--out", nav, capped=True, quiet=False)
    (nav / "terrain.stamp").write_text(ground)
    wesm = world(data, OUT / "terrain", sample=False, nav=nav)
    sys.path.insert(0, str(ROOT))
    from tools.navmesh import checks as nav_checks
    v = nav_checks.verify_esm(wesm, nav)  # every NAVM in the plugin byte for byte as built, and the NAVI's entries
    print(f"navmesh: {json.dumps(v)}")
    if not v["green"]:
        raise SystemExit("navmesh: ArgoniaWorld.esm's navmesh differs from the build")
    shutil.copyfile(wesm, OUT / WORLD_ESM)
    print(f"navmesh: out/{WORLD_ESM} ({wesm.stat().st_size} bytes) sha256 {sha256(wesm)}")
    return 0


def vegetation_world() -> int:
    """`pipeline.py vegetation` (2.W4 §a, opt-in): out/ArgoniaWorld.esm with the province's vegetation spliced in."""
    data = data_dir()
    build_tool()
    wesm = world(data, OUT / "terrain", sample=False, veg=True)
    shutil.copyfile(wesm, OUT / WORLD_ESM)
    print(f"vegetation: out/{WORLD_ESM} ({wesm.stat().st_size} bytes) sha256 {sha256(wesm)}")
    return 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    sys.exit(plan() if cmd == "plugin" and "--plan" in sys.argv else plugin() if cmd == "plugin" else plugin(force=True, world=False) if cmd == "ids" else check() if cmd == "check" else stamps() if cmd == "stamps" else navmesh() if cmd == "navmesh"
             else vegetation_world() if cmd == "vegetation" else (print(__doc__) or 2))
