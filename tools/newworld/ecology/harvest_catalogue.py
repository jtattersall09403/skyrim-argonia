"""The harvestable catalogue (editor ids and names of the harvestable bases and ingredients of the plugins we hold),
read from the game files on a machine that has them: `python -m tools.newworld.ecology.harvest catalogue`. The stage never
reads it; harvest.py reads its output, newworld/sources/ecology/harvest_bases.json."""
from __future__ import annotations

import struct

from tools.newworld.ecology.harvest import CATALOGUE_PLUGINS, EXTRA_BASES


def catalogue() -> dict:
    """Every FLOR and TREE of the plugins that yields an ingredient (PFIG), the Nirnroot activators, and every INGR with
    its effects: editor ids and names only, to bind kinds to records and to check the binding."""
    from tools.argonia_world.esm import Plugin
    from tools.newworld.ecology.census import plugin_path
    plugs = {n: Plugin.read(plugin_path(n), {"FLOR", "TREE", "ACTI", "INGR", "MGEF"}) for n in CATALOGUE_PLUGINS}
    edid = {r.key: r.edid for p in plugs.values() for r in p.records() if r.edid}
    names = {r.key: r.name for p in plugs.values() for r in p.records("INGR")}
    bases, ingredients = [], {}
    for n, p in plugs.items():
        for r in p.records("INGR"):
            if r.own and r.edid:
                ingredients[f"{n}:{r.edid}"] = {"name": r.name, "effects": [edid.get(p.form_key(struct.unpack("<I", d)[0]), "?") for d in r.all("EFID")]}
        for r in p.records():
            if not r.own or not r.edid or r.sig not in ("FLOR", "TREE", "ACTI"):
                continue
            ref = f"{n}:{r.edid}"
            ing = r.ref("PFIG") if r.sig != "ACTI" else None
            if r.sig == "ACTI" and ref not in EXTRA_BASES:
                continue
            if r.sig != "ACTI" and not ing:
                continue
            model = (r.zstr("MODL") or "").replace("\\", "/").split("/")[-1].lower()
            bases.append({"ref": ref, "sig": r.sig, "name": r.name, "model": model,
                          "yields": edid.get(ing) or None if ing else "Nirnroot", "yields_name": names.get(ing)})
    bases.sort(key=lambda b: b["ref"])
    return {"schema": 1, "about": "editor ids and names of the harvestable bases and ingredients of the plugins we hold (read by tools.newworld.ecology.harvest catalogue)",
            "bases": bases, "ingredients": dict(sorted(ingredients.items()))}
