"""The one classifier of a place's pieces: what a base IS, from its record kind, edid and model path.

Every measuring tool (units, the look tool's probe, draft check's rules, the build's checks in Python) takes its word
lists from here, and `kind_of` is the one answer to "what is this piece". A rule list, first match wins; a piece no
rule matches is the fallback class "thing" with `fallback` set, which `python -m tools.places truth` counts per place
so a new source's pieces cannot be silently misread.

A piece is a dict with at least `kind` (the record kind: building, static, door, light, ...), `edid` and `model`.
"""
from __future__ import annotations

import re

# ---- the word lists (each named for what it means; a tool needing a different meaning gets a different name) ----
BODY_WORDS = ("house", "hut", "shack", "tent", "hall", "home", "cabin", "shop", "stall", "tower", "yurt", "longhouse", "inn")
DECK_WORDS = ("platform", "deck", "floor", "dock", "pier", "boardwalk", "scaffold")
# a unit of its own that joins others (units): what a builder would call a walkway, bridge or dock
SPAN_UNIT_WORDS = ("walkway", "bridge", "gangway", "plank", "boardwalk", "pier", "dock", "platform")
# a walked span whose two ends must each rest on something (probe's unsupported-end rule)
WALKED_SPAN_WORDS = ("bridge", "walkway", "dock", "boardwalk", "pier", "plank", "gangway", "stair", "ramp", "deck")
STEPS_RE = re.compile(r"stair|steps|ramp|ladder")
RAIL_WORDS = ("rail", "fence", "wall", "balust", "banister")
POST_WORDS = ("post", "pillar", "stilt", "pole", "pile", "column", "support")
NOT_POST_WORDS = ("woodpile", "firewood", "pile01", "rockpile", "bonepile", "lamppost", "signpost")
HANG_WORDS = ("lantern", "sconce", "rope", "chain", "hang", "banner", "sign", "lamp", "bell", "cage", "net", "candle")
WALL_WORDS = HANG_WORDS + ("window",)
HULL_WORDS = ("/ships/", "ship", "boat", "barge", "hull")
PART_WORDS = ("door", "window", "floor")
MOUND_WORDS = ("mound", "mudpile", "dirtpile", "/landscape/", "root")
TREE_WORDS = ("tree", "hist", "trunk", "/trees/")
ROCK_WORDS = ("rock", "cliff", "boulder", "/rocks/")
FURNITURE_WORDS = ("bed", "chair", "bench", "table", "barrel", "crate", "rack", "shelf", "chest", "woodpile", "firewood", "cart")

GROUND_KINDS = {"tree", "rock", "plant", "groundcover", "flora", "grass", "landscape", "water"}
PLANT_KINDS = {"plant", "groundcover", "flora", "grass"}
LOOSE_KINDS = {"light", "marker", "sound", "actor"}
NO_SOLID_KINDS = {"light", "marker", "sound", "actor", "groundcover", "plant"}
STRUCTURAL_KINDS = {"building", "static", "furniture", "door", "container", "activator"}

CLASSES = ("building body", "deck", "post", "steps", "door", "hanging fixture", "light", "effect", "marker", "plant",
           "tree", "rock", "ground piece", "water", "boat", "furniture", "span", "railing", "thing")


def words(p: dict) -> str:
    return f"{p.get('edid') or ''} {p.get('model') or ''}".lower().replace("\\", "/")


def has(p: dict, ws) -> bool:
    w = words(p)
    return any(x in w for x in ws)


def effect(p: dict) -> bool:
    """A game effect (mist, fire, spray): no body; nothing holds it up and it holds nothing up."""
    m, e = str(p.get("model") or "").lower().replace("\\", "/"), str(p.get("edid") or "").lower()
    return m.startswith(("effects/", "fx")) or "/fx" in m or e.startswith("fx")


def post(p: dict) -> bool:
    return has(p, POST_WORDS) and not has(p, NOT_POST_WORDS)


def classify(p: dict) -> tuple[str, bool]:
    """(class, fallback): the piece's class from CLASSES, and whether no rule matched (the fallback "thing")."""
    k = p.get("kind")
    w = words(p)
    if effect(p):
        return "effect", False
    if k == "light":
        return ("hanging fixture" if has(p, HANG_WORDS) else "light"), False
    if k in ("marker", "sound", "actor") or w.strip().startswith("markers/") or "/markers/" in w:
        return "marker", False
    if k == "door":
        return "door", False
    if k == "water":
        return "water", False
    if k == "tree" or (k not in STRUCTURAL_KINDS and has(p, TREE_WORDS)):
        return "tree", False
    if k == "rock":
        return "rock", False
    if k in PLANT_KINDS:
        return "plant", False
    if k == "landscape" or has(p, MOUND_WORDS):
        return "ground piece", False
    if k in ("building", "static") and has(p, ROCK_WORDS) and not has(p, BODY_WORDS + DECK_WORDS):
        return "rock", False
    if k in ("building", "static") and has(p, HULL_WORDS):
        return "boat", False
    if STEPS_RE.search(w) and k in ("building", "static"):
        return "steps", False
    if has(p, HANG_WORDS):
        return "hanging fixture", False
    if k in ("furniture", "container") or has(p, FURNITURE_WORDS):
        return "furniture", False
    if k == "building" and has(p, BODY_WORDS) and not has(p, DECK_WORDS + ("plank", "walkway", "bridge")):
        return "building body", False
    if k in ("building", "static") and has(p, SPAN_UNIT_WORDS + ("walkway", "bridge")):
        return ("deck" if has(p, DECK_WORDS) and not has(p, ("walkway", "bridge", "gangway", "plank")) else "span"), False
    if k in ("building", "static") and has(p, DECK_WORDS):
        return "deck", False
    if post(p):
        return "post", False
    if has(p, RAIL_WORDS):
        return "railing", False
    return "thing", True


def kind_of(p: dict) -> str:
    return classify(p)[0]


# classes that never stand as a building, carry a deck or need feet: what units must keep out of its structures
NOT_STRUCTURE = {"light", "effect", "marker", "hanging fixture", "ground piece", "plant", "tree", "rock", "water"}
