"""The things the quest records put at a place, and where each stands (docs/design/quests-on-a-world.md, "Where a
quest's thing stands"; docs/design/place-studio.md, "Quest things").

A quest record's `placements` row anchored `{place: <place id>}` says what the quest puts there, in words (`need`,
`room`); the exact spot is the owner's, set in the studio, and kept in one row of the place's `quests.jsonl`:
`{id: "<quest id>/<ref>", quest, ref, space, pos: [x, y, z], rot: [0, 0, heading]}`. Nothing else holds a quest
thing's spot: the quest builder reads it from there as the form's `at`.

`payload(place_id)` is what the studio shows: every such thing with when it is in the world (the stage or ending that
switches it on and off, or from the start of the game), the words the record asks for, its spot or none yet, and
links into the story explorer at its quest and stage. A spot row whose placement has gone from the records is listed
too (`orphan`), so it is seen and cleared rather than kept by a record that no longer asks for it."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
QUESTS = ROOT / "newworld" / "story" / "quests"
PLACES = ROOT / "newworld" / "places"
SOURCES = ROOT / "newworld" / "sources"
EXPLORER = ROOT / "tools" / "newworld" / "story_explorer.json"
FILE = "quests.jsonl"
KIND_WORD = {"person": "person", "door": "door", "thing": "thing", "container": "container", "marker": "marker"}


def spot_id(quest: str, ref: str) -> str:
    return f"{quest}/{ref}"


def hash_id(code: str) -> str:
    """The story explorer's id of a quest in its address (story_explorer_page.html hashId)."""
    return re.sub(r"[^a-z0-9]+", "-", str(code).lower())


def explorer_url(path: Path = EXPLORER) -> str | None:
    try:
        return json.loads(path.read_text()).get("url")
    except (OSError, ValueError):
        return None


def link(url: str | None, code: str, stage=None) -> str | None:
    """The explorer's address of a quest, or of one stage of it (`#q-<quest>/s-<stage>`)."""
    if not url:
        return None
    return f"{url}#q-{hash_id(code)}" + (f"/s-{stage}" if stage is not None else "")


def _one(s) -> str:
    return " ".join(str(s or "").split())


def _short(s, n: int = 140) -> str:
    s = _one(s)
    return s if len(s) <= n else s[: n - 1].rsplit(" ", 1)[0] + "…"


def records(quests: Path = QUESTS) -> list[dict]:
    import yaml
    out = []
    for p in sorted(quests.glob("*/*.yaml")):
        q = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        if isinstance(q, dict) and q.get("id"):
            out.append(q)
    return out


def switches(recs: list[dict]) -> dict[str, list[dict]]:
    """ref -> every switch of it in the records: {on: bool, quest, code, stage | None, ending | None, when}."""
    out: dict[str, list[dict]] = {}

    def walk(o, q, stage, ending):
        if isinstance(o, dict):
            for k in ("enableRef", "disableRef"):
                if isinstance(o.get(k), str):
                    out.setdefault(o[k], []).append({"on": k == "enableRef", "quest": q["id"], "code": q.get("code"),
                                                     "stage": stage, "ending": ending})
            for v in o.values():
                walk(v, q, stage, ending)
        elif isinstance(o, list):
            for v in o:
                walk(v, q, stage, ending)
    for q in recs:
        for s in q.get("stages") or []:
            walk(s, q, s.get("id"), None)
        for e in q.get("endings") or []:
            walk(e, q, None, e)
    return out


def _stage(q: dict, sid) -> dict:
    return next((s for s in q.get("stages") or [] if str(s.get("id")) == str(sid)), {})


def _when_words(sw: dict, by_id: dict[str, dict]) -> str:
    q = by_id.get(sw["quest"]) or {}
    name = f"{q.get('code')} {_one(q.get('title'))}"
    if sw["stage"] is not None:
        j = _short(_stage(q, sw["stage"]).get("journalText"), 110)
        return f"when {name} reaches stage {sw['stage']}" + (f" (“{j}”)" if j else "")
    return f"at an ending of {name}: {_short((sw['ending'] or {}).get('when'), 110)}"


def _rooms(place_dir: Path) -> dict[str, str]:
    """A room's name (lower case) -> its space id."""
    out = {}
    for sj in sorted((place_dir / "spaces").glob("*/space.json")) if (place_dir / "spaces").exists() else []:
        try:
            s = json.loads(sj.read_text())
        except ValueError:
            continue
        if s.get("name"):
            out[str(s["name"]).lower()] = sj.parent.name
    return out


def _cast(place_id: str, sources: Path) -> dict[str, dict]:
    """ref -> the place's people source row cast as it (a quest's person who is the place's person)."""
    p = sources / "people" / f"{place_id}.json"
    try:
        doc = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return {r["cast"]: r for r in doc.get("people") or [] if isinstance(r, dict) and r.get("cast")}


def read(place_dir: Path) -> list[dict]:
    p = Path(place_dir) / FILE
    if not p.exists():
        return []
    return [json.loads(ln) for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]


def payload(place_id: str, places: Path = PLACES, quests: Path = QUESTS, sources: Path = SOURCES,
            url: str | None = None) -> dict:
    """{items: [...], spots: [quests.jsonl rows], explorer}: every quest thing at the place (see the module's words)."""
    url = url if url is not None else explorer_url()
    place_dir = places / place_id
    recs = records(quests)
    by_id = {q["id"]: q for q in recs}
    sw = switches(recs)
    rooms, cast = _rooms(place_dir), _cast(place_id, sources)
    spots = read(place_dir)
    have = {r["id"]: r for r in spots}
    items, seen = [], set()
    for q in recs:
        start = q.get("start") if q.get("start") is not None else ((q.get("stages") or [{}])[0].get("id"))
        for r in q.get("placements") or []:
            a = r.get("anchor") if isinstance(r.get("anchor"), dict) else {}
            if a.get("place") != place_id or not r.get("ref"):
                continue
            sid = spot_id(q["id"], r["ref"])
            seen.add(sid)
            ons = [s for s in sw.get(r["ref"], []) if s["on"]]
            offs = [s for s in sw.get(r["ref"], []) if not s["on"]]
            if r.get("enabled", True):
                appears = {"words": f"In the world from the start of the game; {q.get('code')} uses it from stage {start}.",
                           "stage": start, "quest": q["id"], "code": q.get("code")}
            elif ons:
                first = ons[0]
                appears = {"words": f"Appears {_when_words(first, by_id)}.", "stage": first["stage"],
                           "quest": first["quest"], "code": first["code"]}
            else:
                appears = {"words": "Starts switched off, and no quest switches it on yet.", "stage": None,
                           "quest": q["id"], "code": q.get("code")}
            gone = [{"words": f"Goes {_when_words(s, by_id)}.", "stage": s["stage"], "quest": s["quest"], "code": s["code"],
                     "url": link(url, s["code"], s["stage"])} for s in offs]
            room = a.get("room")
            person = cast.get(r["ref"])
            items.append({
                "id": sid, "quest": q["id"], "code": q.get("code"), "title": _one(q.get("title")), "ref": r["ref"],
                "kind": r.get("kind"), "kind_word": KIND_WORD.get(r.get("kind"), r.get("kind")),
                "name": r.get("name") or r.get("placeName") or r["ref"],
                "base": (r.get("base") or {}).get("id") if isinstance(r.get("base"), dict) else r.get("base"),
                "need": _one(a.get("need")), "room": room, "space": rooms.get(str(room).lower(), "exterior") if room else "exterior",
                "rule": a.get("rule"), "hostile": bool(r.get("hostile")), "enabled": bool(r.get("enabled", True)),
                "lock": r.get("lock"),
                "appears": appears | {"url": link(url, appears["code"], appears["stage"])}, "gone": gone,
                "quest_url": link(url, q.get("code")),
                "place_person": {"id": person.get("id"), "name": person.get("name")} if person else None,
                "spot": have.get(sid)})
    for r in spots:
        if r["id"] not in seen:
            items.append({"id": r["id"], "quest": r.get("quest"), "ref": r.get("ref"), "name": r.get("ref"), "orphan": True,
                          "spot": r, "appears": {"words": "No quest record places this here any more: clear its spot."},
                          "gone": [], "space": r.get("space", "exterior"), "kind": "thing", "kind_word": "thing"})
    return {"place_id": place_id, "explorer": url, "items": items, "spots": spots}


def check(place_id: str, places: Path = PLACES, quests: Path = QUESTS) -> list[str]:
    """Problems with the place's quest spots: a row no record asks for, a row in a space the place lacks."""
    d = payload(place_id, places, quests, url="")
    spaces = {"exterior"} | {p.name for p in (places / place_id / "spaces").glob("*")}
    out = []
    for it in d["items"]:
        s = it.get("spot")
        if it.get("orphan"):
            out.append(f"{it['id']}: a spot no quest record asks for")
        elif s and s.get("space") not in spaces:
            out.append(f"{it['id']}: its spot is in {s.get('space')}, a space {place_id} does not have")
    return out
