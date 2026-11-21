"""Two places on one source are planned to differ before the later one's baseline is laid (skill place-plan).

The place whose baseline was laid FIRST from a source is the reference; every place laid later from the same source
owes a `draft.plan.differs` entry for each earlier one:

  {"place": "<the earlier place id>", "takes": ..., "turn_and_approach": ..., "landmark": ..., "prunes": ...,
   "adds": ..., "dressing_and_people": ...}

each field a sentence of at least MIN_WORDS words, not copied from the earlier place's plan. "Laid first" is a fact
of the files: `place.json` `wholesale.laid` (the UTC time `draft wholesale` stamps when it lays a baseline); a
baseline with no stamp was laid before stamps existed and counts as earliest; a place with no baseline yet is later
than every place with one. Ties go by place id. A variant (`<id>@<variant>`) never counts.

Once both have baselines, the later one fails when it takes the same part of the source the same way: its
`fit.pivot` within SAME_PIVOT units of the earlier one's AND its `fit.rot_deg` within SAME_TURN degrees.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

FIELDS = ("takes", "turn_and_approach", "landmark", "prunes", "adds", "dressing_and_people")
MIN_WORDS = 4
SAME_PIVOT = 1500.0     # units (about 21 m) on the source: the same centre
SAME_TURN = 30.0        # degrees


def _places_dir(places: Path | None) -> Path:
    if places is not None:
        return Path(places)
    from tools.places.draft import io
    return io.PLACES


def _read(pdir: Path) -> dict:
    try:
        return json.loads((pdir / "place.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _order(pid: str, place: dict) -> tuple:
    w = place.get("wholesale")
    if not w:
        return (2, "", pid)                      # no baseline yet: later than any laid one
    return (0 if not w.get("laid") else 1, str(w.get("laid") or ""), pid)


def sharing(place_id: str, places: Path | None = None) -> list[str]:
    """The other drafted places (each with a baseline) on this place's source, variants left out."""
    root = _places_dir(places)
    me = _read(root / place_id)
    src = me.get("source_id")
    if not src:
        return []
    out = []
    for d in sorted(root.iterdir()) if root.exists() else []:
        if d.name == place_id or "@" in d.name or not d.is_dir():
            continue
        p = _read(d)
        if p.get("source_id") == src and p.get("wholesale"):
            out.append(d.name)
    return out


def owed(place_id: str, places: Path | None = None) -> list[str]:
    """The earlier places on this place's source: one `differs` entry is owed for each."""
    root = _places_dir(places)
    mine = _order(place_id, _read(root / place_id))
    return [o for o in sharing(place_id, root) if _order(o, _read(root / o)) < mine]


def _sentence(v) -> bool:
    return isinstance(v, str) and len(v.split()) >= MIN_WORDS


def faults(place_id: str, places: Path | None = None, laying: bool = False) -> list[str]:
    """What this place owes and has not done: a missing or thin `differs` entry for each earlier place on its source,
    and, once both are laid, taking the same part of the source at the same turn. The checks ask it of a place with a
    baseline; `laying` (draft wholesale) asks it before the baseline is laid."""
    root = _places_dir(places)
    me = _read(root / place_id)
    if not laying and not me.get("wholesale"):
        return []          # a draft of the earlier stages owes it when its baseline is laid
    plan = ((me.get("draft") or {}).get("plan") or {})
    rows = {str(r.get("place")): r for r in plan.get("differs") or [] if isinstance(r, dict)}
    bad = []
    for o in owed(place_id, root):
        other = _read(root / o)
        theirs = {str(v).strip().lower() for r in (((other.get("draft") or {}).get("plan") or {}).get("differs") or [])
                  if isinstance(r, dict) for v in r.values()}
        theirs |= {str(v).strip().lower() for k in ("source",) for v in [((other.get("draft") or {}).get("plan") or {}).get(k)] if v}
        r = rows.get(o)
        if r is None:
            bad.append(f"differs: {o} was laid first from the same source ({me.get('source_id')}): write draft.plan.differs "
                       f"{{place: {o}, {', '.join(FIELDS)}}} before laying this baseline; see it with `look {o} at <middle> "
                       f"--top` and eye-level views, and the source with `look --source {me.get('source_id')} overview`")
            continue
        for f in FIELDS:
            v = r.get(f)
            if not _sentence(v):
                bad.append(f"differs[{o}].{f}: a sentence of at least {MIN_WORDS} words is owed")
            elif v.strip().lower() in theirs:
                bad.append(f"differs[{o}].{f}: copied from {o}'s plan: say what THIS place does")
        if me.get("wholesale") and other.get("wholesale"):
            a, b = me.get("fit") or {}, other.get("fit") or {}
            if a.get("pivot") and b.get("pivot"):
                d = math.dist(a["pivot"][:2], b["pivot"][:2])
                t = abs((float(a.get("rot_deg", 0)) - float(b.get("rot_deg", 0)) + 180) % 360 - 180)
                if d < SAME_PIVOT and t < SAME_TURN:
                    bad.append(f"differs[{o}]: the same part of the source the same way: centres {d:.0f} units apart "
                               f"(under {SAME_PIVOT:.0f}) and turns {t:.0f} degrees apart (under {SAME_TURN:.0f}): take "
                               f"another part or turn, as the plan says")
    return bad
