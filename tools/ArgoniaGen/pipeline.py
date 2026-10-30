#!/usr/bin/env python3
"""The record pipeline end to end (0.4 §a): `make plugin` and the gate's `plugin` part.

    pipeline.py plugin   scan the masters, index the pieces, write the intermediate JSON, generate Argonia.esm
                         (out/), serialise it with Spriggit into plugin/Argonia/; build the generated ground,
                         out/ArgoniaWorld.esm (decision 0031: never serialised; the terrain is rebuilt only when its
                         code or inputs change) and print its sha256
    pipeline.py vegetation  (2.W4 §a; `plugin` and the gate's sample build already include it) out/ArgoniaWorld.esm with the province's vegetation REFRs spliced in
                         (tools/argonia_world/vegetation; its L1 checks and the spliced plugin's read-back)
    pipeline.py navmesh  the province's navmesh (tools/navmesh), then out/ArgoniaWorld.esm with its NAVM and NAVI
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


def generate(data: Path, into: Path, frozen: bool) -> tuple[Path, Path]:
    """intermediate -> ESM -> YAML, all under `into`; returns (esm, yaml dir)."""
    into.mkdir(parents=True, exist_ok=True)
    inter, esm, yaml = into / "argonia.json", into / "Argonia.esm", into / "yaml"
    run(sys.executable, "-m", "tools.argonia_world.intermediate", "--data", data, "--out", inter,
        "--frozen", "1" if frozen else "0")
    run(GEN, "generate", "--in", inter, "--data", data, "--out", esm, capped=True)
    shutil.rmtree(yaml, ignore_errors=True)
    run("spriggit", "serialize", "-i", esm, "-o", yaml, "-g", "SkyrimSE", *SPRIGGIT, capped=True)
    return esm, yaml


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
WORLD_ENV = {"DOTNET_GCHeapHardLimit": "0x60000000", "DOTNET_GCConserveMemory": "9"}  # 1.1 GB peak measured


def _terrain_stamp() -> str:
    """The terrain's code, the world tables it reads and its inputs (by size and time): a change rebuilds."""
    import hashlib
    sys.path.insert(0, str(ROOT))
    from tools.argonia_world import db
    from tools.argonia_world.terrain import vault
    from tools.argonia_world.terrain.landcover import table
    h = hashlib.sha256(repr(sorted(table(db.open()).items())).encode())
    for f in sorted(TERRAIN / n for n in ("__main__.py", "build.py", "grid.py", "landcover.py", "paint.py", "png.py",
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
    return h.hexdigest()


WATER = ROOT / "tools" / "argonia_world" / "water"
WATER_OUT = OUT / "water"


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
                    if n.startswith(("hydrology_", "water_"))):
        h.update(t.encode() + repr([tuple(r) for r in w.query(f'SELECT * FROM "{t}"')]).encode())
    for f in (OUT / "pieces-index.json",):
        h.update(f.read_bytes() if f.exists() else b"-")
    return h.hexdigest()


def water(into: Path, sample: bool) -> Path:
    """The water plan (out/water, replanned only when its stamp changes), and for the sample its cells only."""
    WATER_OUT.mkdir(parents=True, exist_ok=True)
    stamp = WATER_OUT / "water.stamp"
    now = _water_stamp()
    if not (stamp.exists() and stamp.read_text() == now and (WATER_OUT / "cells.jsonl").exists()):
        run(sys.executable, "-m", "tools.argonia_world.water", "plan", "--out", WATER_OUT, capped=True)
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
    return h.hexdigest()


def vegetation(into: Path, sample: bool) -> Path:
    """The province's vegetation (2.W4 §a: our placement from the region rules) with its L1 checks against the
    LAND under `into`: the sample's cells for the gate, else every cell (re-placed only when its stamp changes)."""
    d = into / "vegetation"
    stamp = d / "veg.stamp"
    now = None if sample else _veg_stamp()
    if sample or not (stamp.exists() and stamp.read_text() == now):
        stamp.unlink(missing_ok=True)
        run(sys.executable, "-m", "tools.argonia_world.vegetation", "build", "--out", d, "--water",
            WATER_OUT / "cells.jsonl", "--land", into / "land", *(["--sample"] if sample else []), capped=True)
        if now:
            stamp.write_text(now)
    return d


def world(data: Path, into: Path, sample: bool, nav: Path | None = None, veg: bool = True) -> Path:
    """terrain cells -> world.json -> ArgoniaWorld.esm under `into`; the full grid's cells are reused while the
    stamp holds. `nav`: a built navmesh (tools/navmesh) whose NAVM and NAVI go in too (`make navmesh`)."""
    into.mkdir(parents=True, exist_ok=True)
    stamp = into / "terrain.stamp"
    now = _terrain_stamp()
    if sample or not (stamp.exists() and stamp.read_text() == now and (into / "land").is_dir()):
        run(sys.executable, "-m", "tools.argonia_world.terrain", "build", "--out", into,
            *(["--sample"] if sample else []), capped=True)
        if not sample:
            stamp.write_text(now)
    run(sys.executable, "-m", "tools.argonia_world.terrain", "world", "--out", into)
    wdir = water(into, sample)
    esm = into / "esm" / WORLD_ESM
    esm.parent.mkdir(parents=True, exist_ok=True)
    full = (CAP if CAP else []) + [str(GEN), "world", "--in", str(into / "world.json"), "--land", str(into / "land"),
                                   "--data", str(data), "--out", str(esm), "--water", str(wdir),
                                   *(["--navmesh", str(nav)] if nav else [])]
    r = subprocess.run(full, cwd=ROOT, env=dict(ENV, **WORLD_ENV), capture_output=True, text=True, check=False)
    if r.returncode:
        raise SystemExit(f"plugin: ArgoniaWorld.esm failed\n{(r.stdout + r.stderr)[-3000:]}")
    if veg:  # 2.W4 §a, part of the build (the sample too: the gate's vegcheck): the REFRs spliced into each cell (VegetationRecords.cs)
        vdir = vegetation(into, sample)
        tmp = esm.with_suffix(".veg.esm")
        run(*(CAP if CAP else []), GEN, "vegetation", "--in", esm, "--veg", vdir, "--out", tmp)
        tmp.replace(esm)
        print(run(sys.executable, "-m", "tools.argonia_world.vegetation", "readback", "--out", vdir, "--esm", esm,
                  "--gen", GEN).strip())
    return esm


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


def plugin() -> int:
    data = data_dir()
    build_tool()
    scans(data)
    master_world(data, rebuild=True)  # first: Argonia.esm's place cells override its cells
    esm, yaml = generate(data, OUT / "build", frozen=False)
    shutil.copyfile(esm, OUT / "Argonia.esm")
    shutil.rmtree(YAML, ignore_errors=True)
    shutil.copytree(yaml, YAML)
    from tools.argonia_world import forms_table; forms_table.write()  # the allocator may have added rows (1.1)
    n = sum(1 for _ in YAML.rglob("*.yaml"))
    print(f"plugin: out/Argonia.esm ({esm.stat().st_size} bytes), {n} YAML files in plugin/Argonia/")
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
    sys.exit(plugin() if cmd == "plugin" else check() if cmd == "check" else navmesh() if cmd == "navmesh"
             else vegetation_world() if cmd == "vegetation" else (print(__doc__) or 2))
