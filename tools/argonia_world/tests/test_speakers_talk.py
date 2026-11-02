"""L1 (play test 3, finding 24): every person a place build marks as a speaker (the ARG_Speaker keyword, so the
dialogue intercept takes their Talk) has written lines in the in-game topic store; a marked speaker without them is
silent, since the intercept replaces the vanilla Talk and the store refuses them."""
from tools.argonia_world import db, topic_tables


def test_every_built_speaker_is_in_the_store():
    w = db.open()
    store = {n for n, status in topic_tables.speakers(w) if status == "written"}
    marked = {p.npc_id for p in w.rows("build_person") if p.speaker and p.npc_id.startswith(topic_tables.PLACE.replace("place.", "npc.") + ".")}
    assert marked, "no speaker is built at the fixture place"
    assert marked <= store, f"silent speakers (marked, no written lines): {sorted(marked - store)}"
