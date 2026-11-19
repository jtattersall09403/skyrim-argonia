"""`draft structures <place_id>`: the source is a pool of pieces and a layout to draw from; each major structure of it
is kept only where the place record supports it or it is an ordinary part of such a place.

A major structure is a class of source pieces named by their record (`CLASSES`: terraces, walls, keeps and towers,
mines, harbours, temples). Its verdict:
- kept when the record (`interiors.record_text`: the place's row, its promises and the stories' needs) names one of
  the class's words;
- kept when it is an ordinary part of the place (`ordinary`): a harbour of a place on water;
- a door is never a structure's piece: the room behind it is kept or dropped with its own verdict;
- otherwise dropped, with the reason.
Read-only: it lists each structure kept or dropped and the source pieces of each; the place's `draft.drop` carries a
verdict into the draft.
"""
from __future__ import annotations

import re
import sys

CLASSES: list[tuple[str, re.Pattern, tuple[str, ...]]] = [
    ("harbour", re.compile(r"dock|pier|jetty|wharf|harbou?r|mooring", re.I),
     ("harbour", "harbor", "dock", "pier", "jetty", "wharf", "quay", "port")),
    ("mine", re.compile(r"mine(?!ral)", re.I), ("mine", "mining", "ore ", "quarry")),
    ("temple", re.compile(r"temple|chapel|cathedral", re.I), ("temple", "chapel", "cathedral", "priest")),
    ("terrace", re.compile(r"plaza|ledge|terrace|foundation", re.I),
     ("terrace", "plaza", "raised", "upper town", "platform")),
    ("walls", re.compile(r"wall(?!hang)|gate(?!house)|rampart|palisade|stockade", re.I),
     ("walls", "walled", "town wall", "city wall", "outer wall", "outward wall", "rampart", "palisade", "stockade",
      "gates", "gatehouse")),
    ("keep", re.compile(r"fort(?!une)|castle|tower(?!post)|battlement|citadel", re.I),
     ("a keep", "the keep", "fort", "castle", "tower", "garrison", "legion", "battlement")),
]
HOUSE = re.compile(r"house|hut|home|dwelling", re.I)
FORTIFIED = ("walls", "keep")   # a palisade's and a tower's pieces are often clutter-kind statics (Stockade*)
# the words a record rules a structure out with ("no stone and no outward wall": the marsh is the wall)
NEGATED = {"walls": ("wall", "walls", "palisade", "stockade", "rampart"), "keep": ("keep", "fort", "castle", "tower"),
           "mine": ("mine",), "temple": ("temple",), "harbour": ("harbour", "harbor", "dock", "pier"),
           "terrace": ("terrace", "plaza")}
WATER_WORDS = ("river", "lake", "coast", "shore", "sea", "harbour", "harbor", "landing", "fish", "boat", "water")


def classify(base: dict) -> str | None:
    """The major structure a source base belongs to, by its record's editor id and model; None for any other."""
    if base.get("kind") not in ("building", "static", "rock", "clutter", None) or base.get("type") == "Door":
        return None
    if HOUSE.search(str(base.get("edid") or "")):
        return None     # a house is a home, whatever its mesh is called (an Argonian tower house: exttower.nif)
    name = f"{base.get('edid') or ''} {str(base.get('model') or '').rsplit('/', 1)[-1]}"
    for cls, pat, _ in CLASSES:
        if pat.search(name) and (base.get("kind") != "clutter" or cls in FORTIFIED):
            return cls
    return None


def ordinary(cls: str, text: str) -> bool:
    """A structure that is an ordinary part of the place the record describes."""
    return cls == "harbour" and any(w in text for w in WATER_WORDS)


def supported(cls: str, text: str) -> str | None:
    """The record's word that supports the structure, or None."""
    words = next(w for c, _, w in CLASSES if c == cls)
    return next((w for w in words if re.search(rf"\b{re.escape(w.strip())}\b", text)), None)


def ruled_out(cls: str, text: str) -> str | None:
    """The record's words that rule the structure out ("no outward wall", "without a keep"), or None."""
    alt = "|".join(re.escape(w) for w in NEGATED.get(cls, ()))
    m = re.search(rf"\b(?:no|without|never)\s+(?:[a-z-]+\s+){{0,2}}?(?:{alt})\b", text, re.I) if alt else None
    return m.group(0) if m else None


def judge(refs: list[dict], bases: dict, text: str) -> dict[str, dict]:
    """{class: {"kept": bool, "why": str, "refs": [source ids]}} for each major structure among `refs` (the source's
    exterior refs)."""
    found: dict[str, list[str]] = {}
    for r in refs:
        if r.get("door"):
            continue
        cls = classify(bases.get(r.get("base")) or {})
        if cls:
            found.setdefault(cls, []).append(r["id"])
    out = {}
    for cls, ids in sorted(found.items()):
        w, no = supported(cls, text), ruled_out(cls, text)
        if no:
            out[cls] = {"kept": False, "why": f"the record rules it out ('{no}')", "refs": sorted(ids)}
        elif w:
            out[cls] = {"kept": True, "why": f"the record names it ('{w}')", "refs": sorted(ids)}
        elif ordinary(cls, text):
            out[cls] = {"kept": True, "why": "an ordinary part of a place on the water", "refs": sorted(ids)}
        else:
            out[cls] = {"kept": False, "why": f"the record has no use for the source's {cls}", "refs": sorted(ids)}
    return out


def for_place(place_id: str) -> dict[str, dict]:
    from tools.places.draft import interiors, stages
    from tools.places.draft.run import place_record
    st = stages.Standing(place_id)
    return judge(st.src_ext, st.bases, record_words(place_id))


def record_words(place_id: str) -> str:
    """The record's own words, lower-case: its row, its promises, its notes (the look, the summary, the source note)
    and what the stories ask of the place; never the source note (it describes the source). Never the judgements written against the needs (a need's `why`, `sight`):
    those are our words about the draft, not the record's."""
    import json
    from tools.newworld.place_card import rows
    from tools.places.draft.run import place_record
    rec, gives = place_record(place_id)
    # the source note says what the source is, not what the place is: it is the source choice's, never a support
    notes = [n for n in rows("place_note") if n.get("place_id") == place_id and n.get("aspect_id") != "source"]
    try:
        from tools.places import needs as needs_mod
        asks = [n.get("thing") for n in needs_mod.read(place_id).get("needs") or []]
    except (FileNotFoundError, OSError, ValueError):
        asks = []
    return json.dumps([rec, gives, notes, asks], default=str).lower()


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: python -m tools.places draft structures <place_id>")
        return 2
    for cls, v in for_place(argv[0]).items():
        print(f"{argv[0]}: {cls}: {'kept' if v['kept'] else 'dropped'}: {v['why']} ({len(v['refs'])} pieces)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
