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
from tools.argonia_world.vegetation import rocks

PICK = {"canopy": 12, "emergent": 6, "gallery": 6, "mangrove": 4, "palm": 8, "shrub": 12, "aquatic": 8,
        "mushroom": 8, "deadwood": 5, "rock": 8}
CORE = 3
FAUNA = "lore topics/fauna-hazards.md:92-95 (Flora: cypress, mangrove, bamboo, palms, ferns, lucan mold)"
AUDIT = "docs/design/research/vegetation/regional-variety-audit-2026-09-08.md"
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
COAST = ("coastal-lagoon", "tidal-delta")
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
# rocks: the share of the OBND height below the ground (rock-placement-rules.md rule 1: boulders p50 -1.6 m on a
# ~4 m RockL01 = 0.40; small -0.26 m of ~0.7 m = 0.35; cliff shells -4..-12 m pushed into the hill = 0.25 of ~36 m)
SINK_BOULDER, SINK_CLIFF = 0.38, 0.25
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


def admits(eco: str, f) -> bool:
    t = tags(f)
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
    """role -> usable forms (a mod supplies the mesh, an OBND known), BM&V first, then most placed by their mod."""
    out = defaultdict(list)
    rows = w.query("SELECT * FROM object_form WHERE mesh_source <> 'vanilla' AND bound_z1 IS NOT NULL "
                   "AND bound_z1 > bound_z0")
    for r in sorted(rows, key=lambda r: (r["mod"] != "bmv", -(r["placed_by_mod"] or 0), r["form_key"])):
        if r["role_id"] == "rock" and r["mesh_source"] in VANILLA_SHAPE:
            continue  # a vanilla rock's shape under another texture is still a vanilla rock (1.15 §e.2)
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
