"""LF83's `new` things as world rows (decision 0024 §4, 0030): two quest items, three place sockets, three local
state variants and the quest's new topics at Claywater Station, which the block's place layer reads (the `socket` layout program) for hand placement in 0.4 §d / 1.4.

Idempotent: re-running upserts the same rows.  python3 -m tools.argonia_world.content.lf83_things
Positions are metres in the place frame (east, south from the province's north-west corner), read from the
layout's own sockets: the well head (socket.claywater-station.evidence-the-cracked-well, 323.95, 3060.79) and the
crocodile den (socket.claywater-station.den-crocodile, 398.5, 3013.7). The clay cut is on the landing (north) bank
beside the den; its exact spot is confirmed by hand in game.
"""
from __future__ import annotations

from tools.argonia_world import db

PLACE = "place.imperial-fringe.claywater-station"
QUEST = "quest.local.lf83"
LIVIA = "npc.imperial-fringe.claywater-station.well-keeper"
SIGNS = "npc.imperial-fringe.claywater-station.landing-s-poler"

ITEMS = [
    dict(id="item.lf83.well-silt", status="derived", name="Jar of Well Silt", kind="quest", pocket="keyItems",
         unique=True, verb="take", stackable=False, weight_kg=0.5, value=0, ladder_band="D1", ladder_position=0.0,
         model="clutter/clay-jug.glb", icon="clutter-icons/clay-jug.png",
         description="A small clay jar of fine grey-brown silt from the bottom of the well bucket.",
         why_here="Livia Varinius keeps the silt from the morning bucket to show a mason.",
         notes="LF83's sample of the ford's clay in the well; the clay-jug model stands in, no new art.",
         asset_availability_status="vanilla", asset_availability_via="meshes/clutter/glazedjugsmall01.nif",
         asset_availability_notes="Shares the model and icon built for item.clay-jug (no new art).",
         quest=QUEST),
    dict(id="item.lf83.clay-basket", status="derived", name="The Landing's Clay Basket", kind="quest",
         pocket="keyItems", unique=True, verb="take", stackable=False, weight_kg=8.0, value=0, ladder_band="D1",
         ladder_position=0.0, model="clutter/basket.glb", icon="clutter-icons/basket.png",
         description="A reed basket half full of wet plaster clay, dug at the bend below the raft.",
         why_here="Signs-For-The-Cargo dropped it at the cut when the crocodile came up at him.",
         notes="LF83's leverage on the landing; the basket model stands in, no new art.",
         asset_availability_status="vanilla", asset_availability_via="meshes/clutter/basket01.nif",
         asset_availability_notes="Shares the model and icon built for item.basket (no new art).",
         quest=QUEST),
]

SOCKETS = [
    dict(id="socket.claywater-station.lf83-well-silt", kind="item", at_x=323.6, at_y=3061.2, zone="evidence",
         why="LF83: Livia Varinius's jar of well silt on the coping, on the ford side.",
         host="parcel.claywater-station.the-well", parcel="parcel.claywater-station.the-well", value_tier="trivial",
         owner=LIVIA, item_kind="quest", item="item.lf83.well-silt"),
    dict(id="socket.claywater-station.lf83-clay-bend", kind="marker", at_x=396.0, at_y=3006.0, zone="evidence",
         why="LF83: the clay bend, a bare clay cut over deep water on the landing bank below the raft, beside the "
             "crocodile's den; spade cuts and waders' prints in the clay."),
    dict(id="socket.claywater-station.lf83-clay-basket", kind="item", at_x=395.0, at_y=3006.5, zone="evidence",
         why="LF83: the landing's clay basket, dropped at the cut.", value_tier="trivial", owner=SIGNS,
         item_kind="quest", item="item.lf83.clay-basket"),
]


VARIANTS = [
    dict(id="lf83-well-clayed", when="LF83 e-shared (stage 40)",
         what_changes="thing.lf83.well-head: a band of fresh grey clay pressed in behind the coping on the ford side",
         description="The landing has sealed the cracked well head with clay."),
    dict(id="lf83-well-closed", when="LF83 e-keeper-dead (stage 92)",
         what_changes="thing.lf83.well-head: a board over the windlass; the bucket gone",
         description="The well is boarded over; nobody keeps it."),
    dict(id="lf83-walls-unplastered", when="LF83 e-station (stage 41) or e-rains (stage 90)",
         what_changes="thing.lf83.landing-walls: the mud huts on the landing bank go unplastered, the old plaster "
                      "cracked and streaked",
         description="The landing had no clay to replaster before the rains."),
]

TOPICS = [   # LF83's new topics (the record's `new: true` rows; quest_record.md: 2.5 adds them, here the first rung)
    ("topic.lf83-cracked-well", "the failing well"),
    ("topic.lf83-clay-bend", "the clay bend"),
    ("topic.lf83-one-charge", "one charge for the stop"),
    ("topic.lf83-ford-charge", "the ford charge"),
    ("topic.lf83-stop-charge", "the station's charge"),
]


def apply(w: db.World) -> None:
    for tid, label in TOPICS:
        w.upsert("topic", dict(id=tid, topic_class="quest", label=label, keys_quest=QUEST))
    if w.get("line_type", "goodbye") is None:
        w.insert("line_type", id="goodbye")
    have_v = {r.id: r.ord for r in w.rows("place_local_state_variants", place_id=PLACE) if r.id}
    nxt_v = max([r.ord for r in w.rows("place_local_state_variants", place_id=PLACE)], default=-1) + 1
    for v in VARIANTS:
        ord_ = have_v.get(v["id"])
        if ord_ is None:
            ord_, nxt_v = nxt_v, nxt_v + 1
        w.upsert("place_local_state_variants", dict(place_id=PLACE, ord=ord_, **v))
    for it in ITEMS:
        w.upsert("item", it)
    have = {r.id: r.ord for r in w.rows("socket", place_id=PLACE)}
    nxt = max(have.values(), default=-1) + 1
    for s in SOCKETS:
        ord_ = have.get(s["id"])
        if ord_ is None:
            ord_, nxt = nxt, nxt + 1
        w.upsert("socket", dict(place_id=PLACE, ord=ord_, op="socket", **s))


def main() -> int:
    w = db.open()
    apply(w)
    w.save()
    print(f"{len(ITEMS)} items, {len(SOCKETS)} sockets at {PLACE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
