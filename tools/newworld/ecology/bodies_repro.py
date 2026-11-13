"""The bodies-and-sinking reproduction (walk 2, lines 22 and 25) as two console batch files for the play machine.

    python3 -m tools.newworld.ecology.bodies_repro [--esm <ArgoniaNewWorld.esm>] [--out <dir>] [--index <hex load index>]

The walk's save showed, on Aphon Isle, a living bandit 22 units under flat land and a dead one 5 units under it. This picks
the built file's placed bandit and spider crab nearest that spot and writes:
- `repro_a.txt` (run `bat repro_a` in game): goes to the spot, logs each actor's height and life, then kills each;
- `repro_b.txt` (run `bat repro_b` some seconds later): logs each again (dead or not, height, swimming).
Both log to `bodies_repro_log.txt` beside the game (`scof`), so the result is written output: heights read against the
land height this prints for each actor's x, y from the same file.
"""
from __future__ import annotations

import argparse
import struct
from pathlib import Path

from tools.navmesh import esm as E, land_gap

REPO = Path(__file__).resolve().parents[3]
ESM = REPO / "out/newworld/plugin/ArgoniaNewWorld.esm"
WORLD = "ArgoniaBlackMarsh"
SPOT = (-270724.0, -766271.0)   # Aphon Isle: the walk save's sunken living bandit, on flat land
KINDS = {"bandit": "Bandit", "crab": "SpiderCrab"}


def nearest(esm: Path) -> dict[str, tuple[int, tuple[float, float, float], str]]:
    """Each kind's placed ACHR nearest SPOT: kind -> (ref form id without load index, position, base editor id)."""
    npc: dict[int, str] = {}
    best: dict[str, tuple[float, int, tuple, str]] = {}
    achr = []
    for r in E.records(esm, {b"NPC_", b"ACHR"}):
        s = dict(E.subrecords(r.data))
        if r.sig == b"NPC_":
            npc[r.fid] = s.get(b"EDID", b"")[:-1].decode("cp1252")
        else:
            achr.append((r.fid, struct.unpack("<I", s[b"NAME"])[0], struct.unpack_from("<fff", s[b"DATA"])))
    for fid, base, pos in achr:
        name = npc.get(base, "")
        for kind, key in KINDS.items():
            if key in name:
                d = (pos[0] - SPOT[0]) ** 2 + (pos[1] - SPOT[1]) ** 2
                if kind not in best or d < best[kind][0]:
                    best[kind] = (d, fid & 0xFFFFFF, pos, name)
    missing = [k for k in KINDS if k not in best]
    if missing:
        raise SystemExit(f"no placed {missing} in {esm}")
    return {k: v[1:] for k, v in best.items()}


def land_at(esm: Path, pos) -> float:
    cx, cy = int(pos[0] // 4096), int(pos[1] // 4096)
    world = next(r.fid for r in E.records(esm, {b"WRLD"}, {b"WRLD"}))
    land, _ = land_gap.read(esm, world, box=(cx, cy, cx, cy))
    h = land[(cx, cy)]
    u, v = (pos[0] - cx * 4096) / 128, (pos[1] - cy * 4096) / 128
    return min(land_gap.land_z(h, u, v))


def batches(found: dict, index: str) -> tuple[str, str]:
    cx, cy = int(SPOT[0] // 4096), int(SPOT[1] // 4096)
    a = ["scof bodies_repro_log.txt", f"cow {WORLD} {cx} {cy}"]
    b = ["scof bodies_repro_log.txt"]
    for kind, (fid, _, _) in found.items():
        ref = f"{index}{fid:06X}"
        a += [f"prid {ref}", "moveto player", "getpos x", "getpos y", "getpos z", "getdead", "kill"]
        b += [f"prid {ref}", "getpos x", "getpos y", "getpos z", "getdead", "isswimming"]
    return "\n".join(a + ["scof 0"]) + "\n", "\n".join(b + ["scof 0"]) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--esm", type=Path, default=ESM)
    ap.add_argument("--out", type=Path, default=REPO / "out/newworld/bodies_repro")
    ap.add_argument("--index", default="0A", help="ArgoniaNewWorld.esm's load index on the card (0A at walk 2)")
    o = ap.parse_args(argv)
    found = nearest(o.esm)
    o.out.mkdir(parents=True, exist_ok=True)
    ta, tb = batches(found, o.index)
    (o.out / "repro_a.txt").write_text(ta)
    (o.out / "repro_b.txt").write_text(tb)
    for kind, (fid, pos, name) in found.items():
        print(kind, f"{o.index}{fid:06X}", name, "placed", [round(p, 1) for p in pos], "land", round(land_at(o.esm, pos), 1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
