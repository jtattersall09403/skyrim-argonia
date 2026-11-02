"""The region object lists from the Black Marsh mods' forms (1.15 §e.1): `land_region_object` and `vegetation_form`.

Each region (a packet x an eco class, regions/classify.py) gets, per role, the role's density mixed over its old
region classes by cell share (`region_class_role`, the imported flora palette) or, for a role the palette never had
(mushrooms, aquatic plants), the eco class's own (EXTRA). The role's density is split over up to PICK forms of that
role: the forms the eco class admits (AFFINITY), BM&V's first and then by how often their own mod places them; the
first CORE are every region's, the rest rotate by the packet so two packets of one eco class differ (between-region
variety) while each list holds several forms per role (within-region variety). A form whose mesh no mod supplies
(`mesh_source = 'vanilla'`) is never listed. Every row's `why` cites the dossier or research line that grounds the
role in that ecology (decision 0032).
"""
from __future__ import annotations

import zlib
from collections import defaultdict

from tools.argonia_world import skyrim_units as su
from tools.argonia_world.vegetation import forms, rocks

PICK = {"canopy": 12, "emergent": 6, "gallery": 6, "mangrove": 4, "palm": 8, "shrub": 12, "aquatic": 8,
        "mushroom": 8, "deadwood": 5, "rock": 8}
CORE = 3
FAUNA = "lore topics/fauna-hazards.md:92-95 (Flora: cypress, mangrove, bamboo, palms, ferns, lucan mold)"
AUDIT = "research/vegetation/regional-variety-audit-2026-09-08.md"
ROCKS = "docs/design/research/vegetation/rock-placement-rules.md rule 1"
# eco class -> (the ecology's grounding, {role: why})
WHY = {
    "coastal-lagoon": ("lore regions/murkmire.md:23 (the mangrove wall); " + AUDIT + " row 4 (strand "
                       "palms landward of the mangrove)", {}),
    "tidal-delta": ("lore regions/waters.md:31 (a river mouth screened by mangroves); " + AUDIT +
                    " row 3", {}),
    "flooded-forest": ("lore regions/blackwood-and-gloommire.md:34 (reeds to the chin); " + FAUNA, {}),
    "interior-swamp": (AUDIT + " row 7; " + FAUNA, {}),
    "rootland": (AUDIT + " row 6 (giant fungus landmarks, tall mushroom stalks); docs/owner-brief.md 2026-11-01 "
                 "(deep-marsh strangeness from flora variety, giant mushrooms)", {}),
    "deep-sink-basin": ("docs/owner-brief.md 2026-11-01 (giant mushrooms in the deep marsh); " + AUDIT + " row 12 "
                        "(lily pads on standing water)", {}),
    "deep-river-corridor": (AUDIT + " row 5 (a river wall of tall trees); lore regions/waters.md:28",
                            {}),
    "northern-transition": (AUDIT + " row 1 (the north 'more temperate', the only rocky ground); " + ROCKS, {}),
    "western-frontier": ("lore regions/blackwood-and-gloommire.md:13-14 (steep, lightly forested "
                         "hills); " + ROCKS, {}),
}
DEEP = ("rootland", "deep-sink-basin", "interior-swamp", "flooded-forest")
UPLAND = ("northern-transition", "western-frontier")
# Upland trees stand on any dry ground. The marsh palette bounds a tree to 6 m above the nearest water level (its
# roots in the wet); in the hills that level is the sea's (0 m) and the ground stands 40-95 m over it, so every tree
# was refused there (cells (-12,63), (-11,63): 0 trees, 145 shrubs) while the shrubs, which carry no such bound, were
# not. Skyrim.esm's field (10 trees a cell, skyrim-does-it-this-way.md section 6) puts trees on hill and flat alike.
UPLAND_DRY = ("canopy", "emergent", "palm", "gallery")
# ... and the marsh palette's tree densities (BM&V lowland) put the dry hills at 20.8 trees a cell on the province
# (vanilla's field 10, band 2.5-15, "lightly forested", blackwood-and-gloommire.md:13-14): halved, a measured ratio
UPLAND_TREE_SCALE = 0.5
COAST = ("coastal-lagoon", "tidal-delta")
# Marsh trees (session 6, golden rule 0034): Skyrim.esm's Morthal-marsh trees (159 cells with their own water level,
# 1,465 TREE refs) stand p5 -0.02, p10 0.17, p50 2.0, p90 4.8, p99 8.8 m above their cell's water, 7.5 % with the
# ground under the waterline, their bases p10 0.4 m under the ground; Riften shore p50 4.4 m, p90 13 m. So a tree
# is placed from the water's edge to 6 m above it (the old palette's band, -1.5..1.0, left only the 1-2 m ground
# of our relief); the owner's vibe board (vibe-01/05/07) puts mangrove and cypress trunks IN the water, so those
# forms may stand to 1.5 m under it. (water min/max: depth over the ground, minus the height above the table.)
MARSH = DEEP + COAST + ("deep-river-corridor",)
MARSH_TREE = {"canopy": (-6.0, 1.2), "emergent": (-6.0, 1.2), "palm": (-6.0, 1.2), "gallery": (-6.0, 1.2)}
# ... and a marsh class's palette often has no canopy at all (dunmer-north coastal-lagoon: deadwood only; palms
# 0.17 a ha elsewhere) against Skyrim.esm's marsh 18 trees a cell (52 a ha, skyrim-does-it-this-way.md section 6):
# the canopy role tops the class's trees up to this many a ha (as placed, before the posture and slope refuse some)
MARSH_TREE_HA = 52.0
# ... per class, scaled by what the window measurements showed the ground refuses: a tree stands in at most 2 m of
# water, and a lagoon or sink cell is mostly deeper (window means before the scale: lagoon 5.4, sink 4.5-6.6,
# delta 34 trees a cell against the band 9-27)
MARSH_TREE_HA_BY = {"coastal-lagoon": 170.0, "deep-sink-basin": 90.0, "tidal-delta": 68.0, "rootland": 100.0, "deep-river-corridor": 80.0}
# ... and per region (id "packet.class"), where the new ground leaves a region's cells mostly deeper than a tree stands
# in (session 9: calibrated on the check's own countable cells, trees standing to the marsh posture's 1.2-2 m only:
# lagoon means 19-25 a cell against the band 9-27)
MARSH_TREE_HA_REGION = {"mercantile-coast.coastal-lagoon": 250.0, "saxhleel-coast.coastal-lagoon": 130.0,
                        "imperial-penal-south.coastal-lagoon": 199.0, "dunmer-north.coastal-lagoon": 297.0,
                        "dunmer-north.deep-sink-basin": 153.0}
# ONE definition of a countable cell, for the planner's targets here and the check's band (checks.py): a cell counts
# toward its tree band when a quarter of its vertices lie within 2 m under the water (the cypress band's depth) or
# above it. A cell of open water (a lagoon's sea floor) is no marsh cell: Skyrim.esm's marsh cells have ground to
# stand on, and 5.8% of its trees stand in water at all (skyrim-does-it-this-way.md section 6), so the targets
# below are trees per standable hectare-share, never a depth the trees stand in.
STAND_DEPTH_M, STAND_SHARE = 2.0, 0.25


def countable(ground, level) -> bool:
    """True when the cell with these vertex heights and water levels (m) is a standable marsh cell."""
    return bool((ground >= level - STAND_DEPTH_M).mean() >= STAND_SHARE)


TREE_ROLES = ("canopy", "emergent", "palm", "mangrove", "gallery")
# Skyrim.esm trees per cell by the cell's dominant ground (docs/research/2026-11-01/skyrim-does-it-this-way.md
# section 6): (mean, p90 or None); the rest of the audit's table is not needed for our classes
TREE_BANDS = {"forest": (31.0, 53.0), "marsh": (18.0, 36.0), "field": (10.0, None)}
# our eco classes mapped to a band: the tall-tree river wall and the flooded and interior swamp forests are forest;
# the open wet ground (sinks, lagoons, deltas) is marsh; the lightly forested hills and the rocky north are field
# (lore regions/blackwood-and-gloommire.md:13-14)
ECO_BAND = {"deep-river-corridor": "forest", "flooded-forest": "forest", "interior-swamp": "forest",
            "rootland": "forest", "deep-sink-basin": "marsh", "coastal-lagoon": "marsh", "tidal-delta": "marsh",
            "northern-transition": "field", "western-frontier": "field"}
BAND_TREE_ROLES = ("canopy", "emergent", "palm", "mangrove", "gallery", "cliff-tree")  # what the band counts
BAND_MIN_CELLS = 10  # a region of fewer standable cells is a handful of cells of one coast, not a stand: reported only
BAND_LO, BAND_HI = 0.5, 1.5  # a region's mean trees per cell within these multiples of its band's mean
BAND_LO_FIELD = 0.25  # the hills are "lightly forested", the rocky north rock-dominated: down to a quarter of the mean


def band_limits(band: str) -> tuple[float, float, float]:
    """(lower bound, mean, upper bound) of trees per countable cell for a band."""
    m = TREE_BANDS[band][0]
    return (BAND_LO_FIELD if band == "field" else BAND_LO) * m, m, BAND_HI * m


IN_WATER_TREE = (-6.0, 2.0)  # mangrove and cypress: trunks and roots in the water, and on the bank
IN_WATER_NAMES = ("mangrove", "cypress")
# role -> eco classes that admit it (None: all)
ROLE_ECO = {"mangrove": COAST + ("deep-river-corridor",), "palm": COAST + UPLAND + ("deep-river-corridor",),
            "rock": UPLAND + ("deep-river-corridor",), "mushroom": DEEP + ("deep-river-corridor",)}
# eco class -> {role: (per ha, clustering, radius m, max slope, water min, water max)} for roles the palette lacks
EXTRA = {
    "rootland": {"mushroom": (9.0, 3, 8.0, 30, -4.0, 0.4), "aquatic": (20.0, 6, 5.0, 10, 0.1, 1.2)},
    "deep-sink-basin": {"mushroom": (7.0, 3, 8.0, 30, -4.0, 0.4), "aquatic": (60.0, 6, 6.0, 10, 0.1, 1.5),
                        "gallery": (40.0, 4, 6.0, 38, -4.0, 0.8), "emergent": (1.5, 1, 0.0, 30, -6.0, 1.0),
                        "deadwood": (2.0, 2, 12.0, 35, None, None)},
    "interior-swamp": {"mushroom": (5.0, 3, 8.0, 30, -4.0, 0.4), "aquatic": (40.0, 6, 5.0, 10, 0.1, 1.2)},
    "flooded-forest": {"mushroom": (3.0, 3, 8.0, 30, -4.0, 0.4), "aquatic": (50.0, 6, 5.0, 10, 0.1, 1.5)},
    "deep-river-corridor": {"mushroom": (1.0, 2, 6.0, 30, -4.0, 0.3), "aquatic": (30.0, 6, 5.0, 10, 0.1, 1.2)},
    "coastal-lagoon": {"aquatic": (25.0, 6, 6.0, 10, 0.1, 1.2)},
    "tidal-delta": {"aquatic": (40.0, 6, 5.0, 10, 0.1, 1.2)},
    "northern-transition": {"rock": (6.0, 3, 9.0, 70, -60.0, 0.2)},
    "western-frontier": {"rock": (5.0, 3, 9.0, 70, -60.0, 0.2)},
}
# rocks a hectare, the research's target (the palette's border-mountains 516/ha was the old renderer's scale):
# rock-placement-rules.md rule 4, Clark-Evans R 0.32-0.58 at a mean nearest neighbour of 7-15 m gives
# (R / 2nn)^2 = 3-7 a ha on rocky ground; 16f-ledger.md:109 3 a ha on firm lowland
ROCK_HA = {"northern-transition": 6.0, "western-frontier": 5.0, "deep-river-corridor": 3.0}
BOULDER_SLOPE = 45  # rule 3: boulders and piles stand on 10-35 deg (p25-p75); the gate is p75 + 10
CLIFFS, CLIFF_HA = 2, 0.4  # cliff shells: at most two forms a list, each this sparse (a landmark face, not a field)
SEA = ("kelp", "coral", "seaweed")  # sea-floor aquatic: only on the coast, in deeper water
SEA_POSTURE = (1.5, 25.0)
GIANT_M = 6.0  # a mushroom taller than this is a giant (landmark) one: deep marsh only, sparse
CLIFF_M = 12.0  # a rock taller than this is a cliff shell: uplands, steep ground only
SCALE = {"canopy": (0.8, 1.2), "emergent": (0.9, 1.3), "mushroom": (0.8, 1.3), "rock": (0.6, 1.25),
         "aquatic": (0.8, 1.2), "palm": (0.85, 1.2), "mangrove": (0.85, 1.15), "gallery": (0.85, 1.15),
         "shrub": (0.8, 1.2), "deadwood": (0.8, 1.2), "cliff-tree": (0.8, 1.2)}
# rocks: the share of the OBND height below the ground, Skyrim.esm's own medians (docs/research/2026-11-01/
# skyrim-does-it-this-way.md section 5, decision 0034): boulders and rock piles 0.5 (p10-p90 0.1-0.8), cliff and
# mountain shells 0.7 (0.4-0.9); ours were 0.38 and 0.25
SINK_BOULDER, SINK_CLIFF = 0.5, 0.7
# the share of boulders that stand upright instead of conforming to the slope (vanilla 26 %, same section 5);
# chosen per stem by the position-seeded draw (place.candidates "up"); shells always conform
UPRIGHT_BOULDER = 0.25
VANILLA_SHAPE = ("laid:tropical-skyrim-sse",)  # Tropical Skyrim's meshes at vanilla paths: vanilla geometry


def height_m(f) -> float:
    return ((f["bound_z1"] or 0) - (f["bound_z0"] or 0)) / su.UNITS_PER_METRE


def tags(f) -> set[str]:
    s = f"{f['edid']} {f['model']}".lower()
    out = set()
    if any(x in s for x in SEA):
        out.add("sea")
    if f["role_id"] == "mushroom" and height_m(f) > GIANT_M:
        out.add("giant")
    if f["role_id"] == "rock" and height_m(f) > CLIFF_M:
        out.add("cliff")
    return out


def sink_frac(f) -> float:
    if f["role_id"] != "rock":
        return 0.0
    return SINK_CLIFF if "cliff" in tags(f) else SINK_BOULDER


def upright_share(sink: float | None) -> float:
    """The share of a rock form's stems that stand upright: boulders (the boulder sink), never shells."""
    return UPRIGHT_BOULDER if sink == SINK_BOULDER else 0.0


# Session 7 (round-1 session 1b, northern-transition stills 22-25: tall drooping conifer-like trunks with tiered
# hanging fronds, weeping birch-like columns, read as Nordic; decision 0006): the hills are "more temperate" and
# "lightly forested" (lore regions/blackwood-and-gloommire.md:13-14; AUDIT row 1), so their trees are broadleaf: no
# cypress (tiered, drooping boughs), willow and hanging moss (weeping), birch, poplar, juniper, bristlecone and
# redwood (boreal or columnar). (Building pieces are no flora anywhere: forms.EXCLUDE.)
UPLAND_DENY = ("cypress", "willow", "hangingmoss", "birch", "poplar", "juniper", "bristlecone", "redwood", "salix")


def admits(eco: str, f) -> bool:
    t = tags(f)
    if eco in UPLAND and f["role_id"] in TREE_ROLES:
        s = f"{f['edid']} {f['model']}".lower()
        if any(n in s for n in UPLAND_DENY):
            return False
    if "sea" in t and eco not in COAST:
        return False
    if "giant" in t and eco not in DEEP:
        return False
    if "cliff" in t and eco not in UPLAND:
        return False
    fam = rocks.family(f["model"]) if f["role_id"] == "rock" else None
    if fam and eco not in rocks.FAMILY_ECO[fam]:
        return False  # our own BM&V rock forms vary by region (rocks.py's families)
    return eco in ROLE_ECO.get(f["role_id"], (eco,))


def usable(w) -> dict[str, list]:
    """role -> usable forms (a mod supplies the mesh and every diffuse it names, an OBND known; a rock or tree with
    a measured body that is not climbable, or a rock never measured, dropped: forms.climbable), BM&V first, then most placed by their mod."""
    from tools.argonia_world.vegetation import mesh_textures
    out = defaultdict(list)
    man = mesh_textures.load()
    bare = mesh_textures.untextured(man)  # a diffuse no row lays: Skyrim's missing texture
    bare_forms = mesh_textures.untextured_forms(man)  # a MODS diffuse no row lays, not overridden (lane 1.15-r3-mods)
    rows = w.query("SELECT * FROM object_form WHERE mesh_source <> 'vanilla' AND bound_z1 IS NOT NULL "
                   "AND bound_z1 > bound_z0")
    for r in sorted(rows, key=lambda r: (r["mod"] != "bmv", -(r["placed_by_mod"] or 0), r["form_key"])):
        if forms.role_of(r["edid"], r["model"]) is None:
            continue  # excluded since the inventory was read (forms.EXCLUDE: a building piece is not flora)
        if mesh_textures.mesh_path(r["model"]) in bare or r["form_key"] in bare_forms:
            continue  # round 1's white plants and pale rocks (lane 1.15-r2-textures)
        if r["role_id"] == "rock" and r["mesh_source"] in VANILLA_SHAPE:
            continue  # a vanilla rock's shape under another texture is still a vanilla rock (1.15 §e.2)
        if r["collision_layer"] is not None or r["role_id"] == "rock":
            if not forms.climbable(r["role_id"], r["collision_layer"], r["collision_mass"]):
                continue  # no Static/Terrain/Trees mass-0 body: Free Climb cannot attach, the player cannot stand
        out[r["role_id"]].append(r)
    return out


def pick(pool: list, n: int, packet: str) -> list:
    if len(pool) <= n:
        return list(pool)
    if n <= CORE:  # too few to hold a core: a packet's own rotation
        k = zlib.crc32(packet.encode()) % len(pool)
        return (pool[k:] + pool[:k])[:n]
    core, rest = pool[:CORE], pool[CORE:]
    k = zlib.crc32(packet.encode()) % len(rest)
    rest = rest[k:] + rest[:k]
    return core + rest[:n - CORE]


def role_mix(w, rid: str) -> dict[str, dict]:
    """role -> mixed palette numbers over the region's class shares (regions/classify.object_list's mixing)."""
    shares = {r["region_class_id"]: r["cells"] for r in w.query(
        "SELECT region_class_id, cells FROM land_region_class_share WHERE land_region_id = ?", rid)}
    total = sum(shares.values()) or 1
    acc = defaultdict(lambda: {"per_ha": 0.0, "clump": 0.0, "rad": 0.0, "slope": 0.0, "wmin": None, "wmax": None})
    for rc, n in shares.items():
        for r in w.query("SELECT * FROM region_class_role WHERE region_class_id = ?", rc):
            a = acc[r["role_id"]]
            q = n / total * r["per_ha"]
            a["per_ha"] += q
            a["clump"] += q * (r["clump_median"] or 1)
            a["rad"] += q * (r["clump_radius_m"] or 0)
            a["slope"] = max(a["slope"], r["slope_max_deg"] or 35)
            if r["water_min_m"] is not None:
                a["wmin"] = r["water_min_m"] if a["wmin"] is None else min(a["wmin"], r["water_min_m"])
                a["wmax"] = r["water_max_m"] if a["wmax"] is None else max(a["wmax"], r["water_max_m"])
    out = {}
    for role, a in acc.items():
        if a["per_ha"] >= 0.05:
            q = a["per_ha"]
            out[role] = {"per_ha": q, "clust": max(1, min(255, round(a["clump"] / q))), "rad": round(a["rad"] / q, 2),
                         "slope": int(round(a["slope"])), "wmin": a["wmin"], "wmax": a["wmax"]}
    return out


def build(w) -> dict:
    """Write land_region_object and vegetation_form; returns {region: {mod: forms}}."""
    for t in ("land_region_object", "vegetation_form"):
        w.con.execute(f'DELETE FROM "{t}"')
        w.dirty.add(t)
    pool = usable(w)
    used: dict[str, dict] = {}
    report: dict[str, dict] = {}
    for reg in w.query("SELECT id, region_id, eco_class_id FROM land_region WHERE border = 0 ORDER BY id"):
        rid, packet, eco = reg["id"], reg["region_id"], reg["eco_class_id"]
        mix = role_mix(w, rid)
        for role, (q, cl, rad, sl, lo, hi) in EXTRA.get(eco, {}).items():
            mix.setdefault(role, {"per_ha": q, "clust": cl, "rad": rad, "slope": sl, "wmin": lo, "wmax": hi})
        if eco in MARSH:
            # roles the palette lists but no form of ours serves (the delta's mangrove, 650 a ha) count for nothing
            real = [r for r in TREE_ROLES if r in mix and any(admits(eco, f) for f in pool.get(r, ()))]
            have = sum(mix[r]["per_ha"] for r in real)
            want = MARSH_TREE_HA_REGION.get(rid) or MARSH_TREE_HA_BY.get(eco, MARSH_TREE_HA)
            for r in real:  # a slope bound of 14 degrees (the delta's) refused the coast's banks: trees take 38
                mix[r]["slope"] = max(mix[r]["slope"], 38)
            if have < want:
                c = mix.setdefault("canopy", {"per_ha": 0.0, "clust": 3, "rad": 8.0, "slope": 30, "wmin": None, "wmax": None})
                c["per_ha"] += want - have
            elif eco in MARSH_TREE_HA_BY or rid in MARSH_TREE_HA_REGION:  # the palette's own trees overshoot: scaled down to the class's number
                for r in real:
                    mix[r]["per_ha"] *= want / have
        if "rock" in mix and eco in ROCK_HA:
            mix["rock"]["per_ha"] = ROCK_HA[eco]
        ground, _ = WHY[eco]
        counts: dict[str, int] = defaultdict(int)
        for role in sorted(mix):
            m = mix[role]
            ok = [f for f in pool.get(role, ()) if admits(eco, f)]
            forms = pick([f for f in ok if "cliff" not in tags(f)], PICK.get(role, 4), packet)
            wts = [2.0 if i < CORE else 1.0 for i in range(len(forms))]
            cliffs = pick([f for f in ok if "cliff" in tags(f)], CLIFFS, packet)
            forms, wts = forms + cliffs, wts + [0.0] * len(cliffs)
            if not forms:
                continue
            for f, wt in zip(forms, wts):
                t = tags(f)
                q = m["per_ha"] * wt / (sum(wts) or 1.0)
                lo, hi, mn, conform = m["wmin"], m["wmax"], 0, role == "rock"
                if eco in UPLAND and role in UPLAND_DRY:
                    lo, q = None, q * UPLAND_TREE_SCALE  # session 5: see UPLAND_DRY
                if eco in MARSH and role in MARSH_TREE:
                    lo, hi = MARSH_TREE[role]
                if eco in MARSH and (role == "mangrove" or (role in MARSH_TREE and any(
                        n in f["model"].lower() or n in f["edid"].lower() for n in IN_WATER_NAMES))):
                    lo, hi = IN_WATER_TREE
                if "sea" in t:
                    lo, hi = SEA_POSTURE
                mx = m["slope"]
                if role == "rock":  # rock-placement-rules.md rule 5: only wet rocks stand in water; ours are dry
                    lo, hi = None, None
                    mx = 70 if "cliff" in t else BOULDER_SLOPE
                    conform = "cliff" not in t  # rule 2: a cliff shell takes ~0.12 of the pitch: buried upright
                if "giant" in t:
                    q = min(q, 0.6)  # a landmark, not a stand
                if "cliff" in t:
                    q, mn = CLIFF_HA, 28  # rock-placement-rules.md rule 3: cliff pieces need >= 28 deg
                if q < 0.01:
                    continue
                why = (f"{role} in {eco}: {ground}"
                       + (" [giant mushroom: deep marsh only]" if "giant" in t else "")
                       + (" [cliff shell: uplands, steep ground]" if "cliff" in t else ""))
                w.insert("land_region_object", land_region_id=rid, form_key=f["form_key"],
                         density_per_ha=round(q, 4), clustering=m["clust"] if m["rad"] >= 1 else 1,
                         min_slope_deg=mn, max_slope_deg=max(mn, mx), min_height_m=None,
                         max_height_m=None, radius_m=m["rad"], water_min_m=lo, water_max_m=hi, conform=conform,
                         why=why)
                used[f["form_key"]] = f
                counts[f["mod"]] += 1
        report[rid] = dict(counts)
    for fk, f in sorted(used.items()):
        lo, hi = SCALE.get(f["role_id"], (0.8, 1.2))
        if "cliff" in tags(f):
            lo, hi = 0.5, 0.9
        sf = sink_frac(f)
        w.insert("vegetation_form", form_key=fk, scale_min=lo, scale_max=hi, sink_frac=sf,
                 why=f"1.15 veg: the {f['role_id']} role's range (ours; the L4 stills judge it)"
                     + (f"; sunk {sf:.2f} of its OBND height ({ROCKS})" if sf else ""))
    return report


def bmv_keep(w) -> list[str]:
    """The BM&V mesh paths the lists use (the dependency row's keep list must name them, so stack.py lays them)."""
    from tools.argonia_world.vegetation.forms import mesh_key
    rows = w.query("SELECT DISTINCT f.model FROM land_region_object o JOIN object_form f USING (form_key) "
                   "WHERE f.mesh_source = 'bmv' ORDER BY f.model")
    return sorted({mesh_key(r["model"]) for r in rows})
