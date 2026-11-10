"""The travel network of the new world: boat, coach and rootworm (docs/design/travel-network.md).

The network is authored in `newworld/sources/travel/network.json` (modes, operators, stops, routes, remote places);
this module measures it on the world's own roads and water and loads it into the database:

- a stop is a place's promise: a give of the mode's kind in the place record (`boat-stop`, `coach-stop`,
  `rootworm-stop`), named by the network's stop row (operator, hub or spoke, why);
- a route runs between two stops of one mode, both ways. Its distance is measured: a boat's along navigable water
  (the water raster's bodies of the mode's kinds and widths, shortest water path, the length over open sea kept apart),
  a coach's along roads of the mode's class (the road graph), a rootworm's straight through the Hist roots;
  its fare and hours follow the mode's fixed rule (never levelled, decision 0035);
- every place without a stop gets its approach: the nearest stop and how one gets there from it (by road, across the
  marsh, by water, by diving), or the network's stated reason it is remote.

    python3 -m tools.newworld.travel candidates   # what each place's ground offers each mode (authoring aid)
    python3 -m tools.newworld.travel check        # the network's checks on the built database
    python3 -m tools.newworld.travel report       # counts, hubs, unreachable places
build_db calls `load(w)` with the rest.
"""
from __future__ import annotations

import heapq
import json
import math
import sys
from collections import defaultdict

import numpy as np

from tools.newworld import frame as f

NETWORK = f.ROOT / "sources" / "travel" / "network.json"
M_PER_PX = f.UNITS_PER_PX / f.UNITS_PER_METRE   # 2.93 m
DOWN = 2                                        # the water search runs on 2 x 2 px blocks (max-pooled: a channel stays open)
OPEN_SEA = ("ocean", "bay")                     # open sea: a raft-master's craft does not cross it
TABLES = ("travel_mode", "travel_mode_water", "travel_operator", "travel_stop", "travel_route", "travel_approach")


def network() -> dict:
    return json.loads(NETWORK.read_text(encoding="utf-8"))


def fare(mode: dict, distance_m: float) -> int:
    """The mode's fixed fare: base plus a rate per km, rounded to the mode's step, held between its floor and cap."""
    raw = mode["fare_base"] + mode["fare_per_km"] * distance_m / 1000.0
    step = mode["fare_step"]
    return int(min(mode["fare_max"], max(mode["fare_min"], step * round(raw / step))))


def hours(mode: dict, distance_m: float) -> int:
    """Hours on the way, boarding included, whole hours (at least one)."""
    return max(1, round(mode["board_h"] + distance_m / 1000.0 / mode["speed_kmh"]))


# ---- the ground: water and roads ------------------------------------------------------------------------------------

_WATER: dict = {}


def _water(w, kinds_key: tuple) -> tuple[np.ndarray, np.ndarray]:
    """(navigable, open sea) on the DOWN grid for a mode's water rows ((kind, min width), ...), from the database's
    water bodies (owner edits applied) over the water raster."""
    if kinds_key in _WATER:
        return _WATER[kinds_key]
    from PIL import Image
    R = np.asarray(Image.open(f.OUT / "water_classified.png")).astype(np.int32)
    rows = json.loads((f.OUT / "water_classified.json").read_text())
    kind_of = {r.id: (r.water_kind_id, r.width_m) for r in w.rows("water_body")}
    want = dict(kinds_key)
    nav = np.zeros(R.max() + 1, bool)
    sea = np.zeros(R.max() + 1, bool)
    for r in rows:
        k, width = kind_of.get(r["id"], (r["water_kind_id"], r.get("width_m")))
        if k in want and (width is None or want[k] is None or width >= want[k]):
            nav[r["raster_index"]] = True
        sea[r["raster_index"]] = k in OPEN_SEA
    h, wd = (R.shape[0] // DOWN) * DOWN, (R.shape[1] // DOWN) * DOWN

    def pool(m):
        return m[:h, :wd].reshape(h // DOWN, DOWN, wd // DOWN, DOWN).any(axis=(1, 3))
    _WATER[kinds_key] = pool(nav[R]), pool(sea[R])
    return _WATER[kinds_key]


def _water_key(w, mode_id: str) -> tuple:
    return tuple(sorted((r.water_kind_id, r.min_width_m) for r in w.rows("travel_mode_water", travel_mode_id=mode_id)))


def water_access(nav: np.ndarray, px: float, py: float, reach_m: float) -> list[tuple[int, int]]:
    """The navigable cells within reach of a place's glyph (its landing may stand anywhere on its edge)."""
    r = reach_m / M_PER_PX / DOWN
    cy, cx = py / DOWN, px / DOWN
    y0, y1 = max(0, int(cy - r)), min(nav.shape[0], int(cy + r) + 1)
    x0, x1 = max(0, int(cx - r)), min(nav.shape[1], int(cx + r) + 1)
    ys, xs = np.nonzero(nav[y0:y1, x0:x1])
    ys, xs = ys + y0, xs + x0
    near = (ys - cy) ** 2 + (xs - cx) ** 2 <= r * r
    return list(zip(ys[near].tolist(), xs[near].tolist()))


def reach_m(p) -> float:
    """How far from its glyph a place's landing may stand: its built radius (a city's capped) plus a jetty."""
    return min(p.footprint_radius_m or 60.0, 200.0) + 80.0


def water_paths(nav, sea, start, ends: dict[str, list]) -> dict[str, tuple[float, float]]:
    """From one place's water to each other place's: (metres along the water, metres of it over open sea). One search
    over the whole water from the start's cells; each end is its nearest reached cell."""
    from skimage.graph import MCP_Geometric
    mcp = MCP_Geometric(np.where(nav, 1.0, np.inf))
    acc, _ = mcp.find_costs(start)
    out = {}
    for pid, cs in ends.items():
        if not cs:
            continue
        ys, xs = np.array(cs).T
        vals = acc[ys, xs]
        i = int(np.argmin(vals))
        if not np.isfinite(vals[i]):
            continue
        path = mcp.traceback((int(ys[i]), int(xs[i])))
        on_sea = int(sea[tuple(np.array(path).T)].sum())
        out[pid] = (float(vals[i]) * DOWN * M_PER_PX, on_sea * DOWN * M_PER_PX)
    return out


def road_graph(w, classes: set[str] | None):
    adj = defaultdict(list)
    for r in w.rows("road"):
        if classes is None or r.road_class_id in classes:
            adj[r.from_node_id].append((r.to_node_id, r.length_m))
            adj[r.to_node_id].append((r.from_node_id, r.length_m))
    node_of = {}
    for n in w.rows("road_node"):
        if n.place_id:
            node_of.setdefault(n.place_id, n.id)
    return adj, node_of


def road_dist(adj, a: str, targets: set[str]) -> dict[str, float]:
    dist, seen, h = {a: 0.0}, set(), [(0.0, a)]
    out = {}
    while h:
        d, n = heapq.heappop(h)
        if n in seen:
            continue
        seen.add(n)
        if n in targets:
            out[n] = d
        for m, ln in adj[n]:
            if d + ln < dist.get(m, math.inf):
                dist[m] = d + ln
                heapq.heappush(h, (dist[m], m))
    return out


def straight_m(p, q) -> float:
    return math.hypot(p.world_x - q.world_x, p.world_y - q.world_y) / f.UNITS_PER_METRE


# ---- the load -------------------------------------------------------------------------------------------------------

def load(w) -> None:
    """The network's tables from its source, measured on the database's roads and water (build_db calls this after
    the places, roads and water are in)."""
    N = network()
    places = {p.id: p for p in w.rows("place")}
    for m in N["modes"]:
        w.insert("travel_mode", **{k: m.get(k) for k in (
            "id", "name", "give_kind_id", "needs", "road_class_id", "operated_by", "fare_base", "fare_per_km",
            "fare_step", "fare_min", "fare_max", "speed_kmh", "board_h", "evidence", "why")})
        for wk in m.get("water", []):
            w.insert("travel_mode_water", travel_mode_id=m["id"], water_kind_id=wk["kind"], min_width_m=wk.get("min_width_m"))
    w.insert_many("travel_operator", [{k: o.get(k) for k in ("id", "travel_mode_id", "name", "craft", "open_sea_max_m", "who", "why")}
                                      for o in N["operators"]])
    modes = {m["id"]: m for m in N["modes"]}
    kind_mode = {m["give_kind_id"]: m["id"] for m in N["modes"]}
    gives = defaultdict(dict)
    for g in w.rows("place_give"):
        if g.give_kind_id in kind_mode:
            gives[g.place_id][kind_mode[g.give_kind_id]] = g.seq
    for s in N["stops"]:
        seq = gives.get(s["place"], {}).get(s["mode"])
        if seq is None:
            raise ValueError(f"travel stop {s['place']} ({s['mode']}): the place record has no {modes[s['mode']]['give_kind_id']} give")
        w.insert("travel_stop", place_id=s["place"], travel_mode_id=s["mode"], give_seq=seq,
                 travel_operator_id=s["operator"], rank=s["rank"], why=s["why"])
    stops = {(s["place"], s["mode"]) for s in N["stops"]}
    for pid, by_mode in gives.items():
        for mode in by_mode:
            if (pid, mode) not in stops:
                raise ValueError(f"{pid}: a {modes[mode]['give_kind_id']} give with no stop in the network")

    measured = measure(w, N, places)
    for rt in N["routes"]:
        key = (rt["a"], rt["b"], rt["mode"])
        d, sea = measured[key]
        m = modes[rt["mode"]]
        for a, b in ((rt["a"], rt["b"]), (rt["b"], rt["a"])):
            w.insert("travel_route", from_place_id=a, to_place_id=b, travel_mode_id=rt["mode"], distance_m=round(d),
                     open_sea_m=round(sea), fare=fare(m, d), hours=hours(m, d), why=rt["why"])
    for row in approaches(w, N, places):
        w.insert("travel_approach", **row)


def measure(w, N: dict, places: dict) -> dict:
    """Each authored route's distance by its mode's way, and its open-sea share; a route the ground does not carry
    raises (a boat route with no water path, a coach route with no road of the mode's class)."""
    out = {}
    by_mode = defaultdict(list)
    for rt in N["routes"]:
        by_mode[rt["mode"]].append(rt)
    for mid, rts in by_mode.items():
        mode = next(m for m in N["modes"] if m["id"] == mid)
        if mode.get("water"):
            nav, sea = _water(w, _water_key(w, mid))
            acc = {pid: water_access(nav, places[pid].px, places[pid].py, reach_m(places[pid]))
                   for rt in rts for pid in (rt["a"], rt["b"])}
            by_a = defaultdict(list)
            for rt in rts:
                by_a[rt["a"]].append(rt["b"])
            for a, bs in by_a.items():
                if not acc[a]:
                    raise ValueError(f"boat route from {a}: no navigable water within {reach_m(places[a]):.0f} m")
                got = water_paths(nav, sea, acc[a], {b: acc[b] for b in bs})
                for b in bs:
                    if b not in got:
                        raise ValueError(f"boat route {a} - {b}: no water path between them")
                    out[(a, b, mid)] = got[b]
        elif mode.get("road_class_id"):
            adj, node_of = road_graph(w, {mode["road_class_id"]})
            for rt in rts:
                na, nb = node_of.get(rt["a"]), node_of.get(rt["b"])
                d = road_dist(adj, na, {nb}).get(nb) if na and nb else None
                if d is None:
                    raise ValueError(f"coach route {rt['a']} - {rt['b']}: no {mode['road_class_id']} road between them")
                out[(rt["a"], rt["b"], mid)] = (d, 0.0)
        else:
            for rt in rts:
                out[(rt["a"], rt["b"], mid)] = (straight_m(places[rt["a"]], places[rt["b"]]), 0.0)
    return out


def approaches(w, N: dict, places: dict) -> list[dict]:
    """Every place with no stop: the stop it is the shortest way from (of the four nearest), and how: diving for a
    place on the seabed, over the water for one on the water or an island, by road where a road joins them no more
    than a third longer than the straight line, else across the marsh on foot. The network's remote rows say why a
    place is left off it on purpose."""
    stops = defaultdict(list)
    for s in N["stops"]:
        stops[s["place"]].append(s["mode"])
    remote = {r["place"]: r["why"] for r in N.get("remote", [])}
    adj, node_of = road_graph(w, None)
    rows = []
    for pid, p in sorted(places.items()):
        if pid in stops:
            continue
        ways = []
        for s in sorted(stops, key=lambda s: straight_m(p, places[s]))[:4]:
            d = straight_m(p, places[s])
            if p.siting == "seabed":
                way = "dive"
            elif p.on_water or p.siting == "island":
                way = "water"
            else:
                na, nb = node_of.get(pid), node_of.get(s)
                rd = road_dist(adj, na, {nb}).get(nb) if na and nb else None
                way = "road" if rd is not None and rd <= 1.35 * d + 100 else "marsh"
                d = rd if way == "road" else d
            ways.append((d, s, way))
        d, s, way = min(ways)
        mode = sorted(stops[s], key=lambda m: ("boat", "coach", "rootworm").index(m))[0]
        rows.append({"place_id": pid, "stop_place_id": s, "travel_mode_id": mode, "foot_m": round(d), "way": way,
                     "remote": int(pid in remote),
                     "why": remote.get(pid) or f"{round(d)} m {WAY_WORDS[way]} from the {mode} stop at {places[s].name}"})
    return rows


WAY_WORDS = {"road": "by road", "marsh": "across the marsh on foot", "water": "over the water", "dive": "down through the water"}


# ---- the checks -----------------------------------------------------------------------------------------------------


def problems(w) -> list[str]:
    """The network as authored and built: no fast-travel promise remains; every stop is a give of its mode's kind with
    an operator of that mode and people to run it; every route's ends are stops of its mode, it runs both ways, at the
    mode's fare, and crosses no more open sea than both operators take; every stop has a route; the stops make the
    number of networks the source says (routes, and walks between stops); every other place is a walk from a stop or
    remote with its reason."""
    import dataclasses
    N = network()
    bad = []
    modes = {m.id: dataclasses.asdict(m) for m in w.rows("travel_mode")}
    stops = {(s.place_id, s.travel_mode_id): s for s in w.rows("travel_stop")}
    ops = {o.id: o for o in w.rows("travel_operator")}
    places = {p.id: p for p in w.rows("place")}
    if w.query("SELECT count(*) FROM give_kind WHERE id IN ('fast-travel', 'carriage-or-boat')")[0][0]:
        bad.append("give_kind still holds fast-travel or carriage-or-boat")
    n = w.query("SELECT count(*) FROM place_give WHERE give_kind_id IN ('fast-travel', 'carriage-or-boat')")[0][0]
    if n:
        bad.append(f"{n} place_give rows still promise fast-travel or carriage-or-boat")
    kind_mode = {m["give_kind_id"]: mid for mid, m in modes.items()}
    for g in w.rows("place_give"):
        if g.give_kind_id in kind_mode and (g.place_id, kind_mode[g.give_kind_id]) not in stops:
            bad.append(f"{g.place_id}: give {g.seq} ({g.give_kind_id}) is no stop of the network")
    for (pid, mid), s in stops.items():
        g = w.get("place_give", pid, s.give_seq)
        if g is None or g.give_kind_id != modes[mid]["give_kind_id"]:
            bad.append(f"stop {pid} ({mid}): its give {s.give_seq} is not a {modes[mid]['give_kind_id']}")
        if ops[s.travel_operator_id].travel_mode_id != mid:
            bad.append(f"stop {pid} ({mid}): operator {s.travel_operator_id} works another mode")
        if not places[pid].population:
            bad.append(f"stop {pid} ({mid}): nobody lives there to run it")
    routes = w.rows("travel_route")
    have = {(r.from_place_id, r.to_place_id, r.travel_mode_id) for r in routes}
    for r in routes:
        for end in (r.from_place_id, r.to_place_id):
            if (end, r.travel_mode_id) not in stops:
                bad.append(f"route {r.from_place_id} -> {r.to_place_id} ({r.travel_mode_id}): {end} is no {r.travel_mode_id} stop")
        if (r.to_place_id, r.from_place_id, r.travel_mode_id) not in have:
            bad.append(f"route {r.from_place_id} -> {r.to_place_id} ({r.travel_mode_id}) has no return")
        m = modes[r.travel_mode_id]
        if r.fare != fare(m, r.distance_m) or r.hours != hours(m, r.distance_m):
            bad.append(f"route {r.from_place_id} -> {r.to_place_id}: fare {r.fare} or hours {r.hours} are not the "
                       f"{m['id']} rule's")
        for end in (r.from_place_id, r.to_place_id):
            s = stops.get((end, r.travel_mode_id))
            cap = ops[s.travel_operator_id].open_sea_max_m if s else None
            if cap is not None and r.open_sea_m > cap:
                bad.append(f"route {r.from_place_id} -> {r.to_place_id}: {r.open_sea_m} m of open sea, more than {end}'s "
                           f"operator ({s.travel_operator_id}) crosses ({cap:.0f} m)")
    for (pid, mid) in stops:
        if not any(r.from_place_id == pid and r.travel_mode_id == mid for r in routes):
            bad.append(f"stop {pid} ({mid}) has no route")
    parts = reach(w)["parts"]
    if len(parts) != N["networks"]:
        bad.append(f"the stops make {len(parts)} networks, the source says {N['networks']}: "
                   + "; ".join(", ".join(p) for p in parts[1:]))
    for a in w.rows("travel_approach"):
        if not a.remote and a.foot_m > N["walk_max_m"]:
            bad.append(f"{a.place_id}: {a.foot_m} m from the nearest stop ({a.stop_place_id}) and not marked remote")
    on = {pid for pid, _ in stops} | {a.place_id for a in w.rows("travel_approach")}
    for pid in places:
        if pid not in on:
            bad.append(f"{pid}: neither a stop nor approached")
    for r in N.get("remote", []):
        if r["place"] in {pid for pid, _ in stops}:
            bad.append(f"{r['place']}: marked remote but is a stop")
    return bad


def reach(w) -> dict:
    """The stops as one graph: joined by every mode's routes and by a walk (two stops within walk_max_m of each
    other); its parts, largest first."""
    walk = network()["walk_max_m"]
    places = {p.id: p for p in w.rows("place")}
    adj = defaultdict(set)
    for r in w.rows("travel_route"):
        adj[r.from_place_id].add(r.to_place_id)
    nodes = sorted({s.place_id for s in w.rows("travel_stop")})
    for i, a in enumerate(nodes):
        for b in nodes[i + 1:]:
            if straight_m(places[a], places[b]) <= walk:
                adj[a].add(b)
                adj[b].add(a)
    seen, parts = set(), []
    for n in nodes:
        if n in seen:
            continue
        part, st = set(), [n]
        while st:
            x = st.pop()
            if x in part:
                continue
            part.add(x)
            st += adj[x]
        seen |= part
        parts.append(sorted(part))
    return {"parts": sorted(parts, key=len, reverse=True)}


# ---- authoring aid --------------------------------------------------------------------------------------------------

def candidates(w) -> None:
    """For each lived-in place: navigable water within reach (boat), its road node's major roads (coach), and the
    places it reaches by water and by major road; read while authoring network.json."""
    N = network()
    places = {p.id: p for p in w.rows("place")}
    boat = next(m for m in N["modes"] if m["id"] == "boat")
    nav, sea = _water(w, tuple(sorted((x["kind"], x.get("min_width_m")) for x in boat["water"])))
    live = [p for p in places.values() if (p.population or 0) > 0]
    acc = {p.id: water_access(nav, p.px, p.py, reach_m(p)) for p in live}
    # water groups: places whose water connects (one search per unvisited place)
    from scipy import ndimage as ndi
    lab, _ = ndi.label(nav, np.ones((3, 3)))
    group = {pid: sorted({int(lab[c]) for c in cs}) for pid, cs in acc.items()}
    adj, node_of = road_graph(w, {"major"})
    for p in sorted(live, key=lambda p: (-(p.importance or 0), -(p.population or 0))):
        print(f"{p.id:26} {p.place_kind_id:12} pop {p.population:3} water {str(group[p.id][:3]) if acc[p.id] else '-':16} "
              f"major-road {'yes' if p.id in node_of and adj.get(node_of[p.id]) else '-'}")


def main(argv: list[str]) -> int:
    from tools.argonia_world import db
    w = db.open(f.ROOT)
    cmd = argv[0] if argv else "report"
    if cmd == "candidates":
        candidates(w)
        return 0
    if cmd == "check":
        bad = problems(w)
        for b in bad:
            print("FAIL", b)
        print(f"travel: {len(bad)} problem(s)")
        return 1 if bad else 0
    if cmd == "report":
        for m in w.rows("travel_mode"):
            st = w.rows("travel_stop", travel_mode_id=m.id)
            rt = w.rows("travel_route", travel_mode_id=m.id)
            print(f"{m.id}: {len(st)} stops, {len(rt) // 2} routes")
        parts = reach(w)["parts"]
        print("network parts:", [len(p) for p in parts])
        for p in parts[1:]:
            print("  apart:", p)
        ap = w.rows("travel_approach")
        print(f"approached: {len(ap)} (remote {sum(a.remote for a in ap)})")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
