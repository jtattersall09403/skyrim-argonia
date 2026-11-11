"""Proof that a keyed stage's standing output was made from today's inputs: the key its tool stored beside the
output, against the same key computed now by the tool's own functions. Read-only; exit 0 when they are equal.

    python3 -m tools.newworld.proofs land|landcover|paint [--plugin out/newworld/plugin]

tools/newworld/rebuild.py asks this of a stage it holds no stamp for. It lives here, outside the tools, because each
of these tools hashes its own file into its key: a line added to the tool would make its whole output stale.
The key's make-up is each tool's, restated here beside the lines it comes from; a tool that changes how it keys
changes its line here in the same commit (the proof then fails closed: the stage runs).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def land(plugin: Path) -> tuple[str, str]:
    """world/land.py build(): f"{build id}:{heightmap sha256[:16]}:{code_key()}" in land/manifest.json "key"."""
    from tools.newworld.world import land as L
    from tools.newworld.world import units as su
    terrain = REPO / "out/newworld/terrain"
    now = f"{su.load_grid(terrain / 'build.json').build_id}:{L.sha256_file(terrain / 'heightmap.npy')[:16]}:{L.code_key()}"
    return json.loads((plugin / "land/manifest.json").read_text()).get("key"), now


def landcover(plugin: Path) -> tuple[str, str]:
    """landcover.py build(): f"{build id}:{_hash(inputs)}" in landcover/key.txt, with stats.json written last."""
    from tools.newworld import frame as f
    from tools.newworld import landcover as lc
    inputs = [lc.TERRAIN / "build.json", f.OUT / "water_classified.json", f.OUT / "cell_region.json",
              f.OUT / "margin_cells.json", lc.TERRAIN / "places_terrain.json", Path(lc.__file__)] + \
             [lc.DB / f"{t}.jsonl" for t in ("habitat", "region_habitat", "road", "road_vertex")]
    now = f"{json.loads((lc.TERRAIN / 'build.json').read_text())['id']}:{lc._hash(inputs)}"
    return (lc.OUT / "key.txt").read_text() if (lc.OUT / "stats.json").exists() else "(unfinished)", now


def paint(plugin: Path) -> tuple[str, str]:
    """world/texture.py build(): f"{land manifest key}:{landcover key.txt}:{code_key()}" in tex/manifest.json "key",
    the manifest listing every cell row of the grid (a sample run lists its rows alone)."""
    from tools.newworld.world import texture as tx
    man = json.loads((plugin / "land/manifest.json").read_text())
    now = f"{man['key']}:{(tx.LC / 'key.txt').read_text()}:{tx.code_key()}"
    m = json.loads((plugin / "tex/manifest.json").read_text())
    whole = len(m.get("shards") or []) == man["grid"]["cy_top"] - man["grid"]["cy_bottom"] + 1
    return m.get("key") if whole else "(a sample of rows)", now


PROOFS = {"land": land, "landcover": landcover, "paint": paint}


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] not in PROOFS:
        print(f"usage: python3 -m tools.newworld.proofs {'|'.join(PROOFS)} [--plugin DIR]", file=sys.stderr)
        return 2
    plugin = Path(argv[argv.index("--plugin") + 1]) if "--plugin" in argv else REPO / "out/newworld/plugin"
    try:
        stored, now = PROOFS[argv[0]](plugin)
    except (OSError, ValueError, KeyError) as e:
        print(f"{argv[0]}: no record to prove it ({type(e).__name__}: {e})")
        return 1
    ok = stored == now
    print(f"{argv[0]}: its key is today's" if ok else f"{argv[0]}: its key {stored} is not today's {now}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
