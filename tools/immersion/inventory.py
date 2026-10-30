#!/usr/bin/env python3
"""The immersion inventory (decision 0006 §1; chunk 0.4 §c): every element a player could meet, one row each.

    python3 tools/immersion/inventory.py            enumerate the profile and write the inventory and its counts
    python3 tools/immersion/inventory.py --gate     the gate part: report the counts (always passes through Part 1)
    python3 tools/immersion/inventory.py --gate --bind   the binding gate (from 2.17): fails on a reachable
                                                     `unreviewed` row, or a replace/hide/remove row without a check
    python3 tools/immersion/inventory.py --block claywater   also label each row with its hops from the block's cells
                                                     (`block`; counts.json gains `block`): what a player there meets

Sources: every record of 0006 §1's types across the load order (InventoryDump, Mutagen), every menu SWF in the
profile's archives and loose files, every view of ours (ui/), the UI translate keys. Reachability: from our
plugin (Argonia.esm, or --root) transitively, then from the quests that start with the game; menus, GMSTs, music
types and loading screens are reached by the engine itself.

The inventory holds vanilla editor IDs and paths derived from game files, so it stays out of git (data/README,
decision 0003): `data/immersion/inventory.jsonl` is ignored; the committed record is `counts.json`, and the
verdicts we write live in `verdicts.jsonl` (ours, committed) keyed by row id.
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import bsa  # noqa: E402

REPO = HERE.parent.parent
OUT_DIR = REPO / "data" / "immersion"
INVENTORY = OUT_DIR / "inventory.jsonl"
COUNTS = OUT_DIR / "counts.json"
VERDICTS = OUT_DIR / "verdicts.jsonl"
DUMP_PROJECT = HERE / "InventoryDump"
DUMP_BIN = DUMP_PROJECT / "bin" / "Release" / "net10.0" / "InventoryDump.dll"

OFFICIAL = ["Skyrim.esm", "Update.esm", "Dawnguard.esm", "HearthFires.esm", "Dragonborn.esm"]
VERDICT_VALUES = {"unreviewed", "keep", "restyle", "replace", "hide", "remove"}
NEEDS_CHECK = {"replace", "hide", "remove"}
ENGINE_TYPES = {"GMST", "MUST", "LSCR"}  # the engine shows these without our world placing them
AUDIO = {"SOUN", "SNDR", "MUSC", "MUST", "ASPC", "SNCT", "VTYP"}
TEXT = {"BOOK", "MESG", "LSCR", "DIAL", "INFO", "QUST"}


def data_dir() -> Path:
    root = os.environ.get("ARGONIA_GAME_ROOT")
    return Path(root) / "Data" if root else Path.home() / "games" / "skyrimse" / "Data"


def root_plugin(data: Path, given: str | None) -> Path | None:
    """Our plugin: --root, $ARGONIA_PLUGIN, then Argonia.esm in Data or in the pipeline's out/ tree."""
    for c in [given, os.environ.get("ARGONIA_PLUGIN"), data / "Argonia.esm", REPO / "out" / "plugin" / "Argonia.esm",
              REPO / "out" / "Argonia.esm"]:
        if c and Path(c).is_file():
            return Path(c)
    return None


def load_order(data: Path, root: Path | None) -> list[str]:
    """Official masters, then Creation Club plugins in Skyrim.ccc order, then the dependency plugins: in
    $ARGONIA_PLUGINS_TXT's order when given, else masters before plugins, alphabetically. Our plugin is the root,
    passed separately."""
    present = {p.name.lower(): p.name for p in data.iterdir() if p.suffix.lower() in (".esm", ".esp", ".esl")}
    order = [present[n.lower()] for n in OFFICIAL if n.lower() in present]
    ccc = data.parent / "Skyrim.ccc"
    if ccc.is_file():
        order += [present[n.strip().lower()] for n in ccc.read_text().splitlines() if n.strip().lower() in present]
    if (ptxt := os.environ.get("ARGONIA_PLUGINS_TXT")) and Path(ptxt).is_file():
        listed = [n.strip().lstrip("*") for n in Path(ptxt).read_text().splitlines() if n.strip() and not n.startswith("#")]
        order += [present[n.lower()] for n in listed if n.lower() in present]
    rest = sorted((n for k, n in present.items() if n not in order), key=lambda n: (n.lower().endswith(".esp"), n.lower()))
    order += rest
    skip = root.name.lower() if root else None
    return list(dict.fromkeys(n for n in order if n.lower() != skip))


def dotnet() -> tuple[str, dict]:
    exe = shutil.which("dotnet") or str(Path.home() / ".dotnet" / "dotnet")
    env = dict(os.environ)
    env.setdefault("DOTNET_ROOT", str(Path(exe).resolve().parent))
    env["DOTNET_CLI_TELEMETRY_OPTOUT"] = "1"
    return exe, env


def run_dump(*args: str) -> str:
    """Run InventoryDump, building it first when its source is newer than the build."""
    exe, env = dotnet()
    src = max(p.stat().st_mtime for p in DUMP_PROJECT.glob("*.cs*"))
    if not DUMP_BIN.is_file() or DUMP_BIN.stat().st_mtime < src:
        subprocess.run([exe, "build", str(DUMP_PROJECT), "-c", "Release", "-v", "q", "--nologo"], check=True, env=env,
                       stdout=subprocess.DEVNULL)
    r = subprocess.run([exe, str(DUMP_BIN), *args], env=env, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"InventoryDump {args[0]} failed:\n{r.stderr[-2000:]}")
    return r.stdout


BLOCKS = ("claywater",)  # tools/navmesh BLOCKS names the place
BLOCK_WORLD = "ARG_Province"


def block_args(name: str) -> list[str]:
    """InventoryDump's block arguments: the place's cell box (tools/navmesh's, from db.py's place row) in the
    province, and the borrowed interiors its build_cell rows name."""
    sys.path.insert(0, str(REPO))
    from tools.argonia_world import db  # noqa: E402
    from tools.navmesh.__main__ import BLOCKS as NAV_BLOCKS, block as cell_box  # the one block-box rule (numpy: the venv)
    x0, y0, x1, y1 = cell_box(name)
    hosts = [r[0] for r in db.open().query(
        "SELECT host_form_key FROM build_cell WHERE place_id = ? AND host_form_key IS NOT NULL ORDER BY id",
        NAV_BLOCKS[name])]
    return ["--block", f"{BLOCK_WORLD}:{x0},{y0},{x1},{y1}"] + (["--block-cells", ",".join(hosts)] if hosts else [])


def record_rows(data: Path, order: list[str], root: Path | None, tmp: Path, block: list[str] | None = None):
    """Stream the record rows: InventoryDump writes JSONL, read here one line at a time."""
    out = tmp / "records.jsonl"
    args = ["dump", "--data", str(data), "--load-order", ",".join(order), "--out", str(out)]
    if root:
        args += ["--root", str(root)]
    run_dump(*args, *(block or []))
    with out.open() as f:
        for line in f:
            r = json.loads(line)
            t = r["type"]
            reach = r["reach"] or ("engine" if t in ENGINE_TYPES else None)
            surface = "audio" if t in AUDIO else "text" if t in TEXT or (t == "GMST" and (r["edid"] or "").startswith("s")) else "record"
            row = {"id": r["formkey"], "kind": "record", "type": t, "edid": r["edid"], "source": r["origin"],
                   "plugins": r["plugins"], "surface": surface, "reach": reach}
            if r.get("block") is not None:
                row["block"] = r["block"]
                if r.get("block_via"):
                    row["block_via"] = r["block_via"]
            yield row


def archives(data: Path) -> list[Path]:
    """The profile's archives: every BSA in Data (the profile is clean, decision 0012), in name order."""
    return sorted((p for p in data.iterdir() if p.suffix.lower() == ".bsa"), key=lambda p: p.name.lower())


def menu_rows(data: Path) -> tuple[list[dict], dict[str, int]]:
    """Every SWF under interface/ in any archive or loose in Data; a loose file overrides the archives."""
    found: dict[str, list[str]] = collections.defaultdict(list)
    per_archive: dict[str, int] = {}
    for a in archives(data):
        swfs = [p for p in bsa.listing(a) if p.startswith("interface/") and p.endswith(".swf")]
        per_archive[a.name] = len(swfs)
        for p in swfs:
            found[p].append(a.name)
    loose = data / "interface"
    if loose.is_dir():
        for f in loose.rglob("*"):
            if f.suffix.lower() == ".swf":
                found[f.relative_to(data).as_posix().lower()].append("loose")
    rows = [{"id": p, "kind": "menu", "type": "SWF", "edid": None, "source": srcs[-1] if "loose" not in srcs else "loose",
             "plugins": srcs, "surface": "ui", "reach": "engine"} for p, srcs in sorted(found.items())]
    return rows, per_archive


def translate_rows(data: Path, tmp: Path) -> tuple[list[dict], dict[str, list[str]]]:
    """The UI's $-string keys (interface/translate_english.txt), read through Mutagen's archive reader, which also
    gives an independent listing of every archive to check the SWF count against."""
    out = tmp / "archives.json"
    run_dump("archives", "--data", str(data), "--archives", ",".join(a.name for a in archives(data)), "--out", str(out))
    listing = json.loads(out.read_text())
    rows, seen = [], set()
    for name, a in listing.items():
        for k in a["translate_keys"]:
            if k not in seen:
                seen.add(k)
                rows.append({"id": k, "kind": "string", "type": "UI_STRING", "edid": None, "source": name,
                             "plugins": [name], "surface": "text", "reach": "engine"})
    return rows, {name: a["files"] for name, a in listing.items()}


def view_rows() -> list[dict]:
    """Every view of ours: each HTML page under ui/ (PrismaUI views). None exist yet."""
    ui = REPO / "ui"
    if not ui.is_dir():
        return []
    return [{"id": p.relative_to(REPO).as_posix(), "kind": "view", "type": "VIEW", "edid": None, "source": "ours",
             "plugins": [], "surface": "ui", "reach": "engine"} for p in sorted(ui.rglob("*.html"))]


def load_verdicts(path: Path | None = None) -> dict[str, dict]:
    path = path or VERDICTS
    if not path.is_file():
        return {}
    out = {}
    for n, line in enumerate(path.read_text().splitlines(), 1):
        if line.strip():
            v = json.loads(line)
            if v.get("verdict") not in VERDICT_VALUES:
                raise SystemExit(f"{path}:{n}: verdict {v.get('verdict')!r} not in {sorted(VERDICT_VALUES)}")
            out[v["id"]] = v
    return out


def merge(rows, verdicts: dict[str, dict]):
    """Rows are streamed: each gains its verdict (ours, from verdicts.jsonl) and is passed on."""
    for r in rows:
        v = verdicts.get(r["id"], {})
        r.update(verdict=v.get("verdict", "unreviewed"), replacement=v.get("replacement"),
                 evidence=v.get("evidence"), check=v.get("check"), check_passed=v.get("check_passed", False))
        yield r


def failure(r: dict) -> str | None:
    """0006 §2: a reachable row with no verdict, or a replace/hide/remove row with no passing check."""
    if r["reach"] and r["verdict"] == "unreviewed":
        return f"{r['id']} ({r['type']}): reachable via {r['reach']}, unreviewed"
    if r["verdict"] in NEEDS_CHECK and not (r.get("check") and r.get("check_passed")):
        return f"{r['id']} ({r['type']}): {r['verdict']} without a passing check"
    return None


class Tally:
    """Counts and the first failures, kept while rows stream past (never the rows themselves)."""

    def __init__(self):
        self.n = self.reachable = self.reachable_unreviewed = self.failing = 0
        self.by = {k: collections.Counter() for k in ("kind", "reach", "verdict", "type")}
        self.first_failures: list[str] = []
        self.block = {k: collections.Counter() for k in ("type", "verdict", "depth", "source")}

    def add(self, r: dict) -> dict:
        self.n += 1
        self.reachable += bool(r["reach"])
        self.reachable_unreviewed += bool(r["reach"] and r["verdict"] == "unreviewed")
        for k in ("kind", "verdict", "type"):
            self.by[k][r[k]] += 1
        self.by["reach"][r["reach"] or "unreached"] += 1
        if r.get("block") is not None:
            self.block["type"][r["type"]] += 1
            self.block["verdict"][r["verdict"]] += 1
            self.block["depth"][str(r["block"])] += 1
            self.block["source"][r["source"]] += 1
        if (f := failure(r)) is not None:
            self.failing += 1
            if len(self.first_failures) < 20:
                self.first_failures.append(f)
        return r

    def counts(self) -> dict:
        c = {"rows": self.n, "reachable": self.reachable, "reachable_unreviewed": self.reachable_unreviewed,
             **{f"by_{k}": dict(sorted(v.items())) for k, v in self.by.items()}}
        if self.block["type"]:
            c["block"] = {"rows": sum(self.block["type"].values()),
                          "unreviewed": self.block["verdict"].get("unreviewed", 0),
                          **{f"by_{k}": dict(sorted(v.items())) for k, v in self.block.items()}}
        return c


def stream(path: Path):
    with path.open() as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def gate(inventory: Path = INVENTORY, counts_path: Path = COUNTS, bind: bool = False) -> int:
    tally = None
    if inventory.is_file():
        tally = Tally()
        for r in merge(stream(inventory), load_verdicts()):
            tally.add(r)
        c = tally.counts()
    elif counts_path.is_file():
        c = json.loads(counts_path.read_text())
        c = c.get("counts", c)
    else:
        print("immersion: no inventory and no counts; run python3 tools/immersion/inventory.py")
        return 1 if bind else 0
    print(f"immersion: {c['rows']} rows, {c['reachable']} reachable, {c['reachable_unreviewed']} reachable unreviewed; "
          f"kinds {c['by_kind']}" + ("" if tally else " (from counts.json)"))
    if not bind:
        return 0
    if tally is None:
        print("immersion --bind: needs the inventory itself, not only counts")
        return 1
    for b in tally.first_failures:
        print("  " + b)
    if tally.failing:
        print(f"immersion --bind: {tally.failing} rows fail (decision 0006 §2)")
        return 1
    return 0


def build(root_arg: str | None, out: Path, block: str | None = None) -> int:
    data = data_dir()
    if not (data / "Skyrim.esm").is_file():
        raise SystemExit(f"no Skyrim.esm in {data} (set ARGONIA_GAME_ROOT)")
    root = root_plugin(data, root_arg)
    order = load_order(data, root)
    tmp = REPO / "out" / "immersion"
    tmp.mkdir(parents=True, exist_ok=True)
    menus, per_archive = menu_rows(data)
    strings, mutagen_listing = translate_rows(data, tmp)
    for name, n in per_archive.items():  # two independent readers must agree on every archive's SWF count
        m = sum(1 for p in mutagen_listing[name] if p.startswith("interface/") and p.endswith(".swf"))
        if m != n:
            raise SystemExit(f"{name}: {n} SWFs by bsa.py, {m} by Mutagen")
    tally, verdicts = Tally(), load_verdicts()
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w") as f:
        bargs = block_args(block) if block else None
        for part in (record_rows(data, order, root, tmp, bargs), menus, strings, view_rows()):
            for r in merge(part, verdicts):
                f.write(json.dumps(tally.add(r), sort_keys=True) + "\n")
    c = tally.counts()
    COUNTS.write_text(json.dumps({
        "load_order": order, "root": root.name if root else None, "block_args": bargs,
        "menu_swfs_per_archive": {k: v for k, v in per_archive.items() if v},
        "counts": c}, indent=1, sort_keys=True) + "\n")
    print(f"wrote {out} ({c['rows']} rows; root {root.name if root else 'none'}; {len(order)} plugins; "
          f"{c['by_kind'].get('menu', 0)} menus; {c['reachable']} reachable)")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gate", action="store_true", help="report counts from the existing inventory")
    ap.add_argument("--bind", action="store_true", help="with --gate: fail on reachable unreviewed rows (from 2.17)")
    ap.add_argument("--root", help="our plugin (default: $ARGONIA_PLUGIN, Data/Argonia.esm, out/plugin/Argonia.esm)")
    ap.add_argument("--out", type=Path, default=INVENTORY)
    ap.add_argument("--block", choices=sorted(BLOCKS), help="label rows by hops from this block's cells")
    a = ap.parse_args(argv)
    if a.gate:
        return gate(a.out, bind=a.bind or os.environ.get("IMMERSION_BIND") == "1")
    return build(a.root, a.out, a.block)


if __name__ == "__main__":
    sys.exit(main())
