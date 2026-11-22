# ruff: noqa: F811   (the fixture fx is imported and named by each test)
"""An agent's stroke on a row the owner's finalised save touched is refused, unless it answers him
(tools/places/edits.py `apply_agent_save`): every op carries `answers`, a note of that owner save (or a lead's
decision in the agent save's own notes), and the agent save was made after his. The answering stroke applies over
his save (its `before` is his `after`) and is listed in place.json `agent_answers` for the studio to show him."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from test_places_draft_stages import fx, rows  # noqa: E402,F401

from tools.places import edits  # noqa: E402
from tools.places.draft import stages  # noqa: E402

EXT = "spaces/exterior/refs.jsonl"


def move(r, dx):
    before = {"pos": list(r["pos"])}
    after = {"pos": [r["pos"][0] + dx, r["pos"][1], r["pos"][2]]}
    return {"op": "ref.move", "space": "exterior", "id": r["id"], "before": before, "after": after}


def owner_saves(pdir: Path, rid: str):
    """The owner's finalised save: he moves the row and notes "you should fix" as g8."""
    files = edits.load_place(pdir)
    r = next(x for x in files["spaces"]["exterior"]["refs"] if x["id"] == rid)
    op = dict(move(r, 100.0), n=1, call="fault", note_group="g8")
    save = {"save_id": "s1", "place_id": pdir.name, "name": "his", "at": "2026-11-22T15:48:08Z", "final": True,
            "ops": [op], "notes": [{"id": "g8", "text": "house door in bad position, you should fix", "at": "x"}]}
    out = edits.apply_save(files, save)
    edits.write_place(pdir, out)
    (pdir / "edits").mkdir(exist_ok=True)
    (pdir / "edits" / "s1.json").write_text(json.dumps(save))
    return save


def agent(pdir: Path, rid: str, at: str, answers=None, notes=None):
    files = edits.load_place(pdir)
    r = next(x for x in files["spaces"]["exterior"]["refs"] if x["id"] == rid)
    op = dict(move(r, 7.0), n=1, stroke=1, call="fault")
    if answers:
        op["answers"] = answers
    save = {"save_id": "agent-x", "place_id": pdir.name, "name": "fix", "at": at, "by": "agent", "final": False,
            "ops": [op]}
    if notes:
        save["notes"] = notes
    return edits.apply_agent_save(files, save, stages.owner_rows(pdir), None, stages.owner_touches(pdir))


def first_ref(fx):
    return rows(fx / "places/fx" / EXT)[0]["id"]


def test_a_stroke_answering_his_note_applies_over_his_save(fx):
    pdir = fx / "places/fx"
    rid = first_ref(fx)
    owner_saves(pdir, rid)
    his = next(x for x in rows(pdir / EXT) if x["id"] == rid)["pos"][0]
    out, left = agent(pdir, rid, "2026-11-22T20:00:00Z", answers="g8")
    assert not left
    got = next(x for x in out["spaces"]["exterior"]["refs"] if x["id"] == rid)
    assert abs(got["pos"][0] - (his + 7.0)) < 1e-6
    a = out["place"]["agent_answers"]
    assert a[0]["answers"] == "g8" and a[0]["owner_save"] == "s1" and rid in a[0]["rows"] and "you should fix" in a[0]["note"]


def test_any_other_stroke_on_his_row_is_refused_and_says_why(fx):
    pdir = fx / "places/fx"
    rid = first_ref(fx)
    owner_saves(pdir, rid)
    for kw in ({}, {"answers": "g9"}):
        out, left = agent(pdir, rid, "2026-11-22T20:00:00Z", **kw)
        assert left and left[0]["why"].startswith("refused")
    out, left = agent(pdir, rid, "2026-11-22T10:00:00Z", answers="g8")   # made before his save
    assert left


def test_a_lead_decision_in_the_save_answers_too(fx):
    pdir = fx / "places/fx"
    rid = first_ref(fx)
    owner_saves(pdir, rid)
    note = [{"id": "lead-1", "text": "the barge must be walkable for main quest 1", "at": "x", "by": "lead"}]
    out, left = agent(pdir, rid, "2026-11-22T20:00:00Z", answers="lead-1", notes=note)
    assert not left and out["place"]["agent_answers"][0]["owner_save"] == "lead"
