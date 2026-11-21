"""`python -m tools.places look --source <source id> <verb> [args] [--ring <metres>] [--centre x,y]`: the look tool's
eyes on a SOURCE place by itself, in its own ground, before any draft: the first step of drafting a place is choosing
its source by looking at the candidates as places (docs/design/agent-view.md).

The source is shown as a view-only place of its own: every exterior piece of its bundle (out/places/bundles/src.<id>,
extracted on demand) where the source has it, grouped into the source's own structures (draft/cluster.py), standing
on the source's own terrain with no world of ours about it. Every view verb of the look tool works on it (overview,
at, orbit, section, survey, walk, probe, pick, measure); the hands do not (a source is never edited).

`--ring <metres>` draws the footprint of a place of that radius on the ground in every view, centred on the source's
anchor or on `--centre x,y`: what a place of that size would take. With a ring, the overview and the whole-place
survey frame what stands inside it, and pieces outside it are a structure named `outside`.

`units`: what the source holds inside the ring (all of it without one), counted offline: houses with rooms, beds,
work stations, docks and boats, palisades, towers, tents, shrines, mines, farms; the pieces by class
(tools/places/classify.py) and the Nordic, Imperial, orc, Dunmer and Argonian pieces by class; the people and their
roles.

The view place lives under this checkout's look folder (never newworld/places); its look daemon is a separate one on
its own port, stopped by `look --source stop`."""
from __future__ import annotations

import json
import math
import os
import re
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

from tools.places.look.scene import LOOK_PORT, ROOT, TREE, data_out

UNITS_PER_M = 70.0
PREFIX = "source."
# short, under the shared out folder: a unix socket path is capped at 108 bytes
BASE = Path(os.environ.get("LOOK_SOURCE_BASE") or data_out().resolve() / "look" / f"{TREE}s")
PORT = LOOK_PORT + 1000
HANDS = {"move", "turn", "sink", "delete", "duplicate", "steps", "land", "commit", "release", "undo", "snapshot",
         "restore", "compare", "reset"}


def place_id(sid: str) -> str:
    return PREFIX + sid


def env(base: Path = BASE) -> dict:
    """The child environment the look modules read at import: this view's folders and port."""
    return dict(os.environ, LOOK_OUT=str(base), LOOK_PORT=str(PORT), PLACES_DIR=str(base / "places"),
                PLACES_OUT=str(base / "data"), PYTHONPATH=str(ROOT))


def _jsonl(p: Path) -> list[dict]:
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()] if p.exists() else []


def _write_if_changed(p: Path, text: str) -> None:
    """A file rewritten only when its text changes: the daemon reloads the page when a place file changes."""
    if p.exists() and p.read_text(encoding="utf-8") == text:
        return
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def ensure_bundle(sid: str, bundles: Path) -> Path:
    src = bundles / f"src.{sid}"
    if not (src / "bundle.json").exists():
        r = subprocess.run([sys.executable, "-m", "tools.places", "extract", sid], cwd=ROOT)
        if r.returncode or not (src / "bundle.json").exists():
            raise SystemExit(f"no bundle for source {sid!r} and its extract failed")
    return src


def ring_of(meta: dict, ring_m: float | None, centre: tuple[float, float] | None) -> dict | None:
    if not ring_m:
        return None
    c = centre or (float(meta["anchor"][0]), float(meta["anchor"][1]))
    return {"centre": [round(c[0], 1), round(c[1], 1)], "radius_m": float(ring_m)}


def inside(ring: dict | None, x: float, y: float) -> bool:
    return ring is None or math.dist((x, y), ring["centre"]) <= ring["radius_m"] * UNITS_PER_M


def rows_of(sid: str, src: Path, ring: dict | None) -> list[dict]:
    """The source's exterior refs as view rows, unmoved, each with its source structure (`outside` past the ring)."""
    from tools.places.draft import io
    from tools.places.draft.cluster import decompose
    from tools.places.seat import Ground
    b = io.load(src.name, src.parent)
    refs = b.exterior.refs if b.exterior else []
    try:
        _, of, _ = decompose(refs, b.bases, Ground.load(src))
    except Exception:   # a source the clusterer cannot read still shows, as loose pieces
        of = {}
    pid, rows = place_id(sid), []
    for r in refs:
        if not r.get("pos") or not r.get("base"):
            continue
        row = {"id": f"{pid}.{r['id']}", "base": r["base"], "kind": r.get("kind"), "pos": r["pos"],
               "rot": r.get("rot") or [0, 0, 0], "scale": r.get("scale", 1.0), "layer": "place",
               "flags": r.get("flags") or [], "src": r["id"], "seat": {"mode": "free", "dz": 0.0},
               "cluster": of.get(r["id"]) or "loose"}
        if not inside(ring, r["pos"][0], r["pos"][1]):
            row["cluster"] = "outside"
        for k in ("lock", "door", "primitive", "edid", "radius", "count", "owner"):
            if r.get(k) is not None:
                row[k] = r[k]
        rows.append(row)
    return rows


def ground_bundle(sid: str, src: Path, bundles: Path) -> None:
    """ground.source.<sid>: the source's own terrain and water, with no world refs (its pieces are the view's rows)."""
    gdir = bundles / f"ground.{place_id(sid)}"
    meta = json.loads((src / "bundle.json").read_text())
    stamp = meta.get("stamp") or {}
    old = gdir / "bundle.json"
    if old.exists() and (json.loads(old.read_text()).get("stamp") or {}).get("key") == stamp.get("key"):
        return
    if gdir.is_symlink() or gdir.is_file():
        gdir.unlink()
    elif gdir.exists():
        shutil.rmtree(gdir)
    sx = gdir / "spaces" / "exterior"
    sx.mkdir(parents=True)
    for f in ("terrain.f32", "terrain.json", "space.json"):
        if (src / "spaces" / "exterior" / f).exists():
            shutil.copyfile(src / "spaces" / "exterior" / f, sx / f)   # the studio serves no link out of a bundle
    (sx / "refs.jsonl").write_text("")
    (gdir / "bases.jsonl").write_text("")
    (gdir / "npcs.jsonl").write_text("")
    g = dict(meta, bundle_id=f"ground.{place_id(sid)}", kind="ground", spaces=["exterior"],
             title=f"the source's own ground: {meta.get('title')}")
    (gdir / "bundle.json").write_text(json.dumps(g, indent=1))


def prepare(sid: str, ring_m: float | None = None, centre: tuple[float, float] | None = None,
            base: Path = BASE, shared: Path | None = None) -> str:
    """The view place of a source written (only what changed); returns its place id."""
    from tools.places.look.daemon import own_out
    shared = shared or data_out()
    src = ensure_bundle(sid, shared / "bundles")
    data = own_out(shared, base / "data")
    meta = json.loads((src / "bundle.json").read_text())
    ring = ring_of(meta, ring_m, centre)
    ground_bundle(sid, src, data / "bundles")
    pid = place_id(sid)
    pdir = base / "places" / pid
    place = {"place_id": pid, "source_id": sid, "similar": [], "view_only": True, "look_ring": ring,
             "radius_m": ring["radius_m"] if ring else 0, "title": meta.get("title")}
    _write_if_changed(pdir / "place.json", json.dumps(place, indent=1) + "\n")
    rows = rows_of(sid, src, ring)
    _write_if_changed(pdir / "spaces" / "exterior" / "refs.jsonl",
                      "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
    return pid


# ---------- units: what the source holds inside the ring ----------
FEATURES = {   # feature -> words of a piece's edid or model (classify.words)
    "bed": ("bed", "bedroll", "hammock"),
    "work station": ("forge", "anvil", "tanningrack", "tanning", "smelter", "alchemy", "enchant", "cookingpot",
                     "cooking", "workbench", "grindstone", "spit", "woodchopping", "chopping"),
    "dock": ("dock", "pier", "jetty", "wharf"),
    "boat": ("boat", "ship", "barge", "canoe", "rowboat", "hull"),
    "palisade": ("palisade", "stockade", "fortwall", "wallpost", "fence"),
    "tower": ("tower", "watchtower", "lookout"),
    "tent": ("tent", "yurt", "lean-to", "leanto"),
    "shrine": ("shrine", "altar", "totem", "histtree", "hist0", "/hist"),
    "mine": ("mine", "minecart", "orevein", "/mines/"),
    "farm": ("farm", "crop", "cabbage", "potato", "wheat", "garden", "plough", "scarecrow", "trough"),
}
CULTURE = {   # culture -> model path or edid words
    "Imperial": ("/imperial/", "imperial", "impcity", "cyrodiil", "/legion"),
    "orc": ("/orc/", "orc", "orsimer"),
    "Dunmer": ("/dunmer/", "dunmer", "velothi", "/solstheim/", "dlc02", "/redoran", "/hlaalu", "/telvanni"),
    "Argonian": ("argonian", "/blackmarsh/", "/argonia", "xanmeer", "/kotm", "murkmire", "/saxhleel", "/lilmoth",
                 "/hist"),
}


def _words(b: dict) -> str:
    from tools.places import classify
    return classify.words(b)


def culture_of(b: dict) -> str | None:
    if b.get("nordic"):
        return "Nordic"
    w = _words(b)
    for c, ws in CULTURE.items():
        if any(x in w for x in ws):
            return c
    return None


def role_of(n: dict) -> str:
    """A person's role from what the record says: a creature, a service, the editor id, the class or a faction."""
    fac = " ".join((f.get("edid") or "") if isinstance(f, dict) else str(f) for f in n.get("factions") or []).lower()
    cls = (n.get("class_edid") or "").lower()
    if "creaturefaction" in fac or cls.startswith("encclass"):
        return "creature"
    if n.get("services"):
        return "/".join(sorted(str(k) for k in n["services"]))
    e = f"{n.get('edid') or ''} {cls} {fac}".lower()
    for word, role in (("guard", "guard"), ("soldier", "soldier"), ("legion", "soldier"), ("bandit", "bandit"),
                       ("merchant", "trader"), ("vendor", "trader"), ("blacksmith", "smith"), ("smith", "smith"),
                       ("innkeep", "innkeeper"), ("priest", "priest"), ("farmer", "farmer"), ("fisher", "fisher"),
                       ("hunter", "hunter"), ("miner", "miner"), ("child", "child"), ("kid", "child"),
                       ("chiled", "child"), ("sailor", "sailor"), ("captain", "captain"), ("archer", "soldier"),
                       ("villager", "villager"), ("citizen", "villager")):
        if word in e:
            return role
    return cls or "unknown"


def units(sid: str, ring_m: float | None = None, centre: tuple[float, float] | None = None,
          bundles: Path | None = None) -> dict:
    from tools.places import classify
    bundles = bundles or data_out() / "bundles"
    src = ensure_bundle(sid, bundles)
    meta = json.loads((src / "bundle.json").read_text())
    ring = ring_of(meta, ring_m, centre)
    bases = {b["key"]: b for b in _jsonl(src / "bases.jsonl")}
    npcs = {n["key"]: n for n in _jsonl(src / "npcs.jsonl")}
    refs = [r for r in _jsonl(src / "spaces" / "exterior" / "refs.jsonl") if r.get("pos")]
    within = [r for r in refs if inside(ring, r["pos"][0], r["pos"][1])]
    by_class, culture, features, people = Counter(), Counter(), Counter(), Counter()
    rooms: dict[str, list[str]] = {}
    for r in within:
        b = dict(bases.get(r["base"]) or {}, kind=r.get("kind") or (bases.get(r["base"]) or {}).get("kind"))
        cls = classify.kind_of(b)
        by_class[cls] += 1
        if r.get("kind") == "actor":
            n = npcs.get(r["base"]) or b
            people[role_of(n)] += 1
            continue
        c = culture_of(b)
        if c and cls not in ("plant", "tree", "rock", "marker", "light", "effect"):
            culture[f"{c} {cls}"] += 1
        w = _words(b)
        for f, ws in FEATURES.items():
            if (cls not in ("marker", "effect") and any(x in w for x in ws)) or (f == "boat" and cls == "boat"):
                features[f] += 1
        to = (r.get("door") or {}).get("to_space")
        if r.get("kind") == "door" and to:
            rooms.setdefault(to, []).append(r["id"])
    space_info = {}
    for sp in rooms:
        sj = src / "spaces" / sp / "space.json"
        try:
            s = json.loads(sj.read_text())
            space_info[sp] = {"name": s.get("name"), "refs": s.get("refs"), "doors": len(rooms[sp])}
        except (OSError, ValueError):
            space_info[sp] = {"name": None, "refs": None, "doors": len(rooms[sp])}
    return {"source": sid, "title": meta.get("title"), "ring": ring, "pieces": len(within), "of": len(refs),
            "houses_with_rooms": space_info, "features": dict(features.most_common()),
            "by_class": dict(by_class.most_common()), "culture": dict(culture.most_common()),
            "people": dict(people.most_common()), "people_n": sum(people.values())}


def units_text(u: dict) -> str:
    r = u["ring"]
    L = [f"{u['source']}: {u['title']}",
         f"inside {'the ring of ' + str(r['radius_m']) + ' m at ' + str(r['centre']) if r else 'the whole source'}: "
         f"{u['pieces']} of {u['of']} exterior pieces"]
    L.append(f"rooms ({len(u['houses_with_rooms'])}): " + "; ".join(
        f"{k} '{v['name']}' {v['refs']} refs" for k, v in u["houses_with_rooms"].items()) or "none")
    for k in ("features", "by_class", "culture", "people"):
        L.append(f"{k}: " + (", ".join(f"{n} {c}" for n, c in u[k].items()) or "none"))
    return "\n".join(L) + "\n"


def _opts(argv: list[str]) -> tuple[list[str], float | None, tuple[float, float] | None]:
    rest, ring, centre, i = [], None, None, 0
    while i < len(argv):
        a = argv[i]
        if a == "--ring":
            ring = float(argv[i + 1])
            i += 2
            continue
        if a == "--centre":
            x, y = (float(v) for v in argv[i + 1].split(","))
            centre = (x, y)
            i += 2
            continue
        rest.append(a)
        i += 1
    return rest, ring, centre


def main(argv: list[str]) -> int:
    if argv and argv[0] == "stop":
        return subprocess.run([sys.executable, "-m", "tools.places", "look", "stop"], env=env(), cwd=ROOT).returncode
    if len(argv) < 2:
        print(__doc__)
        return 2
    sid, rest = argv[0], argv[1:]
    rest, ring, centre = _opts(rest)
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,120}", sid):
        raise SystemExit(f"not a source id: {sid!r}")
    verb = rest[0]
    if verb in HANDS:
        raise SystemExit(f"look --source is read-only: {verb!r} is a hand")
    if verb == "units":
        u = units(sid, ring, centre)
        if "--json" in rest:
            print(json.dumps(u, indent=1))
        else:
            print(units_text(u), end="")
        return 0
    pid = prepare(sid, ring, centre)
    return subprocess.run([sys.executable, "-m", "tools.places", "look", pid, *rest], env=env(), cwd=ROOT).returncode
