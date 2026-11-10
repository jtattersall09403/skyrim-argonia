"""Ground danger for every cell: what roams there, fixed in the world (decision 0035: the player grows into a band,
the band never grows with the player). The places' own facts (disposition, strength inside, reward) are
tools/newworld/place_danger.py's; the recipe is docs/design/danger.md.

Each cell gets two bands, each with its reason:
- natural (`cell.natural_band_id`): the country as it is, before any town or road tames it.
  1. Depth into the province: a cell's distance in cells from the province's outer edge (the open sea and the
     border with foreign land), measured over land and inland water: under 4 cells D2, under 10 D3, under 16 D4,
     deeper D5. The edge is safer; the heartland is the most dangerous.
  2. The region's researched baseline (`region.danger_band_id`), when two or more bands from that depth band, moves
     it one band toward itself (a quiet region tames its deep cells, a dreadful one darkens its edge); one band
     from the baseline stands, so the heart of a dreadful region keeps the province's worst band.
  Sea cells take their region's baseline within 2 cells of a coast, and one band higher (at most D3) beyond.
- ground (`cell.danger_band_id`): what a traveller meets there now, the natural band less what keeps it down.
  3. A city or town makes its cell Safe (D0), and a metropolis or large city its eight neighbours too: guards keep it.
  4. Otherwise the cell is lowered by the strongest one of: a major road through it, two bands; a minor road, one
     band; a village, or a fort or keep that is garrisoned, one band (it holds its own footprint). Never below D1,
     and the lowerings do not add up. Hamlets, outposts, farms, mines, stations, ferries and camps change nothing:
     their people live with the country round them.
Margin cells (border scenery past the province) take no band; the province's edge is measured against them.

    from tools.newworld import danger; danger.assign(w)     # fills cell natural_band_id, danger_band_id, danger_why
"""
from __future__ import annotations

from collections import deque

from tools.argonia_world import db
from tools.newworld.frame import px_to_cell

RANK = {"D0": 0, "D1": 1, "D2": 2, "D3": 3, "D4": 4, "D5": 5}
BAND = {v: k for k, v in RANK.items()}
DEPTH = ((4, "D2"), (10, "D3"), (16, "D4"))       # (cells from the edge under, band); deeper is D5
SAFE_KINDS = {"city", "town"}                     # guards: the cell is Safe
HOLDING_KINDS = {"village"}                       # holds its footprint: one band
GARRISON_KINDS = {"fort", "keep"}                 # holds its footprint when garrisoned: one band
SOFTEN = {"major": 2, "minor": 1}                 # a road through the cell lowers it this many bands
NB8 = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy]


def natural(w: db.World, cells: dict, regions: dict) -> tuple[dict, dict]:
    """The natural band of every non-margin cell and its reason (rules 1 and 2 and the sea)."""
    sea = {k for k, c in cells.items() if regions[c.region_id].kind == "sea"}
    land = {k for k in cells if k not in sea}
    depth, q = {}, deque()
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
    band, why = {}, {}
    for k in land:
        d = depth.get(k, 99)
        b = next((bb for lim, bb in DEPTH if d < lim), "D5")
        reason = f"{d} cells from the province's edge {b}"
        region = regions[cells[k].region_id]
        base = region.danger_band_id
        if base and abs(RANK[base] - RANK[b]) >= 2:
            b = BAND[RANK[b] + (1 if RANK[base] > RANK[b] else -1)]
            reason += f", moved toward {region.name}'s baseline {base}: {b}"
        band[k], why[k] = b, reason
    for k in sea:
        region = regions[cells[k].region_id]
        base = region.danger_band_id or "D2"
        if any((k[0] + dx, k[1] + dy) in land for dx in range(-2, 3) for dy in range(-2, 3)):
            band[k], why[k] = base, f"coastal water of {region.name} {base}"
        else:
            band[k] = BAND[min(RANK[base] + 1, 3)]
            why[k] = f"open water of {region.name} {band[k]}"
    return band, why


def softeners(w: db.World) -> tuple[dict, dict]:
    """What keeps each cell down: Safe cells (with the town's name) and the strongest lowering (bands, reason)."""
    safe, lower = {}, {}

    def put(k, n, reason):
        if n > lower.get(k, (0, ""))[0]:
            lower[k] = (n, reason)

    for p in w.rows("place"):
        k = (p.cell_x, p.cell_y)
        if p.place_kind_id in SAFE_KINDS:
            safe.setdefault(k, p.name)
            if p.symbol_id in ("settlement.metropolis", "settlement.large-city"):
                for dx, dy in NB8:
                    safe.setdefault((k[0] + dx, k[1] + dy), p.name)
        elif p.place_kind_id in HOLDING_KINDS or (p.place_kind_id in GARRISON_KINDS and p.status == "garrisoned"):
            put(k, 1, f"{p.name} holds its footprint")
    for r in w.rows("road"):
        n = SOFTEN.get(r.road_class_id)
        if n:
            for v in w.rows("road_vertex", road_id=r.id):
                put(px_to_cell(v.px, v.py), n, f"a {r.road_class_id} road")
    return safe, lower


def assign(w: db.World) -> None:
    cells = {(c.x, c.y): c for c in w.rows("cell") if not c.margin}   # the margin is scenery: no band
    regions = {r.id: r for r in w.rows("region")}
    nat, nwhy = natural(w, cells, regions)
    safe, lower = softeners(w)
    for k in cells:
        b, why = nat[k], nwhy[k]
        if k in safe and regions[cells[k].region_id].kind != "sea":
            g, why = "D0", f"inside {safe[k]}: guards keep it (natural: {why})"
        elif k in lower and RANK[b] > 1:
            n, reason = lower[k]
            g = BAND[max(1, RANK[b] - n)]
            why = f"{why}; {reason} lowers it to {g}"
        else:
            g = b
        w.update("cell", k[0], k[1], natural_band_id=b, danger_band_id=g, danger_why=why)
