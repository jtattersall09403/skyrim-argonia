"""The `records:` reach lines of the look and creature journeys (tools/pass_ledger.py): each journey's reach names the
records it judges and the cells it stands in, not the whole ESM, so a bridge or a road re-route elsewhere does not rerun
a passed journey. `python3 -m tools.journeys refresh` writes them last (`apply`), from the journey's own steps."""
from __future__ import annotations

import json
import re

from tools import pass_ledger
from tools.argonia_world import skyrim_units as su
from tools.journeys import JOURNEYS

SKY = ("Weathers", "ImageSpaces", "Climates", "Regions", "wrld")
# journey id -> (record folders / specs, persistent-ref editor id prefixes, cell ring, base paths when it has no reach)
# Water levels live only in the built ESM, so water-types and river-steps keep `esm`; navmesh-paths keeps it (the
# navmesh is in every cell).
TABLE = {
    "sky-ab": (SKY, (), 1, ("tests/scenes/world-panel.txt", "data/dependencies.json")),
    "world-panel": (SKY, (), 1, ("tests/scenes/world-panel.txt", "data/dependencies.json")),
    "road-look": ((), (), 1, ("tools/argonia_world/regions/**", "tools/argonia_world/routes/**", "data/dependencies.json")),
    "bridge-look": ((), ("ARG_Ref_Bridge",), 1, None),
    "junction-dry": ((), ("ARG_Ref_Bridge",), 1, None),
    "ground-materials": (("LandscapeTextures", "TextureSets"), (), 1, None),
    "rain-look": (("Weathers", "ImageSpaces", "Regions"), (), 1, None),
    "rock-booth": (("Statics",), (), 1, ("data/dependencies.json",)),
    "tree-seat": (("Statics",), (), 1, ("data/dependencies.json",)),
    "creature-spots": (("Npcs", "LeveledNpcs", "EncounterZones"), (), 1, ("data/dependencies.json",)),
    "creatures-kinds": (("Npcs", "LeveledNpcs", "EncounterZones"), (), 1, None),
    "claywater-look": (("Statics",), ("ARG_Ref_Claywater",), 1, None),
    "claywater-walk": (("Statics",), ("ARG_Ref_Claywater",), 1, None),
}


def _strings(node):
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for v in node.values():
            yield from _strings(v)
    elif isinstance(node, list):
        for v in node:
            yield from _strings(v)


def stop_cells(j: dict, repo: str = str(pass_ledger.REPO)) -> tuple[set, set]:
    """(the cells a journey stands in, the persistent refs it moves to): from its `cow` lines, its setpos x/y pairs,
    its `moveto` markers and the bounds its steps expect of the player's position."""
    cells, refs = set(), set()
    named = pass_ledger.wrld_parts(repo)[1]
    for st in j.get("steps", []):
        xs, ys = [], []
        for s in _strings(st.get("do")):
            if (m := re.match(r"cow ARG_Province (-?\d+) (-?\d+)", s)):
                cells.add((int(m[1]), int(m[2])))
            if (m := re.match(r"player\.setpos ([xy]) (-?\d+(?:\.\d+)?)", s)):
                (xs if m[1] == "x" else ys).append(float(m[2]))
            if (m := re.match(r"player\.moveto (\w+)", s)):
                refs.add(m[1])
                if (p := re.search(r"Position: (-?[\d.]+), (-?[\d.]+)", named.get(m[1], ""))):
                    cells.add(su.cell_of(float(p[1]), float(p[2])))
        cells |= {su.cell_of(x, y) for x in xs for y in ys[:1]} if xs and ys else set()
        bx, by = {}, {}
        for e in st.get("expect") or []:
            if isinstance(e, dict) and e.get("path") in ("pos.x", "pos.y"):
                (bx if e["path"] == "pos.x" else by).setdefault("v", []).extend(
                    v for k, v in e.items() if k in ("gt", "lt"))
        if bx.get("v") and by.get("v"):
            cells.add(su.cell_of(sum(bx["v"]) / len(bx["v"]), sum(by["v"]) / len(by["v"])))
    return cells, {r for r in refs if r in named}


def reach_for(jid: str, j: dict, repo: str = str(pass_ledger.REPO)) -> list[str]:
    folders, prefixes, ring, base = TABLE[jid]
    old = [p for p in (j.get("reach") or []) if p != "esm" and not p.startswith(pass_ledger.RECORDS)]
    paths = old if "reach" in j else list(base or [])
    cells, refs = stop_cells(j, repo)
    named = pass_ledger.wrld_parts(repo)[1]
    refs |= {n for n in named if any(n.startswith(pre) for pre in prefixes)}
    specs = list(folders) + [f"ref {r}" for r in sorted(refs)] + [f"cell {x},{y} r{ring}" for x, y in sorted(cells)]
    return paths + [pass_ledger.RECORDS + " " + s for s in specs]


def apply(only: set[str] | None = None) -> list[str]:
    """Rewrite each tabled journey's reach statement; the ids written."""
    import yaml
    done = []
    for jid in TABLE:
        f = JOURNEYS / f"{jid}.yaml"
        if (only is not None and jid not in only) or not f.is_file():
            continue
        text = f.read_text()
        j = yaml.safe_load(text)
        new = reach_for(jid, j)
        flow = json.dumps(new)
        if (m := re.search(r'^(reach: )\[[^\n]*?\](?=\s*(?:#|$))', text, re.M)):
            out = text[:m.start()] + m[1] + flow + text[m.end():]
        elif (m := re.search(r'^( "reach": )\[[^\]]*\]', text, re.M)):
            out = text[:m.start()] + m[1] + flow + text[m.end():]
        elif (m := re.search(r'^id: .*\n', text, re.M)):
            out = text[:m.end()] + f"reach: {flow}   # the pass ledger's inputs (tools/pass_ledger.py)\n" + text[m.end():]
        else:
            raise SystemExit(f"{jid}: no id line to put reach after")
        if out != text:
            f.write_text(out)
        done.append(jid)
    return done
