"""python -m tools.places extract <source_id> | --ground <place_id> [--radius-m M] [--force]

Writes the bundle `src.<source_id>` (a source place declared in newworld/places/sources.jsonl, read out of its
plugins) or `ground.<place_id>` (our own world file round the place, newworld/story/data/db/place.jsonl) under
out/places/bundles/ (docs/design/place-studio.md, "Bundles"). The C# extractor (tools/ArgoniaPlaces/Extract) reads
the plugins; this module resolves the inputs, stamps the bundle and skips a rerun whose key is unchanged.
A new source is a row in sources.jsonl, never a code change.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

from tools.places import worldparts
from tools.places.bundle import BUNDLES, REPO, publish, settle, sha256_file, stamp_key, write_json

SOURCES = REPO / "newworld" / "places" / "sources.jsonl"
PLACES = REPO / "newworld" / "story" / "data" / "db" / "place.jsonl"
ALLOCATIONS = REPO / "newworld" / "places"
PROJECT = REPO / "tools" / "ArgoniaPlaces" / "Extract"
BIN = REPO / "out" / "tools" / "ArgoniaPlacesExtract"
WORLD_ESM = REPO / "out" / "newworld" / "plugin" / "ArgoniaNewWorld.esm"
WORLD_EDID = "ArgoniaBlackMarsh"
UNITS_PER_M = 70.0          # 1 game unit = 1.428 cm
GROUND_REACH_M = 500.0      # a town may be fitted anywhere within this of the place's centre
DEFAULT_HALF_EXTENT_M = 300.0


def game_root() -> Path:
    return Path(os.environ.get("ARGONIA_GAME_ROOT", Path.home() / "games" / "skyrimse"))


def search_dirs() -> list[str]:
    """Where plugins are found, first hit wins: the game's Data, the staged mods in MO2 priority order (highest
    first, as tools/ArgoniaPlugin/plugin.sh resolves them), the asset mods, our world file's directory."""
    data = game_root() / "Data"
    mo2 = Path.home() / ".argonia" / "stack" / "MO2"
    dirs = [data]
    modlist = mo2 / "profiles" / "Argonia" / "modlist.txt"
    if modlist.exists():
        for line in modlist.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if line.startswith("+"):
                dirs.append(mo2 / "mods" / line[1:])
    assets = game_root() / "newworld-assets"
    if assets.is_dir():
        dirs += sorted(p for p in assets.iterdir() if p.is_dir())
    dirs.append(WORLD_ESM.parent)
    return [str(d) for d in dirs if d.is_dir()]


def find_plugin(name: str, dirs: list[str]) -> Path:
    for d in dirs:
        p = Path(d) / name
        if p.exists():
            return p
    raise FileNotFoundError(f"plugin {name} not found in the search directories")


def load_sources() -> dict[str, dict]:
    rows = {}
    for line in SOURCES.read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            rows[r["source_id"]] = r
    return rows


def load_place(place_id: str) -> dict:
    for line in PLACES.read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            if r.get("id") == place_id:
                return r
    raise KeyError(f"no place {place_id!r} in {PLACES.relative_to(REPO)}")


def tool_hash() -> str:
    """The extractor's own hash: its C# sources, project file and this module."""
    h = hashlib.sha256()
    for p in sorted(PROJECT.glob("*.cs")) + [PROJECT / "Extract.csproj", Path(__file__)]:
        h.update(p.name.encode())
        h.update(p.read_bytes())
    return h.hexdigest()


def build_tool() -> Path:
    dll = BIN / "ArgoniaPlacesExtract.dll"
    env = dict(os.environ, DOTNET_ROOT=str(Path.home() / ".dotnet"), DOTNET_CLI_TELEMETRY_OPTOUT="1", DOTNET_NOLOGO="1",
               PATH=f"{Path.home() / '.dotnet'}:{os.environ.get('PATH', '')}")
    newest = max(p.stat().st_mtime for p in [*PROJECT.glob("*.cs"), PROJECT / "Extract.csproj"])
    BIN.mkdir(parents=True, exist_ok=True)
    with open(BIN / ".build.lock", "w") as lk:  # two extracts at once: one builds, the other waits and finds it built
        fcntl.flock(lk, fcntl.LOCK_EX)
        if not dll.exists() or dll.stat().st_mtime < newest:
            r = subprocess.run(["dotnet", "build", "-c", "Release", "-o", str(BIN), str(PROJECT)], env=env,
                               capture_output=True, text=True)
            if r.returncode != 0:
                sys.stderr.write(r.stdout[-4000:] + r.stderr[-2000:])
                raise RuntimeError("the extractor did not build")
    return dll


# ---- the jobs -------------------------------------------------------------------------------------------------------

def source_job(row: dict) -> dict:
    job = {
        "bundle_id": f"src.{row['source_id']}", "kind": "source", "title": row.get("title", row["source_id"]),
        "plugins": list(row["plugins"]) + list(row.get("extra_refs_plugins", [])),
        "worldspace": row.get("worldspace", ""), "layer": "place",
        "follow_doors": row.get("follow_doors", True), "terrain": True, "navmesh": True,
    }
    for k in ("cells", "areas", "location", "marker", "radius"):
        if k in row:
            job[k] = row[k]
    return job


def ground_job(place: dict, radius_m: float | None) -> dict:
    if not all(isinstance(place.get(k), (int, float)) for k in ("world_x", "world_y")):
        raise KeyError(f"place {place['id']!r} has no world_x, world_y in {PLACES.relative_to(REPO)}: it is not on the map yet")
    if radius_m is None:
        radius_m = GROUND_REACH_M + source_half_extent_m(place["id"]) + 50.0
    return {
        "bundle_id": f"ground.{place['id']}", "kind": "ground", "title": f"Our ground round {place.get('name', place['id'])}",
        "plugins": [WORLD_ESM.name], "worldspace": WORLD_EDID, "layer": "world",
        "areas": [{"x": place["world_x"], "y": place["world_y"], "r": radius_m * UNITS_PER_M}],
        "follow_doors": False, "terrain": True, "navmesh": True, "radius_m": radius_m,
        "place": {"id": place["id"], "world_x": place["world_x"], "world_y": place["world_y"]},
    }


def source_half_extent_m(place_id: str) -> float:
    """Half the allocated source's measured size (its row's extent_m), so the whole source fits wherever it goes."""
    alloc = ALLOCATIONS / place_id / "place.json"
    try:
        sid = json.loads(alloc.read_text())["source_id"]
        ext = load_sources()[sid].get("extent_m")
        if ext:
            return max(float(ext[0]), float(ext[1])) / 2
    except (OSError, KeyError, ValueError, TypeError):
        pass
    return DEFAULT_HALF_EXTENT_M


def _inputs(plugins, dirs: list, world: dict | None) -> dict:
    """What a bundle's stamp holds of each plugin it read: the file's sha256; of the world file, the key of the
    world records the bundle stands on (tools/places/worldparts.py), so a rewrite that leaves them is no new input."""
    inputs = {f: sha256_file(find_plugin(f, dirs)) for f in plugins if not (world and f == WORLD_ESM.name)}
    if world:
        inputs[WORLD_ESM.name] = "parts:" + world["key"]
    return inputs


def run(job: dict, force: bool = False) -> Path:
    final = BUNDLES / job["bundle_id"]
    settle(final)
    dirs = search_dirs()
    tool = tool_hash()
    params = {k: v for k, v in job.items() if k not in ("out", "search")}
    prev = final / "bundle.json"
    if prev.exists() and not force:
        was = json.loads(prev.read_text())
        st = was.get("stamp", {})
        try:
            world = worldparts.again(was["world"], WORLD_ESM) if job["kind"] == "ground" and was.get("world") else None
            # a ground bundle that names no world records it stands on is read again: it cannot be shown current
            inputs = _inputs(st.get("inputs", {}), dirs, world) if world or job["kind"] != "ground" else None
        except FileNotFoundError:
            inputs = None
        if inputs and stamp_key(inputs, tool, params) == st.get("key"):
            print(f"{job['bundle_id']}: up to date (key {st['key'][:12]})")
            return final
    dll = build_tool()
    tmp = BUNDLES / f".tmp.{job['bundle_id']}"
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)
    jf = tmp / "job.json"
    jf.write_text(json.dumps(dict(job, out=str(tmp), search=dirs), indent=1))
    env = dict(os.environ, DOTNET_ROOT=str(Path.home() / ".dotnet"))
    t0 = time.time()
    r = subprocess.run([str(Path.home() / ".dotnet" / "dotnet"), str(dll), "extract", str(jf)], env=env,
                       capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stderr[-6000:])
        raise RuntimeError(f"the extractor failed on {job['bundle_id']}")
    jf.unlink()
    meta = json.loads((tmp / "bundle.json").read_text())
    world = worldparts.stamp(WORLD_ESM, meta["cells"]) if job["kind"] == "ground" else None
    inputs = _inputs(meta["plugins"], dirs, world)
    meta["stamp"] = {"key": stamp_key(inputs, tool, params), "inputs": inputs, "tool": tool,
                     "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "seconds": round(time.time() - t0)}
    if job["kind"] == "ground":
        meta["esm"] = {"file": WORLD_ESM.name, "sha256": world["sha256"]}   # the file it was read from, for the record
        meta["world"] = world                                               # the records of it the bundle stands on
        meta["place"] = job["place"]
        meta["radius_m"] = job["radius_m"]
    write_json(tmp / "bundle.json", meta)
    publish(tmp, final)
    c = meta["counts"]
    print(f"{job['bundle_id']}: {len(meta['cells'])} cells, {len(meta['spaces'])} spaces, {c['refs']} refs, "
          f"{c['bases']} bases, {c.get('actors', 0)} actors, {c.get('navmeshes', 0)} navmeshes -> {final.relative_to(REPO)}")
    return final


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="python -m tools.places extract")
    ap.add_argument("source_id", nargs="?")
    ap.add_argument("--ground", metavar="PLACE_ID")
    ap.add_argument("--radius-m", type=float)
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args(argv)
    if bool(a.ground) == bool(a.source_id):
        ap.error("give one source_id or --ground <place_id>")
    if a.ground:
        job = ground_job(load_place(a.ground), a.radius_m)
    else:
        rows = load_sources()
        if a.source_id not in rows:
            ap.error(f"no source {a.source_id!r} in {SOURCES.relative_to(REPO)}; sources: {' '.join(sorted(rows))}")
        job = source_job(rows[a.source_id])
    run(job, a.force)
    return 0
