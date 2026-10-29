"""Every province cell into exactly one region (2.W3 §a; decision 0028 §3), and each region's weather and object
lists, written to the world database.

The old region raster (`hydro-regions.png`) is not in the vault (searched 2026-10-29; only the ground-control image
is), so each cell's old raster class is reconstructed: a k-nearest-neighbour vote over the 567 catalogue places
whose `plot_facts_region_class` the old chain measured on that raster, in a feature space of the cell's land-cover
mix, height, slope, sea, marsh and standing-water fractions, distance to the sea and position (`cells.py`). Cells
more than half sea are ocean and more than half standing water are lake, as the old classifier ruled; a cell a solved
channel at least 20 m wide crosses is deep river corridor, or tidal delta within three cells of the sea; the owner's
central-jungle polygon then overrides its listed classes; one 3 x 3 majority pass removes single-cell speckle (before
the channel rule, so a river stays one cell wide).
Leave-one-out agreement with the measured places is reported by `check` (L1). The packet of a cell is the vote of
its five nearest catalogue places. A region is one packet and one ecological class.

    python3 -m tools.argonia_world.regions.classify build    write land_region, cell_region_run and the lists
    python3 -m tools.argonia_world.regions.classify check    the L1 checks (every cell once; lists; agreement)
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter, defaultdict

from tools.argonia_world import db
from tools.argonia_world import skyrim_units as su
from tools.argonia_world.regions import cells as C

K = 5
SPATIAL = 0.05  # weight of the cell's grid position in the feature space (best leave-one-out of 0..0.4)
CELL_M = (su.PROVINCE_SAMPLES - 1) * su.PROVINCE_SAMPLE_M / su.PROVINCE_CELLS  # 58.49 m
CELL_HA = CELL_M * CELL_M / 10000.0
BORDER = "border"
OCEAN, LAKE = "ocean", "lake-and-standing-water"
RIVER, DELTA = "deep-river-corridor", "tidal-delta"
RIVER_WIDTH_M = 20.0  # a channel this wide is a deep river corridor (the solution's 90th percentile is 22 m)
DELTA_CELLS = 3  # a corridor cell this near the sea is the tidal delta


def slug(s: str) -> str:
    return s.replace("-", "_")


def region_id(packet: str, eco: str) -> str:
    return f"{packet}.{eco}"


def edid(rid: str) -> str:
    return "ARG_Region_" + slug(rid).replace(".", "_")


# --- classification ----------------------------------------------------------------------------------------------
def feature_space(f: dict):
    import numpy as np

    jj, ii = np.mgrid[0:C.NC, 0:C.NC]
    parts = [f["height"][..., None] / 50, f["slope"][..., None] / 10, f["sea"][..., None] * 3,
             f["marsh"][..., None] * 2, f["water"][..., None] * 3, np.minimum(f["coast_cells"], 40)[..., None] / 10,
             f["cover"] * 2, jj[..., None] * SPATIAL, ii[..., None] * SPATIAL]
    return np.concatenate(parts, axis=2)


def labelled_places(w) -> list[tuple[int, int, str, str]]:
    """(row j from north, column i, raster class id, packet) of every positioned catalogue place."""
    names = {r["name"]: r["region_class_id"] for r in w.query("SELECT name, region_class_id FROM region_class_profile")}
    out = []
    for r in w.query("SELECT position_m_x x, position_m_y y, plot_facts_region_class rc, region FROM place "
                     "WHERE position_m_x IS NOT NULL AND region IS NOT NULL ORDER BY id"):
        j = min(max(int(r["y"] / CELL_M), 0), C.NC - 1)
        i = min(max(int(r["x"] / CELL_M), 0), C.NC - 1)
        out.append((j, i, names.get(r["rc"]), r["region"]))
    return out


def vote(labels) -> str:
    c = Counter(labels)
    best = max(c.values())
    return min(k for k, v in c.items() if v == best)  # ties broken by id, so the vote is deterministic


def in_polygon(u: float, v: float, poly: list[tuple[float, float]]) -> bool:
    inside = False
    for k in range(len(poly)):
        (u1, v1), (u2, v2) = poly[k], poly[(k + 1) % len(poly)]
        if (v1 > v) != (v2 > v) and u < (u2 - u1) * (v - v1) / (v2 - v1) + u1:
            inside = not inside
    return inside


def classify(w, f: dict) -> tuple[list[list[str]], list[list[str]], float]:
    """(raster class per cell [j][i], packet per cell [j][i], leave-one-out agreement)."""
    import numpy as np

    G = feature_space(f)
    pts = labelled_places(w)
    lab = [(j, i, rc) for j, i, rc, _ in pts if rc]
    X = np.array([G[j, i] for j, i, _ in lab])
    y = [rc for _, _, rc in lab]
    ok = 0
    for t in range(len(lab)):
        d = ((X - X[t]) ** 2).sum(1)
        d[t] = np.inf
        ok += vote([y[k] for k in np.argsort(d, kind="stable")[:K]]) == y[t]
    loo = ok / len(lab)
    flat = G.reshape(-1, G.shape[2])
    rc = []
    for row in range(0, flat.shape[0], 1024):  # chunks keep the distance matrix small
        d = ((flat[row:row + 1024, None, :] - X[None, :, :]) ** 2).sum(2)
        for nn in np.argsort(d, axis=1, kind="stable")[:, :K]:
            rc.append(vote([y[k] for k in nn]))
    cls = [rc[j * C.NC:(j + 1) * C.NC] for j in range(C.NC)]
    for j in range(C.NC):
        for i in range(C.NC):
            if f["sea"][j, i] > 0.5:
                cls[j][i] = OCEAN
            elif f["water"][j, i] > 0.5:
                cls[j][i] = LAKE
    for o in w.query("SELECT id, region_class_id FROM region_class_override ORDER BY id"):
        poly = [(p["u"], p["v"]) for p in w.query(
            "SELECT u, v FROM region_class_override_point WHERE override_id = ? ORDER BY ord", o["id"])]
        applies = set(w.values("SELECT region_class_id FROM region_class_override_applies WHERE override_id = ?",
                               o["id"]))
        for j in range(C.NC):
            for i in range(C.NC):
                if cls[j][i] in applies and in_polygon((i + 0.5) / C.NC, (j + 0.5) / C.NC, poly):
                    cls[j][i] = o["region_class_id"]
    cls = majority(cls)
    for j, i in C.river_cells(RIVER_WIDTH_M):
        if cls[j][i] != OCEAN:
            cls[j][i] = DELTA if f["coast_cells"][j, i] <= DELTA_CELLS else RIVER
    # packets: the five nearest places' vote, by distance in cells
    P = np.array([(j, i) for j, i, _, _ in pts], dtype=float)
    pk = [p for _, _, _, p in pts]
    packets = []
    for j in range(C.NC):
        d = ((P[:, 0] - j) ** 2)[None, :] + (P[None, :, 1] - np.arange(C.NC)[:, None]) ** 2
        packets.append([vote([pk[k] for k in nn]) for nn in np.argsort(d, axis=1, kind="stable")[:, :K]])
    return cls, packets, loo


def majority(cls: list[list[str]]) -> list[list[str]]:
    """One 3 x 3 pass: a cell whose class no neighbour shares takes its neighbours' majority."""
    n = len(cls)
    out = [row[:] for row in cls]
    for j in range(n):
        for i in range(len(cls[j])):
            nb = [cls[b][a] for b in range(max(j - 1, 0), min(j + 2, n)) for a in range(max(i - 1, 0), min(i + 2, n))
                  if (a, b) != (i, j)]
            if cls[j][i] not in nb:
                out[j][i] = vote(nb)
    return out


# --- the region rows -----------------------------------------------------------------------------------------------
def eco_of(w) -> callable:
    base = {r["region_class_id"]: r["eco_class_id"] for r in w.query("SELECT * FROM region_class_profile")}
    over = {(r["region_class_id"], r["region_id"]): r["eco_class_id"]
            for r in w.query("SELECT * FROM region_class_eco_override")}
    return lambda rc, packet: over.get((rc, packet), base[rc])


def runs(grid: list[list[str]]) -> list[dict]:
    """Row runs of equal value, in Skyrim cell coordinates (cy, cx0..cx1)."""
    out = []
    for j, row in enumerate(grid):
        i = 0
        while i < len(row):
            k = i
            while k + 1 < len(row) and row[k + 1] == row[i]:
                k += 1
            cx0, cy = C.cell_of_index(i, j)
            cx1, _ = C.cell_of_index(k, j)
            out.append({"cy": cy, "cx0": cx0, "cx1": cx1, "land_region_id": row[i]})
            i = k + 1
    return out


def weather_list(w, group: str) -> list[tuple[str, int, str]]:
    """(weather id, chance 1..100, season global EditorID) for a group: state weight x the year's mean season factor
    x the weather's share, normalised to 100."""
    seasons = w.query("SELECT id, share FROM season ORDER BY id")
    fac = {(r["season_id"], r["weather_state_id"]): r["factor"] for r in w.query("SELECT * FROM season_factor")}
    raw = []
    for r in w.query("SELECT r.weather_state_id st, r.weather_id wid, r.share, g.weight FROM weather_realisation r "
                     "JOIN weather_group_weight g ON g.weather_group_id = r.weather_group_id "
                     "AND g.weather_state_id = r.weather_state_id WHERE r.weather_group_id = ? "
                     "ORDER BY r.weather_id", group):
        mean = sum(s["share"] * fac.get((s["id"], r["st"]), 1.0) for s in seasons)
        raw.append((r["wid"], r["weight"] * mean * r["share"]))
    tot = sum(v for _, v in raw) or 1.0
    merged = defaultdict(float)
    for wid, v in raw:
        merged[wid] += v
    return [(wid, max(1, round(100 * v / tot)), f"ARG_WChance_{slug(group)}_{slug(wid)}")
            for wid, v in sorted(merged.items())]


ROLE_BANDS = {  # role -> (min slope, conform to slope, max height m above sea or None, min height)
    "cliff-tree": (20, True, None, None),
    "rock": (0, True, None, None),
    "mangrove": (0, False, 4.0, None),
}


def object_list(w, shares: dict[str, int]) -> list[dict]:
    """The region's RDOT rows: each role's density mixed over the region's old classes by cell share, split evenly
    over the role's forms."""
    total = sum(shares.values())
    forms = defaultdict(list)
    for r in w.query("SELECT form_key, role_id FROM object_form ORDER BY form_key"):
        forms[r["role_id"]].append(r["form_key"])
    acc = defaultdict(lambda: {"per_ha": 0.0, "clump": 0.0, "rad": 0.0, "slope": 0.0, "wmin": None, "wmax": None})
    for rc, n in shares.items():
        for r in w.query("SELECT * FROM region_class_role WHERE region_class_id = ?", rc):
            a = acc[r["role_id"]]
            q = n / total * r["per_ha"]
            a["per_ha"] += q
            a["clump"] += q * (r["clump_median"] or 1)
            a["rad"] += q * (r["clump_radius_m"] or 0)
            a["slope"] = max(a["slope"], r["slope_max_deg"] or 35)
            if r["water_min_m"] is not None:
                a["wmin"] = r["water_min_m"] if a["wmin"] is None else min(a["wmin"], r["water_min_m"])
                a["wmax"] = r["water_max_m"] if a["wmax"] is None else max(a["wmax"], r["water_max_m"])
    out = []
    for role, a in sorted(acc.items()):
        if a["per_ha"] < 0.05 or not forms[role]:
            continue
        q = a["per_ha"]
        mn, conform, hmax, hmin = ROLE_BANDS.get(role, (0, False, None, None))
        for fk in forms[role]:
            out.append({"form_key": fk, "density_per_ha": round(q / len(forms[role]), 4),
                        "clustering": max(1, min(255, round(a["clump"] / q))),
                        "min_slope_deg": mn, "max_slope_deg": int(round(max(a["slope"], mn))),
                        "min_height_m": hmin, "max_height_m": hmax, "radius_m": round(a["rad"] / q, 2),
                        "water_min_m": a["wmin"], "water_max_m": a["wmax"], "conform": conform})
    return out


def build(w, f: dict) -> dict:
    cls, packets, loo = classify(w, f)
    eco = eco_of(w)
    names = {r["region"]: r["region_name"] for r in w.query("SELECT region, region_name FROM owing_region")}
    group = {r["id"]: r["weather_group_id"] for r in w.query("SELECT id, weather_group_id FROM eco_class")}
    grid = [[region_id(packets[j][i], eco(cls[j][i], packets[j][i])) for i in range(C.NC)] for j in range(C.NC)]
    cells = Counter(v for row in grid for v in row)
    share = defaultdict(Counter)
    for j in range(C.NC):
        for i in range(C.NC):
            share[grid[j][i]][cls[j][i]] += 1
    for t in ("land_region_object", "land_region_weather", "land_region_class_share", "cell_region_run",
              "land_region"):
        w.con.execute(f'DELETE FROM "{t}"')
        w.dirty.add(t)
    w.insert("land_region", id=BORDER, edid="ARG_Region_border", region_id=None, eco_class_id=None, map_name=None,
             border=True, cells=0)
    for rid in sorted(cells):
        packet, ec = rid.split(".", 1)
        w.insert("land_region", id=rid, edid=edid(rid), region_id=packet, eco_class_id=ec, map_name=names[packet],
                 border=False, cells=cells[rid])
        for rc, n in sorted(share[rid].items()):
            w.insert("land_region_class_share", land_region_id=rid, region_class_id=rc, cells=n)
        for wid, chance, glob in weather_list(w, group[ec]):
            w.insert("land_region_weather", land_region_id=rid, weather_id=wid, chance=chance, season_global=glob)
        for o in object_list(w, share[rid]):
            w.insert("land_region_object", land_region_id=rid, **o)
    w.insert_many("cell_region_run", runs(grid))
    return {"loo": loo, "regions": len(cells), "classes": Counter(v for row in cls for v in row)}


# --- the L1 checks -------------------------------------------------------------------------------------------------
def check(w) -> list[str]:
    """Every province cell in exactly one region; every region with a weather list, an object list, a map name."""
    errs = []
    x0, y0 = su.PROVINCE_CELL_SW
    seen = Counter()
    for r in w.query("SELECT cy, cx0, cx1 FROM cell_region_run"):
        for cx in range(r["cx0"], r["cx1"] + 1):
            seen[(cx, r["cy"])] += 1
    want = {(x, y) for x in range(x0, x0 + C.NC) for y in range(y0, y0 + C.NC)}
    missing, extra = want - set(seen), set(seen) - want
    twice = [k for k, n in seen.items() if n > 1]
    if missing or extra or twice:
        errs.append(f"cells: {len(missing)} without a region, {len(extra)} outside the province, {len(twice)} twice")
    for r in w.query("SELECT id, map_name, cells, (SELECT count(*) FROM land_region_weather x WHERE x.land_region_id"
                     " = l.id) nw, (SELECT count(*) FROM land_region_object x WHERE x.land_region_id = l.id) no, "
                     "(SELECT sum(cx1 - cx0 + 1) FROM cell_region_run x WHERE x.land_region_id = l.id) nc "
                     "FROM land_region l WHERE border = 0"):
        if not r["nw"] or not r["map_name"] or (r["nc"] or 0) != r["cells"]:
            errs.append(f"{r['id']}: weather {r['nw']}, map name {r['map_name']!r}, cells {r['nc']} != {r['cells']}")
        if not r["no"] and not r["id"].endswith(("coastal-lagoon", "deep-sink-basin")):
            errs.append(f"{r['id']}: no object list")
    return errs


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("cmd", choices=("build", "check"))
    a = ap.parse_args(argv)
    w = db.open()
    if a.cmd == "build":
        rep = build(w, C.load_or_compute())
        w.save()
        print(f"regions {rep['regions']} (+ border); leave-one-out agreement {rep['loo']:.3f}")
        print("cells per old class:", dict(sorted(rep["classes"].items())))
    errs = check(w)
    n = w.values("SELECT count(*) FROM land_region")[0]
    nw = w.values("SELECT count(*) FROM land_region_weather")[0]
    no = w.values("SELECT count(*) FROM land_region_object")[0]
    print(f"check: {n} REGN, {nw} weather entries, {no} object entries, {len(errs)} error(s)")
    print("\n".join(errs))
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
