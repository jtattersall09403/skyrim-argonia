"""Probe (1.15 ground): mean |dx| and |dy| (m per sample) in apron strips beyond each province edge (the materials
lane's streak measure). Usage: python3 -m tools.argonia_world.terrain.probes.apron_streaks"""
import numpy as np

from tools.argonia_world.terrain.grid import Sources

s = Sources.load()
p, n = s.pad, s.n
k = 200  # samples out from the border
mid = slice(p + n // 4, p + 3 * n // 4)
for name, (rs, cs) in {"west": (mid, slice(p - k, p)), "east": (mid, slice(p + n + 1, p + n + 1 + k)),
                       "north": (slice(p - k, p), mid), "south": (slice(p + n + 1, p + n + 1 + k), mid)}.items():
    h = s.heights(rs.start, rs.stop, cs.start, cs.stop)
    print(f"{name}: |dx| {np.abs(np.diff(h, axis=1)).mean():.3f}  |dy| {np.abs(np.diff(h, axis=0)).mean():.3f}")
