"""LF83's `new` things as world rows (decision 0024 §4, 0030): two quest items, three place sockets, three local
state variant, the quest's new topics and its objective text rows at Claywater Station, which the block's place layer reads (the `socket` layout program) for hand placement in 0.4 §d / 1.4.

Idempotent: re-running upserts the same rows.  python3 -m tools.argonia_world.content.lf83_things
Positions are metres in the place frame (east, south from the province's north-west corner), read from the
layout's own sockets: the well head (socket.claywater-station.evidence-the-cracked-well, 323.95, 3060.79) and the
river's first swing below the ford (hydrology_reach_point reach.169-1660). The clay cut is on the station bank
there; its exact spot is confirmed by hand in game.
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
    dict(id="item.lf83.well-water", status="derived", name="Dipper of Well Water", kind="quest", pocket="keyItems",
         unique=True, verb="take", stackable=False, weight_kg=0.5, value=0, ladder_band="D1", ladder_position=0.0,
         model="clutter/clay-jug.glb", icon="clutter-icons/clay-jug.png",
         description="A clay dipper of water from the station well. It tastes faintly of the ford.",
         why_here="Livia Varinius gives a dipper of the well's water to any traveller who has paid the stop.",
         notes="LF83's taste-test sample for Takes-The-Short-Weight; the clay-jug model stands in, no new art.",
         asset_availability_status="vanilla", asset_availability_via="meshes/clutter/glazedjugsmall01.nif",
         asset_availability_notes="Shares the model and icon built for item.clay-jug (no new art).",
         quest=QUEST),
]

SOCKETS = [
    dict(id="socket.claywater-station.lf83-well-silt", kind="item", at_x=323.6, at_y=3061.2, zone="evidence",
         why="LF83: Livia Varinius's jar of well silt, kept under the windlass cover to show a mason, beside her trowel and "
             "mortar tub (thing.lf83.mortar-tub).",
         host="parcel.claywater-station.the-well", parcel="parcel.claywater-station.the-well", value_tier="trivial",
         owner=LIVIA, item_kind="quest", item="item.lf83.well-silt"),
    dict(id="socket.claywater-station.lf83-well-water", kind="item", at_x=324.4, at_y=3060.4, zone="evidence",
         why="LF83: Livia Varinius's dipper of well water on the windlass; taken unasked it is theft if seen.",
         host="parcel.claywater-station.the-well", parcel="parcel.claywater-station.the-well", value_tier="trivial",
         owner=LIVIA, item_kind="quest", item="item.lf83.well-water"),
    dict(id="socket.claywater-station.lf83-clay-bend", kind="marker", at_x=281.5, at_y=3058.5, zone="evidence",
         why="LF83: the clay cut, a bare clay bank on the station (south) bank where the river swings west below the "
             "ford (reach.169-1660 apex 280.2, 3049.4), the landing's clay since before the well; spade cuts and "
             "waders' prints in the clay. Needs a scour pool of 2.5 m or more and the crocodile den here (planner)."),
    dict(id="socket.claywater-station.lf83-clay-basket", kind="item", at_x=282.0, at_y=3058.0, zone="evidence",
         why="LF83: the landing's clay basket, dropped at the cut.", value_tier="trivial", owner=SIGNS,
         item_kind="quest", item="item.lf83.clay-basket"),
]


VARIANTS = [
    dict(id="lf83-well-clayed", when="LF83 e-shared (stage 40)",
         what_changes="thing.lf83.well-head: a band of fresh grey clay rammed in behind the coping and down the lining "
                      "on the ford side",
         description="The landing has sealed the cracked well lining with clay."),
]
DROPPED_VARIANTS = ["lf83-well-closed", "lf83-walls-unplastered"]   # cut to keep LF83 within tier M (review R2-M9)

TOPICS = [   # LF83's new topics (the record's `new: true` rows; quest_record.md: 2.5 adds them, here the first rung)
    ("topic.lf83-cracked-well", "the failing well"),
    ("topic.lf83-clay-bend", "the clay bend"),
    ("topic.lf83-one-charge", "one charge for the stop"),
    ("topic.lf83-ford-charge", "the ford charge"),
    ("topic.lf83-stop-charge", "the station's charge"),
]


STALE_TEXT = ["text.objective.lf83.carry-terms"]   # the imported objective the rebuilt record dropped


def objective_entries(w: db.World) -> None:
    """The objective text keys' journal rows, from the record's own words (quest_objective.objective_text): the
    record is the one source, these rows are what the generator reads by key."""
    for k in STALE_TEXT:
        if w.get("journal_entry", k) is not None:
            w.delete("journal_entry_fact", journal_entry_id=k)
            w.delete("journal_entry_grounding", journal_entry_id=k)
            w.delete("journal_entry", k)
    for r in w.query("SELECT text, objective_text FROM quest_objective WHERE quest_id = ? ORDER BY stages_ord, ord",
                     QUEST):
        if r["objective_text"]:
            w.upsert("journal_entry", dict(id=r["text"], quest_id=QUEST, surface="journal", text=r["objective_text"]))


def apply(w: db.World) -> None:
    for tid, label in TOPICS:
        w.upsert("topic", dict(id=tid, topic_class="quest", label=label, keys_quest=QUEST))
    if w.get("line_type", "goodbye") is None:
        w.insert("line_type", id="goodbye")
    for r in w.rows("place_local_state_variants", place_id=PLACE):
        if r.id in DROPPED_VARIANTS:
            w.delete("place_local_state_variants", PLACE, r.ord)
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
    objective_entries(w)


def main() -> int:
    w = db.open()
    apply(w)
    w.save()
    print(f"{len(ITEMS)} items, {len(SOCKETS)} sockets at {PLACE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
