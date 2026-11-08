"""Danger bands for every cell (nw-01 step 3c): how dangerous the land is, fixed in the world (decision 0035: the
player grows into a band, the band never grows with the player).

The rules, applied in order, each cell keeping the first that sets it:
1. Safe (D0): the cells of a city or town (a metropolis's or large city's eight neighbours too): guards keep it.
2. Settled (D1): the cells a major road passes through and their neighbours; the cell of every village, hamlet,
   outpost, fort, estate, farm and other worked place.
3. The rest by depth into the province: a cell's distance in cells from the province's outer edge (the open sea and
   the border with foreign land), measured over land and inland water, sets its base band: under 4 cells D2, under 10
   D3, under 16 D4, deeper D5. The edge is safer; the heartland is the most dangerous.
4. The region's researched baseline (`region.danger_band_id`), when two or more bands from that base, moves it one
   band toward itself (a quiet region tames its deep cells, a dreadful one darkens its edge); a base one band from
   the baseline stands, so the heart of a dreadful region keeps the province's worst band.
5. A minor road lowers the cells it passes through by one band, never below D1.
Sea cells take their region's baseline within 2 cells of a coast, and one band higher (at most D3) beyond.
Margin cells (border scenery past the province) take no band; the province's edge is measured against them.

    from tools.newworld import danger; danger.assign(w)     # fills cell.danger_band_id and cell.danger_why
"""
from __future__ import annotations

from collections import deque

from tools.argonia_world import db
from tools.newworld.frame import px_to_cell

RANK = {"D0": 0, "D1": 1, "D2": 2, "D3": 3, "D4": 4, "D5": 5}
BAND = {v: k for k, v in RANK.items()}
DEPTH = ((4, "D2"), (10, "D3"), (16, "D4"))       # (cells from the edge under, band); deeper is D5
SAFE_KINDS = {"city", "town"}
SETTLED_KINDS = {"village", "hamlet", "outpost", "fort", "prison", "estate", "farm", "homestead", "logging-camp",
                 "quarry", "mine", "lighthouse", "ferry", "station", "belvedere"}
NB8 = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy]


def assign(w: db.World) -> None:
    cells = {(c.x, c.y): c for c in w.rows("cell") if not c.margin}   # the margin is scenery: no band
    regions = {r.id: r for r in w.rows("region")}
    sea = {k for k, c in cells.items() if regions[c.region_id].kind == "sea"}
    band: dict = {}
    why: dict = {}

    def put(k, b, reason):
        if k in cells and k not in band:
            band[k], why[k] = b, reason

    for p in w.rows("place"):
        if p.place_kind_id in SAFE_KINDS:
            put((p.cell_x, p.cell_y), "D0", f"inside {p.name}")
            if p.symbol_id in ("settlement.metropolis", "settlement.large-city"):
                for dx, dy in NB8:
                    put((p.cell_x + dx, p.cell_y + dy), "D0", f"inside {p.name}")
    for r in w.rows("road"):
        if r.road_class_id != "major":
            continue
        for v in w.rows("road_vertex", road_id=r.id):
            cx, cy = px_to_cell(v.px, v.py)
            for dx, dy in [(0, 0)] + NB8:
                put((cx + dx, cy + dy), "D1", "on or beside a major road")
    for p in w.rows("place"):
        if p.place_kind_id in SETTLED_KINDS:
            put((p.cell_x, p.cell_y), "D1", f"at {p.name}")

    # depth from the outer edge: multi-source BFS over non-sea cells from those touching the sea or the scope's rim
    land = {k for k in cells if k not in sea}
    depth = {}
    q = deque()
    for k in land:
        if any((k[0] + dx, k[1] + dy) in sea or (k[0] + dx, k[1] + dy) not in cells for dx, dy in NB8):
            depth[k] = 0
            q.append(k)
    while q:
        k = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (k[0] + dx, k[1] + dy)
            if n in land and n not in depth:
                depth[n] = depth[k] + 1
                q.append(n)
    minor = set()
    for r in w.rows("road"):
        if r.road_class_id == "minor":
            minor |= {px_to_cell(v.px, v.py) for v in w.rows("road_vertex", road_id=r.id)}
    for k in land:
        if k in band:
            continue
        d = depth.get(k, 99)
        b = next((bb for lim, bb in DEPTH if d < lim), "D5")
        reason = f"{d} cells from the province's edge"
        base = regions[cells[k].region_id].danger_band_id
        if base and abs(RANK[base] - RANK[b]) >= 2:
            step = 1 if RANK[base] > RANK[b] else -1
            b = BAND[RANK[b] + step]
            reason += f"; moved toward {regions[cells[k].region_id].name}'s baseline {base}"
        if k in minor and RANK[b] > 1:
            b = BAND[RANK[b] - 1]
            reason += "; a minor road"
        put(k, b, reason)
    # seas
    coast = {k for k in sea if any((k[0] + dx, k[1] + dy) in land for dx in range(-2, 3) for dy in range(-2, 3))}
    for k in sea:
        base = regions[cells[k].region_id].danger_band_id or "D2"
        if k in coast:
            put(k, base, f"coastal water of {regions[cells[k].region_id].name}")
        else:
            put(k, BAND[min(RANK[base] + 1, 3)], f"open water of {regions[cells[k].region_id].name}")
    for k, c in cells.items():
        w.update("cell", k[0], k[1], danger_band_id=band.get(k), danger_why=why.get(k))
