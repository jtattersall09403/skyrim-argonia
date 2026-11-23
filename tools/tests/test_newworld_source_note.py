"""Every place record says what it is built from: a `source` note (FORMAT.md), shown in the atlas as "Built from"."""
import json
from pathlib import Path

DB = Path(__file__).resolve().parents[2] / "newworld" / "story" / "data" / "db"


def rows(name: str) -> list[dict]:
    return [json.loads(x) for x in (DB / f"{name}.jsonl").read_text().splitlines() if x.strip()]




def test_every_place_has_a_source_note():
    places = {r["id"] for r in rows("place")}
    noted = {r["place_id"] for r in rows("place_note") if r["aspect_id"] == "source"}
    assert places - noted == set()




def test_source_note_agrees_with_the_allocated_source():
    """The note is a first-idea plan for its rank-0 source (decision 0040, 4): it names that source or says the place
    is built from the pool, never that the source does not fit, and ends with what is still to add."""
    import re
    match = DB.parents[2] / "sources" / "source_match"
    names = {}
    for x in (match / "source_place.jsonl").read_text().splitlines():
        if x.strip():
            s = json.loads(x)
            names[s["id"]] = s["name"]
    r0 = {}
    for x in (match / "place_source.jsonl").read_text().splitlines():
        if x.strip() and json.loads(x)["rank"] == 0:
            r = json.loads(x)
            r0[r["place_id"]] = r["source_place_id"]

    def norm(s):
        return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()

    bad = []
    for r in rows("place_note"):
        if r["aspect_id"] != "source" or r["place_id"] not in r0:
            continue
        t = r["text"]
        if (re.search(r"(does|do) not (fit|suit)|fits? better|suits? better|not fit well", t)
                or (norm(names.get(r0[r["place_id"]], "")) not in norm(t) and "from the pool" not in t)
                or "Still to add" not in t):
            bad.append(r["place_id"])
    assert bad == []
