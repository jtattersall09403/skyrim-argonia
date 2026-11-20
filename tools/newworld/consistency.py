"""Whether every data record of the new world agrees with every other (decision 0040; owner ruling #80, 2026-11-19).

    ~/.argonia/venv/bin/python -m tools.newworld.consistency [--place ID] [--json] [--family F] [--baseline]

Reads the real data in place: the place database (newworld/story/data/db), the quest records
(newworld/story/quests/**), the story-line pages (story/design/quests/lines), the drafts (newworld/places/<id>), the
Atlas raster and classified water (out/newworld), the built place checks (out/places/shards/<id>/check.json) and
the generated pages (story digest, story explorer, Atlas). Reports every inconsistency with file:line evidence,
grouped by cause. Edits nothing.

Check families, each a function of one context dict so the tests feed it a small broken fixture:
  internal   a place record against itself (disposition, gives, population, tier, peers, held_by, wording)
  ground     a record's water words, siting and on_water against the raster; Hist pools are sap
  source     the source note against the allocated source (place_source rank 0); main-quest sources judged;
             a shared source's notes say how each adaptation differs
  atlas      symbol, tier, footprint, roads and region against the record; the map page's data against the record
  story      every place, person, faction named by the quests and the line pages exists; what a quest says of a
             place is in its record or draft; each placement's place exists and has a spot (quests.jsonl).
             The main quest is the fixed side: the record is reported as wrong, never the quest.
  draft      a drafted place: draft.plan has a delivered row per gives row and look line and a verdict per structure;
             people against population; the built check (nordic, seat, primitives) green and newer than the draft
  generated  the story digest, the story explorer and the Atlas current with their sources

draft.plan's shape and faults are tools/places/draft/plan.py's.

`--baseline` writes the counts per cause to tools/newworld/consistency_baseline.json; a plain run compares with it.
The stage (`make consistency`) is report-only: it exits 0 and prints the counts against the baseline.
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import re
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DBREL = Path("newworld/story/data/db")
BASELINE = Path(__file__).with_name("consistency_baseline.json")
M_PER_PX = 2.93  # metres per Atlas raster pixel


def out_root(repo: Path = REPO) -> Path:
    """out/ is untracked; a lane's worktree reads the main checkout's."""
    if (repo / "out" / "newworld").exists():
        return repo / "out"
    parts = repo.parts
    if ".claude" in parts:
        return Path(*parts[:parts.index(".claude")]) / "out"
    return repo / "out"


@dataclass
class Finding:
    family: str
    cause: str
    place: str | None
    what: str
    evidence: str


class Report:
    def __init__(self):
        self.items: list[Finding] = []

    def add(self, family, cause, place, what, evidence):
        self.items.append(Finding(family, cause, place, what, evidence))


# ---------------------------------------------------------------- loading
def load_table(root: Path, name: str) -> list[tuple[dict, str]]:
    p = root / DBREL / f"{name}.jsonl"
    rel = DBREL / f"{name}.jsonl"
    rows = []
    if p.exists():
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if line.strip():
                rows.append((json.loads(line), f"{rel}:{i}"))
    return rows


def sentences(text: str) -> list[str]:
    return [s for s in re.split(r"(?<=[.;!?])\s+", text or "") if s.strip()]


def load(root: Path = REPO, out: Path | None = None) -> dict:
    out = out or out_root(root)
    T = {n: load_table(root, n) for n in (
        "place", "place_note", "place_give", "place_danger", "place_source", "source_place", "settlement_tier",
        "symbol", "region", "culture", "road_node", "place_alias", "person")}
    ctx: dict = {"root": root, "out": out}
    ctx["places"] = {r["id"]: r for r, _ in T["place"]}
    ctx["place_ev"] = {r["id"]: ev for r, ev in T["place"]}
    notes: dict = collections.defaultdict(dict)
    for r, ev in T["place_note"]:
        notes[r["place_id"]][r["aspect_id"]] = (r["text"], ev)
    ctx["notes"] = notes
    gives: dict = collections.defaultdict(list)
    for r, ev in T["place_give"]:
        gives[r["place_id"]].append(dict(r, _ev=ev))
    ctx["gives"] = gives
    ctx["danger"] = {r["place_id"]: dict(r, _ev=ev) for r, ev in T["place_danger"]}
    ps: dict = collections.defaultdict(list)
    for r, ev in T["place_source"]:
        ps[r["place_id"]].append(dict(r, _ev=ev))
    ctx["place_source"] = ps
    ctx["source_place"] = {r["id"]: r for r, _ in T["source_place"]}
    ctx["tiers"] = {r["id"]: r for r, _ in T["settlement_tier"]}
    ctx["symbols"] = {r["id"]: r for r, _ in T["symbol"]}
    ctx["regions"] = {r["id"]: r for r, _ in T["region"]}
    ctx["cultures"] = {r["id"]: r for r, _ in T["culture"]}
    ctx["on_road"] = {r["place_id"] for r, _ in T["road_node"] if r.get("place_id")}
    al: dict = collections.defaultdict(list)
    for r, _ in T["place_alias"]:
        al[r["place_id"]].append(r["alias"])
    ctx["aliases"] = al
    ctx["person_names"] = {r["name"].lower() for r, _ in T["person"] if r.get("name")}
    fj = root / "story/data/db/faction.jsonl"
    ctx["factions"] = {json.loads(x)["id"] for x in fj.read_text().splitlines() if x.strip()} if fj.exists() else set()
    ctx["quests"] = load_quests(root)
    ctx["lines"] = {str(p.relative_to(root)): p.read_text(encoding="utf-8")
                    for p in sorted((root / "story/design/quests/lines").glob("*.md"))}
    ctx["drafts"] = load_drafts(root, out)
    ctx["main"] = main_places(ctx)
    ctx["ground"] = load_ground(out, ctx["places"])
    ctx["map_page"] = load_map_page(out)
    ctx["generated"] = generated_state(root)
    return ctx


def load_quests(root: Path) -> list[dict]:
    import yaml
    qs = []
    for p in sorted(glob.glob(str(root / "newworld/story/quests/**/*.yaml"), recursive=True)):
        text = Path(p).read_text(encoding="utf-8")
        qs.append({"path": str(Path(p).relative_to(root)), "text": text, "data": yaml.safe_load(text) or {}})
    return qs


def load_drafts(root: Path, out: Path) -> dict:
    def cast_spots(root, pid) -> set[str]:
        """A person a quest places who is one of the place's own people (`cast` in its people source) stands where
        that person's day puts them (tools.places.quest_draft never drafts a spot for one)."""
        src = root / "newworld/sources/people" / f"{pid}.json"
        if not src.exists():
            return set()
        return {f"cast/{p['cast']}" for p in json.loads(src.read_text()).get("people") or [] if p.get("cast")}

    d = {}
    for pj in sorted((root / "newworld/places").glob("*/place.json")):
        pid = pj.parent.name
        people = pj.parent / "people.jsonl"
        spaces = pj.parent / "spaces"
        chk = out / "places/shards" / pid / "check.json"
        d[pid] = {"place": json.loads(pj.read_text()), "rel": str(pj.relative_to(root)),
                  "people": sum(1 for x in people.read_text().splitlines() if x.strip()) if people.exists() else 0,
                  "spaces": sorted(p.stem for p in spaces.glob("*")) if spaces.exists() else [],
                  "spots": ({json.loads(x)["id"] for x in (pj.parent / "quests.jsonl").read_text().splitlines()
                             if x.strip()} if (pj.parent / "quests.jsonl").exists() else set())
                           | cast_spots(root, pid),
                  "check": json.loads(chk.read_text()) if chk.exists() else None,
                  "check_newer": chk.exists() and chk.stat().st_mtime >= changed_at(root, pj.parent)}
    return d


def changed_at(root: Path, d: Path) -> float:
    """When a place's files last changed: the later of its last commit and any uncommitted edit (a checkout's
    file times are the checkout's, so the commit time is the honest one)."""
    import subprocess
    try:
        ct = float(subprocess.run(["git", "-C", str(root), "log", "-1", "--format=%ct", "--", str(d.relative_to(root))],
                                  capture_output=True, text=True, timeout=30).stdout.strip() or 0)
        dirty = subprocess.run(["git", "-C", str(root), "status", "--porcelain", "--", str(d.relative_to(root))],
                               capture_output=True, text=True, timeout=30).stdout.strip()
    except (OSError, ValueError, subprocess.SubprocessError):
        ct, dirty = 0.0, "x"
    if dirty or not ct:
        ct = max([ct] + [f.stat().st_mtime for f in d.glob("*.json*")])
    return ct


def main_places(ctx) -> set[str]:
    txt = "".join(q["text"] for q in ctx["quests"] if "/main/" in q["path"])
    txt += ctx["lines"].get("story/design/quests/lines/main-plot.md", "")
    low = txt.lower()
    found = set()
    for pid, p in ctx["places"].items():
        for n in [pid, p["name"].lower()]:
            if re.search(r"(?<![\w-])" + re.escape(n) + r"(?![\w-])", low):
                found.add(pid)
    return found


def load_ground(out: Path, places: dict) -> dict:
    """Distance (m) from each place to each water group, and the raster's water at its pixel."""
    try:
        import numpy as np
        from PIL import Image
        from scipy import ndimage as ndi
    except ImportError:
        return {}
    wp, lp, jp = out / "newworld/raster/water.png", out / "newworld/water_classified.png", out / "newworld/water_classified.json"
    if not (wp.exists() and lp.exists() and jp.exists()):
        return {}
    water = np.array(Image.open(wp)).astype(bool)
    lab = np.array(Image.open(lp)).astype(np.int32)
    kinds = {w["raster_index"]: w["water_kind_id"] for w in json.loads(jp.read_text())}
    groups = {"sea": {"ocean", "bay", "shallow-coast", "estuary"}, "river": {"river", "stream", "estuary"},
              "lake": {"lake", "pond"}, "swamp": {"blackwater-swamp", "green-marsh"}}
    edt = {g: ndi.distance_transform_edt(~np.isin(lab, [i for i, k in kinds.items() if k in ks])) * M_PER_PX
           for g, ks in groups.items()}
    edt["any"] = ndi.distance_transform_edt(~(water | (lab > 0))) * M_PER_PX
    g = {}
    for pid, p in places.items():
        x, y = int(p["px"]), int(p["py"])
        if 0 <= y < water.shape[0] and 0 <= x < water.shape[1]:
            g[pid] = {"d": {k: float(a[y, x]) for k, a in edt.items()}, "water": bool(water[y, x]),
                      "ev": f"out/newworld/raster/water.png px {x},{y}"}
    return g


def load_map_page(out: Path) -> dict | None:
    p = out / "newworld/map/index.html"
    if not p.exists():
        return None
    html = p.read_text(encoding="utf-8", errors="replace")
    rows = {}
    for m in re.finditer(r'\{"id":"([^"]+)","n":"([^"]*)",[^{}]*?"symid":"([^"]*)"[^{}]*?"reg":"([^"]*)"'
                         r'[^{}]*?"pop":(\d+|null),"radius":([\d.]+|null)', html):
        rows[m.group(1)] = {"n": m.group(2), "symid": m.group(3), "reg": m.group(4),
                            "pop": None if m.group(5) == "null" else int(m.group(5)),
                            "radius": None if m.group(6) == "null" else float(m.group(6))}
    return rows


def generated_state(root: Path) -> dict:
    st = {}
    try:
        from tools.newworld import atlas_state, story_explorer
        st["atlas"] = atlas_state.check(root)
        st["explorer"] = story_explorer.check(root)
    except Exception as e:  # noqa: BLE001 - reported, not hidden
        st["error"] = f"{type(e).__name__}: {e}"
    st["digest"] = digest_stale(root)
    return st


def digest_stale(root: Path) -> list[str]:
    """The story digest's files that differ from a fresh generation (story/design/world)."""
    try:
        from tools.newworld import story_digest as sd
    except Exception as e:  # noqa: BLE001
        return [f"story digest could not be imported: {e}"]
    with tempfile.TemporaryDirectory() as td:
        try:
            sd.generate(Path(td), today="0000-00-00") if "today" in sd.generate.__code__.co_varnames else sd.generate(Path(td))
        except Exception as e:  # noqa: BLE001
            return [f"story digest failed to generate: {type(e).__name__}: {e}"]
        stale = []
        for f in sorted(Path(td).rglob("*.md")):
            rel = f.relative_to(td)
            cur = sd.OUT / rel
            new = re.sub(r"\d{4}-\d{2}-\d{2}", "D", f.read_text(encoding="utf-8"))
            old = re.sub(r"\d{4}-\d{2}-\d{2}", "D", cur.read_text(encoding="utf-8")) if cur.exists() else None
            if new != old:
                stale.append(str(cur.relative_to(root)) if cur.is_relative_to(root) else str(cur))
        return stale


# ---------------------------------------------------------------- helpers
def tier_of(ctx, p):
    s = ctx["symbols"].get(p.get("symbol_id"), {})
    t = ctx["tiers"].get(s.get("settlement_tier_id"))
    return (t, s.get("id", "").endswith("seat")) if t else (None, False)


def texts(ctx, pid) -> dict[str, tuple[str, str]]:
    t = {a: v for a, v in ctx["notes"].get(pid, {}).items()}
    t["summary"] = (ctx["places"][pid].get("summary") or "", ctx["place_ev"].get(pid, "place"))
    g = ctx["gives"].get(pid, [])
    t["gives"] = (" . ".join(x.get("detail") or "" for x in g), g[0]["_ev"] if g else "place_give")
    return t


DEAD = ("ruined", "abandoned", "sunken", "wrecked", "derelict")
SERVICES = {"trader-general", "trader-innkeeper", "trader-hunter", "trader-blacksmith", "trader-apothecary",
            "trader-spells", "trader-jeweller", "trader-clothier", "trader-bookseller", "trader-fletcher", "inn-room",
            "free-bed", "trainer", "shrine-blessing", "fence"}
TREASURE = {"treasure", "boss-chest", "gold-hoard"}
LIVED_IN = ("city", "town", "village", "hamlet", "estate")
TIER_ORDER = ["minor", "outpost", "village", "town", "small-city", "large-city", "metropolis"]


# ---------------------------------------------------------------- 1 internal
def check_internal(ctx, R: Report, only=None):
    P = ctx["places"]
    for pid, p in P.items():
        if only and pid != only:
            continue
        ev = ctx["place_ev"].get(pid, "place")
        pop = p.get("population") or 0
        dg = ctx["danger"].get(pid, {})
        disp = dg.get("disposition_id")
        G = ctx["gives"].get(pid, [])
        kinds = collections.Counter(g["give_kind_id"] for g in G)
        T = texts(ctx, pid)
        t, seat = tier_of(ctx, p)
        if t:
            hi = t["population_hi"] * (1.25 if seat else 1)
            if not t["population_lo"] <= pop <= hi:
                R.add("internal", "population outside its settlement tier", pid,
                      f"{p['name']} is drawn as {t['id']} ({t['population_lo']}-{t['population_hi']}) with population {pop}",
                      f"{ev}; settlement_tier {t['id']}")
        else:
            if pop > 0 and p.get("status") in DEAD:
                R.add("internal", "a dead place with people", pid, f"status {p['status']} but population {pop}", ev)
            if pop == 0 and p.get("status") == "inhabited":
                R.add("internal", "an inhabited place with nobody", pid, "status inhabited, population 0", ev)
        if disp == "friendly" and p.get("place_kind_id") in LIVED_IN:
            bad = [g for g in G if g["give_kind_id"] in ("combat-boss", "combat-foes")]
            for g in bad:
                R.add("internal", "a friendly place gives a fight inside it", pid,
                      f"friendly {p['place_kind_id']} gives {g['give_kind_id']}: {(g.get('detail') or '')[:80]}", g["_ev"])
        if disp in ("abandoned", "hostile"):
            for g in G:
                if g["give_kind_id"] in SERVICES:
                    R.add("internal", "a hostile or abandoned place offers a service", pid,
                          f"{disp} place gives {g['give_kind_id']}", g["_ev"])
        if disp == "abandoned" and pop > 0:
            R.add("internal", "a dead place with people", pid, f"disposition abandoned, population {pop}", dg.get("_ev", ev))
        if pop <= 1:
            for g in G:
                if g["give_kind_id"].startswith("trader") or g["give_kind_id"] == "inn-room":
                    R.add("internal", "trade with no people to keep it", pid,
                          f"population {pop} but gives {g['give_kind_id']}", g["_ev"])
        tr = [g for g in G if g["give_kind_id"] in TREASURE]
        if len(tr) >= 2:
            R.add("internal", "more than one treasure", pid, f"{len(tr)} treasure rows", tr[1]["_ev"])
        if pop > 0 and (p.get("held_by") or "").lower().startswith("nobody"):
            R.add("internal", "held_by says nobody where people live", pid, f"population {pop}, held_by '{p['held_by']}'", ev)
        look = T.get("look", ("", ""))
        if p.get("status") == "inhabited" and pop > 0 and disp == "friendly" and re.search(
                r"\b(abandoned|deserted|uninhabited|nobody lives|no one lives)\b", T["summary"][0] + " " + look[0], re.I):
            R.add("internal", "the words say empty where people live", pid, "summary or look says abandoned/empty", look[1] or ev)
        if pop <= 3:
            for a in ("look", "present"):
                s, e = T.get(a, ("", ""))
                if re.search(r"\b(busy|bustling|crowded|thronged|packed|teeming)\b", s, re.I):
                    R.add("internal", "the words say busy where few live", pid, f"population {pop}; {a} says busy", e)
        if kinds.get("ore-vein") and p.get("place_kind_id") not in ("mine", "cave", "quarry") and not re.search(
                r"\b(ore|mine|vein|quarry|pit|seam)\b", " ".join(v for v, _ in T.values()), re.I):
            R.add("internal", "a give the record's words never name", pid, "ore-vein with no ore or mine in the record",
                  next(g["_ev"] for g in G if g["give_kind_id"] == "ore-vein"))
        s, e = T.get("people", ("", ""))
        mm = re.search(r"\b(\d+) (?:people|residents|souls)\b", s)
        if mm and pop and abs(int(mm.group(1)) - pop) > max(3, pop // 4):
            R.add("internal", "the people note's number differs from the population", pid,
                  f"people note says '{mm.group(0)}', population {pop}", e)
        if disp == "hostile" and re.search(r"\b(welcom\w*|friendly|hospitable)\b", T.get("present", ("", ""))[0], re.I):
            R.add("internal", "the words say welcoming where the place is hostile", pid, "present says welcoming",
                  T["present"][1])
    # peers: every place of a higher tier has more people than every one below it
    by: dict = collections.defaultdict(list)
    for pid, p in P.items():
        t, _ = tier_of(ctx, p)
        if t and p.get("status") == "inhabited" and t["id"] in TIER_ORDER:
            by[t["id"]].append(((p.get("population") or 0), pid))
    present = [t for t in TIER_ORDER if by[t]]
    for lo, up in zip(present, present[1:]):
        for n, pid in by[up]:
            above = [q for m, q in by[lo] if m > n]
            if above and (not only or pid == only):
                R.add("internal", "population out of order with its peers", pid,
                      f"{up} {P[pid]['name']} ({n}) has fewer people than {lo} {', '.join(P[q]['name'] for q in above[:3])}",
                      ctx["place_ev"].get(pid, "place"))


# ---------------------------------------------------------------- 2 ground
WATER_RULES = [
    ("river", r"\b(rivers?|creeks?|streams?|weirs?|rapids|ford|mill-?race|riverbank)\b", ["river"], 700),
    ("harbour", r"\b(harbou?rs?|quays?|wharf|wharves|slipway)\b", ["sea", "river", "lake"], 500),
    ("docks", r"\b(docks?|jett(?:y|ies)|piers?|landing stage|boat-?lanes?|boat sheds?|boathouses?)\b", ["any"], 300),
    ("boats", r"\b(boats?|canoes?|punts?|rafts?|barges?|ferr(?:y|ies))\b", ["any"], 500),
    ("fishing", r"\b(fishing|fish traps?|fisher(?:men|folk)?)\b", ["any"], 500),
    ("over water", r"\b(over (?:the )?water|above the water|built over|on the water)\b", ["any"], 150),
    ("lake", r"\b(lakes?|lagoons?|meres?)\b", ["lake", "swamp"], 900),
    ("pool", r"\b(ponds?|pools?|tarns?)\b", ["any"], 250),
    ("sea", r"\b(sea|ocean|tides?|tidal|surf|beach|shoreline|coastal|coast)\b", ["sea"], 2500),
    ("flooded", r"\b(flooded|half-sunken|waterlogged|submerged|drowned)\b", ["any"], 200),
]
NEG = re.compile(r"\b(no|not|without|never|dry|nor|far from|away from|lacks?|none)\b", re.I)
HIST_WATER = re.compile(r"(waterbreathing|water-breathing|pond|bathe|wade|spring water|clear water|cool water|pool of water|"
                        r"waters? of the (?:hist )?pool|fed by|water[- ]fed)", re.I)


def check_ground(ctx, R: Report, only=None):
    G = ctx["ground"]
    for pid, p in ctx["places"].items():
        if only and pid != only:
            continue
        T = texts(ctx, pid)
        # Hist pools are sap (no raster needed): worded as water anywhere, or named where the record never says sap
        says_sap = any(re.search(r"\bsap\b", v, re.I) for v, _ in T.values())
        hard, soft = [], []
        for a, (v, e) in T.items():
            for s in sentences(v):
                if re.search(r"\bHist\b", s) and re.search(r"\b(pool|pond|pools|basin|spring)\b", s, re.I) \
                        and not re.search(r"\bsap\b", s, re.I):
                    (hard if HIST_WATER.search(s) else soft).append((a, s, e))
        if hard:
            a, s, e = hard[0]
            R.add("ground", "a Hist pool worded as water, not sap", pid, f"[{a}] {s[:140]}", e)
        elif soft and not says_sap:
            a, s, e = soft[0]
            R.add("ground", "a Hist pool the record never calls sap", pid, f"[{a}] {s[:140]}", e)
        g = G.get(pid)
        if not g:
            continue
        d = g["d"]
        for name, rx, grps, lim in WATER_RULES:
            near = min(d[x] for x in grps)
            if near <= lim:
                continue
            for a in ("look", "overview", "present", "summary", "gives", "dangers", "economy"):
                v, e = T.get(a, ("", ""))
                hit = None
                for s in sentences(v):
                    if NEG.search(s) or (name == "pool" and re.search(r"\bHist\b|sap|egg|hatch", s, re.I)):
                        continue
                    if name == "river" and re.search(r"river[- ]road|\b[A-Z][a-z]+ (River|Creek)\b", s):
                        continue
                    if name == "sea" and re.search(r"sea of|Sea-?Folk|coast road", s, re.I):
                        continue
                    m = re.search(rx, s, re.I)
                    if m:
                        hit = (m.group(0), s)
                        break
                if hit:
                    R.add("ground", "a water word with no such water on the ground", pid,
                          f"[{a}] says '{hit[0]}' but the nearest {'/'.join(grps)} water is {near:.0f} m away (limit {lim} m)",
                          f"{e}; {g['ev']}")
                    break
        need = {"riverbank": ("river", 700), "coast": ("sea", 900), "lakeshore": ("lake", 700), "island": ("any", 400)}
        s = p.get("siting")
        if s in need:
            grp, lim = need[s]
            n = min(d["lake"], d["swamp"]) if s == "lakeshore" else d[grp]
            if n > lim:
                R.add("ground", "siting without its water", pid, f"siting {s} but the nearest {grp} water is {n:.0f} m away",
                      f"{ctx['place_ev'][pid]}; {g['ev']}")
        if s == "swamp" and d["any"] > 1500:
            R.add("ground", "siting without its water", pid, f"siting swamp, no water within {d['any']:.0f} m",
                  f"{ctx['place_ev'][pid]}; {g['ev']}")
        if bool(p.get("on_water")) != g["water"]:
            R.add("ground", "on_water disagrees with the raster", pid,
                  f"on_water={p.get('on_water')}, raster says {g['water']}", f"{ctx['place_ev'][pid]}; {g['ev']}")


# ---------------------------------------------------------------- 3 source
def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


WORDS = {"two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
         "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17,
         "eighteen": 18, "nineteen": 19, "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60}


def number(tok: str) -> int | None:
    if tok.isdigit():
        return int(tok)
    parts = tok.lower().split("-")
    if all(x in WORDS for x in parts):
        return sum(WORDS[x] for x in parts)
    return None


def check_source(ctx, R: Report, only=None):
    SP = ctx["source_place"]
    shared: dict = collections.defaultdict(list)
    for pid, rows in ctx["place_source"].items():
        r0 = [r for r in rows if r["rank"] == 0]
        if r0:
            shared[r0[0]["source_place_id"]].append(pid)
    for pid, p in ctx["places"].items():
        if only and pid != only:
            continue
        rows = [r for r in ctx["place_source"].get(pid, []) if r["rank"] == 0]
        note, nev = ctx["notes"].get(pid, {}).get("source", ("", ctx["place_ev"][pid]))
        if not rows:
            R.add("source", "no allocated source", pid, "no place_source rank 0", ctx["place_ev"][pid])
            continue
        r0 = rows[0]
        s0 = SP.get(r0["source_place_id"])
        if not s0:
            R.add("source", "the allocated source is not in source_place", pid, r0["source_place_id"], r0["_ev"])
            continue
        if not note:
            R.add("source", "no source note", pid, f"allocated {s0['title']}", r0["_ev"])
            continue
        m = re.search(r"Its main source, (.*?) \(", note)
        nm = norm(s0.get("name") or s0["title"])
        if m and nm not in norm(note) and " ".join(nm.split()[:2]) not in norm(note):
            R.add("source", "the source note names another source than the allocated one", pid,
                  f"note names '{m.group(1)}', allocated '{s0['title']}'", f"{nev}; {r0['_ev']}")
        if "fixed" not in (r0.get("why") or ""):
            for key in ("buildings", "interiors", "people"):
                sk = "residents" if key == "people" else key
                first = next((x for x in sentences(note) if "Its main source" in x), "")
                mm = re.search(r"\b([a-z-]+|\d+) " + key + r"\b", first)
                n = number(mm.group(1)) if mm else None
                if n is not None and s0.get(sk) is not None and n != s0[sk] and m:
                    R.add("source", "the source note's counts differ from the source", pid,
                          f"note says {mm.group(0)}, {s0['title']} has {s0[sk]} {key}", f"{nev}; {r0['_ev']}")
        if "nordic" in (s0.get("culture_tags") or "") and not re.search(r"replac|reskin|Argonian pieces", note, re.I):
            R.add("source", "a Nordic source whose note does not replace its Nordic pieces", pid, s0["title"], nev)
        if pid in ctx["main"] and not re.search(r"judged|fixed|closest match|from the (asset )?pool", (r0.get("why") or "") + " " + note, re.I):
            R.add("source", "a main-quest place whose source is not judged", pid,
                  f"allocated {s0['title']} by score {r0.get('score')}; no judgement recorded", f"{r0['_ev']}; {nev}")
        others = [q for q in shared[r0["source_place_id"]] if q != pid]
        if others:
            missing = [q for q in others if norm(ctx["places"][q]["name"]) not in norm(note)]
            if missing and not re.search(r"\b(unlike|differs?|whereas|instead of)\b", note, re.I):
                R.add("source", "a shared source whose note does not say how this adaptation differs", pid,
                      f"{s0['title']} also serves {', '.join(ctx['places'][q]['name'] for q in missing[:4])}", nev)


# ---------------------------------------------------------------- 4 atlas
def check_atlas(ctx, R: Report, only=None):
    P = ctx["places"]
    names: dict = collections.defaultdict(list)
    for pid, p in P.items():
        names[norm(p["name"])].append(pid)
    mp = ctx.get("map_page")
    for pid, p in P.items():
        if only and pid != only:
            continue
        ev = ctx["place_ev"][pid]
        if len(names[norm(p["name"])]) > 1:
            R.add("atlas", "two places share a name", pid, f"'{p['name']}' also {names[norm(p['name'])]}", ev)
        if p.get("region_id") not in ctx["regions"]:
            R.add("atlas", "an unknown region or culture", pid, f"region {p.get('region_id')}", ev)
        if p.get("culture_id") and p["culture_id"] not in ctx["cultures"]:
            R.add("atlas", "an unknown region or culture", pid, f"culture {p['culture_id']}", ev)
        if p.get("symbol_id") not in ctx["symbols"]:
            R.add("atlas", "an unknown symbol", pid, f"symbol {p.get('symbol_id')}", ev)
        cr = ctx.get("cell_region", {}).get(f"{p.get('cell_x')},{p.get('cell_y')}")
        if cr and cr != p.get("region_id"):
            R.add("atlas", "the record's region differs from its cell's", pid,
                  f"record {p.get('region_id')}, cell {p.get('cell_x')},{p.get('cell_y')} in {cr}", f"{ev}; out/newworld/cell_region.json")
        t, _ = tier_of(ctx, p)
        if t and p.get("footprint_radius_m") and t.get("footprint_radius_m") and \
                p["footprint_radius_m"] > 1.8 * t["footprint_radius_m"] + 10:
            R.add("atlas", "the footprint is too big for its tier", pid,
                  f"radius {p['footprint_radius_m']} m against {t['id']}'s {t['footprint_radius_m']} m", ev)
        kmap = {"city": {"large-city", "metropolis", "small-city"}, "town": {"town", "small-city"},
                "village": {"village", "town", "outpost"}}
        if t and p.get("place_kind_id") in kmap and t["id"] not in kmap[p["place_kind_id"]]:
            R.add("atlas", "the symbol's tier differs from the kind", pid, f"kind {p['place_kind_id']} drawn as {t['id']}", ev)
        if pid not in ctx["on_road"] and ((p.get("population") or 0) >= 20 or (p.get("importance") or 0) >= 4
                                          or p.get("place_kind_id") in ("city", "town")):
            R.add("atlas", "a town or city on no road", pid,
                  f"{p.get('place_kind_id')} pop {p.get('population')} importance {p.get('importance')}", ev)
        if mp is not None:
            row = mp.get(pid)
            if row is None:
                R.add("atlas", "the map page is behind the records", pid, "not on the map page", "out/newworld/map/index.html")
            else:
                diffs = [f"{k} {row[k]}!={v}" for k, v in (("n", p["name"]), ("symid", p.get("symbol_id")),
                                                            ("reg", p.get("region_id")), ("pop", p.get("population")),
                                                            ("radius", p.get("footprint_radius_m"))) if row[k] != v]
                if diffs:
                    R.add("atlas", "the map page is behind the records", pid, "; ".join(diffs),
                          f"out/newworld/map/index.html; {ev}")
    if mp is None and not only:
        R.add("atlas", "the map page is missing", None, "no out/newworld/map/index.html", "out/newworld/map")


# ---------------------------------------------------------------- 5 story
FEATURES = ["quay", "jetty", "landing", "market", "pool", "dock", "inn", "tavern", "temple", "shrine", "gatehouse",
            "tower", "bridge", "weir", "lodge", "trapdoor", "cage", "forge", "warehouse", "prison", "barracks",
            "boathouse"]
PLACE_ID = re.compile(r"(?<![\w-])(?:[a-z]+-)*(?:outpost|tribal-camp|abandoned-village|imperial-ruin|kothringi-ruin|ruin|cave|camp|"
                      r"shrine|fort|village|wreck)(?:-[a-z0-9]+)*-m?\d+-m?\d+\b")


def walk(o, path=()):
    if isinstance(o, dict):
        yield path, o
        for k, v in o.items():
            yield from walk(v, path + (k,))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from walk(v, path + (i,))


def line_of(text: str, needle: str) -> int:
    i = text.find(needle)
    return text.count("\n", 0, i) + 1 if i >= 0 else 1


def room_names(d) -> list[str]:
    rn = (d["place"].get("draft") or {}).get("room_names") or {}
    vals = rn.values() if isinstance(rn, dict) else rn
    return [v.get("name", "") if isinstance(v, dict) else str(v) for v in vals] + list(d["spaces"])


def place_words(ctx, pid) -> str:
    w = " ".join(v for v, _ in texts(ctx, pid).values())
    w += " " + " ".join(g["give_kind_id"].replace("-", " ") for g in ctx["gives"].get(pid, []))
    w += " " + " ".join(ctx["aliases"].get(pid, [])) + " " + (ctx["places"][pid].get("held_by") or "")
    d = ctx["drafts"].get(pid)
    if d:
        w += " " + " ".join(room_names(d))
    return w.lower()


def has_feature(words: str, f: str) -> bool:
    return re.search(r"\b" + f + r"(s|es)?\b", words) is not None


def check_story(ctx, R: Report, only=None):
    P = ctx["places"]
    by_name = {norm(p["name"]): pid for pid, p in P.items()}
    for pid, al in ctx["aliases"].items():
        for a in al:
            by_name.setdefault(norm(a), pid)
    defined_factions = set(ctx["factions"])
    for q in ctx["quests"]:
        for _, o in walk(q["data"]):
            fid = o.get("id")
            if isinstance(fid, str) and fid.startswith("faction.") and ("name" in o or "kind" in o) and "access" not in o:
                defined_factions.add(fid)
            ref = o.get("ref")
            if isinstance(ref, str) and ref.startswith("faction."):
                defined_factions.add(ref)
    for q in ctx["quests"]:
        data, path, text = q["data"], q["path"], q["text"]
        main = "/main/" in path
        cause_sfx = " (main quest: the record is wrong)" if main else ""
        qid = data.get("id", path)
        refs = []  # (place id, context, need words)
        for v in [data.get("settlement")] + list(data.get("anchorPlaces") or []):
            if isinstance(v, str):
                refs.append((v, "settlement", ""))
            elif isinstance(v, dict) and v.get("place"):
                refs.append((v["place"], "anchorPlaces", ""))
        for c in data.get("cast") or []:
            if not isinstance(c, dict):
                continue
            if not isinstance(c.get("persona"), dict):
                c = dict(c, persona={})
            home = c["persona"].get("home")
            if isinstance(home, str):
                home = re.split(r"[ ,(]", home.strip(), maxsplit=1)[0]
            if home:
                refs.append((home, f"cast {c.get('id')} home", ""))
            name = (c.get("persona") or {}).get("name")
            if (c.get("persona") or {}).get("status") in ("canon", "bmv", "existing") and name and \
                    name.lower() not in ctx["person_names"]:
                R.add("story", "a quest names a person not in the records", home,
                      f"{qid}: cast {c.get('id')} '{name}' ({c['persona']['status']})", f"{path}:{line_of(text, name)}")
        for pl in data.get("placements") or []:
            a = pl.get("anchor") if isinstance(pl, dict) else None
            if not isinstance(a, dict) or not a.get("place"):
                continue
            pid = a["place"]
            refs.append((pid, f"placement {pl.get('ref')}", a.get("need") or ""))
            ln = f"{path}:{line_of(text, 'ref: ' + str(pl.get('ref')))}"
            if pid in P and (not only or pid == only):
                spot = f"{qid.split('.')[-1] if isinstance(qid, str) else qid}/{pl.get('ref')}"
                d = ctx["drafts"].get(pid)
                spots = d["spots"] if d else set()
                if not any(s.endswith("/" + str(pl.get("ref"))) for s in spots):
                    R.add("story", "a quest placement with no spot in its place's quests.jsonl", pid,
                          f"{spot}" + ("" if d else " (place not drafted)"), ln)
                room = a.get("room")
                if room and d:
                    rooms = {norm(x) for x in room_names(d)}
                    # an outdoor enclosure a quest calls a room (a cage) is the quest's own named door or thing,
                    # standing at its spot in this place's quests.jsonl
                    rooms |= {norm(str(o.get("name"))) for o in data.get("placements") or [] if isinstance(o, dict)
                              and o.get("name") and (o.get("anchor") or {}).get("place") == pid
                              and any(s.endswith("/" + str(o.get("ref"))) for s in spots)}
                    if norm(room) not in rooms:
                        R.add("story", "a quest names a room the draft does not have" + cause_sfx, pid,
                              f"{qid}: room '{room}'", ln)
        missing_seen = set()
        for pid, where, need in refs:
            if only and pid != only:
                continue
            if pid not in P:
                if pid in missing_seen:
                    continue
                missing_seen.add(pid)
                R.add("story", "a quest names a place not in the records", pid, f"{qid}: {where} '{pid}'",
                      f"{path}:{line_of(text, pid)}")
                continue
            if need:
                words = place_words(ctx, pid)
                for f in FEATURES:
                    if has_feature(need.lower(), f) and not has_feature(words, f):
                        R.add("story", "a quest asks of a place what its record and draft lack" + cause_sfx, pid,
                              f"{qid} {where}: '{f}' ({need[:90]})", f"{path}:{line_of(text, need[:40])}; {ctx['place_ev'][pid]}")
        for _, o in walk(data):
            for k in ("id", "faction"):
                v = o.get(k)
                if isinstance(v, str) and v.startswith("faction.") and v not in defined_factions and not only:
                    R.add("story", "a quest names a faction not in the records", None, f"{qid}: {v}",
                          f"{path}:{line_of(text, v)}")
                    defined_factions.add(v)  # once per faction
        named = {r[0] for r in refs}
        for m in PLACE_ID.finditer(text):
            if m.group(0) not in P and m.group(0) not in named and (not only or m.group(0) == only):
                named.add(m.group(0))
                R.add("story", "a quest names a place not in the records", m.group(0), f"{qid}: '{m.group(0)}'",
                      f"{path}:{text.count(chr(10), 0, m.start()) + 1}")
    # the story-line pages: place ids and real place names that no record carries
    src_names = {}
    world_names = {norm(r.get("name", "")) for r in ctx["regions"].values()} | {norm(c.get("name", "")) for c in ctx["cultures"].values()}
    squashed = {k.replace(" ", "") for k in by_name}
    alltext = "\n".join(ctx["lines"].values())
    for s in ctx["source_place"].values():
        n = (s.get("name") or "").strip()
        if norm(n).replace(" ", "") in squashed or re.search(r"\b" + re.escape(n.lower()) + r"\b", alltext):
            continue  # a record carries it, or the pages use it as a common word
        if s.get("mined_group") == "bmv" and len(n) >= 5 and n[0].isupper() and norm(n) not in by_name \
                and norm(n) not in world_names and not any(norm(n) in w or w in norm(n) for w in world_names if w):
            src_names[n] = s["id"]
    for rel, text in ctx["lines"].items():
        main = rel.endswith("main-plot.md")
        for m in PLACE_ID.finditer(text):
            if m.group(0) not in P and (not only or m.group(0) == only):
                R.add("story", "a story page names a place not in the records", m.group(0), m.group(0),
                      f"{rel}:{text.count(chr(10), 0, m.start()) + 1}")
        if only:
            continue
        seen = set()
        for n in src_names:
            for m in re.finditer(r"(?<![\w-])" + re.escape(n) + r"(?![\w-])", text):
                if n in seen:
                    break
                seen.add(n)
                R.add("story", "a story page names a source place no record carries" + (" (main quest)" if main else ""),
                      None, f"'{n}' ({src_names[n]})", f"{rel}:{text.count(chr(10), 0, m.start()) + 1}")


# ---------------------------------------------------------------- 6 drafts
def check_drafts(ctx, R: Report, only=None):
    for pid, d in ctx["drafts"].items():
        if only and pid != only:
            continue
        p = ctx["places"].get(pid)
        rel = d["rel"]
        if not p:
            R.add("draft", "a draft with no place record", pid, rel, rel)
            continue
        draft = d["place"].get("draft") or {}
        from tools.places.draft import plan
        gives = ctx["gives"].get(pid, [])
        for cause, detail in plan.faults(draft.get("plan"), gives):
            ev = next((g["_ev"] for g in gives if cause == plan.NO_GIVE and f" {g['give_kind_id']} " in detail), None)
            R.add("draft", cause, pid, detail, f"{rel}; {ev}" if ev else rel)
        pop = p.get("population") or 0
        n = d["people"]
        if n < pop or n > max(pop * 1.5, pop + 4):
            R.add("draft", "the draft's people differ from the population", pid, f"{n} people drafted, population {pop}",
                  f"newworld/places/{pid}/people.jsonl; {ctx['place_ev'][pid]}")
        ck = d["check"]
        if not ck:
            R.add("draft", "a draft with no built check", pid, "no out/places/shards/<id>/check.json", rel)
            continue
        if not d["check_newer"]:
            R.add("draft", "the built check is older than the draft", pid, "check.json predates the place files",
                  f"out/places/shards/{pid}/check.json")
        for k, cause in (("nordic", "a Nordic piece in the draft"), ("seat", "a floating or sunk piece in the draft"),
                         ("land", "a floating or sunk piece in the draft"), ("primitives", "an unresolved model in the draft")):
            r = (ck.get("results") or {}).get(k)
            if r and not r.get("ok"):
                R.add("draft", cause, pid, f"{r.get('n')} failures: {'; '.join(map(str, r.get('failures', [])[:2]))[:160]}",
                      f"out/places/shards/{pid}/check_failures/{k}.txt")


# ---------------------------------------------------------------- 7 generated
def check_generated(ctx, R: Report, only=None):
    if only:
        return
    g = ctx["generated"]
    if g.get("error"):
        R.add("generated", "a generated page could not be checked", None, g["error"], "tools/newworld")
    if g.get("atlas"):
        R.add("generated", "the Atlas is behind its sources", None, g["atlas"][:200], "tools/newworld/atlas.json")
    if g.get("explorer"):
        R.add("generated", "the story explorer is behind its sources", None, g["explorer"][:200],
              "tools/newworld/story_explorer.json")
    for f in g.get("digest") or []:
        R.add("generated", "the story digest is behind its sources", None, f, f)


FAMILIES = {"internal": check_internal, "ground": check_ground, "source": check_source, "atlas": check_atlas,
            "story": check_story, "draft": check_drafts, "generated": check_generated}


def run(ctx, only=None, families=None) -> Report:
    R = Report()
    for name, fn in FAMILIES.items():
        if not families or name in families:
            fn(ctx, R, only)
    return R


def counts(R: Report) -> dict[str, int]:
    c = collections.Counter(f"{f.family}: {f.cause}" for f in R.items)
    return dict(sorted(c.items()))


def render(R: Report, base: dict | None) -> str:
    by: dict = collections.defaultdict(list)
    for f in R.items:
        by[(f.family, f.cause)].append(f)
    lines = []
    for (fam, cause), fs in sorted(by.items()):
        key = f"{fam}: {cause}"
        b = (base or {}).get(key)
        lines.append(f"\n## {key}  ({len(fs)}" + (f", baseline {b}" if b is not None else "") + ")")
        for f in fs:
            lines.append(f"- {f.place or '-'}: {f.what}  [{f.evidence}]")
    lines.append(f"\n{len(R.items)} inconsistencies in {len(by)} causes")
    if base is not None:
        tot = sum(base.values())
        lines.append(f"baseline {tot}; " + ("worse" if len(R.items) > tot else "not worse") + " than the baseline")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--place")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--family", action="append", choices=sorted(FAMILIES))
    ap.add_argument("--baseline", action="store_true", help="write the counts per cause as the baseline")
    ap.add_argument("--summary", action="store_true", help="only the counts per cause")
    a = ap.parse_args(argv)
    ctx = load()
    cr = out_root() / "newworld/cell_region.json"
    ctx["cell_region"] = json.loads(cr.read_text()) if cr.exists() else {}
    R = run(ctx, a.place, a.family)
    c = counts(R)
    if a.baseline:
        BASELINE.write_text(json.dumps({"total": len(R.items), "causes": c}, indent=1) + "\n")
    base = json.loads(BASELINE.read_text())["causes"] if BASELINE.exists() and not (a.place or a.family) else None
    if a.json:
        print(json.dumps({"total": len(R.items), "causes": c, "findings": [asdict(f) for f in R.items]}, indent=1))
    elif a.summary:
        for k, v in c.items():
            print(f"{v:5d}  {k}" + (f"  (baseline {base.get(k, 0)})" if base is not None else ""))
        print(f"{len(R.items):5d}  total" + (f"  (baseline {sum(base.values())})" if base is not None else ""))
    else:
        print(render(R, base))
    return 0


if __name__ == "__main__":
    sys.exit(main())
