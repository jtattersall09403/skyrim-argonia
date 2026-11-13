"""The province as the story sees it (nw-05 step 1): a digest of the new world's database for story writers.

    python3 -m tools.newworld.story_digest [--out story/design/world]

Writes, wholly from the database (newworld/story/data/db through tools.argonia_world.db) and the place folders
(newworld/places/<id>/place.json says a place is drafted):

    province.md            the province in one read: land, travel, peoples, power and law, danger, what it offers,
                           a table of every place, and the gaps the data leaves
    regions/<region>.md    one per region: its nature, peoples, places (what each promises, what it is built from,
                           whether it is built), dangers, and the hooks its notes already hold
    people.md              everyone the data names: the person table, and names the place notes give
    index.md               what the files are, the database's revision and how to regenerate

Nothing is invented. Researched prose is quoted as the notes hold it; every other sentence is composed from rows.
Each paragraph ends with an HTML comment naming the rows it rests on (place:<id>, place_note:<place>/<aspect>,
region_note:<region>/<aspect>, culture:<id>, place_give:<place>/<seq>, travel_route:<from>/<to>/<mode>, ...),
so a fact can be checked. Where the data is silent the digest says "the data does not say" and the gap is
collected at the end of province.md.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

from tools.argonia_world import db
from tools.newworld import frame as f

REPO = f.REPO
OUT = REPO / "story" / "design" / "world"
PLACES_DIR = f.ROOT / "places"
SILENT = "the data does not say"

# Words that mark a sentence of a note (other than the hooks note) as a tension, shortage, rivalry, mystery or loss.
TENSION = re.compile(
    r"\b(feud\w*|rival\w*|raid(?:s|ed|ers?|ing)?|smuggl\w*|sour\w*|sicken\w*|sick|blight\w*|lost|missing|vanish\w*|"
    r"disput\w*|debt\w*|quarrel\w*|stolen|steal\w*|fled|flee\w*|haunt\w*|curse\w*|"
    r"will not|won't|resent\w*|secret\w*|forbid\w*|forbidden|threat\w*|ransom\w*|kidnap\w*|slave\w*|"
    r"grudge\w*|mutin\w*|desert\w*|poison\w*|plague\w*|murder\w*|killed|drowned|failed|fails|shortage|scarce|"
    r"hungry|famine|exile\w*|contested|schism|heres\w*|extort\w*|hostage\w*|unpaid|"
    r"betray\w*|unstaked|walk(?:s|ing)? again|restless|cut off|withdrew|emptied|overrun|burned|burnt)\b",
    re.I)
HOOK_ASPECTS = ("overview", "present", "people", "history", "economy", "faith")
REGION_HOOK_ASPECTS = ("overview", "present", "people", "history", "economy", "faith")

COMPASS = ["north", "north-east", "east", "south-east", "south", "south-west", "west", "north-west"]
WATER_WORDS = {"river": ("river", "rivers"), "estuary": ("estuary", "estuaries"), "stream": ("stream", "streams"),
               "lake": ("lake", "lakes"), "pond": ("pond", "ponds"), "green-marsh": ("open reed marsh", "open reed marshes"),
               "blackwater-swamp": ("blackwater swamp", "blackwater swamps"), "bay": ("bay", "bays"),
               "shallow-coast": ("stretch of shallow coast", "stretches of shallow coast"),
               "ocean": ("reach of open sea", "reaches of open sea")}
SPEED = {"still": "still", "slow": "slowly", "moderate": "steadily", "fast": "fast"}
# The give groups a story writer reads first when a place's main gives are chosen, best first.
GIVE_ORDER = ["rootworm-stop", "boat-stop", "coach-stop", "trainer", "unique-item", "follower", "player-home",
              "spell-tome", "skill-book", "shrine-blessing", "trader-spells", "trader-blacksmith", "trader-apothecary",
              "trader-general", "trader-innkeeper", "fence", "trader-jeweller", "trader-bookseller", "trader-clothier",
              "trader-hunter", "trader-fletcher", "arcane-enchanter", "alchemy-lab", "forge", "inn-room", "gold-hoard",
              "boss-chest", "combat-boss", "combat-foes", "combat-creature", "harvest-rare", "ore-vein", "treasure",
              "free-bed", "fishing", "harvest-common"]


# ---------------------------------------------------------------------------------------------------------------
# Small writing helpers
# ---------------------------------------------------------------------------------------------------------------

def cite(*ids: str) -> str:
    """The rows a paragraph rests on, kept out of the reader's way."""
    ids = [i for i in dict.fromkeys(ids) if i]
    return f" <!-- {'; '.join(ids)} -->" if ids else ""


def cell(s) -> str:
    """Text safe in a table cell."""
    return str(s if s is not None else "").replace("|", "/").replace("\n", " ")


def sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])", (text or "").strip())
    return [p.strip() for p in parts if p.strip()]


def first_sentence(text: str) -> str:
    s = sentences(text)
    return s[0] if s else ""


def join_and(items: list[str]) -> str:
    items = [i for i in items if i]
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " and " + items[-1]


def plural(n: int, one: str, many: str | None = None) -> str:
    return f"{n} {one if n == 1 else (many or one + 's')}"


def km(m: float) -> str:
    return f"{m / 1000:.1f} km" if m >= 1000 else f"{int(round(m, -1))} m"


def compass(dx: float, dy: float) -> str:
    """dx east, dy north."""
    ang = (math.degrees(math.atan2(dx, dy)) + 360) % 360
    return COMPASS[int((ang + 22.5) // 45) % 8]


def sentence_case(s: str) -> str:
    return s[:1].upper() + s[1:] if s else s


def article(s: str) -> str:
    return "an" if s[:1].lower() in "aeiou" else "a"


def humanise(fid: str) -> str:
    return fid.replace("_", " ").replace("-", " ")


# ---------------------------------------------------------------------------------------------------------------
# The world, read once
# ---------------------------------------------------------------------------------------------------------------

class World:
    def __init__(self, root: Path = f.ROOT, places_dir: Path = PLACES_DIR):
        w = db.open(root)
        self.root = root
        q = lambda sql, *a: [dict(r) for r in w.query(sql, *a)]  # noqa: E731
        self.q = q
        self.regions = {r["id"]: r for r in q("SELECT * FROM region ORDER BY name")}
        self.cultures = {r["id"]: r for r in q("SELECT * FROM culture ORDER BY name")}
        self.places = {r["id"]: r for r in q("SELECT * FROM place ORDER BY name")}
        self.kinds = {r["id"]: r for r in q("SELECT * FROM place_kind")}
        self.symbols = {r["id"]: r for r in q("SELECT * FROM symbol")}
        self.tiers = {r["id"]: r for r in q("SELECT * FROM settlement_tier")}
        self.bands = {r["id"]: r for r in q("SELECT * FROM danger_band")}
        self.dispositions = {r["id"]: r for r in q("SELECT * FROM disposition")}
        self.laws = {r["id"]: r for r in q("SELECT * FROM law")}
        self.give_kinds = {r["id"]: r for r in q("SELECT * FROM give_kind")}
        self.modes = {r["id"]: r for r in q("SELECT * FROM travel_mode")}
        self.operators = {r["id"]: r for r in q("SELECT * FROM travel_operator")}
        self.atmos_class = {r["id"]: r for r in q("SELECT * FROM atmosphere_class")}
        self.atmos = {r["region_id"]: r for r in q("SELECT * FROM region_atmosphere")}
        self.pnotes = defaultdict(dict)
        for r in q("SELECT * FROM place_note"):
            self.pnotes[r["place_id"]][r["aspect_id"]] = r["text"]
        self.rnotes = defaultdict(dict)
        for r in q("SELECT * FROM region_note"):
            self.rnotes[r["region_id"]][r["aspect_id"]] = r["text"]
        self.gives = defaultdict(list)
        self.deleted_gives = []           # rows the research marked for deletion and never removed
        for r in q("SELECT * FROM place_give ORDER BY place_id, seq"):
            if r["detail"].strip().lower() == "(delete entry)":
                self.deleted_gives.append(r)
                continue
            self.gives[r["place_id"]].append(r)
        self.danger = {r["place_id"]: r for r in q("SELECT * FROM place_danger")}
        self.law = {r["place_id"]: r for r in q("SELECT * FROM place_law")}
        self.wealth = {r["place_id"]: r for r in q("SELECT * FROM place_wealth")}
        self.wealth_bands = {r["id"]: r for r in q("SELECT * FROM place_wealth_band")}
        self.aliases = defaultdict(list)
        for r in q("SELECT * FROM place_alias ORDER BY alias"):
            self.aliases[r["place_id"]].append(r["alias"])
        self.goods = defaultdict(list)
        for r in q("SELECT pg.*, g.name AS good FROM place_good pg JOIN good g ON g.id = pg.good_id"):
            self.goods[r["place_id"]].append(r)
        self.stops = defaultdict(list)
        for r in q("SELECT * FROM travel_stop"):
            self.stops[r["place_id"]].append(r)
        self.routes = defaultdict(list)       # place -> (other, row), both ways
        self.route_rows = q("SELECT * FROM travel_route ORDER BY from_place_id, to_place_id")
        pairs = {}
        for r in self.route_rows:            # authored as a pair, each way: one link per pair and mode
            pairs.setdefault((min(r["from_place_id"], r["to_place_id"]), max(r["from_place_id"], r["to_place_id"]),
                              r["travel_mode_id"]), r)
        self.links = list(pairs.values())
        for r in self.links:
            self.routes[r["from_place_id"]].append((r["to_place_id"], r))
            self.routes[r["to_place_id"]].append((r["from_place_id"], r))
        self.approach = {r["place_id"]: r for r in q("SELECT * FROM travel_approach")}
        self.sources = {r["id"]: r for r in q("SELECT * FROM source_place")}
        self.place_sources = defaultdict(list)
        for r in q("SELECT * FROM place_source ORDER BY place_id, rank"):
            self.place_sources[r["place_id"]].append(r)
        self.people = q("SELECT * FROM person ORDER BY place_id, name")
        self.households = {r["id"]: r for r in q("SELECT * FROM household")}
        self.person_notes = defaultdict(dict)
        for r in q("SELECT * FROM person_note"):
            self.person_notes[r["person_id"]][r["aspect_id"]] = r["text"]
        self.races = {r["id"]: r for r in q("SELECT * FROM race")}
        self.pw_bands = {r["id"]: r for r in q("SELECT * FROM person_wealth_band")}
        self.counts = {t: q(f'SELECT count(*) AS n FROM "{t}"')[0]["n"]
                       for t in ("person_faction", "person_relation", "unique_item", "place_good", "person")}
        self.drafted = {p for p in self.places if (places_dir / p / "place.json").exists()}
        self._geography()
        self._roads()
        self._water()

    # -- geography ------------------------------------------------------------------------------------------
    def _geography(self) -> None:
        cells = self.q("SELECT x, y, region_id, land_share, danger_band_id FROM cell WHERE margin = 0")
        by = {(c["x"], c["y"]): c["region_id"] for c in cells}
        sx, sy, n = Counter(), Counter(), Counter()
        self.ground_bands = defaultdict(Counter)
        self.land_share = defaultdict(float)
        for c in cells:
            r = c["region_id"]
            sx[r] += c["x"]
            sy[r] += c["y"]
            n[r] += 1
            self.land_share[r] += c["land_share"]
            if c["danger_band_id"]:
                self.ground_bands[r][c["danger_band_id"]] += 1
        self.centroid = {r: (sx[r] / n[r], sy[r] / n[r]) for r in n}
        self.cell_count = dict(n)
        self.land_share = {r: self.land_share[r] / n[r] for r in n}
        edges = Counter()
        for (x, y), r in by.items():
            for o in ((x + 1, y), (x, y + 1)):
                r2 = by.get(o)
                if r2 and r2 != r:
                    edges[tuple(sorted((r, r2)))] += 1
        self.neighbours = defaultdict(dict)
        for (a, b), k in edges.items():
            if k >= 2:
                self.neighbours[a][b] = k
                self.neighbours[b][a] = k
        land = [c for c in cells if self.regions[c["region_id"]]["kind"] == "land"]
        self.box = (min(c["x"] for c in land), max(c["x"] for c in land),
                    min(c["y"] for c in land), max(c["y"] for c in land))

    def position(self, region_id: str) -> str:
        """Where a region sits in the province, by thirds of the land's box."""
        x, y = self.centroid[region_id]
        x0, x1, y0, y1 = self.box
        col = min(2, max(0, int(3 * (x - x0) / (x1 - x0 + 1))))
        row = min(2, max(0, int(3 * (y - y0) / (y1 - y0 + 1))))
        ns = ["south", "", "north"][row]
        ew = ["west", "", "east"][col]
        if ns and ew:
            return f"the {ns}-{ew}"
        if ns or ew:
            return f"the {ns or ew}"
        return "the middle"

    def direction(self, a: str, b: str) -> str:
        """The way from region a to region b."""
        (ax, ay), (bx, by) = self.centroid[a], self.centroid[b]
        return compass(bx - ax, by - ay)

    def place_direction(self, a: str, b: str) -> str:
        pa, pb = self.places[a], self.places[b]
        return compass(pb["world_x"] - pa["world_x"], pb["world_y"] - pa["world_y"])

    # -- roads ------------------------------------------------------------------------------------------------
    def _roads(self) -> None:
        nodes = {r["id"]: r for r in self.q("SELECT * FROM road_node")}
        adj = defaultdict(list)
        for r in self.q("SELECT * FROM road"):
            adj[r["from_node_id"]].append((r["to_node_id"], r["length_m"], r["road_class_id"], r["id"]))
            adj[r["to_node_id"]].append((r["from_node_id"], r["length_m"], r["road_class_id"], r["id"]))
        self.road_links = defaultdict(dict)   # place -> other -> (metres, class, first road id)
        for nid, n in nodes.items():
            if n["kind"] != "place" or not n["place_id"]:
                continue
            src = n["place_id"]
            best: dict[str, tuple[float, str]] = {}
            # Dijkstra-light: the graph is small; walk junctions until another place node.
            frontier = [(0.0, nid, "major", None)]
            seen = {nid: 0.0}
            while frontier:
                frontier.sort()
                d, cur, cls, first = frontier.pop(0)
                for nxt, length, rc, rid in adj[cur]:
                    nd = d + length
                    ncls = "minor" if "minor" in (cls, rc) else "major"
                    nfirst = first or rid
                    nn = nodes[nxt]
                    if nn["kind"] == "place" and nn["place_id"] and nn["place_id"] != src:
                        o = nn["place_id"]
                        if o not in best or nd < best[o][0]:
                            best[o] = (nd, ncls, nfirst)
                        continue
                    if nxt in seen and seen[nxt] <= nd:
                        continue
                    seen[nxt] = nd
                    frontier.append((nd, nxt, ncls, nfirst))
            for o, v in best.items():
                if o != src:
                    self.road_links[src][o] = v

    # -- water ------------------------------------------------------------------------------------------------
    def _water(self) -> None:
        self.water = defaultdict(list)
        for r in self.q("SELECT * FROM water_body WHERE region_id IS NOT NULL"):
            self.water[r["region_id"]].append(r)
        self.water_by_id = {r["id"]: r for rs in self.water.values() for r in rs}

    # -- per place facts --------------------------------------------------------------------------------------
    def kind_label(self, p: dict) -> str:
        return self.kinds[p["place_kind_id"]]["label"]

    def tier(self, p: dict) -> dict | None:
        t = self.symbols[p["symbol_id"]].get("settlement_tier_id")
        return self.tiers.get(t) if t else None

    def kind_size(self, p: dict) -> str:
        """'large city, about 440 m across': a city by its tier, anything else by its kind."""
        t = self.tier(p)
        k = t["label"] if p["place_kind_id"] == "city" and t else self.kind_label(p)
        if not re.match(r"[A-Z][a-z]+ic\b|Imperial|Kothringi|Lilmothiit|Ayleid|Velothi", k):
            k = k[0].lower() + k[1:]
        if p.get("footprint_radius_m"):
            k += f", about {int(round(2 * p['footprint_radius_m'], -1))} m across"
        return k

    def culture_name(self, cid: str | None) -> str:
        return self.cultures[cid]["name"] if cid in self.cultures else ""

    def band(self, bid: str | None, long: bool = False) -> str:
        if not bid:
            return SILENT
        b = self.bands[bid]
        if long:
            return f"{b['label'].lower()} (band {b['rank']} of 5, foes about level {b['foe_level']})" \
                if b["foe_level"] else f"{b['label'].lower()} (band {b['rank']} of 5)"
        return b["label"]

    def give_text(self, g: dict) -> str:
        name = self.give_kinds[g["give_kind_id"]]["name"]
        detail = g["detail"]
        n = f" (x{g['count']})" if g["count"] > 1 else ""
        where = ""
        if g.get("setting") == "nearby" and g.get("spot"):
            where = f", {km(g['distance_m'])} {compass(math.sin(math.radians(g['bearing_deg'])), math.cos(math.radians(g['bearing_deg'])))} at {g['spot']}"
        elif g.get("setting") == "provoked":
            where = ", only if its own people are provoked"
        elif g.get("setting") == "interior":
            where = ", inside"
        return f"{name}: {detail}{n}{where}"

    def main_gives(self, pid: str, k: int = 4) -> list[str]:
        gs = sorted(self.gives[pid], key=lambda g: (GIVE_ORDER.index(g["give_kind_id"])
                                                   if g["give_kind_id"] in GIVE_ORDER else 99, g["seq"]))
        out, seen = [], set()
        for g in gs:
            gk = g["give_kind_id"]
            if gk in seen:
                continue
            seen.add(gk)
            out.append(f"{self.give_kinds[gk]['name'].lower()} ({g['detail']})")
            if len(out) == k:
                break
        return out

    def travel_short(self, pid: str) -> str:
        if self.stops[pid]:
            bits = []
            for s in sorted(self.stops[pid], key=lambda s: s["travel_mode_id"]):
                others = [o for o, r in self.routes[pid] if r["travel_mode_id"] == s["travel_mode_id"]]
                bits.append(f"{s['travel_mode_id']} {s['rank']} to "
                            + ", ".join(self.places[o]["name"] for o in sorted(others, key=lambda o: self.places[o]["name"])))
            return "; ".join(bits)
        a = self.approach.get(pid)
        if a:
            return f"{km(a['foot_m'])} by {a['way']} from the {a['travel_mode_id']} stop at {self.places[a['stop_place_id']]['name']}" \
                + (" (remote)" if a["remote"] else "")
        return SILENT

    def travel_long(self, pid: str) -> tuple[str, list[str]]:
        p = self.places[pid]
        cites: list[str] = []
        parts = []
        for s in sorted(self.stops[pid], key=lambda s: s["travel_mode_id"]):
            op = self.operators[s["travel_operator_id"]]
            routes = sorted([(o, r) for o, r in self.routes[pid] if r["travel_mode_id"] == s["travel_mode_id"]],
                            key=lambda t: self.places[t[0]]["name"])
            rt = join_and([f"{self.places[o]['name']} ({km(r['distance_m'])}, {r['fare']} gold, "
                           f"{plural(r['hours'], 'hour')})" for o, r in routes])
            parts.append(f"It is a {s['travel_mode_id']} {s['rank']}, kept by {op['name'].lower()}s "
                         f"({op['craft']}), with passage to {rt or 'nowhere yet'}.")
            cites.append(f"travel_stop:{pid}/{s['travel_mode_id']}")
            cites += [f"travel_route:{r['from_place_id']}/{r['to_place_id']}/{r['travel_mode_id']}" for _, r in routes]
        a = self.approach.get(pid)
        if a:
            stop = self.places[a["stop_place_id"]]["name"]
            way = {"road": "by road", "marsh": "across the marsh on foot", "water": "over water",
                   "dive": "by diving"}[a["way"]]
            parts.append(f"The nearest stop is the {a['travel_mode_id']} stop at {stop}, {km(a['foot_m'])} away {way}."
                         + (f" It is remote on purpose: {sentence_case(a['why'])}" if a["remote"] else ""))
            cites.append(f"travel_approach:{pid}")
        links = sorted(self.road_links.get(pid, {}).items(), key=lambda t: t[1][0])
        if links:
            rd = join_and([f"{self.places[o]['name']} ({'cart road' if c == 'major' else 'track'}, {km(d)} "
                           f"{self.place_direction(pid, o)})" for o, (d, c, _) in links[:6]])
            parts.append(f"Roads run from it to {rd}.")
            cites.append(f"road_node:place={pid}")
        elif not p["on_water"]:
            parts.append("No road reaches it.")
            cites.append(f"road_node:place={pid}")
        return " ".join(parts), cites

    def source_text(self, pid: str) -> tuple[str, list[str]]:
        rows = self.place_sources.get(pid, [])
        if not rows:
            return f"What it will be built from: {SILENT}.", []
        main = [r for r in rows if r["rank"] == 0]
        alts = [r for r in rows if r["rank"] > 0]
        out, cites = [], []
        if main:
            s = self.sources[main[0]["source_place_id"]]
            out.append(f"It is to be built from {s['name']} in {s['plugin']} (a {s['kind'].replace('-', ' ')}: "
                       f"{plural(s['buildings'], 'building')}, {plural(s['interiors'], 'interior')}, "
                       f"{plural(s['residents'], 'resident')}, {s['enemies']} hostile, about "
                       f"{int(s['footprint_m'] or 0)} m across). The source reads: \"{s['description']}\"")
            cites.append(f"place_source:{pid}/0")
            cites.append(f"source_place:{s['id']}")
        if alts:
            out.append("Similar sources: " + join_and([
                f"{self.sources[r['source_place_id']]['name']} ({self.sources[r['source_place_id']]['kind'].replace('-', ' ')}, "
                f"{plural(self.sources[r['source_place_id']]['buildings'], 'building')}, "
                f"{plural(self.sources[r['source_place_id']]['interiors'], 'interior')})" for r in alts]) + ".")
            cites += [f"place_source:{pid}/{r['rank']}" for r in alts]
        return " ".join(out), cites


# ---------------------------------------------------------------------------------------------------------------
# Hooks
# ---------------------------------------------------------------------------------------------------------------

def place_hooks(W: World, pid: str) -> list[tuple[str, str]]:
    """(sentence, row id): the place's hooks note whole, then each tension its other notes state."""
    out, seen = [], set()
    notes = W.pnotes.get(pid, {})
    for s in sentences(notes.get("hooks", "")):
        out.append((s, f"place_note:{pid}/hooks"))
        seen.add(s)
    for a in HOOK_ASPECTS:
        for s in sentences(notes.get(a, "")):
            if s not in seen and TENSION.search(s):
                out.append((s, f"place_note:{pid}/{a}"))
                seen.add(s)
    return out


def region_hooks(W: World, rid: str) -> list[tuple[str, str]]:
    out = []
    for a in REGION_HOOK_ASPECTS:
        for s in sentences(W.rnotes.get(rid, {}).get(a, "")):
            if TENSION.search(s):
                out.append((s, f"region_note:{rid}/{a}"))
    return out


# ---------------------------------------------------------------------------------------------------------------
# Gaps
# ---------------------------------------------------------------------------------------------------------------

def gaps(W: World) -> list[str]:
    g = []
    noculture = [p for p in W.places.values() if not p.get("culture_id")]
    byreg = Counter(W.regions[p["region_id"]]["name"] for p in noculture)
    g.append(f"Which people a place belongs to: {plural(len(noculture), 'place')} carry no culture "
             f"({', '.join(f'{k} {v}' for k, v in byreg.most_common())}). Most are ruins, wrecks and camps, but "
             f"some are lived in ({join_and(sorted(p['name'] for p in noculture if (p.get('population') or 0) > 0)[:12])}"
             f"{' and others' if sum(1 for p in noculture if (p.get('population') or 0) > 0) > 12 else ''}).")
    land_nc = [r["name"] for r in W.regions.values() if r["kind"] == "land" and not r.get("culture_id")]
    if land_nc:
        g.append(f"Which culture holds a region: {SILENT} for {join_and(sorted(land_nc))}.")
    g.append("Who rules a region: there is no ruler column for a region or a culture; a place's holder is a line of "
             "free text (held_by), and nothing joins the holders of several places into one authority.")
    noheld = [p["name"] for p in W.places.values() if not p.get("held_by")]
    if noheld:
        g.append(f"Who holds a place: {SILENT} for {join_and(sorted(noheld))}.")
    nopop = [p["name"] for p in W.places.values() if p.get("population") is None]
    if nopop:
        g.append(f"How many live in a place: {SILENT} for {join_and(sorted(nopop))}.")
    named = sum(1 for r in W.water_by_id.values() if r.get("name") and not r["name"].lower().startswith("update"))
    g.append(f"The names of rivers and lakes: of {len(W.water_by_id)} bodies of water in the regions, {named} carry a "
             "name; a river is named only where a region's or a place's notes name it.")
    faith_words = re.compile(r"\b(Hist|Sithis|Nine|Daedr\w*|god\w*|faith|worship\w*|shrine|belie\w*|rite\w*|heres\w*)\b")
    nofaith = [c["name"] for c in W.cultures.values() if not faith_words.search(c["about"] + " " + c["people"])]
    if nofaith:
        g.append(f"What a culture believes: its row says nothing of belief for {join_and(nofaith)} (the places' faith "
                 "notes say what each place keeps).")
    places_people = sorted({W.places[p['place_id']]['name'] for p in W.people})
    g.append(f"Named people: the person table holds {plural(len(W.people), 'person', 'people')}, all of "
             f"{join_and(places_people)}; every other place's people are numbers only. Faction memberships "
             f"({W.counts['person_faction']} rows) and ties between people ({W.counts['person_relation']} rows) are empty.")
    g.append(f"Goods: what places make, trade and need is a table of {W.counts['place_good']} rows "
             "(one place's market); the rest lives only in the economy notes.")
    g.append(f"Uniques: the world's unique things are a table of {W.counts['unique_item']} rows; two places promise "
             "a unique item in their gives.")
    g.append(f"The make-up of a source place: the mining counts buildings, interiors, residents and hostiles, and "
             f"names its piece families, but how many of each kind of building (houses, halls, piers, shrines) it "
             f"holds: {SILENT}.")
    if W.deleted_gives:
        g.append(f"Rows marked for deletion: {plural(len(W.deleted_gives), 'give')} read '(delete entry)' and are left "
                 "out here (" + join_and([f"{W.places[r['place_id']]['name']}, {W.give_kinds[r['give_kind_id']]['name'].lower()}"
                                         for r in W.deleted_gives]) + ").")
    moved = W.q("SELECT count(*) AS n FROM place_source WHERE rank = 0 AND population_before IS NOT NULL "
                "AND population_after IS NOT NULL AND population_before != population_after")[0]["n"]
    if moved:
        g.append(f"How many live in a place: for {plural(moved, 'place')} the population was reset from the research's "
                 "estimate to the residents of the place's source, so the number in a place row can differ from the "
                 "number its people note gives.")
    named = Counter(r["place_id"] for r in W.people)
    for pid, k in sorted(named.items()):
        pop = W.places[pid].get("population")
        if pop is not None and pop != k:
            g.append(f"How many live in {W.places[pid]['name']}: the place row says {pop} (its source's residents), "
                     f"the person table names {k}.")
    drafted = sorted(W.places[p]["name"] for p in W.drafted)
    g.append(f"Built places: only {join_and(drafted) or 'none'} is drafted; every other place is a record and a "
             "source, not yet ground a quest can be checked against.")
    return g


# ---------------------------------------------------------------------------------------------------------------
# province.md
# ---------------------------------------------------------------------------------------------------------------

def region_line(W: World, rid: str) -> str:
    r = W.regions[rid]
    nb = sorted(W.neighbours[rid], key=lambda o: -W.neighbours[rid][o])
    nbt = join_and([f"{W.regions[o]['name']} to the {W.direction(rid, o)}" for o in nb])
    cul = W.culture_name(r.get("culture_id"))
    n = sum(1 for p in W.places.values() if p["region_id"] == rid)
    kind = "sea" if r["kind"] == "sea" else (r.get("landform") or "land").lower().rstrip(".")
    bits = [f"**{r['name']}** lies in {W.position(rid)} of the province: {kind}."]
    if r.get("summary"):
        bits.append(r["summary"])
    bits.append(f"It borders {nbt or 'nothing on the map'}.")
    bits.append(f"It holds {plural(n, 'place')}" + (f"; the region's row gives it to {cul}." if cul else
                                                     "; which culture holds it, the data does not say." if r["kind"] == "land" else "."))
    return " ".join(bits) + cite(f"region:{rid}", f"cell:region={rid}")


def water_line(W: World, rid: str) -> str:
    ws = W.water.get(rid, [])
    if not ws:
        return ""
    c = Counter(w["water_kind_id"] for w in ws)
    order = ["ocean", "bay", "shallow-coast", "estuary", "river", "lake", "stream", "green-marsh", "blackwater-swamp", "pond"]
    parts = [f"{n} {WATER_WORDS[k][0 if n == 1 else 1]}" for k in order if (n := c.get(k))]
    rivers = sorted([w for w in ws if w["water_kind_id"] in ("river", "estuary")], key=lambda w: -w["area_m2"])[:3]
    rv = []
    for w in rivers:
        d = f"{article(w['water_kind_id'])} {w['water_kind_id']} about {int(round(w['width_m'] or 0, -1))} m wide"
        if w["flows"] and w.get("flow_toward_deg") is not None:
            th = math.radians(w["flow_toward_deg"])
            d += f" running {SPEED.get(w.get('speed'), '')} {compass(math.sin(th), math.cos(th))}".replace("  ", " ")
        dn = W.water_by_id.get(w.get("downstream_id") or "")
        if dn and dn.get("region_id") and dn["region_id"] != rid:
            d += f" into {W.regions[dn['region_id']]['name']}"
        rv.append(d)
    out = f"Its water: {join_and(parts)}."
    if rv:
        out += f" The largest flowing water is {join_and(rv)}."
    return out


def province(W: World, digest_hooks: int) -> str:
    L: list[str] = []
    land = [r for r in W.regions.values() if r["kind"] == "land"]
    sea = [r for r in W.regions.values() if r["kind"] == "sea"]
    L += ["# Black Marsh in 4E 201: the province as the story sees it", "",
          f"This is the new world's database read as one province: {plural(len(W.regions), 'region')} "
          f"({len(land)} of land, {len(sea)} of sea), {plural(len(W.cultures), 'culture')} and "
          f"{plural(len(W.places), 'place')}. Everything here is generated from the rows; the researched notes are quoted "
          "as written. Each region has its own file under `regions/` with every place in full and the hooks the notes "
          "hold. Where the data is silent this says so, and the gaps are gathered at the end.", ""]

    # -- the lie of the land
    L += ["## The lie of the land", ""]
    for r in sorted(land, key=lambda r: (-W.centroid[r["id"]][1], W.centroid[r["id"]][0])):
        L += [region_line(W, r["id"]), ""]
    L += ["The seas round it:", ""]
    for r in sea:
        L += [region_line(W, r["id"]), ""]
    L += ["### Water", "",
          "The map's water is classified by kind but almost none of it is named; the region notes name the rivers and "
          "lakes they mean. Per region, counted from the water bodies:", ""]
    for r in sorted(land, key=lambda r: r["name"]):
        wl = water_line(W, r["id"])
        if wl:
            L += [f"- {r['name']}: {wl[len('Its water: '):]}" + cite(f"water_body:region={r['id']}")]
    L += [""]

    # -- travel
    L += ["### Roads, boats, coaches and the rootworm", ""]
    for m in W.modes.values():
        stops = sorted({s["place_id"] for ss in W.stops.values() for s in ss if s["travel_mode_id"] == m["id"]},
                       key=lambda p: W.places[p]["name"])
        hubs = [W.places[p]["name"] for p in stops
                if any(s["rank"] == "hub" and s["travel_mode_id"] == m["id"] for s in W.stops[p])]
        L += [f"**{m['name']}.** {m['operated_by']} It needs {m['needs'][0].lower() + m['needs'][1:]} "
              f"{plural(len(stops), 'place has', 'places have')} a stop; "
              + (f"the hub is {hubs[0]}." if len(hubs) == 1 else f"the hubs are {join_and(hubs) or 'none'}.")
              + cite(f"travel_mode:{m['id']}", "travel_stop:*"), ""]
    for m in W.modes.values():
        ls = sorted([r for r in W.links if r["travel_mode_id"] == m["id"]],
                    key=lambda r: (W.places[r["from_place_id"]]["name"], W.places[r["to_place_id"]]["name"]))
        if ls:
            L += [f"The {m['name'].lower()} links, each both ways: " + "; ".join(
                f"{W.places[r['from_place_id']]['name']} to {W.places[r['to_place_id']]['name']} ({km(r['distance_m'])}, "
                f"{r['fare']} gold, {plural(r['hours'], 'hour')})" for r in ls) + "."
                + cite(f"travel_route:mode={m['id']}"), ""]
    major = Counter()
    for a, links in W.road_links.items():
        for b, (_d, c, _) in links.items():
            if c == "major" and a < b:
                major[W.regions[W.places[a]["region_id"]]["name"]] += 1
    L += ["The cart roads (the coach's roads) join places in "
          + join_and([f"{k} ({plural(v, 'link')})" for k, v in major.most_common()])
          + "; every other road is a track. Each region's file names the roads from each place." + cite("road:*", "road_node:*"), ""]

    # -- the peoples
    L += ["## The peoples", ""]
    for c in W.cultures.values():
        ps = [p for p in W.places.values() if p.get("culture_id") == c["id"]]
        regs = Counter(W.regions[p["region_id"]]["name"] for p in ps)
        pop = sum(p.get("population") or 0 for p in ps)
        L += [f"**{c['name']}.** {c['people']}. {c['about']} They hold {plural(len(ps), 'place')} "
              f"({join_and([f'{k} {v}' for k, v in regs.most_common()])}), about {pop} people in all."
              + cite(f"culture:{c['id']}", f"place:culture={c['id']}"), ""]

    # -- power and law
    L += ["## Power and law", ""]
    for lw in W.laws.values():
        L += [f"**{lw['label']}.** {lw['about']}" + cite(f"law:{lw['id']}"), ""]
    L += ["| Region | Native law | Foreign law | No law |", "|---|---|---|---|"]
    for r in sorted(W.regions.values(), key=lambda r: r["name"]):
        c = Counter(W.law[p]["law_id"] for p in W.places if W.places[p]["region_id"] == r["id"])
        if c:
            L.append(f"| {r['name']} | {c.get('native', 0)} | {c.get('foreign', 0)} | {c.get('none', 0)} |")
    L += ["", "Where foreign law holds (an office the Empire left, with cells), and whose cell takes a sentence:", ""]
    foreign = sorted([p for p in W.places if W.law[p]["law_id"] == "foreign"], key=lambda p: W.places[p]["name"])
    for p in foreign:
        pl = W.places[p]
        L.append(f"- {pl['name']} ({W.regions[pl['region_id']]['name']}), held by {pl.get('held_by') or SILENT}; "
                 f"cells at {W.places[W.law[p]['jail_place_id']]['name']}." + cite(f"place_law:{p}", f"place:{p}"))
    L += ["", "Who holds the places that shape the province (importance 4 and 5):", ""]
    for p in sorted(W.places.values(), key=lambda p: (-(p.get("importance") or 0), p["name"])):
        if (p.get("importance") or 0) < 4:
            continue
        L.append(f"- {p['name']} ({W.regions[p['region_id']]['name']}): {p.get('held_by') or SILENT}."
                 + cite(f"place:{p['id']}"))
    L += ["", "Who rules a region as a whole the data does not say; each region file quotes its notes on the present.", ""]

    # -- danger
    L += ["## Danger", "",
          "Danger is fixed in the world, never levelled to the player. The bands:", ""]
    for b in sorted(W.bands.values(), key=lambda b: b["rank"]):
        L.append(f"- {b['label']} (foes about level {b['foe_level']}): {b['about']}" + cite(f"danger_band:{b['id']}"))
    L += ["", "| Region | Baseline away from roads | Ground: share of cells by band (safe to lethal) | Hostile places |",
          "|---|---|---|---|"]
    for r in sorted(W.regions.values(), key=lambda r: r["name"]):
        gb = W.ground_bands.get(r["id"], Counter())
        tot = sum(gb.values()) or 1
        shares = " / ".join(f"{round(100 * gb.get(b, 0) / tot)}%" for b in sorted(W.bands, key=lambda b: W.bands[b]["rank"]))
        hostile = [W.places[p]["name"] for p in W.places if W.places[p]["region_id"] == r["id"]
                   and W.danger[p]["disposition_id"] == "hostile"]
        L.append(f"| {r['name']} | {W.band(r.get('danger_band_id'))} | {shares} | {', '.join(sorted(hostile)) or 'none'} |")
    L += [""]

    # -- what the world offers
    L += ["## What the world offers a player", "",
          "Counts by region of what the places promise (a place record's gives), and of the kinds of place worth "
          "going into.", "",
          "| Region | Trainers | Traders | Smithing | Shrines | Ruins | Wrecks | Dungeons and caves | Rare things |",
          "|---|---|---|---|---|---|---|---|---|"]
    rare = {"harvest-rare", "unique-item", "skill-book", "spell-tome", "gold-hoard", "follower", "player-home"}
    for r in sorted(W.regions.values(), key=lambda r: r["name"]):
        ps = [p for p in W.places.values() if p["region_id"] == r["id"]]
        gs = [g for p in ps for g in W.gives[p["id"]]]
        cnt = lambda pred: sum(g["count"] for g in gs if pred(g))  # noqa: E731
        fam = Counter(W.kinds[p["place_kind_id"]]["family"] for p in ps)
        dung = sum(1 for p in ps if W.kinds[p["place_kind_id"]]["interior"] in ("dungeon", "cave"))
        L.append(f"| {r['name']} | {cnt(lambda g: g['give_kind_id'] == 'trainer')} | "
                 f"{cnt(lambda g: g['give_kind_id'].startswith('trader-') or g['give_kind_id'] == 'fence')} | "
                 f"{cnt(lambda g: g['give_kind_id'] in ('forge', 'anvil', 'smelter', 'armour-workbench', 'grindstone'))} | "
                 f"{cnt(lambda g: g['give_kind_id'] == 'shrine-blessing')} | {fam.get('ruin', 0) + fam.get('sunken', 0)} | "
                 f"{fam.get('wreck', 0)} | {dung} | {cnt(lambda g: g['give_kind_id'] in rare)} |")
    L += ["", "The notable ones by name:", ""]
    notable = ["unique-item", "follower", "player-home", "spell-tome", "skill-book", "arcane-enchanter", "gold-hoard"]
    for k in notable:
        rows = [(p, g) for p, gs in W.gives.items() for g in gs if g["give_kind_id"] == k]
        if rows:
            L.append(f"- {W.give_kinds[k]['name']}: " + "; ".join(
                f"{W.places[p]['name']} ({g['detail']})" for p, g in sorted(rows, key=lambda t: W.places[t[0]]["name"]))
                + cite(*(f"place_give:{p}/{g['seq']}" for p, g in rows)))
    trainers = sorted([(p, g) for p, gs in W.gives.items() for g in gs if g["give_kind_id"] == "trainer"],
                      key=lambda t: t[1]["detail"])
    L.append("- Trainers: " + "; ".join(f"{g['detail']} at {W.places[p]['name']}" for p, g in trainers) + "."
             + cite("place_give:give_kind=trainer"))
    L += [""]

    # -- every place
    L += ["## Every place", "",
          "| Place | Region | Culture | Kind and size | People | Danger inside | What it gives | Travel | What it is |",
          "|---|---|---|---|---|---|---|---|---|"]
    for p in sorted(W.places.values(), key=lambda p: (W.regions[p["region_id"]]["name"], p["name"])):
        d = W.danger[p["id"]]
        L.append(f"| {cell(p['name'])} | {cell(W.regions[p['region_id']]['name'])} | "
                 f"{cell(W.culture_name(p.get('culture_id')) or SILENT)} | "
                 f"{cell(W.kind_size(p))} | "
                 f"{p['population'] if p.get('population') is not None else SILENT} | "
                 f"{W.dispositions[d['disposition_id']]['label']}, {W.band(d['strength_band_id'])} | "
                 f"{cell('; '.join(W.main_gives(p['id'])) or 'nothing')} | {cell(W.travel_short(p['id']))} | "
                 f"{cell(first_sentence(p.get('summary') or '') or SILENT)} |")
    L += [""]

    # -- gaps
    L += ["## Where the data is silent", "",
          "What a story writer will want and the database does not hold. These are for the lead to research or rule; "
          "the digest never fills them.", ""]
    L += [f"- {g}" for g in gaps(W)]
    L += ["", f"The region files list {digest_hooks} hooks the notes already hold.", ""]
    return "\n".join(L)


# ---------------------------------------------------------------------------------------------------------------
# regions/<region>.md
# ---------------------------------------------------------------------------------------------------------------

def quote(W: World, notes: dict, aspects: tuple, prefix: str) -> str:
    return " ".join(f"{notes[a]}{cite(f'{prefix}/{a}')}" for a in aspects if notes.get(a))


def place_section(W: World, pid: str) -> list[str]:
    p = W.places[pid]
    n = W.pnotes.get(pid, {})
    d = W.danger[pid]
    lw = W.law[pid]
    L = []
    aka = f" (also called {join_and(W.aliases[pid])})" if W.aliases.get(pid) else ""
    head = f"### {p['name']}{aka}"
    cul = W.culture_name(p.get("culture_id"))
    pop = p.get("population")
    ks = W.kind_size(p)
    facts = [f"{sentence_case(article(ks))} {ks}" + (f", sited on {p['siting']}" if p.get("siting") else "")
             + (f", of {cul}" if cul else ", whose culture the data does not say") + "."]
    held = (p.get("held_by") or SILENT).rstrip(".")
    if re.match(r"(A|An|No|Nobody|None)\b", held) or re.match(r"The [a-z]", held):
        held = held[0].lower() + held[1:]
    facts.append(f"In 4E 201 it is {p.get('status') or 'in a state the data does not give'}, held by {held}; "
                 + (f"{plural(pop, 'person lives', 'people live')} there." if pop else "nobody lives there." if pop == 0
                    else f"how many live there {SILENT}."))
    built = ("It is drafted: its place files are in newworld/places/" + pid + "." if pid in W.drafted
             else "It is not built yet.")
    facts.append(built)
    L += [head, "", " ".join(facts) + cite(f"place:{pid}"), ""]
    L += [quote(W, n, ("overview", "present", "people", "history"), f"place_note:{pid}"), ""]
    L += [quote(W, n, ("look", "economy", "faith"), f"place_note:{pid}"), ""]
    # promises
    gs = W.gives[pid]
    if gs:
        L += ["It promises the player: " + "; ".join(W.give_text(g) for g in gs) + "."
              + cite(*(f"place_give:{pid}/{g['seq']}" for g in gs)), ""]
    else:
        L += ["It promises the player nothing in its record." + cite(f"place_give:{pid}"), ""]
    # law, danger, reach
    jail = f", with cells at {W.places[lw['jail_place_id']]['name']}" if lw.get("jail_place_id") else ""
    disp = W.dispositions[d["disposition_id"]]
    tr, tcites = W.travel_long(pid)
    fights = any(g["give_kind_id"].startswith("combat-") for g in gs)
    if d["disposition_id"] in ("hostile", "abandoned") or not pop:
        inside = f"What lives inside is {W.band(d['strength_band_id'], True)}"
    elif fights:
        inside = f"The fights its record sets here are {W.band(d['strength_band_id'], True)}"
    else:
        inside = "Its record sets no fight here"
    L += [f"Law: {W.laws[lw['law_id']]['label'].lower()}{jail}. It meets a visitor as {disp['label'].lower()} ({disp['about'][0].lower() + disp['about'][1:].rstrip('.')}). "
          f"{inside}; the calmest way in crosses {W.band(d['reach_band_id']).lower()} ground; its loot is of the "
          f"{W.band(d['reward_band_id']).lower()} band. "
          + quote(W, n, ("dangers",), f"place_note:{pid}")
          + cite(f"place_law:{pid}", f"place_danger:{pid}"), ""]
    L += [(tr or f"How it is reached: {SILENT}.") + cite(*tcites), ""]
    st, scites = W.source_text(pid)
    L += [st + cite(*scites), ""]
    return L


def region_file(W: World, rid: str) -> tuple[str, int]:
    r = W.regions[rid]
    n = W.rnotes.get(rid, {})
    ps = sorted([p for p in W.places.values() if p["region_id"] == rid],
                key=lambda p: (-(p.get("importance") or 0), -(p.get("population") or 0), p["name"]))
    L = [f"# {r['name']}", ""]
    L += [region_line(W, rid), ""]
    # nature
    L += ["## Its nature", ""]
    rel = []
    if r.get("landform"):
        rel.append(f"The ground is {r['landform'][0].lower() + r['landform'][1:].rstrip('.')}")
    if r.get("elevation_floor_m") is not None and r.get("elevation_summit_m") is not None:
        rel.append(f"dry ground lies about {int(r['elevation_floor_m'])} m above the water and the highest about "
                   f"{int(r['elevation_summit_m'])} m")
    if r.get("wetness") is not None:
        wet = r["wetness"]
        rel.append("the land is mostly standing swamp" if wet >= 0.8 else "the land is wet, with firm rises"
                   if wet >= 0.5 else "the land is mostly dry")
    if r["kind"] == "land" and rid in W.land_share:
        rel.append(f"about {round(100 * W.land_share[rid])}% of it is dry land on the map")
    if rel and r["kind"] == "land":
        L += ["; ".join(rel) + "." + cite(f"region:{rid}", f"cell:region={rid}"), ""]
    L += [quote(W, n, ("landscape", "climate"), f"region_note:{rid}"), ""]
    wl = water_line(W, rid)
    if wl:
        L += [wl + cite(f"water_body:region={rid}"), ""]
    L += [quote(W, n, ("ecology", "look"), f"region_note:{rid}"), ""]
    at = W.atmos.get(rid)
    if at:
        ac = W.atmos_class[at["atmosphere_class_id"]]
        L += [f"Its air is modelled as {ac['name']}, after {ac['analogue'][0].lower() + ac['analogue'][1:]}. {at['why']}"
              + cite(f"region_atmosphere:{rid}", f"atmosphere_class:{ac['id']}"), ""]
    fl = W.q("SELECT b.flora_family_id AS fam, sum(f.weight) AS w FROM region_flora f JOIN flora_base b "
             "ON b.id = f.flora_base_id WHERE f.region_id = ? GROUP BY 1 ORDER BY 2 DESC LIMIT 8", rid)
    if fl:
        L += ["What grows commonest, by share of its plants: "
              + ", ".join(f"{humanise(x['fam'])} ({round(100 * x['w'])}%)" for x in fl) + "."
              + cite(f"region_flora:{rid}"), ""]
    # peoples
    L += ["## Its peoples", ""]
    L += [quote(W, n, ("people",), f"region_note:{rid}"), ""]
    cul = Counter(p.get("culture_id") for p in ps)
    rows = []
    for cid, k in cul.most_common():
        if cid:
            pop = sum(p.get("population") or 0 for p in ps if p.get("culture_id") == cid)
            rows.append(f"{W.cultures[cid]['name']} ({plural(k, 'place')}, about {pop} people)")
    none_n = cul.get(None, 0)
    L += ["The places here belong to " + (join_and(rows) or "no named culture")
          + (f"; {plural(none_n, 'place carries', 'places carry')} no culture in the data" if none_n else "") + "."
          + cite(f"place:region={rid}"), ""]
    # history and the present
    L += ["## Its history, faith, trade and the present", ""]
    for a in ("history", "faith", "economy", "present"):
        if n.get(a):
            L += [n[a] + cite(f"region_note:{rid}/{a}"), ""]
    lc = Counter(W.law[p["id"]]["law_id"] for p in ps)
    law_bits = [f"{v} under {W.laws[k]['label'].lower()}" for k, v in lc.most_common()]
    L += [f"Law here, place by place: {join_and(law_bits)}."
          + cite(f"place_law:region={rid}"), ""]
    # places
    L += ["## Its places", "",
          "Each place below says what its record promises the player, how it is reached, and what it is to be built "
          "from: its allocated source place, quoted as the source mining describes it, and the next most similar "
          "sources. The mining counts a source's buildings, interiors and people and names its piece families; how "
          f"many of each kind of building it holds {SILENT}.", ""]
    for p in ps:
        L += place_section(W, p["id"])
    # dangers
    L += ["## What ranges it", ""]
    L += [quote(W, n, ("dangers",), f"region_note:{rid}"), ""]
    gb = W.ground_bands.get(rid, Counter())
    tot = sum(gb.values()) or 1
    L += [f"Away from roads and towns its baseline is {W.band(r.get('danger_band_id'), True)}. Its ground, cell by cell: "
          + join_and([f"{round(100 * v / tot)}% {W.bands[b]['label'].lower()}"
                      for b, v in sorted(gb.items(), key=lambda t: W.bands[t[0]]["rank"])]) + "."
          + cite(f"region:{rid}", f"cell:region={rid}"), ""]
    hostile = [p for p in ps if W.danger[p["id"]]["disposition_id"] in ("hostile", "abandoned")]
    if hostile:
        L += ["Places that fight a visitor: " + "; ".join(
            f"{p['name']} ({W.dispositions[W.danger[p['id']]['disposition_id']]['label'].lower()}, "
            f"{W.band(W.danger[p['id']]['strength_band_id']).lower()}: {W.danger[p['id']]['disposition_why']})" for p in hostile)
            + "." + cite(*(f"place_danger:{p['id']}" for p in hostile)), ""]
    # hooks
    L += ["## Hooks the data already holds", "",
          "Each is quoted from the notes and cited to its row. The place's own hooks note comes first; then the "
          "tensions, shortages, rivalries, mysteries and losses its other notes state.", ""]
    count = 0
    rh = region_hooks(W, rid)
    if rh:
        L += ["**The region as a whole.**", ""]
        for s, c in rh:
            L.append(f"- {s}{cite(c)}")
            count += 1
        L += [""]
    for p in ps:
        hs = place_hooks(W, p["id"])
        if not hs:
            continue
        L += [f"**{p['name']}.**", ""]
        for s, c in hs:
            L.append(f"- {s}{cite(c)}")
            count += 1
        L += [""]
    return "\n".join(L).replace("\n\n\n", "\n\n"), count


# ---------------------------------------------------------------------------------------------------------------
# people.md
# ---------------------------------------------------------------------------------------------------------------

TITLE = re.compile(r"\b(?:Warden|King|Queen|Vicecanon|Captain|Lord|Lady|Chief|Elder|Matriarch|Patriarch)\s+"
                   r"[A-Z][\w'-]+(?:\s+[A-Z][\w'-]+)?")
HYPHEN_NAME = re.compile(r"\b[A-Z][a-z']+(?:-[A-Z][a-z']+)+\b")


def note_names(W: World) -> list[tuple[str, str, str]]:
    """(name, sentence, row id): names in the place notes that are not a place, an alias, a region, a culture or
    a people's name the data already gives."""
    known_words = set()
    for p in W.places.values():
        known_words |= set(re.findall(r"[\w'-]+", p["name"]))
    for als in W.aliases.values():
        for a in als:
            known_words |= set(re.findall(r"[\w'-]+", a))
    names = " ".join([r["name"] for r in W.regions.values()] + [c["name"] + " " + c["people"] for c in W.cultures.values()])
    known_words |= set(re.findall(r"[\w'-]+", names))
    # A titled phrase the region notes or the culture rows already use as a thing (the Elder Scrolls) is no person.
    things = " ".join([c["about"] for c in W.cultures.values()] + [t for ns in W.rnotes.values() for t in ns.values()])
    out, seen = [], set()
    for pid, ns in sorted(W.pnotes.items()):
        for a, t in sorted(ns.items()):
            for s in sentences(t):
                cands = {re.sub(r"'s?$", "", x) for x in TITLE.findall(s)}
                cands = {x for x in cands if x not in names and x not in things}
                for m in HYPHEN_NAME.findall(s):
                    base = m[:-2] if m.endswith("'s") else m
                    if base not in known_words and base not in things and m.endswith("'s"):
                        cands.add(base)
                for c in cands:
                    key = (c, pid)
                    if key in seen:
                        continue
                    seen.add(key)
                    out.append((c, s, f"place_note:{pid}/{a}"))
    return out


def people_file(W: World) -> str:
    L = ["# Who the new world already names", "",
         f"The person table holds {plural(len(W.people), 'person', 'people')}. They are the people of the drafted "
         "places, given light identities when their place was drafted; their status is 'alive' unless the table says "
         "otherwise. Every other place's people are counted (its population) but not named.", ""]
    by = defaultdict(list)
    for r in W.people:
        by[r["place_id"]].append(r)
    for pid, rows in sorted(by.items(), key=lambda t: W.places[t[0]]["name"]):
        p = W.places[pid]
        L += [f"## {p['name']} ({W.regions[p['region_id']]['name']})", "",
              "| Name | Who | Household | Trade | Means | What the data says of them |", "|---|---|---|---|---|---|"]
        hh_order = defaultdict(list)
        for r in rows:
            hh_order[r.get("household_id") or ""].append(r)
        for hid in sorted(hh_order, key=lambda h: (h == "", h)):
            for r in sorted(hh_order[hid], key=lambda r: (r.get("household_role_id") != "head", r["name"])):
                hh = W.households.get(r.get("household_id") or "")
                head = next((x["name"] for x in hh_order.get(r.get("household_id") or "", [])
                             if x.get("household_role_id") == "head"), None)
                hname = (hh.get("name") or (f"{head}'s" if head else "a household without a head")) if hh else "none"
                notes = " ".join(f"{t}" for a, t in sorted(W.person_notes.get(r["id"], {}).items()))
                who = f"{r['sex']} {W.races[r['race_id']]['name']}, {humanise(r['person_role_id'])}" \
                      + (f", {r['status']}" if r["status"] != "alive" else "")
                L.append(f"| {cell(r['name'])} | {cell(who)} | {cell(hname)}"
                         f"{' (' + humanise(r['household_role_id']) + ')' if r.get('household_role_id') else ''} | "
                         f"{cell(r['trade'])} | {cell(W.pw_bands[r['person_wealth_band_id']]['label'])} | {cell(notes)} |"
                         f"{cite('person:' + r['id'])}")
        L += [""]
    names = note_names(W)
    L += ["## Names the place notes give", "",
          "Names in the places' researched notes that are not a place, a region or a people: a person, a family or a "
          "boat may be meant, and the sentence shows which. None of them has a row in the person table.", "",
          "| Name | Where | The sentence |", "|---|---|---|"]
    for nm, s, c in sorted(names, key=lambda t: (t[0], t[2])):
        pid = c.split(":")[1].split("/")[0]
        L.append(f"| {cell(nm)} | {cell(W.places[pid]['name'])} | {cell(s)} |{cite(c)}")
    L += [""]
    return "\n".join(L)


# ---------------------------------------------------------------------------------------------------------------
# index.md and the whole run
# ---------------------------------------------------------------------------------------------------------------

def db_revision(root: Path = f.ROOT) -> str:
    h = hashlib.sha256()
    data = root / "story" / "data"
    for p in [data / "schema.sql", *sorted((data / "db").glob("*.jsonl"))]:
        h.update(p.name.encode())
        h.update(p.read_bytes())
    return h.hexdigest()[:16]


def index_file(W: World, files: dict[str, int], counts: dict[str, int], today: str) -> str:
    L = ["# The province as the story sees it", "",
         "A digest of the new world's database (Project Tamriel's Black Marsh, built as our own worldspace) for the "
         "people who write its story. It is generated, never edited by hand: change the database or the generator and "
         "regenerate. The other files in this folder (the numbered lore-system notes) are written by hand and are "
         "not part of the digest.", "",
         f"Made {today} from database revision `{db_revision(W.root)}` (the first 16 hex digits of a SHA-256 over "
         "`newworld/story/data/schema.sql` and every `newworld/story/data/db/*.jsonl`, in name order).", "",
         "    python3 -m tools.newworld.story_digest [--out story/design/world]", "",
         "| File | Lines | What it holds |", "|---|---|---|",
         f"| [province.md](province.md) | {files['province.md']} | The province in one read: the regions and what "
         "borders what, water, the travel network, the peoples, power and law, danger, what it offers, a table of "
         "every place, and where the data is silent. |"]
    for name in sorted(k for k in files if k.startswith("regions/")):
        rid = name[len("regions/"):-3]
        L.append(f"| [{name}]({name}) | {files[name]} | {W.regions[rid]['name']}: its nature, peoples, places in "
                 "full (what each promises, what it will be built from, whether it is built), what ranges it, and its "
                 "hooks. |")
    L.append(f"| [people.md](people.md) | {files['people.md']} | Everyone the data names, and names the place notes "
             "give. |")
    L += ["", "How it is made: every sentence is either a note quoted as the database holds it or composed from "
          "rows; the HTML comment after each paragraph names the rows (`place:<id>`, `place_note:<place>/<aspect>`, "
          "`region_note:<region>/<aspect>`, `culture:<id>`, `place_give:<place>/<seq>`, `place_source:<place>/<rank>`, "
          "`travel_route:<from>/<to>/<mode>`, and so on). Hooks are each place's hooks note, then every sentence of its "
          "other notes (and its region's) that names a tension, shortage, rivalry, mystery or loss. Roads are read "
          "from the road graph, place to place through junctions. A place is built when newworld/places/<id>/"
          "place.json exists.", "",
          f"Counts: {counts['places']} places, {counts['regions']} regions, {counts['cultures']} cultures, "
          f"{counts['hooks']} hooks, {counts['people']} named people.", ""]
    return "\n".join(L)


def generate(out: Path = OUT, root: Path = f.ROOT, places_dir: Path = PLACES_DIR,
             today: str | None = None) -> dict[str, int]:
    W = World(root, places_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "regions").mkdir(exist_ok=True)
    files: dict[str, int] = {}
    hooks = 0
    texts = {}
    for rid in W.regions:
        t, k = region_file(W, rid)
        hooks += k
        texts[f"regions/{rid}.md"] = t
    texts["province.md"] = province(W, hooks)
    texts["people.md"] = people_file(W)
    for name, t in texts.items():
        files[name] = t.count("\n") + 1
    counts = {"places": len(W.places), "regions": len(W.regions), "cultures": len(W.cultures), "hooks": hooks,
              "people": len(W.people)}
    texts["index.md"] = index_file(W, files, counts, today or datetime.date.today().isoformat())
    for stale in (out / "regions").glob("*.md"):
        if f"regions/{stale.name}" not in texts:
            stale.unlink()
    for name, t in texts.items():
        (out / name).write_text(t.rstrip("\n") + "\n", encoding="utf-8")
    return counts


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", default=str(OUT.relative_to(REPO)))
    a = ap.parse_args(argv)
    out = Path(a.out)
    if not out.is_absolute():
        out = REPO / out
    c = generate(out)
    print(f"places {c['places']}, regions {c['regions']}, cultures {c['cultures']}, hooks {c['hooks']}, "
          f"people {c['people']} -> {out.relative_to(REPO) if out.is_relative_to(REPO) else out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
