# ruff: noqa: F811   (the fixture fx is imported and named by each test)
"""An agent's stroke on a row the owner's finalised save touched is refused, unless it answers him
(tools/places/edits.py `apply_agent_save`): every op carries `answers`, a note of that owner save (or a lead's
decision in the agent save's own notes), and the agent save was made after his. The answering stroke applies over
his save (its `before` is his `after`) and is listed in place.json `agent_answers` for the studio to show him."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from test_places_draft_stages import drafted, fx, rows  # noqa: E402,F401

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


def test_his_open_session_replays_over_the_agents_answers(fx):
    """His session is still open (unsaved): the agent's answers land in the draft first (each naming his note), then
    his ops replay over the new draft: an op of the answered note is kept as no change (the answer, made over his
    edit, stands); an op of another note on an answered row is his edit over the row as it stands (his favour); an
    op on a row nobody answered that no longer fits is still a conflict."""
    pdir = fx / "places/fx"
    refs = rows(pdir / EXT)
    a_id, b_id = refs[0]["id"], refs[1]["id"]
    files = edits.load_place(pdir)
    ra = next(x for x in files["spaces"]["exterior"]["refs"] if x["id"] == a_id)
    rb = next(x for x in files["spaces"]["exterior"]["refs"] if x["id"] == b_id)
    # his open session: he moves a (note g8) and b (note g6)
    mine = [dict(move(ra, 100.0), n=1, call="fault", note_group="g8"), dict(move(rb, 50.0), n=2, call="fault", note_group="g6")]
    session = {"save_id": "autosave", "place_id": "fx", "at": "2026-11-22T15:48:08Z", "ops": mine,
               "notes": [{"id": "g8", "text": "the door, you should fix", "at": "x"}, {"id": "g6", "text": "hovering", "at": "x"}]}
    # the agent's answers, made over his session, land in the draft: a where he left it plus 7 (g8); b by 3 (g8 too)
    ans = [{"op": "ref.move", "space": "exterior", "id": a_id, "n": 1, "stroke": 1, "call": "fault", "answers": "g8",
            "before": {"pos": list(ra["pos"])}, "after": {"pos": [ra["pos"][0] + 107.0, ra["pos"][1], ra["pos"][2]]}},
           {"op": "ref.move", "space": "exterior", "id": b_id, "n": 2, "stroke": 1, "call": "fault", "answers": "g8",
            "before": {"pos": list(rb["pos"])}, "after": {"pos": [rb["pos"][0] + 3.0, rb["pos"][1], rb["pos"][2]]}}]
    sv = {"save_id": "agent-a", "place_id": "fx", "at": "2026-11-22T20:00:00Z", "by": "agent", "final": False,
          "ops": ans, "notes": session["notes"]}
    drafted, left = edits.apply_agent_save(files, sv)
    assert not left and drafted["place"]["agent_answers"][0]["owner_save"] == "open session"
    out = edits.apply_save(drafted, session)
    got = {r["id"]: r["pos"][0] for r in out["spaces"]["exterior"]["refs"]}
    assert abs(got[a_id] - (ra["pos"][0] + 107.0)) < 1e-6      # g8 answered: the answer stands
    assert abs(got[b_id] - (rb["pos"][0] + 50.0)) < 1e-6       # g6 not the answer's note: his edit wins
    # a row nobody answered that no longer fits is still a conflict
    other = dict(move(ra, 1.0), n=3, call="fault", id=refs[2]["id"], before={"pos": [0.0, 0.0, 0.0]})
    import pytest
    with pytest.raises(edits.EditConflict):
        edits.apply_save(drafted, dict(session, ops=[other]))


def test_an_answer_that_makes_his_change_keeps_his_ops_as_no_change(fx):
    """The agent delivers on the draft what his open session does (removes the row he removed, puts a row where he
    moved it); his ops of that note on that row no longer fit and are kept as no change, so the scene he sees is
    the one his session made."""
    pdir = fx / "places/fx"
    refs = rows(pdir / EXT)
    a_id = refs[0]["id"]
    files = edits.load_place(pdir)
    ra = next(x for x in files["spaces"]["exterior"]["refs"] if x["id"] == a_id)
    m1 = dict(move(ra, 10.0), n=1, call="fault", note_group="g2")
    moved = dict(ra, pos=m1["after"]["pos"])
    rm = {"op": "ref.remove", "space": "exterior", "id": a_id, "before": moved, "n": 2, "call": "fault", "note_group": "g2"}
    session = {"save_id": "autosave", "place_id": "fx", "at": "x", "ops": [m1, rm], "notes": [{"id": "g2", "text": "in the way", "at": "x"}]}
    ans = [{"op": "ref.remove", "space": "exterior", "id": a_id, "n": 1, "stroke": 1, "call": "fault", "answers": "g2",
            "before": ra}]
    drafted, left = edits.apply_agent_save(files, {"save_id": "agent-b", "place_id": "fx", "at": "y", "by": "agent",
                                                    "final": False, "ops": ans, "notes": session["notes"]})
    assert not left
    out = edits.apply_save(drafted, session)
    assert all(r["id"] != a_id or r.get("removed") for r in out["spaces"]["exterior"]["refs"])


def test_a_later_request_undoes_his_earlier_change(fx):
    """He removed a row in his open session, then asked to have it back: the agent's answer lists his earlier note
    under `undoes`, and his ops of that note on that row replay as no change, so the row stays as the answer put it."""
    pdir = fx / "places/fx"
    a_id = rows(pdir / EXT)[0]["id"]
    files = edits.load_place(pdir)
    ra = next(x for x in files["spaces"]["exterior"]["refs"] if x["id"] == a_id)
    m1 = dict(move(ra, 10.0), n=1, call="fault", note_group="g2")
    rm = {"op": "ref.remove", "space": "exterior", "id": a_id, "before": dict(ra, pos=m1["after"]["pos"]), "n": 2,
          "call": "fault", "note_group": "g2"}
    files["place"]["agent_answers"] = [{"answers": "request-1", "rows": [a_id], "undoes": ["g2"]}]
    out = edits.apply_save(files, {"save_id": "autosave", "place_id": "fx", "at": "x", "ops": [m1, rm],
                                   "notes": [{"id": "g2", "text": "in the way", "at": "x"}]})
    got = next(r for r in out["spaces"]["exterior"]["refs"] if r["id"] == a_id)
    assert not got.get("removed") and got["pos"] == ra["pos"]


def test_his_unit_moves_and_spot_edits_replay_over_answers(fx):
    """A unit he moved whole, a member of which the agent answered, and a person's edit of his on a person the agent
    answered, replay by the same rule: the answered note's change is kept as no change (the answer stands), another
    note's is his edit over the row as it stands. The agent's answer lists the person it touched among its rows."""
    pdir = fx / "places/fx"
    refs = rows(pdir / EXT)
    a_id, b_id = refs[0]["id"], refs[1]["id"]
    files = edits.load_place(pdir)
    ra = next(x for x in files["spaces"]["exterior"]["refs"] if x["id"] == a_id)
    rb = next(x for x in files["spaces"]["exterior"]["refs"] if x["id"] == b_id)
    files.setdefault("people", []).append({"id": "fx.p1", "name": "P", "routine": [{"start": 8, "kind": "wander", "at": {"space": "exterior", "pos": [0, 0]}}]})
    p0 = json.loads(json.dumps(files["people"][-1]))
    p_his = dict(p0, routine=[{"start": 8, "kind": "wander", "at": {"space": "exterior", "pos": [5, 5]}}])
    shift = lambda r, dx: {"pos": [r["pos"][0] + dx, r["pos"][1], r["pos"][2]]}   # noqa: E731
    unit = {"op": "unit.move", "space": "exterior", "unit": "u1", "n": 1, "call": "fault", "note_group": "g10",
            "refs": [{"id": a_id, "before": {"pos": list(ra["pos"])}, "after": shift(ra, 100.0)},
                     {"id": b_id, "before": {"pos": list(rb["pos"])}, "after": shift(rb, 100.0)}]}
    pe = {"op": "person.edit", "n": 2, "call": "fault", "note_group": "g12", "person": p_his, "before": p0}
    session = {"save_id": "autosave", "place_id": "fx", "at": "x", "ops": [unit, pe],
               "notes": [{"id": "g10", "text": "tent in the way", "at": "x"}, {"id": "g12", "text": "taste", "at": "x"}]}
    p_ans = dict(p0, routine=[{"start": 8, "kind": "wander", "at": {"space": "exterior", "pos": [9, 9]}}])
    ans = [{"op": "ref.move", "space": "exterior", "id": a_id, "n": 1, "stroke": 1, "call": "fault", "answers": "g10",
            "before": {"pos": list(ra["pos"])}, "after": shift(ra, 107.0)},
           {"op": "person.edit", "n": 2, "stroke": 2, "call": "fault", "answers": "g12", "person": p_ans, "before": p0},
           {"op": "ref.move", "space": "exterior", "id": b_id, "n": 3, "stroke": 3, "call": "fault", "answers": "g6",
            "before": {"pos": list(rb["pos"])}, "after": shift(rb, 3.0)}]
    drafted, left = edits.apply_agent_save(files, {"save_id": "agent-u", "place_id": "fx", "at": "y", "by": "agent",
                                                    "final": False, "ops": ans, "notes": session["notes"]})
    assert not left
    assert "fx.p1" in drafted["place"]["agent_answers"][1]["rows"]
    out = edits.apply_save(drafted, session)
    got = {r["id"]: r["pos"][0] for r in out["spaces"]["exterior"]["refs"]}
    assert abs(got[a_id] - (ra["pos"][0] + 107.0)) < 1e-6     # g10 answered on a: the answer stands
    assert abs(got[b_id] - (rb["pos"][0] + 100.0)) < 1e-6     # b answered for another note: his move wins
    person = next(p for p in out["people"] if p["id"] == "fx.p1")
    assert person["routine"][0]["at"]["pos"] == [9, 9]           # g12 answered: the answer stands
