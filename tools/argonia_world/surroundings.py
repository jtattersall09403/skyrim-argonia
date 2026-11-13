"""The surroundings sheet: what the built world holds round a person or a spot, in plain words a writer and a reader
can use (owner-bar "Truth and lore"). Each fact is marked fixed (it stands there) or moving (it goes with someone's
routine), so a line places a thing only by fixed things and describes only what is there.

The raw facts come from the load order with our built plugin last (`plugin.sh inspect surroundings:<spot>`,
tools/ArgoniaPlugin/Surroundings.cs: the cell, the surfaces under the spot, the land and water, every placed thing and
person within the radius with its base's model, and the map markers near); this module only puts them into words.
What a placed thing reads as comes from KINDS, a short table of model path and editor id fragments; a model the table
does not know is listed as unknown with its file name, never guessed.

    python3 -m tools.argonia_world.surroundings <ref form key | person or thing id> [--radius N] [--built DIR|ESP]
        a person or thing id is looked up in the quest forms read back from the built plugin (DIR, default
        out/questform-read) or among BM&V's talkers; --built ESP reads that plugin in place of out/Argonia.esp
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

from tools.argonia_world import db

READ_BACK = db.REPO / "out/questform-read"
CACHE = db.REPO / "out/surroundings"
RADIUS = 3000.0
FORM_KEY = re.compile(r"^[0-9A-Fa-f]{6}:.+\.(esm|esp|esl)$")

# What a placed thing reads as: (kind, plural, pattern over the model path and editor id in lower case). First match
# wins, so the specific comes before the general. "skip" is never told (markers, lights, sounds, effects).
KINDS = [
    ("skip", "", r"marker|fxlight|lightbeam|fogvolume|^fx(?!fire)|collision|navcut|portal|window|^light|ambient"),
    ("big ship", "big ships", r"shiplarge|imperialship|shipimperial|caravel|carrack|galleon|dunship"),
    ("wrecked boat", "wrecked boats", r"wreck|sunken"),
    ("ship's stairs", "ship's stairs", r"shipstair"),
    ("longboat", "longboats", r"shiplongboat"),
    ("rowing boat", "rowing boats", r"rowboat"),
    ("boat", "boats", r"(?<![a-z])boat|canoe|raft"),
    ("bridge", "bridges", r"bridge"),
    ("paved road", "paved roads", r"road|cobble|paving|pathstone"),
    ("plank walkway", "plank walkways", r"walkway|boardwalk|plank|catwalk"),
    ("pier", "piers", r"pier|jetty"),
    ("dock", "docks", r"dock"),
    ("lighthouse", "lighthouses", r"lighthouse(?!fire)"),
    ("wooden scaffold", "wooden scaffolds", r"scaf"),
    ("wooden posts", "wooden posts", r"towerpost|fencepost|post\d|posts"),
    ("lamp post", "lamp posts", r"lamppost|lightpost|slightpost"),
    ("stone tower", "stone towers", r"tower"),
    ("stone keep", "stone keeps", r"cyrkeep|keep\d|fort"),
    ("Hist tree", "Hist trees", r"(?<![a-z])hist(?!le)"),
    ("giant tree", "giant trees", r"giantredwood|treegiant|giant.?tree|bigtree"),
    ("tree root", "tree roots", r"root"),
    ("dead tree", "dead trees", r"deadtree|treepineforestdead|vurt_dead"),
    ("stepped ruin", "stepped ruins", r"xanmeer|ziggurat"),
    ("Ayleid ruin", "Ayleid ruins", r"ayleid|arcolumn"),
    ("Dwemer ruin", "Dwemer ruins", r"dwemer|dweruin|dwespecial"),
    ("rope", "ropes", r"rope"),
    ("ruin", "ruins", r"ruins?"),
    ("burnt-out house", "burnt-out houses", r"destroyed|burnt|burned"),
    ("stilt house", "stilt houses", r"stilthouse|stilt"),
    ("hut", "huts", r"bamboohut|hidehut|alhut|hut(?!ch)"),
    ("shack", "shacks", r"shack|shed"),
    ("tent", "tents", r"tent(?!acle)"),
    ("inn", "inns", r"tavern"),
    ("stone house", "stone houses", r"manor|castlehouse|stonehouse"),
    ("house", "houses", r"house|haus|longhs|farmhouse"),
    ("stockade of stakes", "stockades of stakes", r"stockade|palisade|pike\d|spikes"),
    ("wall", "walls", r"wall|fence"),
    ("floor", "floors", r"floor|platform"),
    ("torture pole", "torture poles", r"torturepole|pillory|gibbet|cage"),
    ("human remains", "human remains", r"bloody|skull|skeleton|corpse|bones"),
    ("shrine", "shrines", r"shrine|altar"),
    ("statue", "statues", r"statue|totem|idol|obelisk|standingstone|monument|figurine|carving"),
    ("well", "wells", r"^well|well\d"),
    ("cart", "carts", r"cart\b|cart\d|wagon"),
    ("fire burning", "fires burning", r"fxfire|firelog|fire\d|fireplace|campfirelit|burning"),
    ("campfire (unlit unless a fire burns)", "campfires (unlit unless a fire burns)",
     r"campfire|firepit|firespit|cookfire"),
    ("lantern or candle", "lanterns and candles", r"lantern|candle|torch|brazier|sconce|lamp"),
    ("cooking pot", "cooking pots", r"cookpot|cauldron|spit"),
    ("bedroll", "bedrolls", r"bedroll"),
    ("bed", "beds", r"bed(?!rock)"),
    ("table", "tables", r"table"),
    ("chair or bench", "chairs and benches", r"chair|bench|stool|throne"),
    ("chest", "chests", r"chest|strongbox|lockbox"),
    ("barrel", "barrels", r"barrel"),
    ("crate", "crates", r"crate"),
    ("sack", "sacks", r"sack|bag"),
    ("basket", "baskets", r"basket"),
    ("urn or jar", "urns and jars", r"urn|jar|pot\b|pot\d|vase"),
    ("shelf", "shelves", r"shelf|shelves|cupboard|wardrobe|dresser"),
    ("rug", "rugs", r"rug"),
    ("anvil or workbench", "anvils and workbenches", r"anvil|forge|smelter|grindstone|workbench|tanningrack|"
                                                    r"alchemylab|enchanter"),
    ("giant mushroom", "giant mushrooms", r"tel_ext_cap|giantmush|tallmush"),
    ("mushroom", "mushrooms", r"mushroom|shroom|fungus|mush"),
    ("banner", "banners", r"banner|flag"),
    ("rock", "rocks", r"rock|boulder|stone|cliff|mountain|lava"),
    ("tree", "trees", r"tree|tropical|palm|mangrove|cypress|willow|oak|pine"),
    ("plant", "plants", r"plant|fern|reed|bush|shrub|grass|flora|vine|lily|lilli|kelp|braken|bracken|weed|swamp"),
    ("pillar", "pillars", r"pillar|column"),
    ("stairs", "stairs", r"stair|steps"),
    ("door", "doors", r"door"),
]
BUILDING = {"house", "stone house", "shack", "hut", "stilt house", "inn", "wall", "floor", "tent", "stairs", "pillar"}
KINDS_RX = [(k, pl, re.compile(p)) for k, pl, p in KINDS]
LOOSE_SIGS = {"Weapon", "MiscItem", "Book", "Ingredient", "Ingestible", "Armor", "Key", "Ammunition", "Scroll",
              "SoulGem"}
PLAYABLE = {"Argonian", "Breton", "DarkElf", "HighElf", "Imperial", "Khajiit", "Nord", "Orc", "Redguard", "WoodElf"}
COMPASS = ["east", "north-east", "north", "north-west", "west", "south-west", "south", "south-east"]
NOT_DONE = [
    "No tides: the water stands at one height all day and all year.",
    "No seasons: the plants, the light and the weather do not change with the time of year.",
    "No weather a quest can call: rain and mist come and go by the region's own chance.",
    "No crowds, marches or work going on unless a person here is shown doing it.",
]


def kind_of(text: str) -> tuple[str, str] | None:
    """(kind, plural) for a model path and editor id, or None when the table does not know it."""
    t = text.lower().replace("\\", "/")
    t = " ".join(w.rsplit("/", 1)[-1].removesuffix(".nif") for w in t.split())  # the file's own name and the editor id
    for k, pl, rx in KINDS_RX:
        if rx.search(t):
            return k, pl
    return None


def compass(dx: float, dy: float) -> str:
    return COMPASS[round(math.degrees(math.atan2(dy, dx)) % 360 / 45) % 8]


# Words for how far (Skyrim units; 70 a metre), never a count. A quest's sheet reads close detail; a talker's sheet
# reads the talk's own bands (talk_route.BANDS: "just" under 60 m, "a short way" under 200 m, "a fair way" under
# 600 m, "a long walk" under 2 km), so a line's distance word and the sheet's are the same words.
NEAR_BANDS = ((150, "right here"), (500, "a few steps"), (1200, "close by"), (3000, "a short walk"),
              (6000, "a fair way"))
TALK_BANDS = ((150, "right here"), (1200, "a few steps"), (4200, "just"), (14000, "a short way"),
              (42000, "a fair way"), (140000, "a long walk"))
TALK_RADIUS = 14000.0     # a talker's sheet reaches every thing a line may call "just" or "a short way"
_bands = NEAR_BANDS


def how_far(d: float) -> str:
    """A word for how far, never a count."""
    for lim, w in _bands:
        if d < lim:
            return w
    return "far"


def where(dx: float, dy: float, dz: float = 0.0) -> str:
    d = math.hypot(dx, dy)
    w = how_far(d) if d < 150 else f"{compass(dx, dy)}, {how_far(d)}"
    if dz > 250:
        w += ", above"
    elif dz < -250:
        w += ", below"
    return w


def count(n: int) -> str:
    return ["no", "one", "two", "three", "four", "five", "six"][n] if n < 7 else "many"


def race_word(edid: str | None) -> str:
    r = (edid or "").replace("Race", "").replace("Vampire", "")
    return {"DarkElf": "Dunmer", "HighElf": "Altmer", "WoodElf": "Bosmer"}.get(r, r) or "unknown race"


# --- the raw facts ------------------------------------------------------------------------------------------------

def raw(specs: list[str], esp: str | None = None) -> list[dict]:
    """The raw facts for each spot (`<ref>@<r>` or `<cell>@<x>,<y>,<z>@<r>`), cached in out/surroundings by spot and
    plugin; one load of the load order answers every spot not cached."""
    CACHE.mkdir(parents=True, exist_ok=True)
    plugin = Path(esp) if esp else db.REPO / "out/Argonia.esp"
    stamp = f"{plugin.stat().st_mtime_ns}" if plugin.exists() else "none"
    key = lambda s: CACHE / (re.sub(r"[^A-Za-z0-9]+", "_", s) + f".{stamp}.json")  # noqa: E731
    todo = [s for s in specs if not key(s).exists()]
    if todo:
        env = dict(os.environ)
        if esp:
            env["ARGONIA_ESP"] = str(plugin)
        out = subprocess.run([str(db.REPO / "tools/ArgoniaPlugin/plugin.sh"), "inspect", "surroundings:" + ";".join(todo)],
                             capture_output=True, text=True, env=env, cwd=db.REPO)
        got = {}
        for line in out.stdout.splitlines():
            if line.startswith("SURR "):
                d = json.loads(line[5:])
                got[d["spot"]] = d
        for s in todo:
            if s not in got:
                raise SystemExit(f"surroundings: no answer for {s}\n{out.stderr[-2000:]}")
            key(s).write_text(json.dumps(got[s]))
    return [json.loads(key(s).read_text()) for s in specs]


def forms(built: str | Path | None) -> dict[str, tuple[dict, dict]]:
    """Every ref of the read-back forms by id: (ref, its form)."""
    d = Path(built) if built else READ_BACK
    out = {}
    for p in sorted(d.glob("*.json")) if d.is_dir() else []:
        f = json.loads(p.read_text())
        for r in f.get("refs", []):
            out.setdefault(r["id"], (r, f))
    return out


def spot_of(target: str, refs: dict, radius: float = RADIUS) -> str:
    """The spot spec for a ref form key, a form's ref id (a thing in a container or carried: its holder's spot) or a
    BM&V talker's ref."""
    if FORM_KEY.match(target):
        return f"{target}@{radius:g}"
    seen = set()
    while target in refs and target not in seen:
        seen.add(target)
        r = refs[target][0]
        if r.get("at"):
            a = r["at"]
            return f"{a['cell']}@{a['x']:g},{a['y']:g},{a['z']:g}@{radius:g}"
        pl = r["placement"]
        if pl.get("existing"):
            return f"{pl['existing']}@{radius:g}"
        target = pl.get("container") or pl.get("carried_by") or ""
    raise SystemExit(f"surroundings: {target!r} is not a form key, a read-back ref or a held thing's holder")


# --- the words ------------------------------------------------------------------------------------------------------

def moves(p: dict) -> tuple[str, str]:
    """(fixed|moving, how) from a person's packages."""
    pk = p.get("packages") or []
    if not pk:
        return "fixed", "stands where placed (no AI package)"
    kinds = {(x.get("template") or x.get("edid") or "?") for x in pk}
    own = all("NearEditorLocation" in " ".join(x.get("where", [])) or not x.get("where") for x in pk)
    radius = max((int(m.group(1)) for x in pk for w in x.get("where", []) if (m := re.search(r" r(\d+)", w))),
                 default=0)
    timed = any(x.get("hour", -1) >= 0 for x in pk)
    places = sorted({w.split(" r")[0] for x in pk for w in x.get("where", [])
                     if "NearEditorLocation" not in w and "NearSelf" not in w})
    if own and not timed and len(pk) == 1:
        span = how_far(radius) if radius else "a few steps"
        if "Sandbox" in kinds:
            return "moving", f"wanders about this spot (sandbox; strays as far as {span} from it), so not always beside anything here"
        return "fixed", f"keeps to this spot ({', '.join(sorted(kinds))})"
    told = "; ".join(f"{x.get('template') or x.get('edid')}"
                     + (f" from hour {x['hour']}" if x.get("hour", -1) >= 0 else "")
                     + (f" at {', '.join(x['where'])}" if x.get("where") else "") for x in pk)
    return "moving", f"follows a routine across {'several places' if len(places) > 1 else 'the day'}: {told}"


def underfoot(d: dict) -> str:
    """What the spot stands on: the modelled surface just under it (a canopy or a plant never is one), else the land
    against the water's height."""
    z = d["at"][2]
    water, land, best = d.get("water"), d.get("land"), None
    for h in d["surfaces"]:
        if h["kind"] == "land" or not (-100 < z - h["top"] < 120):
            continue
        k = kind_of(f"{h['model']} {h['edid'] or ''}")
        if k and k[0] in ("tree", "plant", "skip", "mushroom"):
            continue
        if best is None or h["top"] > best[0]["top"]:
            best = (h, k)
    if best:
        h, k = best
        what = {"big ship": "the deck of a big ship", "plank walkway": "planks", "pier": "a pier's planks",
                "dock": "a dock", "giant tree": "the roots of a giant tree", "tree root": "tree roots",
                "rock": "rock", "bridge": "a bridge", "floor": "a floor", "paved road": "a paved road"}.get(k[0] if k else "")
        if what is None:
            what = ("the floor or top of " + (f"a {k[0]}" if k else
                    f"a model the kinds table cannot name ({h['model'].rsplit('/', 1)[-1]})"))
        if water is not None and land is not None and land < water - 5:
            what += f", over {'deep' if water - land >= 90 else 'shallow'} water"
        return what
    if d["cell"]["interior"]:
        return "no floor model found under the spot"
    if land is None:
        return "unknown (no land here)"
    if z > max(land, water if water is not None else land) + 60:
        # trees are not read as surfaces: a person held up by the navmesh next to a big tree stands on its roots
        x0, y0 = d["at"][0], d["at"][1]
        big = [t for t in d["things"] if t["sig"] == "Tree" and t["size"] > 1000 and t["d"] < 900]
        if big:
            t = min(big, key=lambda t: t["d"])
            k = kind_of(f"{t.get('model') or ''} {t.get('edid') or ''}")
            return (f"raised above the {'water' if water is not None and land < water else 'ground'} with no "
                    f"model under it: the roots of the {k[0] if k else 'big tree'} {where(t['x'] - x0, t['y'] - y0)}")
    if water is not None and land < water - 5:
        depth = "deep" if water - land >= 90 else "shallow"
        return f"{depth} water" if z < water + 40 else f"no model under the spot, above {depth} water"
    if water is not None and land < water + 40:
        return "bare earth at the water's edge"
    return "bare earth"


def water_round(d: dict) -> list[str]:
    w = d.get("water")
    if d["cell"]["interior"] or w is None:
        return []
    near: dict[str, float] = {}
    deep: dict[str, bool] = {}
    for a, r, land in d.get("ring") or []:
        if land is not None and land < w - 5:
            k = COMPASS[int(a // 45) % 8]
            near[k] = min(near.get(k, 1e9), r)
            deep[k] = deep.get(k, False) or land < w - 90
    if not near:
        return ["No open water within a short walk."]
    by = defaultdict(list)
    for k, r in near.items():
        by[how_far(r)].append(k)
    return [f"Open water ({'deep in places' if any(deep[x] for x in ks) else 'shallow'}) {', '.join(ks)}: {dist}." for dist, ks in sorted(by.items(), key=lambda kv: min(near[x] for x in kv[1]))]


def things_round(d: dict) -> tuple[list[str], list[str], list[str], list[str], bool]:
    """(built things grouped by kind, loose things, doors, unknown models, a fire burns)."""
    x0, y0, z0 = d["at"]
    groups: dict[tuple, list] = defaultdict(list)
    loose, doors, unknown, fire = [], [], defaultdict(int), False
    for t in sorted(d["things"], key=lambda t: t["d"]):
        text = f"{t.get('model') or ''} {t.get('edid') or ''}"
        if t["sig"] == "Door" or t.get("door"):
            to = f"to {t['door']}" if t.get("door") else "(no destination)"
            doors.append(f"a door {to}{', locked (' + t['locked'] + ')' if t.get('locked') else ''}: "
                         f"{where(t['x'] - x0, t['y'] - y0, t['z'] - z0)}")
            continue
        if t["sig"] in LOOSE_SIGS:
            loose.append(f"{t.get('name') or t.get('edid')}: {where(t['x'] - x0, t['y'] - y0, t['z'] - z0)}")
            continue
        k = kind_of(text)
        if k is None:
            if t["sig"] in ("Light", "SoundMarker", "IdleMarker", "TextureSet") or not t.get("model"):
                continue
            unknown[(t.get("model") or "").rsplit("/", 1)[-1]] += 1
            continue
        if k[0] == "skip":
            continue
        fire |= k[0] in ("fire burning",)
        if d["cell"]["interior"] and k[0] in BUILDING:   # indoors, a building's kit pieces are the room itself
            k = (f"room: the walls, floors and roof of a {k[0]}'s inside", f"room: the walls, floors and roof of a "
                 f"{k[0]}'s inside")
        groups[k].append(t)
    told = []
    for (k, pl), ts in sorted(groups.items(), key=lambda kv: kv[1][0]["d"]):
        n = ts[0]
        name = f" ({n['name']})" if n.get("name") and n["sig"] in ("Container", "Furniture", "Activator") else ""
        told.append(f"{count(len(ts)) if len(ts) > 1 else 'a' if k[0] not in 'aeiouAEIOU' else 'an'} "
                    f"{pl if len(ts) > 1 else k}{name}: nearest {where(n['x'] - x0, n['y'] - y0, n['z'] - z0)}")
    unk = [f"{m} ({c})" for m, c in sorted(unknown.items(), key=lambda kv: -kv[1])]
    return told, loose[:12], doors, unk, fire


def person_line(p: dict, x0: float, y0: float, z0: float, me: bool) -> tuple[str, str]:
    race = race_word(p.get("race"))
    creature = (p.get("race") or "").replace("Race", "") not in PLAYABLE
    who = (f"{p.get('name') or p.get('edid')}, " + ("a creature" if creature else
           f"{race} {'woman' if p.get('female') else 'man'}"))
    work = [f for f in p.get("factions") or [] if re.search(r"job|vendor|merchant|guard|crew|innkeeper|fisher|farm", f,
                                                                   re.I)]
    if not creature:
        who += f"; class {p.get('class') or 'none'}" + (f"; work factions {', '.join(work)}" if work else "")
    if p.get("aggression") in ("Aggressive", "VeryAggressive", "Frenzied"):
        who += "; hostile"
    fm, how = moves(p)
    at = "this is the spot" if me else where(p["x"] - x0, p["y"] - y0, p["z"] - z0)
    return fm, f"{who}: {at}; {how}"


def sheet(d: dict, title: str | None = None, names: dict | None = None, bands=None) -> str:
    """The sheet in words; every fact marked [fixed] or [moving]; `bands` the distance words (NEAR_BANDS)."""
    global _bands
    _bands, keep = bands or NEAR_BANDS, _bands
    try:
        return _sheet(d, title, names)
    finally:
        _bands = keep


def _sheet(d: dict, title: str | None, names: dict | None) -> str:
    if d.get("error"):
        return f"## {title or d['spot']}\n- error: {d['error']}\n"
    x0, y0, z0 = d["at"]
    c = d["cell"]
    L = [f"## Surroundings of {title or d['spot']}"]
    if c["interior"]:
        L.append(f"- Place [fixed]: indoors, {c.get('name') or c.get('edid') or c['key']}.")
    else:
        mk = sorted(d.get("markers") or [], key=lambda m: m["d"])
        near = "; ".join(f"{m['name']} lies {where(m['x'] - x0, m['y'] - y0)}" for m in mk[:3] if m.get("name"))
        L.append(f"- Place [fixed]: outdoors in {(d.get('world') or {}).get('name') or 'the world'}"
                 + (f", {c['name']}" if c.get("name") else "") + (f"; {near}" if near else "; no named place near") + ".")
    L.append(f"- Underfoot [fixed]: {underfoot(d)}.")
    L += [f"- Water [fixed]: {w}" for w in water_round(d)]
    told, loose, doors, unk, fire = things_round(d)
    L.append(f"- Built things within {how_far(d['radius'] - 1)} (nothing further is listed) [fixed], nearest first:")
    L += [f"  - {t}" for t in told] or ["  - none"]
    if doors:
        L.append("- Doors [fixed]:")
        L += [f"  - {x}" for x in doors]
    if loose:
        L.append("- Loose things [fixed until taken]:")
        L += [f"  - {x}" for x in loose]
    if unk:
        L.append(f"- Models the kinds table cannot name (not described; look before naming them): {', '.join(unk[:12])}")
    L.append("- People and creatures near:")
    me_at = lambda p: abs(p["x"] - x0) < 2 and abs(p["y"] - y0) < 2  # noqa: E731
    ppl = sorted(d.get("people") or [], key=lambda p: p["d"])
    for p in ppl[:24]:
        fm, line = person_line(p, x0, y0, z0, me_at(p))
        L.append(f"  - [{fm}] {line}")
    if not ppl:
        L.append("  - none")
    L.append("- What the game does not do here [fixed]:")
    L += [f"  - {x}" for x in NOT_DONE]
    L.append("  - " + ("A fire object stands within the radius (above)." if fire else
                       "No fire burns here: nothing is alight, nothing smokes."))
    return "\n".join(L) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("target", nargs="+")
    ap.add_argument("--radius", type=float, default=RADIUS)
    ap.add_argument("--built", help="the read-back forms' folder, or a built plugin (.esp) to read in place of ours")
    a = ap.parse_args(argv)
    esp = a.built if a.built and a.built.endswith(".esp") else None
    refs = forms(None if esp else a.built)
    specs = [spot_of(t, refs, a.radius) for t in a.target]
    for t, d in zip(a.target, raw(specs, esp)):
        name = refs[t][0].get("name") if t in refs else None
        print(sheet(d, f"{name} ({t})" if name else t))
    return 0


if __name__ == "__main__":
    sys.exit(main())
