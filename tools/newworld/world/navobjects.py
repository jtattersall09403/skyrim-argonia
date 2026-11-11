"""The navmesh was cut round what stands on the ground: the placed trees, rocks and cliffs reached it.

    python3 -m tools.newworld.world.navobjects [--plugin out/newworld/plugin]     # two rows, PASS/FAIL; exit 1 on a FAIL

Reads the navmesh build's own records under <plugin>/navmesh (never its plan) and the placed-refs shards under
<plugin>/refs/<producer>/:
- `check.json` "objects": the placed objects' collision triangles the build rasterised. Zero means no placed object
  cut the mesh, whatever was placed.
- `build.json` "placed" "objects": how many placed objects the build was fed, against how many refs in the shards
  collide.

The hook. What counts as a ref that collides is the navmesh's own rule, so it is read from the navmesh tool, never
restated here: HOOK names the function, `tools.navmesh.placed.collidable_count(refs_dir, data_dir) -> int`, the
count of refs under refs/<producer>/cy*.jsonl whose base carries collision, and FED names where the build records
the count it was fed. While either is absent the second row fails and says which is owed.
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
HOOK = ("tools.navmesh.placed", "collidable_count")     # (refs_dir: Path, data_dir: Path) -> int
FED = ("build.json", "placed", "objects")               # <plugin>/navmesh/build.json["placed"]["objects"]: int


def collidable(refs: Path, data: Path) -> int | None:
    """The shards' refs that collide, by the navmesh tool's own rule; None while the tool has no such function."""
    try:
        fn = getattr(importlib.import_module(HOOK[0]), HOOK[1], None)
    except ImportError:
        return None
    return int(fn(refs, data)) if fn else None


def rows(plugin: Path, data: Path, count=collidable) -> list[tuple[str, object, bool, str]]:
    nav = plugin / "navmesh"
    out = []
    try:
        tris = json.loads((nav / "check.json").read_text()).get("objects")
    except (OSError, ValueError):
        tris = None
    out.append(("placed objects cut the navmesh (collision triangles rasterised > 0)", tris, bool(tris),
                "" if tris else "no placed object reached the navmesh build: its refs folder holds no shard it reads"))
    try:
        fed = json.loads((nav / FED[0]).read_text())
        for k in FED[1:]:
            fed = fed[k]
    except (OSError, ValueError, KeyError, TypeError):
        fed = None
    want = count(plugin / "refs", data)
    owed = [w for w, v in ((f"{nav.name}/{FED[0]} {' '.join(FED[1:])}", fed), (".".join(HOOK), want)) if v is None]
    out.append(("every ref that collides was fed to the navmesh (fed = collidable refs in the shards)",
                f"{fed} fed, {want} collidable", not owed and fed == want and fed > 0,
                f"owed by the navmesh tool: {', '.join(owed)}" if owed else ""))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--plugin", type=Path, default=REPO / "out/newworld/plugin")
    a = ap.parse_args(argv)
    data = Path(os.environ.get("ARGONIA_GAME_ROOT", Path.home() / "games/skyrimse")) / "Data"
    bad = 0
    for req, v, ok, det in rows(a.plugin, data):
        print(f"{'PASS' if ok else 'FAIL'}  navmesh objects: {req} = {v}" + (f"  ({det})" if det else ""))
        bad += not ok
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
