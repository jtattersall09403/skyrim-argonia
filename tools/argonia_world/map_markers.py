"""1.12: the map markers of the province. Every place with a placed position gets one persistent map marker reference
(Skyrim's MapMarker static, an XMRK block: the place's name, a marker type for its kind, no flags), riding in the
WRLD override's persistent cell (regions/api.py). With neither Visible nor CanTravelTo it is hidden until Skyrim's
own discovery fires as the player reaches it; the engine sets the flags then, and our chart (views.cpp) reads the
player's marker list. Fast travel stays off engine-side (Game.EnableFastTravel(false))."""
from __future__ import annotations

import re

from tools.argonia_world import skyrim_units as su

# (classification_class, classification_family) -> a Mutagen MapMarker.Types name; a class alone is the fallback.
# No Nordic or civil-war icon is used (0006): the chart draws our own glyph for each type.
TYPE_BY_FAMILY = {
    ("settlement", "major-city"): "City", ("settlement", "mixed-settlement"): "Town",
    ("sacred", "hist"): "Grove", ("lair", "hazard-ground"): "Clearing", ("lair", "open-water"): "Landmark",
    ("ruin", "imperial-ruin"): "Fort", ("lone", "lone-dwelling"): "Shack", ("transit", "landing"): "Docks",
    ("transit", "road"): "Pass", ("transit", "elevated"): "Pass", ("works", "extraction"): "Mine",
    ("works", "aquaculture"): "Farm", ("civic", "festivity"): "Clearing",
}
TYPE_BY_CLASS = {"settlement": "Settlement", "lair": "Cave", "camp": "Camp", "ruin": "Landmark", "sacred": "Shrine",
                 "lone": "Landmark", "transit": "Landmark", "works": "Landmark", "martial": "Fort", "civic": "Landmark"}
DEFAULT_TYPE = "Landmark"


def marker_type(cls: str | None, family: str | None) -> str:
    return TYPE_BY_FAMILY.get((cls, family)) or TYPE_BY_CLASS.get(cls or "", DEFAULT_TYPE)


def _camel(s: str) -> str:
    return "".join(w.capitalize() for w in re.split(r"[^a-z0-9]+", s) if w)


def marker_edid(place_id: str, shared: bool = False) -> str:
    """`place.imperial-fringe.claywater-station` -> `ARG_MapMarker_ClaywaterStation`; a name two regions share
    (``shared``) carries its region: `ARG_MapMarker_ImperialFringe_ClaywaterStation`."""
    _, region, name = place_id.split(".", 2)
    return "ARG_MapMarker_" + (f"{_camel(region)}_" if shared else "") + _camel(name)


def placed(world) -> list:
    return [p for p in world.rows("place", order="id") if p.position_m_x is not None and p.position_m_y is not None]


def refs(alloc, world, z_at) -> list[dict]:
    """One persistent REFR per placed place, at its position on the final ground."""
    from tools.argonia_world.intermediate import _pos_exterior, _rot
    from collections import Counter
    out, seen = [], {}
    ps = placed(world)
    names = Counter(p.id.rsplit(".", 1)[1] for p in ps)
    for p in ps:
        e = marker_edid(p.id, names[p.id.rsplit(".", 1)[1]] > 1)
        if e in seen:
            raise ValueError(f"{p.id}: map marker {e} already taken by {seen[e]}")
        seen[e] = p.id
        x, y = p.position_m_x, p.position_m_y
        out.append({"formKey": alloc.form_key(e, "REFR", p.id), "edid": e, "base": su.MAP_MARKER,
                    "pos": _pos_exterior([x, y, z_at(x, y)]), "rot": _rot(0.0), "persistent": True,
                    "mapMarker": {"name": p.name, "type": marker_type(p.classification_class, p.classification_family),
                                  "flags": []}})
    return out
