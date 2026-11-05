"""Named checks: the world's rules that SQL constraints cannot state (decision 0030 §3).

Each check reads the loaded world through db.World and returns one line per violation. The load itself (types,
keys, foreign keys, CHECKs) is the rest of the integrity gate; a rule goes here only when the schema cannot hold it:
a column whose target table depends on another column or on the value's prefix, and the vocabulary's argument
shapes, which are prose in `condition_term.args`.
"""
from __future__ import annotations

import re
from typing import Callable

CHECKS: dict[str, tuple[Callable, tuple[str, ...]]] = {}


def check(name: str, *tables: str):
    """Register a named check over `tables`; it runs on a world whose schema has them all (a test's small schema
    skips it)."""
    def deco(fn):
        CHECKS[name] = (fn, tables)
        return fn
    return deco


def run(w, only: list[str] | None = None) -> list[str]:
    out = []
    for name, (fn, tables) in CHECKS.items():
        if (only and name not in only) or not set(tables) <= set(w.tables):
            continue
        out += [f"[{name}] {e}" for e in fn(w)]
    return out


# -- polymorphic references ------------------------------------------------------------------------------------
LOCK_OWNER = {"person": "npc", "household": "npc", "faction": "faction"}  # a household is named by its head


@check("lock-owner", "lock", "npc", "faction")
def lock_owner(w) -> list[str]:
    """lock.owner_id names a row of the table its owner_kind says (person, household -> npc; faction)."""
    out = []
    for r in w.query('SELECT id, owner_kind, owner_id FROM "lock" ORDER BY id'):
        table = LOCK_OWNER.get(r["owner_kind"])
        if table is None:
            out.append(f"lock {r['id']}: owner_kind {r['owner_kind']!r} has no owner table in checks.LOCK_OWNER")
        elif w.get(table, r["owner_id"]) is None:
            out.append(f"lock {r['id']}: owner {r['owner_kind']} {r['owner_id']!r} has no row in {table}")
    return out


@check("person-disposition", "npc", "npc_kind")
def person_disposition(w) -> list[str]:
    """Every person has a starting disposition (npc.base_disposition); a creature has none."""
    out = [f"npc {r[0]}: a person with no base_disposition"
           for r in w.query("SELECT id FROM npc WHERE kind = 'person' AND base_disposition IS NULL ORDER BY id")]
    out += [f"npc {r[0]}: a creature carries a base_disposition"
            for r in w.query("SELECT id FROM npc WHERE kind != 'person' AND base_disposition IS NOT NULL ORDER BY id")]
    return out


@check("journal-grounding", "journal_entry_grounding", "fact", "promise")
def journal_grounding(w) -> list[str]:
    """journal_entry_grounding.value is a fact id or a promise id."""
    return [f"journal_entry {r[0]}: groundedIn {r[1]!r} is neither a fact nor a promise"
            for r in w.query("SELECT journal_entry_id, value FROM journal_entry_grounding g "
                             "WHERE value NOT IN (SELECT id FROM fact) AND value NOT IN (SELECT id FROM promise) "
                             "ORDER BY 1, ord")]


@check("quest-topic", "quest_topic", "quest_essential_topic", "topic")
def quest_topic(w) -> list[str]:
    """A quest's topic is a topic row, or is marked `new` (2.5 adds it); an essential topic is a topic row or one
    of the quest's `new` topics (quest-record.md, field 12)."""
    out = [f"quest {r[0]}: topic {r[1]!r} is not a topic row and is not marked new"
           for r in w.query("SELECT quest_id, id FROM quest_topic WHERE NOT coalesce(new, 0) "
                            "AND id NOT IN (SELECT id FROM topic) ORDER BY 1, ord")]
    out += [f"quest {r[0]}: essential topic {r[1]!r} is neither a topic row nor one of the quest's new topics"
            for r in w.query("SELECT quest_id, value FROM quest_essential_topic e "
                             "WHERE value NOT IN (SELECT id FROM topic) AND NOT EXISTS (SELECT 1 FROM quest_topic t "
                             "WHERE t.quest_id = e.quest_id AND t.id = e.value AND t.new) ORDER BY 1, ord")]
    return out


# -- the vocabulary's argument shapes --------------------------------------------------------------------------
def _split(args: str) -> list[str]:
    """Top-level comma parts of an args shape (commas inside {...} or (...) belong to their part)."""
    parts, depth, cur = [], 0, ""
    for ch in args:
        depth += ch in "{(" and 1 or ch in "})" and -1 or 0
        if ch == "," and depth == 0:
            parts.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip():
        parts.append(cur.strip())
    return parts


DEFAULTABLE = re.compile(r"(`bool`|\bbool|\bcount)$")   # a trailing flag (true) or count (1) may be left out


def arity(args: str | None) -> tuple[int, int]:
    """(fewest, most) arguments an args shape allows. `none` is no argument; `a *or* b + c` takes one or two;
    `optional ...` may be left out; a trailing `bool` or count may be left out (flag(x) is flag(x, true),
    hasItem(x) is hasItem(x, 1): how every authored record writes them)."""
    if not args or args.strip() == "none":
        return 0, 0
    lo = hi = 0
    parts = _split(re.sub(r"\([^)]*\)", "", args))
    for i, part in enumerate(parts):
        alts = [a.count("+") + 1 for a in re.split(r"\*or\*", part)]
        a_lo, a_hi = min(alts), max(alts)
        if part.startswith("optional"):
            a_lo = 0
        hi += a_hi
        lo += a_lo
    # trailing defaultable parts lower the minimum
    for part in reversed(parts):
        if DEFAULTABLE.search(part.strip()) and not part.startswith("optional"):
            lo -= 1
        else:
            break
    return lo, hi


@check("term-arity", "condition_term", "condition", "condition_arg", "action", "action_arg")
def term_arity(w) -> list[str]:
    """Every condition node and action has the argument count its vocabulary term's shape allows; a combinator
    has no arguments and its children (all/any: at least one; not: exactly one)."""
    shapes = {r["id"]: (r["kind"], arity(r["args"]) if r["kind"] != "combinator" else (0, 0))
              for r in w.query("SELECT id, kind, args FROM condition_term")}
    out = []
    for r in w.query("SELECT c.id, c.term, coalesce(a.n, 0), coalesce(k.n, 0) FROM condition c "
                     "LEFT JOIN (SELECT condition_id, count(*) n FROM condition_arg GROUP BY 1) a ON a.condition_id = c.id "
                     "LEFT JOIN (SELECT parent_id, count(*) n FROM condition WHERE parent_id IS NOT NULL GROUP BY 1) k "
                     "ON k.parent_id = c.id ORDER BY c.id"):
        cid, term, n, kids = r
        kind, (lo, hi) = shapes[term]
        if kind == "action":
            out.append(f"condition {cid}: {term} is an action verb, not a predicate")
        elif not lo <= n <= hi:
            out.append(f"condition {cid}: {term} takes {lo}-{hi} argument(s), has {n}")
        if kind == "combinator" and not (kids == 1 if term == "not" else kids >= 1):
            out.append(f"condition {cid}: {term} has {kids} child condition(s)")
        if kind != "combinator" and kids:
            out.append(f"condition {cid}: predicate {term} has {kids} child condition(s)")
    for r in w.query("SELECT a.list_id, a.ord, a.term, coalesce(x.n, 0) FROM action a LEFT JOIN "
                     "(SELECT list_id, ord, count(*) n FROM action_arg GROUP BY 1, 2) x "
                     "ON x.list_id = a.list_id AND x.ord = a.ord ORDER BY 1, 2"):
        lid, ord_, term, n = r
        kind, (lo, hi) = shapes[term]
        if kind != "action":
            out.append(f"action {lid}[{ord_}]: {term} is a {kind}, not an action verb")
        elif not lo <= n <= hi:
            out.append(f"action {lid}[{ord_}]: {term} takes {lo}-{hi} argument(s), has {n}")
    return out


@check("season-is", "condition", "condition_arg", "season")
def season_is(w) -> list[str]:
    """Every seasonIs argument is a row of `season`, the one vocabulary (85 §A6): dry, hatching, wet."""
    return [f"condition {r[0]}: seasonIs {r[1]!r} is not a season row"
            for r in w.query("SELECT a.condition_id, a.value FROM condition_arg a JOIN condition c "
                             "ON c.id = a.condition_id WHERE c.term = 'seasonIs' AND a.ord = 0 "
                             "AND a.value NOT IN (SELECT id FROM season) ORDER BY 1")]


@check("respawn-clearable", "npc_statblock", "npc", "place_build_hostility")
def respawn_clearable(w) -> list[str]:
    """An actor homed in a clearable place respawns only until the place is cleared (owner 2026-10-30)."""
    return [f"npc_statblock {r[0]}: respawn {r[1]!r} in clearable {r[2]}; must be 'untilCleared' or 'never'"
            for r in w.query("SELECT s.npc_id, s.respawn, n.home_place_id FROM npc_statblock s "
                             "JOIN npc n ON n.id = s.npc_id JOIN place_build_hostility h ON h.place_id = n.home_place_id "
                             "WHERE h.clearable = 1 AND s.respawn NOT IN ('untilCleared', 'never') ORDER BY 1")]


ACTIVATOR_CLEARANCE_M = 1.2  # an activator nearer than this to another thing loses the crosshair to it (diag6 3)


@check("activator-clearance", "build_ref")
def activator_clearance(w) -> list[str]:
    """In one cell, an activator ref (base ARG_ACTI_*) sits at least 1.2 m from every other ref the player activates
    (a thing's ref): the LF83 mortar tub 0.9 m inside the well head took E for the well (diag6 3)."""
    import math
    refs = w.query("SELECT id, cell_id, base, x_m, y_m FROM build_ref WHERE thing_id IS NOT NULL "
                   "AND x_m IS NOT NULL AND y_m IS NOT NULL ORDER BY cell_id, id")
    out = []
    for i, a in enumerate(refs):
        for b in refs[i + 1:]:
            if a[1] != b[1] or not any((r[2] or "").startswith("ARG_ACTI_") for r in (a, b)):
                continue
            d = math.hypot(a[3] - b[3], a[4] - b[4])
            if d < ACTIVATOR_CLEARANCE_M:
                out.append(f"build_ref {a[0]} and {b[0]}: {d:.2f} m apart in {a[1]}; an activator needs "
                           f"{ACTIVATOR_CLEARANCE_M} m")
    return out


# -- weather (1.15 §d; owner 2026-11-01: every colour slot authored, never derived; the tint goes) ---------------
SLOT_TOL = 0.5  # a scaled or mixed copy rounded to bytes is within half a byte per channel of the formula


def _rgb(h: str) -> tuple[int, int, int]:
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def derived_colours(cols: dict[tuple[str, str], tuple[int, int, int]]) -> list[str]:
    """For one weather's {(slot, tod): rgb}: every colour that is a scaled copy (k in [0.05, 20], k = 1 included) of
    another colour of the same slot or the same time of day (the old ladder's two paths), or, within one time of day, a mix (t in (0.02, 0.98)) of two others. Black is
    "off" and never a source or a copy."""
    live = {k: v for k, v in cols.items() if any(v)}
    keys = sorted(live)
    out = []
    for a in keys:
        A = live[a]
        for b in keys:
            if b == a or (b[0] != a[0] and b[1] != a[1]):  # a copy path: the same slot or the same time of day
                continue
            B = live[b]
            k = sum(x * y for x, y in zip(A, B)) / sum(y * y for y in B)
            if 0.05 <= k <= 20 and max(abs(x - k * y) for x, y in zip(A, B)) <= SLOT_TOL:
                out.append(f"{a[0]}@{a[1]} is {b[0]}@{b[1]} x {k:.3f}")
                break
        else:
            same = [b for b in keys if b != a and b[1] == a[1]]
            for i, b in enumerate(same):
                B = live[b]
                for c in same[i + 1:]:
                    C = live[c]
                    d = [y - x for x, y in zip(B, C)]
                    dd = sum(x * x for x in d)
                    if not dd:
                        continue
                    t = sum((x - y) * z for x, y, z in zip(A, B, d)) / dd
                    if 0.02 < t < 0.98 and max(abs(x - (y + t * z)) for x, y, z in zip(A, B, d)) <= SLOT_TOL:
                        out.append(f"{a[0]}@{a[1]} is a mix of {b[0]} and {c[0]} (t {t:.2f})")
                        break
                else:
                    continue
                break
    return out


def fog_outside_vanilla(w, r, fog: bool) -> list[str]:
    """Where a weather's fog distances leave Skyrim.esm's measured ranges for its classification (decision 0034;
    skyrim-does-it-this-way §7), and, for a mist regime's weather, where it is thicker than SkyrimFog."""
    from tools.argonia_world import skyrim_units as su
    sky = w.query("SELECT classification FROM weather_sky WHERE weather_id = ?", r["id"])
    if not sky or sky[0]["classification"] not in su.FOG_RANGES_U:
        return []
    near_max, day, night = su.FOG_RANGES_U[sky[0]["classification"]]
    u = {k: su.metres_to_units(r[f"fog_{k}_m"] or 0) for k in ("day_near", "day_far", "night_near", "night_far")}
    out = [f"fog {k} {u[k]:,.0f} u above vanilla's {near_max:,}" for k in ("day_near", "night_near") if u[k] > near_max]
    for k, (lo, hi) in (("day_far", day), ("night_far", night)):
        if fog:
            lo = max(lo, su.FOG_THICKEST_U[0 if k == "day_far" else 1])
        if not lo <= round(u[k], -2) <= hi:
            out.append(f"fog {k} {u[k]:,.0f} u outside vanilla's {sky[0]['classification']} {lo:,}-{hi:,}")
    for k, med in zip(("day_far", "night_far"), su.FOG_MEDIAN_U.get(sky[0]["classification"], ())):
        if round(u[k], -2) < med:
            out.append(f"fog {k} {u[k]:,.0f} u below vanilla's {sky[0]['classification']} median {med:,}")
    out += [f"fog {k} 0: the fog starts at the eye" for k in ("day_near", "night_near") if u[k] <= 0]
    return out


def sky_blocked(cls: str, sky: dict, upper: dict) -> list[str]:
    """Where a weather can hide the sky (owner play test 3 finding 18): fog max above SkyrimFog's, or a grey zenith
    (skyUpper's channel spread below vanilla's p10 for the class) at any time of day."""
    from tools.argonia_world import skyrim_units as su
    out = [f"fog {k} {sky[k]} above vanilla's {su.FOG_MAX_CAP}" for k in ("fog_day_max", "fog_night_max")
           if sky[k] > su.FOG_MAX_CAP]
    floor = su.SKY_CHROMA_MIN.get(cls, 0)
    out += [f"skyUpper@{t} spread {max(c) - min(c)} below vanilla's {cls} {floor} (grey sky)"
            for t, c in upper.items() if max(c) - min(c) < floor]
    return out


HAZE_GREY = {"tannin-haze"}  # a haze held to the mist bounds: a warm grey, never yellow (coordinator 2026-11-03)
MIST_HUE = (120, 230)  # a mist weather's fog: cool grey-green to grey-blue hue (degrees) ...
MIST_GREY_SAT = 0.04  # ... unless near-neutral grey (HSV saturation at most this); olive and yellow fall outside both
HORIZON_FOG_GAP = 0.10  # horizon luma (sunrise, noon, sunset) at least this fraction above or below fog far: no hard white line


def mist_fog_cast(cols: dict) -> list[str]:
    """For a mist-bearing weather's {(slot, tod): rgb} (owner play test 3 finding 18, batch two's olive mist): every
    fogNear and fogFar cool grey-green or grey-blue."""
    import colorsys
    out = []
    for (s, t), c in sorted(cols.items()):
        if s not in ("fogNear", "fogFar"):
            continue
        h, sat, _ = colorsys.rgb_to_hsv(*(x / 255 for x in c))
        if sat > MIST_GREY_SAT and not MIST_HUE[0] <= h * 360 <= MIST_HUE[1]:
            out.append(f"{s}@{t} hue {h * 360:.0f} saturation {sat:.2f}: olive or yellow, not grey-green or grey-blue")
    return out


def horizon_line(cols: dict) -> list[str]:
    """For any weather's {(slot, tod): rgb}: at sunrise, noon and sunset the horizon's luma not within HORIZON_FOG_GAP
    of fog far's (a fog far as bright as the horizon reads as a hard white line where the sky should be, under any
    sky; planner, round 4). Night is exempt: at luma 20-50 a 10 % step is a few levels and no line can read white."""
    from tools.argonia_world import skyrim_units as su
    out = []
    for t in ("sunrise", "day", "sunset"):
        if ("horizon", t) in cols and ("fogFar", t) in cols:
            hz, ff = su.luma(cols["horizon", t]), su.luma(cols["fogFar", t])
            if abs(hz - ff) < HORIZON_FOG_GAP * hz:
                out.append(f"horizon@{t} luma {hz:.0f} within {HORIZON_FOG_GAP:.0%} of fogFar@{t} {ff:.0f} (white horizon line)")
    return out


@check("weather-slots", "weather", "weather_colour", "weather_sky")
def weather_slots(w) -> list[str]:
    """Each of our weathers (a template weather) has every slot at every time of day, a sky row, fog distances inside
    Skyrim.esm's measured ranges for its class (a mist regime's fog no thicker than SkyrimFog), and no colour derived
    from another."""
    from tools.argonia_world.regions.weather_seed import ROLE, TOD
    out = []
    fogs = set(w.values("SELECT weather_id FROM mist_regime")) if "mist_regime" in w.tables else set()
    if "weather_mist_band" in w.tables:
        fogs |= set(w.values("SELECT weather_id FROM weather_mist_band"))
    for r in w.query("SELECT * FROM weather WHERE template_form_key IS NOT NULL ORDER BY id"):
        wid = r["id"]
        cols = {(c["slot"], c["tod"]): _rgb(c["rgb"])
                for c in w.query("SELECT slot, tod, rgb FROM weather_colour WHERE weather_id = ?", wid)}
        missing = [f"{s}@{t}" for s in ROLE for t in TOD if (s, t) not in cols]
        if missing:
            out.append(f"weather {wid}: {len(missing)} slots not authored ({', '.join(missing[:4])}...)")
        # the sky paint is written from the resolved template (lane 1.15-r5-sky-2): judge what is written
        from tools.argonia_world.regions.api import template_sky
        from tools.argonia_world.regions.api import NEUTRAL_SKY
        painted = {} if wid in NEUTRAL_SKY else template_sky(r["template_form_key"])
        sk = w.query("SELECT classification FROM weather_sky WHERE weather_id = ?", wid)
        from tools.argonia_world.regions.api import template_colours
        if sk and sk[0]["classification"] == "Pleasant":  # every colour field is the template's (lane 1.15-r6-light)
            painted = {**template_colours(r["template_form_key"]), **painted}
        cols.update(painted)
        if not w.query("SELECT 1 FROM weather_sky WHERE weather_id = ?", wid):
            out.append(f"weather {wid}: no weather_sky row")
        out += [f"weather {wid}: {e}" for e in fog_outside_vanilla(w, r, wid in fogs)]
        sky = w.query("SELECT * FROM weather_sky WHERE weather_id = ?", wid)
        if sky:
            out += [f"weather {wid}: {e}" for e in sky_blocked(sky[0]["classification"], sky[0],
                                                              {t: cols[s, t] for s, t in cols if s == "skyUpper"})]
        out += [f"weather {wid}: {e}" for e in derived_colours({k: v for k, v in cols.items() if k not in painted})]
        tpl_lit = bool(sk and sk[0]["classification"] == "Pleasant" and template_colours(r["template_form_key"]))
        if tpl_lit:  # every slot is the template's own design (0034): our horizon/luma heuristics judge authored slots
            continue
        out += [f"weather {wid}: {e}" for e in horizon_line(cols)]
        if wid in fogs or wid in HAZE_GREY:
            out += [f"weather {wid}: {e}" for e in mist_fog_cast(cols)]
        from tools.argonia_world import skyrim_units as su
        out += [f"weather {wid}: {s}@{t} luma {su.luma(cols[s, t]):.0f} outside vanilla's {lo}-{hi}"
                for s, band in su.LUMA_RANGES.items() for t, (lo, hi) in band.items()
                if (s, t) in cols and not lo <= round(su.luma(cols[s, t])) <= hi]
    return out


@check("image-tint", "image_space")
def image_tint(w) -> list[str]:
    """No image space washes the screen: tint amount at most 0.03 (owner 2026-11-01: the yellow-green tint goes)."""
    return [f"image_space {r[0]}: tint amount {r[1]}" for r in
            w.query("SELECT id, tint_amount FROM image_space WHERE tint_amount > 0.03 ORDER BY id")]


@check("region-weather", "land_region", "land_region_weather", "region_mist", "season")
def region_weather(w) -> list[str]:
    """Every land region has a region_mist row; every non-border region a weather list of 1-6 entries whose chances
    sum to 100 in the base list and in every season (skyrim-does-it-this-way §7), every entry carrying a season global,
    a different list in each season, its regime's mist weather, and in a marsh list fog at 28-35 % (§7)."""
    from tools.argonia_world.regions import season as S
    out = []
    ch = S.chances(w)
    seasons = S.order(w)
    wins = S.windows(w)
    out += [f"season {s}: {b - a} days, under a 7-day skip" for s, a, b in wins if b - a < 7]
    for r in w.query("SELECT l.id, l.border, m.regime, e.weather_group_id g FROM land_region l LEFT JOIN region_mist m "
                     "ON m.land_region_id = l.id LEFT JOIN eco_class e ON e.id = l.eco_class_id ORDER BY l.id"):
        if r["regime"] is None:
            out.append(f"land_region {r['id']}: no region_mist row")
        if r["border"]:
            continue
        lst = w.query("SELECT x.weather_id, x.chance, x.season_global, y.weather_state_id st FROM land_region_weather x "
                      "JOIN weather y ON y.id = x.weather_id WHERE x.land_region_id = ?", r["id"])
        if not lst:
            out.append(f"land_region {r['id']}: no weather list")
            continue
        if not 1 <= len(lst) <= 6:
            out.append(f"land_region {r['id']}: {len(lst)} entries, vanilla's lists hold 1-6")
        if sum(x["chance"] for x in lst) != 100:
            out.append(f"land_region {r['id']}: chances sum to {sum(x['chance'] for x in lst)}, not 100")
        for s in seasons:
            tot = sum(ch.get(x["season_global"], {}).get(s, 0) for x in lst)
            if tot != 100:
                out.append(f"land_region {r['id']}: season {s} chances sum to {tot}, not 100")
            fog = sum(ch.get(x["season_global"], {}).get(s, 0) for x in lst if x["st"] == "ground-mist")
            if r["g"] == "marsh" and not 28 <= fog <= 35:
                out.append(f"land_region {r['id']}: season {s} fog {fog} %, vanilla's marsh lists hold 28-35")
        out += [f"land_region {r['id']}: {x['weather_id']} has no season global" for x in lst if not x["season_global"]]
        by = {s: tuple(ch.get(x["season_global"], {}).get(s) for x in lst) for s in seasons}
        if len(set(by.values())) < len(seasons):
            out.append(f"land_region {r['id']}: two seasons draw the same list")
        for s, v in by.items():
            if not any(x for x in v if x):
                out.append(f"land_region {r['id']}: nothing to draw in season {s}")
        if r["regime"] and r["regime"] != "none":
            mw = w.values("SELECT weather_id FROM mist_regime WHERE id = ?", r["regime"])
            band = set(w.values("SELECT weather_id FROM weather_mist_band WHERE variant_of = ?", mw[0])) if mw else set()
            if not mw or not ({mw[0]} | band) & {x["weather_id"] for x in lst}:
                out.append(f"land_region {r['id']}: regime {r['regime']} has no mist weather in its list")
    return out


# -- the sky against its template, from the bytes (lane 1.15-r5-sky) ----------------------------------------------
# Not a world check (the values come from Skyrim.esm at write time): pure functions over records read with
# terrain/esm.py, called by the region writer test on the written plugin.
IMGS_TOD = {"sunrise": "DAWN", "day": "DAY", "sunset": ("DAWN", "DUSK"), "night": "NIGHT"}


def _sub(rec, sig: str) -> bytes:
    return rec.first(sig) or b""


def _cloud_slots(rec) -> list[int]:
    """The cloud layers a WTHR gives a texture (00TX is slot 0, 10TX slot 1, ... L0TX slot 28)."""
    return [ord(s[0]) - 48 for s, _ in rec.subs if len(s) == 4 and s.endswith("0TX")]


def sky_clouds(ours, tpl, pleasant: bool) -> list[str]:
    """A WTHR's cloud layers against its template's: each textured layer drawn (NAM1) exactly where the template
    draws it (all on stacked SkyrimCloudy's disabled overcast sheets), and a clear sky's per-layer colours (PNAM)
    the template's (one cream colour on SkyrimClear's full-sky SkyrimCloudsFill layer painted a pale veil)."""
    import struct
    out = []
    n1o, n1t = (struct.unpack("<I", _sub(r, "NAM1") or b"\0\0\0\0")[0] for r in (ours, tpl))
    for i in _cloud_slots(tpl):
        if (n1o >> i) & 1 != (n1t >> i) & 1:
            out.append(f"cloud layer {i} {'off' if (n1o >> i) & 1 else 'on'} where the template has it "
                       f"{'off' if (n1t >> i) & 1 else 'on'}")
        if pleasant and _sub(ours, "PNAM")[i * 16:i * 16 + 16] != _sub(tpl, "PNAM")[i * 16:i * 16 + 16]:
            out.append(f"cloud layer {i} colours not the template's (a clear sky's layers are tinted to it)")
    return out


SKY_PAINT = {0: "sky upper", 5: "sun", 7: "sky lower", 8: "horizon"}  # NAM0 slots, 16 bytes each (4 times of day)


def sky_paint(ours, tpl) -> list[str]:
    """A WTHR's sky paint against its resolved template's (Tropical Skyrim's restyle where it has one; lane
    1.15-r5-sky-2), field by field: sky upper, lower, horizon and sun per time of day (NAM0), and every textured
    cloud layer's colours (PNAM). Our authored northern-pale slots read a grey-blue zenith at noon."""
    out = []
    no, nt = _sub(ours, "NAM0"), _sub(tpl, "NAM0")
    for slot, name in SKY_PAINT.items():
        for t, tod in enumerate(TOD_ORDER):
            a, b = no[slot * 16 + t * 4:slot * 16 + t * 4 + 3], nt[slot * 16 + t * 4:slot * 16 + t * 4 + 3]
            if a != b:
                out.append(f"{name} at {tod} {a.hex().upper()} not the template's {b.hex().upper()}")
    for i in _cloud_slots(tpl):
        if _sub(ours, "PNAM")[i * 16:i * 16 + 16] != _sub(tpl, "PNAM")[i * 16:i * 16 + 16]:
            out.append(f"cloud layer {i} colours not the template's")
    return out


TOD_ORDER = ("sunrise", "day", "sunset", "night")


def sky_image(ours, tpl, tod: str, tpl_edid: str) -> list[str]:
    """An IMGS used at `tod` against its template: HDR (HNAM) the template's (ours put sky scale 1.6 against
    Skyrim.esm's 0.02-0.38 and white 4.0 against 0.82-1.02), and the template a vanilla image space for that time of
    day (ISSkyrimClearDAY_FF for noon; the day image once pointed at ISSkyrimClearDAWN_MA)."""
    out = []
    if _sub(ours, "HNAM")[:36] != _sub(tpl, "HNAM")[:36]:
        out.append("HDR not the template's")
    want = IMGS_TOD[tod]
    if not any(f"{w}_" in tpl_edid or tpl_edid.endswith(w) for w in ((want,) if isinstance(want, str) else want)):
        out.append(f"used at {tod} but its template {tpl_edid} is not a {want} image space")
    return out


def sky_light(ours, tpl) -> list[str]:
    """A clear (Pleasant) WTHR's every colour field against its resolved template's (lane 1.15-r6-light, 0034): all
    17 NAM0 slots per time of day (fog near/far, sunlight, ambient, the sky paint...) and the four DALC."""
    out = []
    no, nt = _sub(ours, "NAM0"), _sub(tpl, "NAM0")
    for k in range(min(len(no), len(nt)) // 16):
        for t, tod in enumerate(TOD_ORDER):
            a, b = no[k * 16 + t * 4:k * 16 + t * 4 + 3], nt[k * 16 + t * 4:k * 16 + t * 4 + 3]
            if a != b:
                out.append(f"NAM0 slot {k} at {tod} {a.hex().upper()} not the template's {b.hex().upper()}")
    if [b for s, b in ours.subs if s == "DALC"] != [b for s, b in tpl.subs if s == "DALC"]:
        out.append("directional ambient not the template's")
    return out


def sky_grade(ours, tpl) -> list[str]:
    """An IMGS's cinematic grade (CNAM saturation, brightness, contrast) and tint (TNAM) against its template's."""
    return [f"{sig} not the template's" for sig, n in (("CNAM", 12), ("TNAM", 16))
            if _sub(ours, sig)[:n] != _sub(tpl, sig)[:n]]


def volumetric_links(ours, tpl, update) -> list[str]:
    """A WTHR's volumetric lighting (HNAM, four VOLI links) is its winner's where that carries any link, else
    Update.esm's (Tropical Skyrim's HNAM is all null: the LE plugin's empty SSE field; lane 1.15-r6-light)."""
    t = _sub(tpl, "HNAM")
    want = t if t and any(t) else _sub(update, "HNAM") if update is not None else t
    return [] if _sub(ours, "HNAM")[:16] == (want or b"")[:16] else ["volumetric lighting not the template's"]


def sky_fill_and_ambient(ours, tpl, clear_template: bool, pleasant: bool) -> list[str]:
    """On a clear template the full-sky fill (slot 28) draws with the template's colour and alpha (tannin-haze's
    cream fill at 1.0 was the refused yellow fog); a clear sky's ambient (NAM0 slot 3) and DALC are the template's
    (clear-dry's olive ground light; coordinator ruling 2026-11-03)."""
    out = []
    if clear_template and 28 in _cloud_slots(tpl):
        for sig, n in (("PNAM", 16), ("JNAM", 16)):
            if _sub(ours, sig)[28 * n:29 * n] != _sub(tpl, sig)[28 * n:29 * n]:
                out.append(f"fill layer {sig} not the template's")
    if pleasant:
        if _sub(ours, "NAM0")[48:64] != _sub(tpl, "NAM0")[48:64]:
            out.append("ambient not the template's")
        if [b for s, b in ours.subs if s == "DALC"] != [b for s, b in tpl.subs if s == "DALC"]:
            out.append("directional ambient not the template's")
    return out
@check("creature-kinds-bar", "creature_list", "creature_list_entry", "creature_form", "creature_region_class",
       "land_region")
def creature_kinds_bar(w) -> list[str]:
    """Every region class holds at least as many wild kinds as Skyrim.esm's biome region and Black Marsh.esm's main
    worldspace of equal area, and 12 kinds in each dry-ground list (owner #37; creatures/checks.kind_bars)."""
    from tools.argonia_world.creatures import checks as cc
    return cc.kind_bars(w)["fail"] or []


@check("creature-grounding", "creature_region_class")
def creature_grounding(w) -> list[str]:
    """Every wild row carries its grounding: lore (why), ecology, bands, climate, day rule (owner #37, 09:23)."""
    return [f"creature_region_class {r[0]} {r[1]}: no grounding" for r in w.query(
        "SELECT creature_id, region_class FROM creature_region_class WHERE COALESCE(why, '') = '' OR "
        "COALESCE(ecology, '') = '' OR COALESCE(bands, '') = '' OR COALESCE(climate, '') = '' OR day_rule IS NULL "
        "ORDER BY 1, 2")][:20]
