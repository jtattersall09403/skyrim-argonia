"""A place's promise list: every physical thing and arrangement its record, its people and its quests promise of it,
made at plan time and built against (docs/design/place-studio.md, Promises).

`newworld/places/<place_id>/promises.jsonl`, one row per promise:

  {"id": "p03", "what": "the young Hist's sap pool with eggs in it",
   "said": [{"key": "<gathered key>", "where": "place note faith", "words": "<the sentence>"}],
   "show": "kept" | "relabelled" | "added" | "schedule" | "state" | "give" | "quest",
   "refs": [ref ids], "person": "<people row id>", "state": "<states.jsonl id>", "give": "<draft.plan gives kind>",
   "quest": ["<quest id>/<ref>"],
   "verdict": "built" | "accepted" | "open", "why": "..."}

The draft.plan's `gives` stay the record's formal promises (the stock's deliveries); this list holds everything said,
and a row may show a promise by a give (`show: give`).

  python -m tools.places promises <place_id> --gather   every sentence that names a thing, a station, an hour or a
                                                        state, with its key (`--json` for rows; `--new` only the
                                                        sentences no row says yet)
  python -m tools.places promises <place_id> --fill     fill each row's `said` from its keys (write a row's said as
                                                        [{"key": ...}] and let the tool copy the where and words)
  python -m tools.places promises <place_id> --check    the list's faults (also the build's and draft check's)

The check fails a gathered sentence no row says (an accepted row with its reason is a row), a row that says a
sentence no longer gathered (the words changed: judge them again), an open row, a built row with no evidence or with
evidence the place files do not hold, a quest's state sentence not shown by a state, and a state with its faults.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLACES = ROOT / "newworld" / "places"
DB = ROOT / "newworld" / "story" / "data" / "db"
QUESTS = ROOT / "newworld" / "story" / "quests"
SHOWS = ("kept", "relabelled", "added", "schedule", "state", "give", "quest")

# words that name a physical thing, a station or trade's place, an hour, or a state of the place
THING = (r"hist|tree|trunk|root|scar|sap|pool|egg|clutch|nest|tent|platform|walkway|plank|post|stilt|weir|boom|log|"
         r"hide|reed|jar|pot|rack|stall|stand|fire|hearth|boat|canoe|raft|landing|dock|pier|jett?y|trap|net|line|shrine|"
         r"altar|idol|totem|statue|house|hut|home|longhouse|hall|room|cellar|door|chest|box|crate|barrel|sack|pack|key|"
         r"bed|bedroll|hammock|forge|anvil|bench|table|kitchen|smok|offal|stone|cage|lantern|lamp|torch|fence|wall|"
         r"gate|well|garden|field|pen|sign|map|note|book|letter|bowl|basket|mound|tower|ruin|bridge|path|road|stair|"
         r"step|ladder|tomb|grave|bone|skull|skin|pelt|fish|eel|gar|carp|crab|meat|grain|mushroom|fungus|herb|moss|"
         r"plant|vine|flower|cart|wagon|well|post|marker|pole|mast|hull|wreck|cave|mine|quarry|kiln|loom|still|cauldron|"
         r"cookpot|spit|smokehouse|shelf|cupboard|desk|chair|throne|banner|flag|weapon|spear|bow|armou?r|tool|gear")
STATION = (r"sells?|selling|trades?|trains?|cooks?|smokes?|tans?|brews?|forges?|mends?|works?|keeps?|minds?|tends?|"
           r"guards?|watch(?:es)?|sleeps?|asleep|lives?|stands?|sits?|fish(?:es)?|hunts?|traps?|carves?|weaves?")
HOUR = (r"morning|noon|evening|night|dusk|dawn|midnight|all day|every day|each day|by day|at \d{1,2}|o'clock|hour|"
        r"before|after|until|while")
STATE = r"dead(?!\s+(?:swamp\s+)?trees?\b)|dies|died|dying|sick|cold|empty|gone|burn\w*|ruin\w*|abandon\w*|leave|deserted|healed|green|blacken\w*"
GATHER = re.compile(rf"\b(?:{THING})\w*|\b(?:{STATION})\b|\b(?:{HOUR})\b|\b(?:{STATE})\b", re.I)
STATE_RE = re.compile(rf"\b(?:{STATE})\b", re.I)
# a place note's aspects that say nothing of the built place
NOTE_SKIP = {"climate", "ecology"}


def jsonl(p: Path) -> list[dict]:
    p = Path(p)
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()] if p.exists() else []


def sentences(text: str) -> list[str]:
    """The sentences of a text, split at a full stop, a semicolon or a colon followed by a capital."""
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    parts = re.split(r"(?<=[.!?;])\s+(?=[A-Z\"'(])", text)
    return [p.strip() for p in parts if len(p.strip()) > 3]


def key(where: str, words: str) -> str:
    return hashlib.sha1(f"{where}|{words.strip().lower()}".encode()).hexdigest()[:10]


def _cand(out: list, seen: set, where: str, text: str, kind: str = "thing", always: bool = False) -> None:
    for s in sentences(text):
        if not (always or GATHER.search(s)):
            continue
        k = key(where, s)
        if k in seen:
            continue
        seen.add(k)
        out.append({"key": k, "where": where, "words": s, "kind": kind})


def place_names(place_id: str, db: Path = DB) -> list[str]:
    names = [r["name"] for r in jsonl(db / "place.jsonl") if r.get("id") == place_id and r.get("name")]
    names += [r["alias"] for r in jsonl(db / "place_alias.jsonl") if r.get("place_id") == place_id and r.get("alias")]
    return names


def _names_place(text: str, names: list[str]) -> bool:
    t = str(text or "").lower()
    return any(n.lower() in t for n in names)


def gather(place_id: str, db: Path = DB, quests: Path = QUESTS) -> list[dict]:
    """Every sentence of the place record's notes, its people rows and the quest rows that touch the place that names
    a physical thing, a station, an hour or a state: [{key, where, words, kind}], kind "state" for what a quest says
    of the place in one of its states (an ending's world, a thing switched in), else "thing"."""
    from tools.places import variant
    rec = variant.record_id(place_id)
    out, seen = [], set()
    names = place_names(rec, db)
    for n in jsonl(db / "place_note.jsonl"):
        if n.get("place_id") == rec and n.get("aspect_id") not in NOTE_SKIP:
            _cand(out, seen, f"place note {n['aspect_id']}", n.get("text"))
    for g in jsonl(db / "place_give.jsonl"):
        if g.get("place_id") == rec:
            _cand(out, seen, f"place give {g.get('seq')}", f"{g.get('give_kind_id')}: {g.get('detail') or ''}", always=True)
    for n in jsonl(db / "place_need.jsonl"):
        if n.get("place_id") == rec:
            _cand(out, seen, f"place need {n.get('seq')}", n.get("thing"), always=True,
                  kind="state" if STATE_RE.search(n.get("thing") or "") else "thing")
    for n in jsonl(db / "place_need_sign.jsonl"):
        if n.get("place_id") == rec:
            _cand(out, seen, f"place need {n.get('need_seq')} {n.get('need_sign_id')}", n.get("detail"), always=True,
                  kind="state" if STATE_RE.search(n.get("detail") or "") else "thing")
    people = {p["id"]: p for p in jsonl(db / "person.jsonl") if p.get("place_id") == rec}
    for pid, p in people.items():
        who = p.get("name") or pid
        if p.get("trade"):
            _cand(out, seen, f"person {who} trade", f"{who}: {p['trade']}", always=True)
    for n in jsonl(db / "person_note.jsonl"):
        p = people.get(n.get("person_id"))
        if p:
            _cand(out, seen, f"person {p.get('name') or p['id']} {n.get('aspect_id')}", n.get("text"))
    for t in jsonl(db / "trader.jsonl"):
        if (t.get("place_id") == rec or t.get("person_id") in people) and t.get("why"):
            who = (people.get(t.get("person_id")) or {}).get("name") or t.get("person_id")
            _cand(out, seen, f"trader {who}", f"{who} trades: {t.get('why') or ''}", always=True)
    for q in _records(quests):
        _quest(out, seen, q, rec, names)
    return out


def _records(quests: Path) -> list[dict]:
    from tools.places import quest_spots
    return quest_spots.records(quests)


def _d(x) -> dict:
    return x if isinstance(x, dict) else {}


def _dicts(x) -> list[dict]:
    return [d for d in x or [] if isinstance(d, dict)]


def _quest(out: list, seen: set, q: dict, rec: str, names: list[str]) -> None:
    qid = q.get("id") or "?"
    code = q.get("code") or qid
    here = {r["ref"] for r in _dicts(q.get("placements"))
            if isinstance(r.get("anchor"), dict) and r["anchor"].get("place") == rec and r.get("ref")}
    for r in _dicts(q.get("placements")):
        a = _d(r.get("anchor"))
        if a.get("place") != rec:
            continue
        bits = [r.get("name") or r.get("ref"), a.get("need"), r.get("note")]
        if r.get("carriedBy"):
            bits.append(f"carried by {r['carriedBy']}")
        if r.get("container"):
            bits.append(f"in {r['container']}")
        if r.get("lock"):
            bits.append(f"locked ({(r['lock'] or {}).get('level')})")
        _cand(out, seen, f"{code} placement {r.get('ref')}", "; ".join(str(b) for b in bits if b).replace("; ", ", "),
              always=True)
    homed = {c.get("id") for c in _dicts(q.get("cast")) if _d(c.get("persona")).get("home") == rec} | \
        {r for r in here if str(r).startswith("npc.")}
    for c in _dicts(q.get("cast")):
        if c.get("id") in homed and _d(c.get("persona")).get("role"):
            _cand(out, seen, f"{code} cast {c.get('name') or c['id']}", f"{c.get('name') or c['id']}: {_d(c.get('persona'))['role']}",
                  always=True)
    for t in _dicts(q.get("things")):
        txt = " ".join(str(t.get(k) or "") for k in ("where", "source"))
        if t.get("where") == rec or _names_place(txt, names) or t.get("id") in here:
            kind = "state" if STATE_RE.search(txt) and (t.get("states") or _names_place(txt, names)) else "thing"
            for k in ("where", "source"):
                if t.get(k):
                    _cand(out, seen, f"{code} thing {t['id']} {k}", t[k], kind=kind if k == "source" else "thing")
    for s in _dicts(q.get("stages")):
        at = s.get("place") == rec
        texts = [s.get("journalText")] + [o.get("objectiveText") for o in _dicts(s.get("objectives"))]
        for i, txt in enumerate(texts):
            if not txt:
                continue
            w = f"{code} stage {s.get('id')} {'journal' if i == 0 else 'objective'}"
            if at:
                _cand(out, seen, w, txt)
            else:
                for sen in sentences(txt):
                    if _names_place(sen, names):
                        _cand(out, seen, w, sen)
    for e in _dicts(q.get("endings")):
        world_here = [w for w in _dicts(e.get("world")) for k, v in w.items()
                      if k in ("enableRef", "disableRef", "moveRef") and (v if isinstance(v, str) else (v or [None])[0]) in here]
        for k in ("seen", "costs", "gives"):
            for sen in sentences(e.get(k) or ""):
                if _names_place(sen, names):
                    _cand(out, seen, f"{code} ending {e.get('id')} {k}", sen,
                          kind="state" if STATE_RE.search(sen) else "thing", always=True)
        if world_here:
            _cand(out, seen, f"{code} ending {e.get('id')} world", f"{e.get('when') or e.get('id')}: "
                  + ", ".join(json.dumps(w) for w in world_here), kind="state", always=True)
    for t in _dicts(q.get("topics")):
        if t.get("person") in homed:
            for sen in sentences(t.get("intent") or ""):
                if re.match(r"(Checks|Does): nothing", sen):
                    continue
                if GATHER.search(sen) and (_names_place(sen, names) or re.search(rf"\b(?:{HOUR})\b|\b(?:{STATION})\b", sen, re.I)):
                    _cand(out, seen, f"{code} topic {t.get('id')}", sen)


# ---- the list and its check ------------------------------------------------------------------------------------

def load(pdir: Path) -> list[dict]:
    return jsonl(Path(pdir) / "promises.jsonl")


def copied_refs(pdir: Path, source_id: str | None, bundles: Path | None = None) -> set[str]:
    """The refs of every room copied from a source cell (`copy_of`), as the build composes it: the source's own refs
    keep their source keys as ids (a carried pay chest, a bed), so a promise can name them. Empty without the bundles."""
    from tools.places import draft_bundle
    bundles = Path(bundles) if bundles else ROOT / "out" / "places" / "bundles"
    out: set[str] = set()
    sp = Path(pdir) / "spaces"
    for d in sorted(p for p in sp.iterdir() if p.is_dir()) if sp.is_dir() else []:
        info = json.loads((d / "space.json").read_text()) if (d / "space.json").exists() else {}
        if not info.get("copy_of") or not source_id:
            continue
        try:
            rows = draft_bundle.copy_space(info, jsonl(d / "refs.jsonl"), bundles / f"src.{source_id}")
        except (OSError, KeyError, ValueError):
            continue
        out |= {r["id"] for r in rows if r.get("id")}
    return out


def evidence(pdir: Path) -> dict:
    """What the place files hold, as ids: refs (every space's, the ledger's placed ids and source keys), people,
    quest spots, states and the plan's gives."""
    from tools.places import states as S
    pdir = Path(pdir)
    refs = {r["id"] for r in S.place_refs(pdir)}
    for r in jsonl(pdir / "ledger.jsonl"):
        if r.get("status") in ("placed", "adapted", "replaced", "kept") or r.get("as"):
            a = r.get("as")
            refs.update(a if isinstance(a, list) else [a])
            refs.add(r.get("src"))
    refs.discard(None)
    place = json.loads((pdir / "place.json").read_text()) if (pdir / "place.json").exists() else {}
    refs |= copied_refs(pdir, place.get("source_id"))
    gives = {g.get("kind") for g in ((place.get("draft") or {}).get("plan") or {}).get("gives") or []}
    qs = jsonl(pdir / "quests.jsonl")
    return {"refs": refs, "people": {p["id"] for p in jsonl(pdir / "people.jsonl")} | {p.get("name") for p in jsonl(pdir / "people.jsonl")},
            "quest": {q["id"] for q in qs if q.get("pos") or q.get("drafted")}, "states": {s["id"]: s for s in S.load(pdir)},
            "gives": gives}


def faults(place_id: str, pdir: Path | None = None, cands: list[dict] | None = None, db: Path = DB,
           quests: Path = QUESTS) -> list[str]:
    """The promise list's faults (see the module's words). A place with no list yet fails only when gathered
    sentences exist: the list is made at plan time."""
    from tools.places import states as S
    pdir = Path(pdir or PLACES / place_id)
    cands = gather(place_id, db, quests) if cands is None else cands
    rows = load(pdir)
    if not rows:
        return [f"{place_id}: no promise list (promises.jsonl); {len(cands)} sentences gathered: make it at plan time "
                f"(`python -m tools.places promises {place_id} --gather`)"] if cands else []
    by_key = {c["key"]: c for c in cands}
    ev = evidence(pdir)
    bad, said = [], {}
    for r in rows:
        rid = r.get("id") or "?"
        for s in r.get("said") or []:
            said.setdefault(s.get("key"), []).append(r)
            if s.get("key") not in by_key:
                bad.append(f"promise {rid}: says {s.get('where')}: \"{s.get('words')}\", which is no longer said "
                           f"(the words changed or went: judge them again)")
        v = r.get("verdict")
        if v == "open":
            bad.append(f"promise {rid} ({r.get('what')}): open: {r.get('why') or 'not built yet'}")
            continue
        if v == "accepted":
            if not (r.get("why") or "").strip():
                bad.append(f"promise {rid} ({r.get('what')}): accepted with no reason")
            continue
        if v != "built":
            bad.append(f"promise {rid}: verdict {v!r} (built, accepted or open)")
            continue
        if r.get("show") not in SHOWS:
            bad.append(f"promise {rid}: show {r.get('show')!r} is not one of {SHOWS}")
        got = 0
        for x in r.get("refs") or []:
            got += 1
            if x not in ev["refs"]:
                bad.append(f"promise {rid} ({r.get('what')}): ref {x} is not in the place files")
        if r.get("person"):
            got += 1
            if r["person"] not in ev["people"]:
                bad.append(f"promise {rid} ({r.get('what')}): person {r['person']} is not in people.jsonl")
        for x in r.get("quest") or []:
            got += 1
            if x not in ev["quest"]:
                bad.append(f"promise {rid} ({r.get('what')}): quest spot {x} is not drafted in quests.jsonl")
        if r.get("give"):
            got += 1
            if r["give"] not in ev["gives"]:
                bad.append(f"promise {rid} ({r.get('what')}): give {r['give']} is not in draft.plan's gives")
        if r.get("state"):
            got += 1
            st = ev["states"].get(r["state"])
            if st is None:
                bad.append(f"promise {rid} ({r.get('what')}): state {r['state']} is not in states.jsonl")
            elif not st.get("key"):
                bad.append(f"promise {rid} ({r.get('what')}): state {r['state']} has no key refs")
        if r.get("show") == "state" and not r.get("state"):
            bad.append(f"promise {rid} ({r.get('what')}): shown by a state but names none")
        if not got:
            bad.append(f"promise {rid} ({r.get('what')}): built with no evidence (refs, person, quest, give or state)")
    for c in cands:
        rs = said.get(c["key"])
        if not rs:
            bad.append(f"unsaid: {c['where']}: \"{c['words']}\" ({c['key']}): no promise row says it")
        elif c["kind"] == "state" and not any(r.get("show") == "state" or r.get("verdict") == "accepted" for r in rs):
            bad.append(f"state: {c['where']}: \"{c['words']}\" ({c['key']}): a quest's state of the place, shown by no "
                       f"state (states.jsonl; place-story, Quest states)")
    return bad + S.faults(pdir)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="python -m tools.places promises")
    ap.add_argument("place_id")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--gather", action="store_true")
    g.add_argument("--check", action="store_true")
    g.add_argument("--fill", action="store_true", help="fill each row's said entries' where and words from their keys")
    ap.add_argument("--json", action="store_true", help="gather: one JSON row per sentence")
    ap.add_argument("--new", action="store_true", help="gather: only the sentences no row says yet")
    ap.add_argument("--places", type=Path, default=PLACES)
    a = ap.parse_args(argv)
    pdir = a.places / a.place_id
    if a.gather:
        cands = gather(a.place_id)
        if a.new:
            have = {s.get("key") for r in load(pdir) for s in r.get("said") or []}
            cands = [c for c in cands if c["key"] not in have]
        for c in cands:
            print(json.dumps(c, ensure_ascii=False) if a.json else
                  f"{c['key']} [{c['kind']}] {c['where']}: {c['words']}")
        print(f"{len(cands)} sentences", file=sys.stderr)
        return 0
    if a.fill:
        cands = {c["key"]: c for c in gather(a.place_id)}
        rows = load(pdir)
        for r in rows:
            r["said"] = [{"key": s["key"], "where": cands[s["key"]]["where"], "words": cands[s["key"]]["words"]}
                         if s.get("key") in cands else s for s in r.get("said") or []]
        (pdir / "promises.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
        left = len({k for k in cands} - {s.get("key") for r in rows for s in r.get("said") or []})
        print(f"promises {a.place_id}: {len(rows)} rows filled; {left} gathered sentences no row says yet (--gather --new)")
        return 0
    bad = faults(a.place_id, pdir)
    for b in bad:
        print(b)
    print(f"promises {a.place_id}: {'PASS' if not bad else f'{len(bad)} faults'}", file=sys.stderr)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
