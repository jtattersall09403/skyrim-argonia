"""The pass ledger (owner, 2026-11-03): a journey step that passed is never run again until something it depends on
changes, its own inputs, not the whole build. A batch shrinks as items pass; a rerun carries only what failed, is
new, or whose inputs moved.

Reach. A journey says what it depends on with `reach:` (repo paths or git pathspec globs, and the word `esm` for the
two plugin hashes, out/Argonia.esm and out/ArgoniaWorld.esm), at the journey level and optionally per step (a step's
own list is added to the journey's). A step's reach hash is the sha256 of: the tracked blob ids of those paths
(`git ls-files -s`), the ESM hashes when `esm` is named, the journey's scene file, the journey's own settings (all
but its steps) and the step itself. A finer item, `records: <spec>`, hashes only the named records' serialised YAML under plugin/Argonia/ (one
file per record) instead of the ESM: `records: Weathers` (any folder there: ImageSpaces, Climates, Statics, Npcs,
LeveledNpcs, Waters; a folder not there hashes as none), `records: wrld` (the worldspace record itself, without its persistent refs), `records: ref EDID` (one
persistent ref of the worldspace by editor id: a vantage marker, a bridge step),
`records: cell -9,27` (the cell's plugin folder, and its lines in the generated shards out/terrain/land,
vegetation and creatures: LAND, plants and rocks, spawns) and `records: cell -9,27 r1` (the cell and its ring of
neighbours). Not in a cell spec: a cell's water level, which only the built ESM holds. A journey with no `records:`
keys is keyed as before. A journey with no `reach:` keys on the whole build (round.sh's build key:
the two ESMs and every deploy input), the conservative default.

The ledger, ~/.argonia/round/passes.jsonl ($ARGONIA_PASSES), one row per journey step run:
{journey, step, reach_hash, build, time, status, run, still, kept}. status is `pass` (its expects held and it has no
reader), `reader` (its expects held; its reader has not ruled: `python3 -m tools.journeys ledger pass <journey>
<step>` records the reader's PASS) or `fail`. A step is skipped while the last row for (journey, step, reach_hash)
is `pass`.
"""
from __future__ import annotations

import datetime
import functools
import gzip
import hashlib
import json
import os
import pathlib
import re
from subprocess import run as _run  # held at import: tests stub subprocess.run for the bridge

REPO = pathlib.Path(__file__).resolve().parents[1]
ESMS = ("out/Argonia.esm", "out/ArgoniaWorld.esm")
# round.sh's build key inputs (keep in step with infra/gpu-box/round.sh)
WHOLE_BUILD = ("esm", "infra/gpu-box", "data", "ui", "skse", "tools/ArgoniaGen", "tests/journeys", "tests/scenes")


def ledger_path() -> pathlib.Path:
    return pathlib.Path(os.environ.get("ARGONIA_PASSES") or pathlib.Path.home() / ".argonia" / "round" / "passes.jsonl")


@functools.lru_cache(maxsize=None)
def _esm_hash(repo: str, rel: str) -> str:
    p = pathlib.Path(repo) / rel
    if not p.is_file():
        return f"{rel}:none"
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return f"{rel}:{h.hexdigest()}"


@functools.lru_cache(maxsize=None)
def _blobs(repo: str, paths: tuple[str, ...]) -> str:
    if not paths:
        return ""
    return _run(["git", "ls-files", "-s", "--", *paths], cwd=repo, capture_output=True, text=True,
                          check=True).stdout


PLUGIN = "plugin/Argonia"
RECORDS = "records:"
_CELL = re.compile(r"^cell\s+(-?\d+)\s*,\s*(-?\d+)(?:\s+r(\d+))?$")
_REF = re.compile(r"^ref\s+(\w+)$")
_XY = re.compile(rb'"x": (-?\d+), "y": (-?\d+)')
_POINT = re.compile(r"^\s*Point:\s*(-?\d+)\s*,\s*(-?\d+)\s*$", re.M)


@functools.lru_cache(maxsize=None)
def cell_dirs(repo: str) -> dict:
    """(x, y) -> the cell's folder (relative to the repo) under plugin/Argonia/Worldspaces: block/sub-block/cell."""
    root = pathlib.Path(repo) / PLUGIN
    out = {}
    for f in sorted(root.glob("Worldspaces/*/*/*/*/RecordData.yaml")):
        m = _POINT.search(f.read_text(errors="replace")[:2000])
        if m:
            out[(int(m[1]), int(m[2]))] = str(f.parent.relative_to(repo))
    return out


def _files(repo: str, spec: str) -> list[str] | None:
    """The files a `records:` spec names (repo-relative), or None when the spec is no valid form."""
    root = pathlib.Path(repo)
    spec = spec.strip()
    if spec == "wrld" or _REF.match(spec):
        return []   # hashed from the worldspace file by wrld_parts, not as files
    m = _CELL.match(spec)
    if m:
        x, y, r = int(m[1]), int(m[2]), int(m[3] or 0)
        dirs = cell_dirs(repo)
        out = []
        for i in range(x - r, x + r + 1):
            for j in range(y - r, y + r + 1):
                if (i, j) in dirs:
                    out += [str(f.relative_to(root)) for f in (root / dirs[(i, j)]).rglob("*") if f.is_file()]
        return sorted(out)
    if re.fullmatch(r"[A-Za-z]+", spec):
        d = root / PLUGIN / spec
        return sorted(str(f.relative_to(root)) for f in d.rglob("*") if f.is_file()) if d.is_dir() else []
    return None


ROW_DIRS = ("out/terrain/land", "out/terrain/vegetation", "out/terrain/creatures")  # one gz JSON line per cell: x, y


@functools.lru_cache(maxsize=None)
def _row_lines(repo: str, rel: str) -> dict:
    """(x, y) -> sha256 of the cell's line in one generated row shard (out/terrain/<land|vegetation|creatures>/cy+NNN)."""
    p = pathlib.Path(repo) / rel
    if not p.is_file():
        return {}
    out = {}
    with gzip.open(p, "rb") as f:
        for ln in f:
            m = _XY.search(ln[-200:] if len(ln) > 200 and ln.rstrip().endswith(b"}") else ln)
            if not m:
                d = json.loads(ln)
                k = (d.get("x"), d.get("y"))
            else:
                k = (int(m[1]), int(m[2]))
            out[k] = hashlib.sha256(ln).hexdigest()
    return out


def cell_lines(repo: str, x: int, y: int) -> list[str]:
    """The cell's generated lines (its LAND, its placed plants and rocks, its creature spawns), as `dir:hash`."""
    return [f"{d}:{_row_lines(repo, f'{d}/cy{y:+04d}.jsonl.gz').get((x, y), 'none')}" for d in ROW_DIRS]


@functools.lru_cache(maxsize=None)
def wrld_parts(repo: str) -> tuple[str, dict]:
    """The worldspace record split in two: everything but its persistent refs (the WRLD record itself), and each
    persistent ref's block by editor id. The refs sit in the WRLD's one file (TopCell.Persistent), so a bridge step
    moved there must not move the record, and a vantage marker is a `ref` of its own."""
    head, refs, cur, in_p = [], {}, None, False
    for f in sorted((pathlib.Path(repo) / PLUGIN).glob("Worldspaces/*/RecordData.yaml")):
        for ln in f.read_text().splitlines():
            if ln == "  Persistent:":
                in_p = True
                continue
            if in_p and not ln.startswith("  -") and not ln.startswith("    "):
                in_p = False
            if not in_p:
                head.append(ln)
            elif ln.startswith("  - "):
                cur = [ln]
                refs[len(refs)] = cur
            else:
                cur.append(ln)
    named = {}
    for blk in refs.values():
        m = next((re.match(r"\s+EditorID: (\w+)", ln) for ln in blk if "EditorID:" in ln), None)
        if m:
            named[m[1]] = "\n".join(blk)
    return "\n".join(head), named


@functools.lru_cache(maxsize=None)
def _file_hash(repo: str, rel: str) -> str:
    return hashlib.sha256((pathlib.Path(repo) / rel).read_bytes()).hexdigest()


@functools.lru_cache(maxsize=None)
def records_hash(repo: str, spec: str) -> str:
    """The sha256 of the named records' files (path and bytes); `none` when the spec names no file."""
    files = _files(repo, spec)
    if files is None:
        raise ValueError(f"bad records spec: {spec!r}")
    h = hashlib.sha256()
    if spec == "wrld":
        h.update(wrld_parts(repo)[0].encode())
        return f"{spec}:{h.hexdigest()}"
    if (m := _REF.match(spec)):
        blk = wrld_parts(repo)[1].get(m[1])
        return f"{spec}:{hashlib.sha256(blk.encode()).hexdigest()}" if blk else f"{spec}:none"
    for rel in files:
        h.update(f"{rel}:{_file_hash(repo, rel)}\n".encode())
    lines = []
    if (m := _CELL.match(spec.strip())):
        x, y, r = int(m[1]), int(m[2]), int(m[3] or 0)
        for i in range(x - r, x + r + 1):
            for j in range(y - r, y + r + 1):
                lines += [f"{i},{j}:{ln}" for ln in cell_lines(repo, i, j)]
        h.update("\n".join(lines).encode())
    empty = not files and all(ln.endswith(":none") for ln in lines)
    return f"{spec}:none" if empty else f"{spec}:{h.hexdigest()}"


def clear_cache() -> None:
    cell_dirs.cache_clear()
    wrld_parts.cache_clear()
    _row_lines.cache_clear()
    _file_hash.cache_clear()
    records_hash.cache_clear()
    _esm_hash.cache_clear()
    _blobs.cache_clear()


def reach_of(j: dict, step: dict) -> list[str]:
    """The step's reach: the journey's plus the step's own; the whole build when the journey names none."""
    if "reach" not in j:
        return list(WHOLE_BUILD)
    return list(j.get("reach") or []) + list(step.get("reach") or [])


def reach_hash(j: dict, step: dict, repo: pathlib.Path = REPO) -> str:
    paths = reach_of(j, step)
    h = hashlib.sha256()
    if "esm" in paths:
        for e in ESMS:
            h.update(_esm_hash(str(repo), e).encode() + b"\n")
    h.update(_blobs(str(repo), tuple(sorted({p for p in paths if p != "esm" and not p.startswith(RECORDS)}))).encode())
    for spec in sorted({p[len(RECORDS):].strip() for p in paths if p.startswith(RECORDS)}):
        h.update(records_hash(str(repo), spec).encode() + b"\n")
    if j.get("scene"):
        h.update(_blobs(str(repo), (f"tests/scenes/{j['scene']}.txt",)).encode())
    settings = {k: v for k, v in j.items() if k != "steps"}
    h.update(json.dumps(settings, sort_keys=True, default=str).encode())
    h.update(json.dumps(step, sort_keys=True, default=str).encode())
    return h.hexdigest()[:16]


def build_key(repo: pathlib.Path = REPO) -> str:
    return reach_hash({"reach": list(WHOLE_BUILD)}, {}, repo)


def rows(path: pathlib.Path | None = None) -> list[dict]:
    p = path or ledger_path()
    if not p.is_file():
        return []
    out = []
    for line in p.read_text().splitlines():
        try:
            out.append(json.loads(line))
        except ValueError:
            continue  # a torn last line (a spot stop mid-write) is ignored
    return out


def last_rows(path: pathlib.Path | None = None) -> dict:
    """(journey, step, reach_hash) -> its last row."""
    return {(r.get("journey"), r.get("step"), r.get("reach_hash")): r for r in rows(path)}


def passed(index: dict, journey: str, step: str, h: str) -> dict | None:
    r = index.get((journey, step, h))
    # `reader`: the run held and its still exists for these inputs; a reader judges the still, and a reader FAIL leads to
    # a fix that moves the step's inputs. Retaking the still buys nothing (12 reboots on 2026-11-04 retook 355 steps).
    return r if r and r.get("status") in ("pass", "reader") else None


def append(row: dict, path: pathlib.Path | None = None) -> None:
    p = path or ledger_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a") as f:
        f.write(json.dumps(row) + "\n")
        f.flush()
        os.fsync(f.fileno())


def now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def plan(j: dict, index: dict, force: bool = False, repo: pathlib.Path = REPO) -> dict:
    """Which steps of a journey run. Steps hand state on (a menu opened, then closed), so a journey runs from its first
    step up to its last step that must run; the passed steps after that are skipped. `independent_steps: true` (each
    step sets its own state) skips every passed step, except one a running step `needs:`. Owed steps are neither.
    Returns {skip: {name: ledger row}, run: [names], hashes: {name: hash}}."""
    steps = [s for s in j.get("steps", []) if not s.get("owed")]
    hashes = {s["name"]: reach_hash(j, s, repo) for s in steps}
    # a `setup: true` step sets session state (HUD off, camera): never a pass to skip, run whenever any other step runs
    done = {} if force else {s["name"]: r for s in steps if not s.get("setup")
                             if (r := passed(index, j["id"], s["name"], hashes[s["name"]]))}
    setup = {s["name"] for s in steps if s.get("setup")}
    if j.get("independent_steps"):
        need = {s["name"] for s in steps if s["name"] not in done and s["name"] not in setup}
        for s in steps:
            if s["name"] in need:
                need |= set(s.get("needs") or [])
        skip = {n: r for n, r in done.items() if n not in need}
        if not need:
            skip.update({n: {"time": "-", "setup_idle": True} for n in setup})
    else:
        last = max((i for i, s in enumerate(steps) if s["name"] not in done and s["name"] not in setup), default=-1)
        skip = {s["name"]: done[s["name"]] for s in steps[last + 1:] if s["name"] in done}
        if last < 0:
            skip.update({n: {"time": "-", "setup_idle": True} for n in setup})
    return {"skip": skip, "run": [s["name"] for s in steps if s["name"] not in skip], "hashes": hashes}


def record(j: dict, rep: dict, hashes: dict | None = None, build: str | None = None,
           path: pathlib.Path | None = None, repo: pathlib.Path = REPO) -> int:
    """A ledger row per step the run judged (skipped steps are not written again); the rows written."""
    by_name = {s["name"]: s for s in j.get("steps", [])}
    build = build or build_key(repo)
    n = 0
    for rec in rep.get("steps", []):
        if rec.get("skipped") or rec["name"] not in by_name:
            continue
        step = by_name[rec["name"]]
        status = "fail" if not rec.get("passed") else ("reader" if step.get("reader") else "pass")
        append({"journey": j["id"], "step": rec["name"],
                "reach_hash": (hashes or {}).get(rec["name"]) or reach_hash(j, step, repo), "build": build,
                "time": now(), "status": status, "run": rep.get("_out"), "still": rec.get("still"),
                "kept": rec.get("kept") or {}}, path)
        n += 1
    return n


def reader_pass(journey: str, step: str, path: pathlib.Path | None = None) -> dict:
    """The planner records a reader's PASS on the step's last run: its last `reader` row becomes a `pass` row."""
    last = next((r for r in reversed(rows(path)) if r.get("journey") == journey and r.get("step") == step), None)
    if last is None:
        raise SystemExit(f"no ledger row for {journey} {step} in {path or ledger_path()}")
    if last.get("status") == "fail":
        raise SystemExit(f"{journey} {step}: its last run failed ({last.get('run')}); a reader cannot pass it")
    row = {**last, "status": "pass", "time": now(), "reader": "PASS"}
    append(row, path)
    return row
