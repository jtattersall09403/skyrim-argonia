"""Each place's danger: its disposition, the strength of what lives inside, the way in and the reward band, each
derived with its reason (docs/design/danger.md). The ground under a place is its cell's (tools/newworld/danger.py);
nothing here is levelled to the player (decision 0035).

- Disposition: friendly, wary, hostile, or abandoned (whatever moved in, or empty); from its status, its kind, who
  holds it, its notes and its combat promises.
- Strength inside: a city or town is safe inside, whatever surrounds it. A friendly or wary place takes the natural
  band of the country it stands in: people who live in lethal land are formidable. A hostile or abandoned place
  with a fight is at least its natural band, one worse when the fight is inside a dungeon, cave or wreck or ends at
  a boss (at most D5); its record's researched band lifts it further (a ruin worse than its surroundings stays
  worse). An empty abandoned place is its natural band.
- Reach: the worst ground on the calmest way in from the network: a travel stop or a road (a bottleneck path over
  the cells' ground bands, the place's own cell included).
- Reward: the higher of reach and strength. Stocking's tiers come from it (tools/newworld/wealth.py).
The owner overrules any of it per place in `newworld/sources/danger/owner.json` ({place_id: {disposition?,
strength?, reward?, why}}); the reward follows an overruled strength unless it is overruled itself.

    python3 -m tools.newworld.place_danger show <place_id>
    python3 -m tools.newworld.place_danger counts       # places by ground, strength, reach, reward, disposition
    python3 -m tools.newworld.place_danger reconcile    # researched bands two or more from the derived strength
    python3 -m tools.newworld.place_danger check        # the invariants (make check runs them)
"""
from __future__ import annotations

import dataclasses
import heapq
import json
import re
import sys
from collections import Counter

from tools.argonia_world import db
from tools.newworld import danger as dg
from tools.newworld import frame as f
from tools.newworld.frame import px_to_cell

OWNER = f.ROOT / "sources" / "danger" / "owner.json"
RANK, BAND = dg.RANK, dg.BAND
SAFE = dg.SAFE_KINDS
LIVED = {"inhabited", "garrisoned"}
GONE = {"ruined", "abandoned", "sunken"}
DEEP = {"dungeon", "cave", "underwater"}          # place_kind.interior: a fight inside is one band worse
COMBAT = ("combat-foes", "combat-boss", "combat-creature")
DEAD = re.compile(r"\b(dead|drowned|ghosts?|skeleton|skeletal|wraith|undead|mumm|shades?|spirits?|risen|atronach|dreugh)")
PEOPLE = re.compile(r"\b(smuggl|bandit|outlaw|pirate|raider|brigand|robber|wrecker|scavenger|squatter|warband|warrior|"
                    r"sarpa|naga|paatru|digger|blackguard|thie|deserter|crew|archers|spearmen|captain|chief|leader|"
                    r"quartermaster|raj-kaal|heirs)")
WARY = re.compile(r"(wary of strangers|hostile to (anyone|those|uninvited|imperial)|attacks? strangers|any intruder|"
                  r"freeze an intruder|turn(s|ed)? (them )?away|uninvited|refuse the riddle|come armed|"
                  r"spells? on strangers|strangers on each other|strangers as suspects|challenge strangers|"
                  r"shoot at anyone|questioned and sometimes held|warn them off)", re.I)
PROVOKED = re.compile(r"(if provoked|not hostile)", re.I)


def owner() -> dict:
    return json.loads(OWNER.read_text(encoding="utf-8"))["places"] if OWNER.exists() else {}


def _people(detail: str) -> bool:
    d = detail.lower()
    return bool(PEOPLE.search(d)) and not DEAD.search(d)


def disposition(p, kind, gives, notes) -> tuple[str, str]:
    fights = [g for g in gives if g.give_kind_id in COMBAT]
    if any(g.setting == "provoked" for g in fights):
        g = next(g for g in fights if g.setting == "provoked")
        return "wary", f"its own people fight only when provoked: {g.detail}"
    if p.status == "occupied":
        return "hostile", f"occupied: {p.held_by}"
    if p.place_kind_id == "outlaw-camp":
        return "hostile", f"an outlaw camp: {p.held_by}"
    held = [g for g in fights if g.give_kind_id != "combat-creature" and g.setting is None and _people(g.detail)]
    if p.status in GONE:
        if held:
            return "hostile", f"{p.status}, held by {held[0].detail}"
        if fights:
            return "abandoned", f"{p.status}; what moved in: {'; '.join(g.detail for g in fights)}"
        return "abandoned", f"{p.status} and empty: {p.held_by}"
    text = " ".join([p.held_by or ""] + [notes.get(a, "") for a in ("dangers", "people", "present")] +
                    [g.detail for g in fights])
    m = WARY.search(text)
    if kind.family == "camp":
        terms = WARY.search(" ".join(g.detail for g in held)) or PROVOKED.search(notes.get("dangers", ""))
        if held and not terms:
            return "hostile", f"a camp whose own people attack: {held[0].detail}"
        return "wary", f"a tribal camp keeps strangers at a distance{': ' + (terms or m).group(0) if terms or m else ''}"
    if m:
        return "wary", f"its people meet strangers warily: '{m.group(0)}'"
    return "friendly", f"{p.status or 'lived in'}: {p.held_by}"


def strength(p, kind, disp, gives, nat: str, nat_why: str) -> tuple[str, str]:
    if p.place_kind_id in SAFE:
        inner = [g.detail for g in gives if g.give_kind_id in COMBAT and g.setting == "interior"]
        return "D0", "a city or town is safe inside, whatever surrounds it" + \
            (f"; its fight lives in an interior: {'; '.join(inner)}" if inner else "")
    fights = [g for g in gives if g.give_kind_id in COMBAT]
    if disp in ("friendly", "wary"):
        b, why = nat, f"its people live with the country round it: natural {nat} ({nat_why})"
    elif not fights:
        b, why = nat, f"empty: what roams the country round it, natural {nat}"
    else:
        deep = kind.interior in DEEP and any(g.give_kind_id == "combat-foes" for g in fights)
        boss = any(g.give_kind_id == "combat-boss" for g in fights)
        b, why = nat, f"its fight is at least the natural {nat}"
        if deep or boss:
            b = BAND[min(5, RANK[nat] + 1)]
            why += f", one worse for {'its boss' if boss else 'foes in its ' + kind.interior}" + \
                (": D5 is the worst band" if nat == "D5" else f": {b}")
        else:
            why += " (no boss, and no foes in a dungeon, cave or wreck)"
    if p.danger_band_id and RANK[p.danger_band_id] > RANK[b]:
        b, why = p.danger_band_id, why + f"; the research knows worse: {p.danger_band_id}"
    return b, why


def reach(w, cells: dict) -> dict:
    """Bottleneck paths from the network (travel stops and road cells): each cell's calmest way in, its worst band."""
    src = {}
    places = {p.id: p for p in w.rows("place")}
    for s in w.rows("travel_stop"):
        p = places[s.place_id]
        src.setdefault((p.cell_x, p.cell_y), f"the {s.travel_mode_id} stop at {p.name}")
    for r in w.rows("road"):
        for v in w.rows("road_vertex", road_id=r.id):
            src.setdefault(px_to_cell(v.px, v.py), f"a {r.road_class_id} road")
    best, origin, q = {}, {}, []
    for k, label in src.items():
        if k in cells:
            best[k], origin[k] = RANK[cells[k]], label
            heapq.heappush(q, (best[k], k))
    while q:
        d, k = heapq.heappop(q)
        if d > best[k]:
            continue
        for dx, dy in dg.NB8:
            n = (k[0] + dx, k[1] + dy)
            if n in cells:
                nd = max(d, RANK[cells[n]])
                if nd < best.get(n, 99):
                    best[n], origin[n] = nd, origin[k]
                    heapq.heappush(q, (nd, n))
    return {k: (BAND[v], origin[k]) for k, v in best.items()}


def derive(w) -> list[dict]:
    kinds = {k.id: k for k in w.rows("place_kind")}
    cells = {(c.x, c.y): c for c in w.rows("cell") if not c.margin}
    gives, notes = {}, {}
    for g in w.rows("place_give"):
        gives.setdefault(g.place_id, []).append(g)
    for n in w.rows("place_note"):
        notes.setdefault(n.place_id, {})[n.aspect_id] = n.text
    ways = reach(w, {k: c.danger_band_id for k, c in cells.items()})
    own = owner()
    rows = []
    for p in w.rows("place"):
        k, c = kinds[p.place_kind_id], cells[(p.cell_x, p.cell_y)]
        gs = gives.get(p.id, [])
        nat_why = c.danger_why.split(";")[0].split(" (natural: ")[-1].rstrip(")")
        disp, dwhy = disposition(p, k, gs, notes.get(p.id, {}))
        st, swhy = strength(p, k, disp, gs, c.natural_band_id, nat_why)
        rb, origin = ways.get((p.cell_x, p.cell_y), (c.danger_band_id, "no way in from the network"))
        rwhy = f"from {origin}, the worst ground on the calmest way in is {rb} (its own cell {c.danger_band_id})"
        o = own.get(p.id) or {}
        by = "owner" if o else "derived"
        if o.get("disposition"):
            disp, dwhy = o["disposition"], f"owner: {o['why']} (derived: {disp}, {dwhy})"
        if o.get("strength"):
            st, swhy = o["strength"], f"owner: {o['why']} (derived: {st}, {swhy})"
        rw = max(rb, st, key=RANK.get)
        wwhy = f"the harder of the way in ({rb}) and what lives inside ({st})"
        if o.get("reward"):
            rw, wwhy = o["reward"], f"owner: {o['why']} (derived: {rw}, {wwhy})"
        rows.append({"place_id": p.id, "disposition_id": disp, "disposition_why": dwhy, "strength_band_id": st,
                     "strength_why": swhy, "reach_band_id": rb, "reach_why": rwhy, "reward_band_id": rw,
                     "reward_why": wwhy, "by": by})
    return rows


def assign(w) -> None:
    unknown = set(owner()) - {p.id for p in w.rows("place")}
    if unknown:
        raise ValueError(f"{OWNER} names unknown places: {sorted(unknown)}")
    w.insert_many("place_danger", derive(w))


def problems(w) -> list[str]:
    """The invariants: every cell's ground is its natural band less only the rules; every hostile or abandoned
    place with a fight is at least its natural band; a settlement's own fight is in an interior or provoked (and
    then the place is wary); reward is never below strength or reach; every derived value has its reason."""
    bad = []
    cells = {(c.x, c.y): c for c in w.rows("cell") if not c.margin}
    regions = {r.id: r for r in w.rows("region")}
    safe, lower = dg.softeners(w)
    for k, c in cells.items():
        n, g = RANK[c.natural_band_id], RANK[c.danger_band_id]
        sea = regions[c.region_id].kind == "sea"
        want = 0 if (k in safe and not sea) else (max(1, n - lower[k][0]) if k in lower and n > 1 else n)
        if g != want:
            bad.append(f"cell {k}: ground {c.danger_band_id} from natural {c.natural_band_id}; the rules give D{want}")
        if not c.danger_why:
            bad.append(f"cell {k}: no reason")
    fam = {k.id: k.family for k in w.rows("place_kind")}
    pd = {r.place_id: r for r in w.rows("place_danger")}
    for p in w.rows("place"):
        r = pd.get(p.id)
        if r is None:
            bad.append(f"{p.id}: no place_danger row")
            continue
        c = cells[(p.cell_x, p.cell_y)]
        gs = w.rows("place_give", place_id=p.id)
        fights = [g for g in gs if g.give_kind_id in COMBAT]
        if r.by == "derived" and r.disposition_id in ("hostile", "abandoned") and fights and \
                RANK[r.strength_band_id] < RANK[c.natural_band_id]:
            bad.append(f"{p.id}: {r.disposition_id} at {r.strength_band_id}, calmer than its natural "
                       f"{c.natural_band_id}")
        if fam[p.place_kind_id] == "settlement" and r.disposition_id != "hostile":
            for g in fights:
                if g.give_kind_id != "combat-creature" and g.setting is None:
                    bad.append(f"{p.id}: give {g.seq} ({g.give_kind_id}) '{g.detail}': a settlement's fight is "
                               f"in an interior or provoked")
        if any(g.setting == "provoked" for g in fights) and r.disposition_id != "wary":
            bad.append(f"{p.id}: a provoked fight at a {r.disposition_id} place")
        if RANK[r.reward_band_id] < max(RANK[r.strength_band_id], RANK[r.reach_band_id]) and r.by == "derived":
            bad.append(f"{p.id}: reward {r.reward_band_id} below strength {r.strength_band_id} or reach "
                       f"{r.reach_band_id}")
        for col in ("disposition_why", "strength_why", "reach_why", "reward_why"):
            if not (getattr(r, col) or "").strip():
                bad.append(f"{p.id}: no {col}")
    return bad


def reconcile(w) -> list[tuple]:
    """Places whose researched band is two or more from the strength the rules alone give."""
    kinds = {k.id: k for k in w.rows("place_kind")}
    cells = {(c.x, c.y): c for c in w.rows("cell")}
    out = []
    for r in w.rows("place_danger"):
        p = w.get("place", r.place_id)
        c = cells[(p.cell_x, p.cell_y)]
        gs = w.rows("place_give", place_id=p.id)
        bare = type("P", (), {**{k: getattr(p, k) for k in p.__dataclass_fields__}, "danger_band_id": None})
        rule, _ = strength(bare, kinds[p.place_kind_id], r.disposition_id, gs, c.natural_band_id, "")
        if p.danger_band_id and abs(RANK[p.danger_band_id] - RANK[rule]) >= 2:
            out.append((p.id, p.place_kind_id, r.disposition_id, p.danger_band_id, rule, c.natural_band_id))
    return out


def counts(w) -> dict:
    cells = {(c.x, c.y): c for c in w.rows("cell")}
    rows = w.rows("place_danger")
    places = {p.id: p for p in w.rows("place")}
    cnt = lambda xs: dict(sorted(Counter(xs).items()))     # noqa: E731
    return {
        "cells by ground": cnt(c.danger_band_id for c in cells.values() if not c.margin),
        "cells by natural": cnt(c.natural_band_id for c in cells.values() if not c.margin),
        "places by ground": cnt(cells[(p.cell_x, p.cell_y)].danger_band_id for p in places.values()),
        "places by natural": cnt(cells[(p.cell_x, p.cell_y)].natural_band_id for p in places.values()),
        "places by researched band": cnt(p.danger_band_id for p in places.values()),
        "places by strength": cnt(r.strength_band_id for r in rows),
        "places by reach": cnt(r.reach_band_id for r in rows),
        "places by reward": cnt(r.reward_band_id for r in rows),
        "places by disposition": cnt(r.disposition_id for r in rows),
    }


def main(argv: list[str]) -> int:
    w = db.open(f.ROOT)
    if argv[:1] == ["show"] and len(argv) > 1:
        r = w.get("place_danger", argv[1])
        p = w.get("place", argv[1])
        c = w.get("cell", p.cell_x, p.cell_y)
        print(json.dumps({"ground": c.danger_band_id, "natural": c.natural_band_id, "ground_why": c.danger_why,
                          "researched": p.danger_band_id, **dataclasses.asdict(r)}, indent=1, ensure_ascii=False))
        return 0
    if argv[:1] == ["counts"]:
        for k, v in counts(w).items():
            print(f"{k}: {v}")
        return 0
    if argv[:1] == ["reconcile"]:
        for row in reconcile(w):
            print("{} ({}, {}): researched {} vs rule {} (natural {})".format(*row))
        return 0
    if argv[:1] == ["check"]:
        bad = problems(w)
        print("\n".join(bad) or "danger: 0 problems")
        return 1 if bad else 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
