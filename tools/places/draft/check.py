"""`draft check <place_id>`: the draft's self-checks, on the place files, the source bundle and the ground bundle.

Fails on: a source ref not accounted for (placed, adapted, replaced, or dropped with a reason); a ref not seated as
its rule says (floating or buried); a building on ground steeper than the source's own with no patch; a door no
path reaches; a promised service with nobody giving it; fewer beds than people; anything in water that the source
had on land, or the reverse; a Nordic or levelled base placed; a person whose bed or routine points at nothing.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from tools.places.draft import interiors, io, people
from tools.places.draft.geom import LEVELLED
from tools.places.draft.fit import relief_allowed
from tools.places.draft.paths import connected, dist_to_paths
from tools.places.seat import Ground, foot_relief, seat_all

SEAT_TOL = 1.0
DOOR_REACH = 160.0


def check(place_id: str, bundles: Path = io.BUNDLES, places: Path = io.PLACES, gives: list | None = None) -> list[str]:
    pdir = places / place_id
    place = json.loads((pdir / "place.json").read_text())
    src = io.load(f"src.{place['source_id']}", bundles)
    grd = io.load(f"ground.{place_id}", bundles)
    bases = io.place_bases(src, grd, place.get("draft") or {})
    if gives is None:
        from tools.places.draft.run import place_record
        gives = place_record(place_id)[1]
    G = Ground.load(grd.path)
    land = io.read_jsonl(pdir / "land.jsonl")
    G.apply_patches(land)
    S = src.ground
    refs = io.read_jsonl(pdir / "spaces" / "exterior" / "refs.jsonl")
    ledger = io.read_jsonl(pdir / "ledger.jsonl")
    paths = io.read_jsonl(pdir / "paths.jsonl")
    folk = io.read_jsonl(pdir / "people.jsonl")
    bad: list[str] = []

    # 1. every source ref accounted for
    seen = {(r["space"], r["src"]) for r in ledger}
    for sid, sp in src.spaces.items():
        whole = (sid, "*") in seen
        for r in sp.refs:
            if (sid, r["id"]) not in seen and not (whole and r.get("kind") != "actor"):
                bad.append(f"unaccounted source ref {sid}/{r['id']}")
    for r in ledger:
        if r["status"] not in ("placed", "adapted", "replaced", "dropped"):
            bad.append(f"ledger {r['src']}: unknown status {r['status']}")
        if r["status"] == "dropped" and not r.get("why"):
            bad.append(f"ledger {r['src']}: dropped without a reason")

    # 2. seated as the rule says
    want = [dict(r, pos=list(r["pos"])) for r in refs]
    seat_all(want, G)
    for r, w in zip(refs, want):
        if abs(r["pos"][2] - w["pos"][2]) > SEAT_TOL:
            bad.append(f"{r['id']} ({r['base']}) not seated: z {r['pos'][2]:.1f}, its rule gives {w['pos'][2]:.1f}")

    # 3. buildings on ground no steeper than the source's (or patched)
    src_by = {r["id"]: r for r in src.exterior.refs}
    patched = {tuple(p["cell"]) for p in land}
    for r in refs:
        if r.get("kind") != "building" or not r["seat"].get("foot"):
            continue
        f = r["seat"]["foot"]
        s = src_by.get(r.get("src"))
        src_rel = foot_relief(S, s["pos"][0], s["pos"][1], s["rot"][2], f) if s else 0.0
        rel = foot_relief(G, r["pos"][0], r["pos"][1], r["rot"][2], f)
        allow = relief_allowed(src_rel, r["seat"])
        if allow is not None and rel > allow + 1:
            cell = (math.floor(r["pos"][0] / 4096), math.floor(r["pos"][1] / 4096))
            bad.append(f"{r['id']} on ground rising {rel:.0f} (source {src_rel:.0f})"
                       f"{' despite a patch' if cell in patched else ' with no patch'}")

    # 4. water where the source had water, land where it had land
    for r in refs:
        s = src_by.get(r.get("src"))
        if not s or r["seat"].get("mode") in ("on", "free", "above"):
            continue
        sw, ow = S.wet(s["pos"][0], s["pos"][1], 16), G.wet(r["pos"][0], r["pos"][1], 16)
        if r.get("kind") in ("building", "static", "furniture", "container", "door") and sw != ow:
            bad.append(f"{r['id']} ({r['kind']}) {'in water' if ow else 'on land'}; the source had it "
                       f"{'in water' if sw else 'on land'}")

    # 5. every door reached by a path, one network
    doors = [r for r in refs if r.get("door") and r["door"].get("to_space") not in (None, "exterior")]
    ends = {}
    for p in paths:
        ends.setdefault(p.get("from"), p["points"][0])
        ends.setdefault(p.get("to"), p["points"][-1])
    for d in doors:
        p = ends.get(d.get("src"))
        if p is None or dist_to_paths(p, paths) > DOOR_REACH:
            bad.append(f"door {d['id']} reached by no path")
    if not connected(paths):
        bad.append("the paths are not one network")
    for d in doors:
        sid = d["door"]["to_space"]
        if not (pdir / "spaces" / sid / "space.json").exists():
            bad.append(f"door {d['id']} leads to {sid}, which is not drafted")

    # 6. services, beds, people
    given = {(g["seq"]) for p in folk for g in p.get("services") or []}
    for g in gives:
        if g["give_kind_id"] in people.PERSON_GIVES and g["seq"] not in given:
            bad.append(f"promised {g['give_kind_id']} ({g.get('detail')}) has nobody giving it")
    beds_total = 0
    bed_refs = {}
    for sdir in sorted((pdir / "spaces").iterdir()):
        sj = sdir / "space.json"
        if sdir.name == "exterior" or not sj.exists():
            continue
        sj = json.loads(sj.read_text())
        copy_of = sj["copy_of"].split("/", 1)[1]
        for b in interiors.beds_in(src.spaces[copy_of].refs, bases, sj.get("room")):
            beds_total += b["sleeps"]
            bed_refs[(sdir.name, b["ref"])] = b["sleeps"]
    if beds_total < len(folk):
        bad.append(f"{len(folk)} people for {beds_total} beds")
    use: dict = {}
    for p in folk:
        if not p.get("bed"):
            bad.append(f"{p['id']} ({p['role']}) has no bed")
            continue
        k = (p["bed"]["space"], p["bed"]["ref"])
        if k not in bed_refs:
            bad.append(f"{p['id']} sleeps in {k}, which is not a bed of the draft")
        use[k] = use.get(k, 0) + 1
        hours = sum(s["hours"] for s in p["routine"])
        if hours != 24:
            bad.append(f"{p['id']} routine covers {hours} hours")
    for k, n in use.items():
        if n > bed_refs.get(k, 0):
            bad.append(f"bed {k} slept in by {n}")
    for p in folk:
        if p["role"] == "guard" and len((p.get("patrol") or {}).get("points") or []) < 2:
            bad.append(f"guard {p['id']} has no patrol")
        if not p.get("base_from"):
            bad.append(f"{p['id']} ({p['role']}) has no actor base")
        elif p["base_from"] in src.npcs and not people.usable(src.npcs[p["base_from"]]):
            bad.append(f"{p['id']} built on a Nordic or levelled actor {p['base_from']}")

    # 7. no Nordic or levelled base placed
    for r in refs:
        b = bases.get(r["base"]) or {}
        if b.get("nordic"):
            bad.append(f"{r['id']} places a Nordic base {r['base']}")
        if str(b.get("type")) in LEVELLED:
            bad.append(f"{r['id']} places a levelled base {r['base']}")
    return bad


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: python -m tools.places draft check <place_id>")
        return 2
    bad = check(argv[0])
    for b in bad[:200]:
        print("FAIL", b)
    if len(bad) > 200:
        print(f"... and {len(bad) - 200} more")
    print(f"draft check {argv[0]}: {'PASS' if not bad else f'{len(bad)} problems'}")
    return 0 if not bad else 1

