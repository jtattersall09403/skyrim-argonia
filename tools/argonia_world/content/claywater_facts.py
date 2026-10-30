"""Claywater Station's road, river and people facts as `fact` rows (decision 0024 §3: the LF83 writers' fact requests,
writing-3; 0030). Each claim is read off the imported world and names the rows it comes from in `from_ref`:
the Blackwood Road's edges and landmarks (route_edge, route_edge_landmark: Cartwright's Cross at chain 0 of
edge.route.road.gideon-blackwood-road.1087, the station at 584.8 m, the Leyawiin exit at 995.7 m; Gideon 1087.9 m
before the junction), the Onkobra boat route, the ford's own stream (hydrology_river river.0-574), the glossary's
glosses and the place build's sockets and schedules. Spoken distances are yards, rounded (1 m = 1.094 yd).

Idempotent: re-running upserts the same rows.  python3 -m tools.argonia_world.content.claywater_facts
"""
from __future__ import annotations

from tools.argonia_world import db

PLACE = "place.imperial-fringe.claywater-station"
P = "fact.claywater-station."
NPC = "npc.imperial-fringe.claywater-station."
# The one carrier each fact names (place_brief.py reads it); the road and river facts are the ford's poler's, the
# station's the well-keeper's, the household's Takes-The-Short-Weight's. Other locals may repeat them (common talk).
CARRIER = {"road-leyawiin": "landing-s-poler", "onkobra-river": "landing-s-poler", "helstrom-way": "landing-s-poler",
           "prison-road": "landing-s-poler", "road-gideon": "well-keeper", "gideon-city": "well-keeper",
           "people-travellers": "well-keeper", "people-household": "n1-3"}

FACTS = [
    ("road-gideon", "feature",
     "Gideon lies east along the Blackwood Road: about 640 yards to the signpost at Cartwright's Cross, then about 1,190 "
     "yards on to the city, a little over a mile in all.",
     "route_edge edge.route.road.gideon-blackwood-road (1098.9 m; Cartwright's Cross at 1087.9 m) and "
     "route_edge_landmark edge.route.road.gideon-blackwood-road.1087 (the station at 584.8 m)"),
    ("road-leyawiin", "feature",
     "West of the station the Blackwood Road runs about 450 yards to the edge of Black Marsh, then on through the "
     "Blackwood hills to Leyawiin in Cyrodiil.",
     "route_edge edge.route.road.gideon-blackwood-road.1087 (exit.blackwood-road, named Leyawiin, at 995.7 m); "
     "term.blackwood"),
    ("gideon-city", "feature",
     "Gideon is the western frontier city at the east end of the Blackwood Road, where the courts still work.",
     "term.gideon; route.road.gideon-blackwood-road"),
    ("onkobra-river", "feature",
     "The Onkobra is the river that runs east through Gideon into the interior. The stream at the Claywater ford is not "
     "the Onkobra: it runs west, away from Gideon.",
     "term.onkobra; route.boat.gideon-onkobra; hydrology_river river.0-574 (the ford's reaches 169-1660 and 183-1646)"),
    ("helstrom-way", "feature",
     "Helstrom, the interior capital grown into a Hist grove, lies far east of Gideon. Canoes reach it from Gideon "
     "down the Onkobra white water.",
     "term.helstrom; route.boat.gideon-onkobra (gideon to helstrom); route_node node.place.hist-heartland.helstrom"),
    ("prison-road", "feature",
     "The Prison road is the old Imperial cordon road from Blackrose to Lilmoth, far to the south-east. The road "
     "through Claywater Station is the Blackwood Road.",
     "route.road.blackrose-lilmoth; term.prison-road"),
    ("people-household", "activity",
     "Gaius Vibius, Keeps-The-Second-Ledger and Takes-The-Short-Weight keep the household hut by the common on the "
     "landing bank, about 30 yards north of the raft. In the morning they cook at the common's fire; by day they work "
     "the common and the drying racks.",
     "socket socket.claywater-station.npc-family, idle-family-cook, idle-family-home; socket_schedule ops 268"),
    ("people-travellers", "activity",
     "Abhuki and Mee-Seesh are road travellers on the Blackwood Road. In the afternoon they sit on the bench by the "
     "brazier at the well, and at night they pay for a bed in the station house.",
     "socket socket.claywater-station.npc-travellers, idle-travellers-rest, idle-travellers-sleep; socket_schedule "
     "ops 271"),
]


def apply(w: db.World) -> None:
    have = {r["id"]: r["ord"] for r in w.query("SELECT id, ord FROM fact WHERE place_id = ?", PLACE)}
    nxt = max(have.values(), default=-1) + 1
    for slug, kind, claim, src in FACTS:
        fid = P + slug
        ord_ = have.get(fid)
        if ord_ is None:
            ord_, nxt = nxt, nxt + 1
        w.upsert("fact", dict(id=fid, claim=claim, kind=kind, place_id=PLACE, ord=ord_, source_field="writing-4",
                              from_ref=src, carrier_queued_type="npc-topic", carrier_queued_ref=NPC + CARRIER[slug]))


def main() -> int:
    w = db.open()
    apply(w)
    errs = w.errors()
    if errs:
        for e in errs:
            print(e)
        return 1
    w.save()
    print(f"{PLACE}: {len(FACTS)} facts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
