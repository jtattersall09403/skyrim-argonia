"""Probe (0034, 1.15 ground/water): Skyrim.esm's tallest single water step at a cell edge, and how vanilla chains
steps: runs of 4-adjacent explicit-level cells each lower than the last (a falls chain over several cells).
Usage: python3 -m tools.argonia_world.terrain.probes.vanilla_step_chains [Skyrim.esm]  (reads only; prints numbers)"""
import struct
import sys
from pathlib import Path

from tools.argonia_world.terrain.esm import records
from tools.argonia_world.terrain.probes.vanilla_lake_cells import TAMRIEL

ESM = Path(sys.argv[1] if len(sys.argv) > 1 else "/home/ubuntu/games/skyrimse/Data/Skyrim.esm")
UPM = 70.0  # units per metre (skyrim_units)


def levels(blob: bytes) -> dict[tuple[int, int], float]:
    water, wrld = {}, None
    for r in records(blob):
        if r.sig == "WRLD":
            wrld = r.formid
        elif r.sig == "CELL" and wrld == TAMRIEL:
            xc, w, d = r.first("XCLC"), r.first("XCLW"), r.first("DATA")
            if xc and w and d and d[0] & 2:
                h = struct.unpack_from("<f", w)[0]
                if -1e6 < h < 1e6:
                    water[struct.unpack_from("<ii", xc)] = h
    return water


def main():
    water = levels(ESM.read_bytes())
    steps = []
    for (x, y), h in water.items():
        for o in ((x + 1, y), (x, y + 1)):
            if o in water and abs(water[o] - h) > 64:
                steps.append((abs(water[o] - h), (x, y), o))
    steps.sort(reverse=True)
    print(f"steps > 64 u: {len(steps)}; tallest 5 (units, m):")
    for d, a, b in steps[:5]:
        print(f"  {d:7.0f} u {d / UPM:6.1f} m  {a}->{b}")
    # chains: longest strictly descending 4-neighbour path, each step > 64 u
    down = {}
    for d, a, b in steps:
        hi, lo = (a, b) if water[a] > water[b] else (b, a)
        down.setdefault(hi, []).append(lo)
    memo = {}

    def longest(c):
        if c not in memo:
            memo[c] = max(([c] + longest(n) for n in down.get(c, [])), key=len, default=[c])
        return memo[c]
    chains = sorted((longest(c) for c in down), key=lambda p: (len(p), water[p[0]] - water[p[-1]]), reverse=True)
    seen, shown = set(), 0
    for p in chains:
        if p[0] in seen or shown >= 5:
            continue
        seen.update(p)
        shown += 1
        hs = [water[c] for c in p]
        print(f"chain {len(p) - 1} steps, total {(hs[0] - hs[-1]) / UPM:.1f} m, per step "
              + ", ".join(f"{(a - b) / UPM:.1f}" for a, b in zip(hs, hs[1:])) + f" m  from {p[0]}")
    multi = sum(1 for c in down if any(n in down for n in down[c]))
    print(f"cells starting a 2+ step chain: {multi}")


if __name__ == "__main__":
    main()
