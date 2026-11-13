"""What the stories need of a place, into the new world's database (docs/design/place-studio.md, "What the stories
need of a place"; tables story_line, need_sign, place_need, place_need_sign, place_need_story, person_need,
need_change).

Sources (committed, the single truth):
- `newworld/sources/needs/lines.json`: the story lines, each named for a reader who knows none of them;
- `newworld/sources/needs/<place_id>.json`: a place's needs and the story's uses of its people (agents write it,
  through `python -m tools.places needs`);
- `newworld/sources/needs/<place_id>.changed.jsonl`: the owner's changes to what a need rests on (the studio writes
  it when the owner carries on past a warning).

    python3 -m tools.newworld.needsdb load       # rewrite these tables alone (build_db does it with the rest)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from tools.argonia_world import db
from tools.newworld import frame as f

NEEDS = f.ROOT / "sources" / "needs"
TABLES = ("story_line", "need_sign", "place_need", "place_need_sign", "place_need_story", "person_need",
          "need_change")
SIGNS = {
    "look": "Its look on sight: the building or thing itself reads as that to someone who knows nothing.",
    "label": "The game's own label: the name on its door, the room's name on entering, a map marker's name, the "
             "name shown on the thing.",
    "beside": "What visibly stands in or by it: nests and eggs, nets, a forge.",
    "person": "A named person who tells the player, placing it by something fixed, before the player needs it.",
}


def _json(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def changes(pid: str, root: Path = NEEDS) -> list[dict]:
    p = root / f"{pid}.changed.jsonl"
    if not p.exists():
        return []
    return [json.loads(ln) for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]


def places(root: Path = NEEDS) -> list[str]:
    return sorted(p.stem for p in root.glob("*.json") if p.name != "lines.json")


def load(w, root: Path = NEEDS) -> None:
    if not (root / "lines.json").exists():
        return
    w.insert_many("story_line", _json(root / "lines.json")["lines"])
    w.insert_many("need_sign", [{"id": k, "about": v} for k, v in SIGNS.items()])
    for pid in places(root):
        doc = _json(root / f"{pid}.json")
        for n in doc.get("needs", []):
            rests = n.get("rests") or {}
            w.insert("place_need", place_id=pid, seq=n["seq"], thing=n["thing"], story_line_id=n["line"],
                     quests=n["quests"], does=n["does"], firmness=n["firmness"], rests_space=rests.get("space"),
                     rests_ref_id=rests.get("ref"), rests_person_id=rests.get("person"), met=bool(n["met"]),
                     why=n["why"], fit=n.get("fit"), narrow=n.get("narrow"),
                     sight=(n.get("sight") or {}).get("result"), sight_said=(n.get("sight") or {}).get("said"),
                     statement_tier_id=n.get("tier", "AGENT_INVENTED"))
            for s in n.get("signs", []):
                w.insert("place_need_sign", place_id=pid, need_seq=n["seq"], need_sign_id=s["sign"],
                         detail=s["detail"], person_id=s.get("person"))
            for st in dict.fromkeys(n.get("stories", [])):
                w.insert("place_need_story", place_id=pid, need_seq=n["seq"], story=st)
        for u in doc.get("people", []):
            w.insert("person_need", person_id=u["person"], seq=u["seq"], story_line_id=u["line"],
                     quests=u["quests"], what_for=u["for"], keep=u["keep"], firmness=u["firmness"],
                     story=u["story"])
        for i, c in enumerate(changes(pid, root)):
            w.insert("need_change", place_id=pid, seq=i, at=c["at"], need_seq=c.get("need"),
                     person_id=c.get("person"), change=c["change"], what=c["what"], save_id=c.get("save"),
                     statement_tier_id="OWNER_STATED")


def clear(w) -> None:
    w._begin()
    for t in reversed(TABLES):
        w.con.execute(f'DELETE FROM "{t}"')
        w.dirty.add(t)


def reload() -> db.World:
    """Rewrite these tables alone, from their sources."""
    w = db.open(f.ROOT, cache=False)
    clear(w)
    load(w)
    w.save()
    return w


def main(argv: list[str]) -> int:
    if argv[:1] == ["load"]:
        w = reload()
        print({t: len(w.rows(t)) for t in TABLES})
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
