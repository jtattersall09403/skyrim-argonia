"""A place's quest states: the place as the player sees it in each state a quest puts it in.

`newworld/places/<place_id>/states.jsonl`, one row per state (docs/design/place-studio.md, Quest states):

  {"id": "hist-dead", "name": "Hist dead (ending)", "default": false,
   "set_by": {"quest": "quest.main.mn19", "ending": "e-take", "flag": "flag.mn.trees-parted"},
   "parents": {"<enable parent ref id>": false},   # the parents' enable state in this state (unlisted: enabled)
   "hide": [ids], "show": [ids],                   # refs or people switched off or on beyond their parents
   "moves": {"<person or ref id>": [x, y, z]},     # where a state moves someone (a quest's move of one reference)
   "key": [ids],                                   # the refs that make the state recognisable (the check needs them)
   "why": "..."}

Exactly one state is the default (the game's start). A ref follows its enable parent as the game does: enabled when
its parent is, or the opposite with `SetEnableStateToOppositeOfParent`. The quest record keeps what sets a state; the
row names it in `set_by` so the studio and the checks can say it.

  python -m tools.places states <place_id> [--state <id>]   list the states, or what one shows and hides
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLACES = ROOT / "newworld" / "places"
OPPOSITE = "SetEnableStateToOppositeOfParent"


def jsonl(p: Path) -> list[dict]:
    return [json.loads(x) for x in Path(p).read_text(encoding="utf-8").splitlines() if x.strip()] if Path(p).exists() else []


def load(pdir: Path) -> list[dict]:
    return jsonl(Path(pdir) / "states.jsonl")


def default(states: list[dict]) -> dict | None:
    return next((s for s in states if s.get("default")), states[0] if states else None)


def find(states: list[dict], name: str | None) -> dict | None:
    """A state by id or by name (any case); None names the default."""
    if not name:
        return default(states)
    n = name.strip().lower()
    return next((s for s in states if s["id"].lower() == n or (s.get("name") or "").lower() == n), None)


def place_refs(pdir: Path) -> list[dict]:
    """Every ref of the place's spaces, each with its space."""
    out = []
    sp = Path(pdir) / "spaces"
    for d in sorted(p for p in sp.iterdir() if p.is_dir()) if sp.is_dir() else []:
        out += [{**r, "space": r.get("space") or d.name} for r in jsonl(d / "refs.jsonl")]
    return out


def enabled(ref: dict, state: dict | None) -> bool:
    """Is the ref enabled in this state? (No state: everything shows, as the place files stand.)"""
    if state is None:
        return True
    rid = ref.get("id")
    if rid in (state.get("hide") or []):
        return False
    if rid in (state.get("show") or []):
        return True
    ep = ref.get("enable_parent") or {}
    if not ep.get("ref"):
        return True
    on = bool((state.get("parents") or {}).get(ep["ref"], True))
    return (not on) if OPPOSITE in str(ep.get("flags") or "") else on


def resolve(pdir: Path, name: str | None = None, refs: list[dict] | None = None, people: list[dict] | None = None) -> dict:
    """{state, hidden: [ids], shown: [ids of refs that switch with the state], moves: {id: pos}} for one state."""
    states = load(pdir)
    st = find(states, name)
    if name and st is None:
        raise KeyError(f"no state {name!r} at {Path(pdir).name}; states: {[s['id'] for s in states]}")
    refs = place_refs(pdir) if refs is None else refs
    people = jsonl(Path(pdir) / "people.jsonl") if people is None else people
    switching = [r for r in refs if (r.get("enable_parent") or {}).get("ref")
                 or any(r.get("id") in (s.get("hide") or []) + (s.get("show") or []) for s in states)]
    hidden = [r["id"] for r in refs if not enabled(r, st)]
    hidden += [p["id"] for p in people if st and p["id"] in (st.get("hide") or [])]
    # a quest's person or thing at the place (quests.jsonl), named by its quest ref or its spot id
    hidden += [q["id"] for q in jsonl(Path(pdir) / "quests.jsonl")
               if st and ({q.get("ref"), q.get("id")} & set(st.get("hide") or []))]
    return {"state": st, "hidden": hidden, "shown": [r["id"] for r in switching if enabled(r, st)],
            "moves": dict((st or {}).get("moves") or {})}


def faults(pdir: Path) -> list[str]:
    """The states file's own faults: one default, every parent, key, hide, show and move naming a ref or person of
    the place, a key that shows in its own state, and a setter for every state but the default."""
    pdir = Path(pdir)
    states = load(pdir)
    if not states:
        return []
    refs = place_refs(pdir)
    ids = {r["id"] for r in refs} | {p["id"] for p in jsonl(pdir / "people.jsonl")} | \
        {q.get("ref") for q in jsonl(pdir / "quests.jsonl")} | {q.get("id") for q in jsonl(pdir / "quests.jsonl")}
    by = {r["id"]: r for r in refs}
    bad = []
    if sum(1 for s in states if s.get("default")) != 1:
        bad.append(f"states: {sum(1 for s in states if s.get('default'))} default states (exactly one is the game's start)")
    seen = set()
    for s in states:
        sid = s.get("id")
        if not sid or sid in seen:
            bad.append(f"states: a state with no id or a repeated id ({sid})")
        seen.add(sid)
        if not s.get("default") and not s.get("set_by"):
            bad.append(f"state {sid}: no set_by (the quest, stage, ending or flag that sets it)")
        for k in ("parents", "hide", "show", "moves", "key"):
            for x in s.get(k) or []:
                if x not in ids:
                    bad.append(f"state {sid}: {k} names {x}, which is no ref or person of the place")
        if not s.get("key"):
            bad.append(f"state {sid}: no key refs (what makes the state recognisable)")
        for x in s.get("key") or []:
            if x in by and not enabled(by[x], s):
                bad.append(f"state {sid}: its key ref {x} is hidden in it")
    return bad


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="python -m tools.places states")
    ap.add_argument("place_id")
    ap.add_argument("--state")
    ap.add_argument("--places", type=Path, default=PLACES)
    a = ap.parse_args(argv)
    pdir = a.places / a.place_id
    states = load(pdir)
    if not states:
        print(f"{a.place_id}: no quest states (states.jsonl)")
        return 0
    if not a.state:
        for s in states:
            r = resolve(pdir, s["id"])
            print(f"{s['id']}{' (default)' if s.get('default') else ''}: {s.get('name')}; set by "
                  f"{json.dumps(s.get('set_by') or 'the game start')}; hides {len(r['hidden'])}, key {s.get('key')}")
        bad = faults(pdir)
        for b in bad:
            print("FAULT", b)
        return 1 if bad else 0
    r = resolve(pdir, a.state)
    print(json.dumps({"state": r["state"]["id"], "hidden": r["hidden"], "shown": r["shown"], "moves": r["moves"]}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
