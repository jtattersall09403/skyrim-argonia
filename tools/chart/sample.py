"""A small synthetic world for the gate: an island with a ridge, a marsh, two rivers, two roads and the seven cities,
rendered at 512^2. Its hash is pinned in sample-manifest.json; any change to the drawing changes it (re-pin with
`python -m tools.chart sample` after looking at the stills)."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from tools.chart.data import CITIES, Features, Line, Place

MANIFEST = Path(__file__).with_name("sample-manifest.json")
SIZE = 512


def features(n: int = 126) -> Features:
    s = 1.82784 * 4032 / n  # the real span on a coarse grid; 126 cells of one sample: 4 px each at 512, on the tile lattice
    yy, xx = np.mgrid[0:n + 1, 0:n + 1].astype(np.float32) / n
    d = np.hypot(xx - 0.45, yy - 0.45)
    ground = (60 * (0.42 - d) / 0.42 + 200 * np.exp(-((xx - 0.3) ** 2 + (yy - 0.25) ** 2) / 0.01)).astype(np.float32)
    cover = np.full(ground.shape, 17, np.int16)
    cover[ground < 0] = 35
    cover[(ground >= 0) & (ground < 12)] = 7  # a marsh fringe
    cover[(ground >= 30) & (xx > 0.42)] = 20  # a wood on the east slope
    span = n * s
    rivers = [Line("river.a", np.array([[0.3, 0.3], [0.45, 0.5], [0.6, 0.7], [0.72, 0.86]]) * span, True, 3.0),
              Line("river.b", np.array([[0.2, 0.5], [0.3, 0.6], [0.45, 0.62]]) * span, False, 1.0)]
    roads = [Line("route.road.a", np.array([[0.2, 0.3], [0.5, 0.35], [0.7, 0.5]]) * span, True, 2.0, "trunk"),
             Line("route.road.b", np.array([[0.5, 0.35], [0.45, 0.6]]) * span, False, 1.0, "track"),
             Line("route.path.c", np.array([[0.33, 0.5], [0.25, 0.4]]) * span, False, 0.7, "footpath")]
    names = ["Gideon", "Soulrest", "Lilmoth", "Blackrose", "Archon", "Stormhold", "Thorn"]
    spots = [(0.3, 0.42), (0.15, 0.6), (0.5, 0.7), (0.38, 0.68), (0.65, 0.45), (0.4, 0.2), (0.62, 0.22)]
    places = [Place(pid, nm, x * span, y * span, "settlement", 5, True) for pid, nm, (x, y) in zip(CITIES, names, spots)]
    places += [Place("place.x.claywater", "Claywater", 0.33 * span, 0.5 * span, "settlement", 2, False),
               Place("place.x.ruin", "Old Stones", 0.55 * span, 0.3 * span, "ruin", 1, False),
               Place("place.x.camp", "Reed Camp", 0.25 * span, 0.35 * span, "camp", 0, False)]
    return Features(ground=ground, cover=cover, sea_level_m=0.0, rivers=rivers, roads=roads, places=places,
                    sample_m=s, cell_samples=1)


def render_sample():
    from tools.chart import render

    return render.Renderer(features(), SIZE).run()


def sample_hash() -> str:
    from tools.chart.__main__ import digest

    c = render_sample()
    return digest(c.base, c.ink, c.revealed, extra=json.dumps(c.index, sort_keys=True).encode())


def pinned() -> str:
    return json.loads(MANIFEST.read_text())["sha256"]
