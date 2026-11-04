"""The region family's records (2.W3 §a; decisions 0028 §3, 0031): what intermediate.py and the terrain's world
writer read, resolved to the last FormKey and unit.

The split across the two plugins (decision 0031, the shell pattern agreed with the planner on 2026-10-29): the
engine reads a cell's regions from its XCLR list, and ArgoniaWorld.esm's cells cannot link to Argonia.esm, their
dependant. So ArgoniaWorld.esm holds one REGN **shell** per region (EditorID and worldspace only), and its cells'
XCLR link the shells. Argonia.esm **overrides** each shell with the authored part: areas, weather list, object list
and map name. That override is what plugin/ serialises and a reviewer reads. The closed border region has a shell too,
and the XCLR of every cell that overlaps the border polygon lists it beside its land region, and no other cell does:
Skyrim.esm lists BorderRegionSkyrim in 5,610 of Tamriel's 11,187 cells, exactly the cells with a corner inside its
173-point polygon (5,609 of 5,610; lane-border-quit 2026-10-31). Ours linked none (game-19 s09, 16 m past the west
edge), then every cell, outside ones too (game-20 s09, 2 km past). The shells' ids sit in a reserved range of ArgoniaWorld.esm (REGION_SHELL_BASE,
below the water's 0x100000) and are kept append-only in the formid table under that plugin, so a region that comes
or goes never renumbers the rest.

    shell_keys(world, frozen)            {land_region id: shell FormKey}
    shell_records(world)                 the shells, for terrain/world.py's document
    cell_region_runs(world)              [{cy, cx0, cx1, region: shell FormKey}], for the XCLR
    border_shell_key(world)              the border region's shell, which the inside cells' XCLR also list
    border_wall_refs(alloc, z_at)        the invisible collision wall on the border polygon (CollisionMarker boxes)
    border_cell_runs(polygon)            [{cy, cx0, cx1}]: the cells overlapping the border polygon (vanilla's rule)
    climate_form_key(alloc)              the CLMT the WRLD override links
    layers(alloc, world, wrld)           the Argonia.esm layer: REGN overrides and the border, CLMT, WTHR, IMGS,
                                         the WChance globals, the TimeScale override, the WRLD override

Weather and image-space numbers are ours where they are the place's (fog distances and curve, the mist bank, the
light on the ground, cinematic grade: weather_colour and weather_sky), and the sky's own paint is the template's: the
sky upper/lower/horizon and sun colours, every cloud layer's colours and the image space's HDR and bloom are copied at
generation from the record the game RESOLVES for the template (the load order's last plugin carrying it: Tropical
Skyrim.esp's restyle before Update.esm before Skyrim.esm; decision 0006 §8, lane 1.15-r5-sky-2), as WATR copies its
winner's body. References (cloud texture paths, precipitation, sounds, sky statics, the lens flare) come from it too.
"""
from __future__ import annotations

import os
import struct
from functools import lru_cache
from pathlib import Path

from tools.argonia_world import skyrim_units as su
from tools.argonia_world.regions.classify import weather_list

GAME_DATA = Path(os.environ.get("ARGONIA_GAME_ROOT", Path.home() / "games/skyrimse")) / "Data"

LAND_PLUGIN = "ArgoniaWorld.esm"
REGION_SHELL_BASE = 0x080000  # ArgoniaWorld.esm: past the terrain's CELL/LAND range (to 0x22A30), below the water's
TIMESCALE = "00003A:Skyrim.esm"  # the engine's TimeScale global (vanilla 20)
PRIORITY = 50  # every region list's priority (no two of our regions overlap, so it orders nothing yet)
TOD = ("sunrise", "day", "sunset", "night")


# --- the shells (ArgoniaWorld.esm) ---------------------------------------------------------------------------
def shell_keys(world, frozen: bool = True) -> dict[str, str]:
    """{land_region id: shell FormKey}, allocating new regions append-only unless frozen."""
    have = {r.editor_id: r.form_id for r in world.rows("formid", plugin=LAND_PLUGIN) if r.record_type == "REGN"}
    out = {}
    for r in world.query("SELECT id, edid, border FROM land_region ORDER BY id"):
        # the border's EditorID already names its Argonia.esm id (before it had a shell); its shell row takes a suffix
        key = f"{r['edid']}Shell" if r["border"] else r["edid"]
        if key not in have:
            if frozen:
                raise KeyError(f"{r['edid']}: no shell id yet; run `make plugin` and commit the formid table")
            fid = max(have.values(), default=REGION_SHELL_BASE - 1) + 1
            world.insert("formid", editor_id=key, plugin=LAND_PLUGIN, form_id=fid, record_type="REGN",
                         entity_key=f"land_region.{r['id']}" + (".shell" if r["border"] else ""))
            have[key] = fid
        out[r["id"]] = f"{have[key]:06X}:{LAND_PLUGIN}"
    return out


def shell_records(world) -> list[dict]:
    keys = shell_keys(world)
    edid = dict(world.query("SELECT id, edid FROM land_region"))
    return [{"type": "REGN", "formKey": keys[k], "edid": edid[k]} for k in sorted(keys, key=keys.get)]


def cell_region_runs(world) -> list[dict]:
    keys = shell_keys(world)
    return [{"cy": r["cy"], "cx0": r["cx0"], "cx1": r["cx1"], "region": keys[r["land_region_id"]]}
            for r in world.query("SELECT * FROM cell_region_run ORDER BY cy, cx0")]


def border_shell_key(world) -> str | None:
    keys = shell_keys(world)
    row = world.query("SELECT id FROM land_region WHERE border = 1 ORDER BY id")
    return keys[row[0]["id"]] if row else None


def _inside(px: float, py: float, poly) -> bool:
    c = False
    for k in range(len(poly)):
        (x1, y1), (x2, y2) = poly[k], poly[k - 1]
        if (y1 > py) != (y2 > py) and px < (x2 - x1) * (py - y1) / (y2 - y1) + x1:
            c = not c
    return c


def border_cell_runs(poly=None) -> list[dict]:
    """The cells whose square overlaps the border polygon, as row runs: vanilla's rule (a cell lists the border
    when a corner lies inside it). Corners are tested 1 unit inside the cell, so a cell that only touches the edge
    from outside is not listed."""
    poly = poly if poly is not None else border_polygon()
    c = su.CELL_UNITS
    xs, ys = [p[0] for p in poly], [p[1] for p in poly]
    out = []
    for cy in range(int(min(ys) // c) - 1, int(max(ys) // c) + 1):
        row = []
        for cx in range(int(min(xs) // c) - 1, int(max(xs) // c) + 1):
            x0, y0 = cx * c, cy * c
            pts = [(x0 + 1, y0 + 1), (x0 + c - 1, y0 + 1), (x0 + 1, y0 + c - 1), (x0 + c - 1, y0 + c - 1),
                   (x0 + c / 2, y0 + c / 2)]
            if any(_inside(px, py, poly) for px, py in pts):
                row.append(cx)
        for cx in row:
            if out and out[-1]["cy"] == cy and out[-1]["cx1"] == cx - 1:
                out[-1]["cx1"] = cx
            else:
                out.append({"cy": cy, "cx0": cx, "cx1": cx})
    return out


def rectangles(runs: list[dict]) -> list[tuple[int, int, int, int]]:
    """Row runs of one region merged down the rows into rectangles (cx0, cy0, cx1, cy1), cells inclusive."""
    open_: dict[tuple[int, int], list[int]] = {}
    out = []
    for r in sorted(runs, key=lambda r: (r["cy"], r["cx0"])):
        k = (r["cx0"], r["cx1"])
        cur = open_.get(k)
        if cur and cur[1] == r["cy"] - 1:
            cur[1] = r["cy"]
        else:
            if cur:
                out.append((k[0], cur[0], k[1], cur[1]))
            open_[k] = [r["cy"], r["cy"]]
    out += [(k[0], v[0], k[1], v[1]) for k, v in open_.items()]
    return sorted(out, key=lambda t: (t[1], t[0], t[3], t[2]))


def area(cx0: int, cy0: int, cx1: int, cy1: int) -> list[list[float]]:
    """A rectangle of cells as a REGN area polygon in worldspace units, counter-clockwise from the south-west."""
    x0, y0 = su.cell_origin(cx0, cy0)
    x1, y1 = su.cell_origin(cx1 + 1, cy1 + 1)
    return [[float(x0), float(y0)], [float(x1), float(y0)], [float(x1), float(y1)], [float(x0), float(y1)]]


def border_polygon() -> list[list[float]]:
    from tools.argonia_world.terrain.edges import border_polygon as bp
    return bp()


# --- the border wall: the native fallback behind the border region -------------------------------------------
# The engine's own invisible collision box: Skyrim.esm's CollisionMarker STAT (000021), placed with a box primitive
# (XPRM type 1) and no XTRI, as Skyrim places 762 of its 2,142 collision refs (SkyHaven's exterior wall among them).
# Reviewed under decision 0012 (lane-border-quit, 2026-10-31): no mesh, no sound, no text; nothing reaches the player
# but the stop. One box per cell length along each polygon edge; the box's x half-size is the whole piece length, so
# the pieces overlap whether the engine reads XPRM as half or full extents (not measured yet).
COLLISION_MARKER = "000021:Skyrim.esm"
WALL_HALF_THICK_UNITS = 64.0
WALL_HALF_HEIGHT_UNITS = 16384.0  # ~234 m each way about the ground at the piece's centre
PRIMITIVE_BOX = 1


def border_wall_pieces(poly=None) -> list[dict]:
    """[{edge, i, x, y, yaw, length}]: the wall's pieces in Skyrim units, centred on the polygon's edges, each at most
    one cell long; yaw is the box's local x as a world-frame yaw (degrees clockwise from north) minus 90."""
    import math
    poly = poly if poly is not None else border_polygon()
    out = []
    for e in range(len(poly)):
        (ax, ay), (bx, by) = poly[e], poly[(e + 1) % len(poly)]
        dx, dy = bx - ax, by - ay
        length = math.hypot(dx, dy)
        n = max(1, math.ceil(length / su.CELL_UNITS - 1e-9))
        bearing = math.degrees(math.atan2(dx, dy))  # clockwise from north (+y)
        for i in range(n):
            t = (i + 0.5) / n
            out.append({"edge": e, "i": i, "x": ax + dx * t, "y": ay + dy * t, "yaw": (bearing - 90.0) % 360.0,
                        "length": length / n})
    return out


def border_wall_refs(alloc, z_at) -> list[dict]:
    """The wall's persistent REFRs (the WRLD override's persistent cell), each on the final ground at its centre."""
    out = []
    for p in border_wall_pieces():
        xm, ym = su.skyrim_to_province(p["x"], p["y"])
        side = (su.PROVINCE_SAMPLES - 1) * su.PROVINCE_SAMPLE_M
        z = su.metres_to_units(max(z_at(min(max(xm, 0.0), side - 0.01), min(max(ym, 0.0), side - 0.01)), 0.0))
        e = f"ARG_BorderWall_{p['edge']}_{p['i']:03d}"
        out.append({"formKey": alloc.form_key(e, "REFR", f"border.wall.{p['edge']}.{p['i']}"), "edid": e,
                    "base": COLLISION_MARKER, "pos": [su.rounded(p["x"], 2), su.rounded(p["y"], 2), su.rounded(z, 2)],
                    "rot": [su.rounded(v, 6) for v in su.yaw_to_rot(p["yaw"])], "persistent": True,
                    "primitive": {"bounds": [su.rounded(p["length"], 2), WALL_HALF_THICK_UNITS,
                                             WALL_HALF_HEIGHT_UNITS], "type": PRIMITIVE_BOX}})
    return out


# --- colours ---------------------------------------------------------------------------------------------------
def rgb(hex6: str) -> list[int]:
    return [int(hex6[i:i + 2], 16) for i in (0, 2, 4)]


LIGHTNING = [214, 230, 190]  # a green-white flash, not blue
DALC = {"dalcUp": ("zPlus",), "dalcSide": ("xPlus", "xMinus", "yPlus", "yMinus"), "dalcDown": ("zMinus",)}


def weather_colours(world, wid: str) -> dict[str, dict[str, list[int]]]:
    """{slot: {time of day: rgb}}: the weather's authored colours (weather_colour), every slot read, none derived."""
    out: dict[str, dict[str, list[int]]] = {}
    for r in world.query("SELECT slot, tod, rgb FROM weather_colour WHERE weather_id = ? ORDER BY slot, tod", wid):
        out.setdefault(r["slot"], {})[r["tod"]] = rgb(r["rgb"])
    return out


def ambient(colours: dict) -> dict[str, dict]:
    """Directional ambient per time of day from the authored faces (dalcUp, dalcSide, dalcDown)."""
    out = {}
    for t in TOD:
        face = {k: colours[slot][t] for slot, ks in DALC.items() for k in ks}
        out[t] = dict(face, specular=[0, 0, 0], scale=1.0)
    return out


# --- the Argonia.esm records -------------------------------------------------------------------------------------
def climate_form_key(alloc) -> str:
    edid = alloc.world.values("SELECT edid FROM climate ORDER BY id")[0]
    return alloc.form_key(edid, "CLMT", "climate." + alloc.world.values("SELECT id FROM climate ORDER BY id")[0])


def weather_key(alloc, w) -> str:
    return w["form_key"] or alloc.form_key(w["edid"], "WTHR", f"weather.{w['id']}")


def _masters(path: Path) -> list[str]:
    """A plugin's master list (TES4 MAST), read from its header record alone."""
    from tools.argonia_world.terrain import esm
    with open(path, "rb") as f:
        head = f.read(24)
        body = f.read(struct.unpack_from("<I", head, 4)[0])
    return [b.rstrip(b"\0").decode() for s, b in esm._subrecords(body) if s == "MAST"]


@lru_cache(maxsize=4)
def sky_winners(data: Path = GAME_DATA) -> dict[str, str]:
    """Every WTHR and IMGS form key ("XXXXXX:Master.esm") -> the last plugin in the load order carrying it: the record
    the game draws (Tropical Skyrim.esp restyles 38 vanilla weathers and 111 image spaces in place; measured 2026-11-03,
    lane 1.15-r5-sky-2). Without game data every template resolves to its own master."""
    from tools.argonia_world.intermediate import load_order
    from tools.argonia_world.water.layer import top_group
    out: dict[str, str] = {}
    if not (Path(data) / "Skyrim.esm").exists():
        return out
    for p in load_order(Path(data)):
        mast = _masters(Path(data) / p)
        for sig in (b"WTHR", b"IMGS"):
            for r in top_group(Path(data) / p, sig):
                i = r.formid >> 24
                out[f"{r.formid & 0xFFFFFF:06X}:{mast[i] if i < len(mast) else p}"] = p
    return out


def template_plugin(form_key: str, data: Path = GAME_DATA) -> str:
    return sky_winners(Path(data)).get(form_key, form_key.split(":")[1])


SKY_SLOTS = {"skyUpper": 0, "sun": 5, "skyLower": 7, "horizon": 8}  # the WTHR NAM0 slots a weather takes from its template


@lru_cache(maxsize=64)
def template_sky(form_key: str, data: Path = GAME_DATA) -> dict[tuple[str, str], bytes]:
    """The sky paint a weather is written with, {(slot, tod): rgb}, read from its resolved template (empty without
    game data): what the checks judge in place of the authored rows the writer no longer uses."""
    from tools.argonia_world.water.layer import top_group
    p = template_plugin(form_key, Path(data))
    if not (Path(data) / p).exists():
        return {}
    fid = int(form_key.split(":")[0], 16)
    r = next((x for x in top_group(Path(data) / p, b"WTHR") if x.formid & 0xFFFFFF == fid), None)
    n = r.first("NAM0") if r else None
    if not n:
        return {}
    return {(s, t): n[k * 16 + i * 4:k * 16 + i * 4 + 3] for s, k in SKY_SLOTS.items() for i, t in enumerate(TOD)}


NAM0_SLOTS = ("skyUpper", "fogNear", "unknown", "ambient", "sunlight", "sun", "stars", "skyLower", "horizon",
              "effectLighting", "cloudLodDiffuse", "cloudLodAmbient", "fogFar", "skyStatics", "waterMultiplier",
              "sunGlare", "moonGlare")


@lru_cache(maxsize=64)
def template_colours(form_key: str, data: Path = GAME_DATA) -> dict[tuple[str, str], bytes]:
    """Every NAM0 colour of a weather's resolved template, {(slot, tod): rgb} (empty without game data): what a clear
    weather is written with (lightFromTemplate, lane 1.15-r6-light)."""
    from tools.argonia_world.water.layer import top_group
    p = template_plugin(form_key, Path(data))
    if not (Path(data) / p).exists():
        return {}
    fid = int(form_key.split(":")[0], 16)
    r = next((x for x in top_group(Path(data) / p, b"WTHR") if x.formid & 0xFFFFFF == fid), None)
    n = r.first("NAM0") if r else None
    if not n:
        return {}
    return {(s, t): n[k * 16 + i * 4:k * 16 + i * 4 + 3] for k, s in enumerate(NAM0_SLOTS) if k * 16 + 16 <= len(n)
            for i, t in enumerate(TOD)}


def template_graded(world) -> set[str]:
    """The image spaces that take their template's cinematic grade and tint: those a clear (Pleasant) weather draws,
    which takes every colour from its template (lane 1.15-r6-light). Every other image space keeps our grade and no
    tint: Tropical Skyrim's rain, storm and overcast IMGS tint the screen yellow-green at 0.65-0.75 under saturation
    1.5-1.9 (RainDAY 10A1C6 tint A3B185 x 0.75; StormRainDAY 0C8217 A9BA65 x 0.75), the smog-yellow rain sky the owner
    refused (#41, lane 1.15-r6-fog-yellow)."""
    return set(world.values("SELECT DISTINCT i FROM (SELECT w.image_day_id i, s.classification c FROM weather w JOIN "
                            "weather_sky s ON s.weather_id = w.id UNION SELECT w.image_dawn_id, s.classification FROM "
                            "weather w JOIN weather_sky s ON s.weather_id = w.id UNION SELECT w.image_night_id, "
                            "s.classification FROM weather w JOIN weather_sky s ON s.weather_id = w.id) "
                            "WHERE c = 'Pleasant' AND i IS NOT NULL"))


def _image_records(alloc, world) -> tuple[list[dict], dict]:
    images = {r["id"]: dict(r) for r in world.query("SELECT * FROM image_space ORDER BY id")}
    graded = template_graded(world)
    recs = []
    for i in images.values():
        i["formKey"] = alloc.form_key(i["edid"], "IMGS", f"image_space.{i['id']}")
        # HDR (HNAM) is the template's, as WATR carries its template's body (decision 0034, lane 1.15-r5-sky): our
        # own starting point put sky scale 1.6 against Skyrim.esm's 0.02-0.3 and white 4.0 against 0.88-1.02, a sky
        # blown to a flat pale sheet at noon
        recs.append({"type": "IMGS", "edid": i["edid"], "formKey": i["formKey"], "template": i["template_form_key"],
                     "templatePlugin": template_plugin(i["template_form_key"]),
                     "cinematic": {"saturation": i["saturation"], "brightness": i["brightness"],
                                   "contrast": i["contrast"]},
                     "tint": {"color": rgb(i["tint"]), "amount": i["tint_amount"]},
                     # ... and its cinematic grade and tint (lane 1.15-r6-light: ours had tint 0 and our own grade)
                     "hdrFromTemplate": True, "gradeFromTemplate": i["id"] in graded})
    return recs, images


def _weather_records(alloc, world, images: dict) -> list[dict]:
    recs = []
    for w in world.query("SELECT w.*, s.* FROM weather w JOIN weather_sky s ON s.weather_id = w.id "
                         "WHERE w.template_form_key IS NOT NULL ORDER BY w.id"):
        allc = weather_colours(world, w["id"])
        col = {k: v for k, v in allc.items() if k not in DALC}
        thunder = w["thunder"]
        recs.append({
            "type": "WTHR", "edid": w["edid"], "formKey": weather_key(alloc, w), "template": w["template_form_key"],
            "templatePlugin": template_plugin(w["template_form_key"]),
            # the sky's paint (upper, lower, horizon, the sun disc) is the resolved template's: our authored
            # northern-pale slots read a grey-blue zenith at noon (lane 1.15-r5-sky-2; 0006 §8 Tropical first)
            "skyFromTemplate": True,
            "flags": [w["classification"]], "colours": col, "ambient": ambient(allc),
            "fog": {"dayNear": su.rounded(su.metres_to_units(w["fog_day_near_m"]), 2),
                    "dayFar": su.rounded(su.metres_to_units(w["fog_day_far_m"]), 2),
                    "nightNear": su.rounded(su.metres_to_units(w["fog_night_near_m"]), 2),
                    "nightFar": su.rounded(su.metres_to_units(w["fog_night_far_m"]), 2),
                    "dayPower": w["fog_day_power"], "nightPower": w["fog_night_power"],
                    "dayMax": w["fog_day_max"], "nightMax": w["fog_night_max"]},
            "images": {"sunrise": images[w["image_dawn_id"]]["formKey"], "day": images[w["image_day_id"]]["formKey"],
                       "sunset": images[w["image_dawn_id"]]["formKey"],
                       "night": images[w["image_night_id"]]["formKey"]},
            "clouds": {"speed": w["cloud_speed"], "colours": col["cloudLodDiffuse"],
                       "alpha": {"sunrise": 1.0, "day": 1.0, "sunset": 1.0, "night": 1.0},
                       # a clear (Pleasant) sky keeps its template's per-layer alphas, as Skyrim's SkyrimClear does
                       # (0.2-0.8 on its upper layers): a full deck on every layer hid the sun (decision 0034)
                       "alphaFromTemplate": w["classification"] == "Pleasant",
                       # ... and its per-layer colours: SkyrimClear tints its full-sky SkyrimCloudsFill layer the
                       # zenith's dark blue (114E77 at noon); one cream cloud colour on it painted a pale veil over
                       # the whole sky (lane 1.15-r5-sky)
                       # (every class since lane 1.15-r5-sky-2: one authored cream-grey on every overcast layer)
                       "coloursFromTemplate": True,
                       # a weather on a clear template draws its full-sky fill as the template does (coordinator
                       # ruling 2026-11-03: tannin-haze's cream fill at alpha 1.0 was the "yellow fog" refused)
                       "fillFromClearTemplate": True},
            # a clear sky's ambient and directional ambient are the template's (ruling 2026-11-03, 0034): the
            # authored olive ground light (7A8367, DALC Z+ 7D8465) was the last candidate for the cast
            "ambientFromTemplate": w["classification"] == "Pleasant",
            # ... and every colour field (fog near/far, sunlight, the rest of NAM0; lane 1.15-r6-light, 0034)
            "lightFromTemplate": w["classification"] == "Pleasant",
            "windSpeed": w["wind"], "transDelta": 4.0, "sunGlare": w["sun_glare"], "sunDamage": w["sun_damage"],
            "precipitationFadeIn": w["precip_fade_in"], "precipitationFadeOut": w["precip_fade_out"],
            "thunderFrequency": thunder,
            "thunderFadeIn": 0.2 if thunder else 0.0, "thunderFadeOut": 0.9 if thunder else 0.0,
            "lightning": LIGHTNING, "windDirection": 0.0, "windDirectionRange": 0.25,  # fractions of a turn
        })
    return recs


def season_globals(alloc, world) -> list[dict]:
    """One GLOB per (weather group, weather) a region list names, holding its mean chance; ArgoniaCore's season
    rule sets it per season (season.py)."""
    out = {}
    for r in world.query("SELECT season_global g, max(chance) c FROM land_region_weather WHERE season_global IS NOT "
                         "NULL GROUP BY season_global ORDER BY season_global"):
        out[r["g"]] = {"type": "GLOB", "edid": r["g"], "formKey": alloc.form_key(r["g"], "GLOB", "weather_chance."
                                                                                   + r["g"]), "value": r["c"]}
    return list(out.values())


def _object(o) -> dict:
    flags = ["ConformToSlope"] if o["conform"] else []
    if world_role(o) == "tree":
        flags.append("Tree")
    rec = {"object": o["form_key"], "density": o["density_per_ha"], "clustering": o["clustering"],
           "minSlope": o["min_slope_deg"], "maxSlope": o["max_slope_deg"], "flags": flags,
           "radius": round(su.metres_to_units(o["radius_m"]))}
    rec["minHeight"] = su.rounded(su.metres_to_units(o["min_height_m"]), 2) if o["min_height_m"] is not None else 0.0
    rec["maxHeight"] = su.rounded(su.metres_to_units(o["max_height_m"]), 2) if o["max_height_m"] is not None else 0.0
    return rec


def world_role(o) -> str:
    return "tree" if o["record_type"] == "TREE" else "static"


def region_records(alloc, world, wrld_key: str) -> list[dict]:
    before = len(world.rows("formid", plugin=LAND_PLUGIN))
    keys = shell_keys(world, frozen=alloc.frozen)
    if len(world.rows("formid", plugin=LAND_PLUGIN)) != before:
        alloc.dirty = True  # the shells' rows are saved with the allocator's formid table
    wkeys = {w["id"]: weather_key(alloc, w) for w in world.query("SELECT * FROM weather ORDER BY id")}
    runs: dict[str, list[dict]] = {}
    for r in world.query("SELECT * FROM cell_region_run ORDER BY cy, cx0"):
        runs.setdefault(r["land_region_id"], []).append(dict(r))
    globs = {g["edid"]: g["formKey"] for g in season_globals(alloc, world)}
    recs = []
    for reg in world.query("SELECT * FROM land_region ORDER BY id"):
        rid = reg["id"]
        if reg["border"]:
            recs.append({"type": "REGN", "override": True, "edid": reg["edid"], "formKey": keys[rid],
                         "worldspace": wrld_key, "border": True, "areas": [{"falloff": 0, "points": border_polygon()}],
                         "mapName": "", "priority": PRIORITY})
            continue
        objs = [_object(o) for o in world.query(
            "SELECT o.*, f.record_type FROM land_region_object o JOIN object_form f USING (form_key) "
            "WHERE o.land_region_id = ? ORDER BY o.form_key", rid)]
        weathers = [{"weather": wkeys[r["weather_id"]], "chance": r["chance"],
                     "global": globs.get(r["season_global"])}
                    for r in world.query("SELECT * FROM land_region_weather WHERE land_region_id = ? ORDER BY "
                                         "weather_id", rid)]
        recs.append({"type": "REGN", "override": True, "edid": reg["edid"], "formKey": keys[rid],
                     "worldspace": wrld_key, "border": False, "priority": PRIORITY,
                     "areas": [{"falloff": 0, "points": area(*t)} for t in rectangles(runs.get(rid, []))],
                     "mapName": reg["map_name"], "weathers": weathers, "objects": objs})
    return recs


def climate_record(alloc, world) -> dict:
    c = world.query("SELECT * FROM climate ORDER BY id")[0]
    wkeys = {w["id"]: weather_key(alloc, w) for w in world.query("SELECT * FROM weather ORDER BY id")}
    return {"type": "CLMT", "edid": c["edid"], "formKey": climate_form_key(alloc), "template": c["template_form_key"],
            "sunriseBegin": c["sunrise_begin_min"], "sunriseEnd": c["sunrise_end_min"],
            "sunsetBegin": c["sunset_begin_min"], "sunsetEnd": c["sunset_end_min"],
            "volatility": c["volatility"], "phaseLength": c["moon_phase_days"], "moons": ["Masser", "Secunda"],
            "weathers": [{"weather": wkeys[wid], "chance": ch} for wid, ch, _ in weather_list(world,
                                                                                             c["weather_group_id"])]}


def wrld_record() -> dict:
    """ArgoniaWorld.esm's WRLD intermediate record over the whole grid (the cell range from the frozen arrays'
    shape alone, memory-mapped)."""
    import numpy as np

    from tools.argonia_world.terrain import world as tw
    from tools.argonia_world.terrain.grid import PAD, Sources, data_root
    g = np.load(data_root() / "terrain" / "refined-height-f32.npy", mmap_mode="r")
    return tw.wrld(Sources(ground=g, apron=None, cover=None, tint=None, pad=PAD).cell_range)


def layers(alloc, world, wrld: dict | None = None, resolver=None) -> list:
    """The Argonia.esm layers of the region family. ``wrld`` is ArgoniaWorld.esm's WRLD intermediate record
    (terrain/world.py), which the override repeats with the climate set (an override replaces the whole record);
    with a piece ``resolver``, the gates, landings and signposts (routes/infra.py) ride in its persistent cell."""
    from tools.argonia_world.intermediate import Layer
    c = world.query("SELECT * FROM climate ORDER BY id")[0]
    images, by_id = _image_records(alloc, world)
    recs = images + _weather_records(alloc, world, by_id) + [climate_record(alloc, world)]
    recs += season_globals(alloc, world)
    recs.append({"type": "GLOB", "override": True, "edid": "TimeScale", "formKey": TIMESCALE,  # a short (measured)
                 "value": c["timescale"]})
    if wrld is not None:
        recs += region_records(alloc, world, wrld["formKey"])
        from tools.chart import fwmf  # the world map is FWMF's flat chart (1.2 §e): its camera and map offset
        cam_min, cam_max, pitch = fwmf.CAMERA
        over = dict(wrld, override=True, climate=climate_form_key(alloc), mapOffset=list(fwmf.OFFSET),
                    map=dict(wrld["map"], cameraMin=cam_min, cameraMax=cam_max, cameraPitch=pitch))
        over.pop("layer", None)
        if resolver is not None:
            from tools.argonia_world.place_build import GameGround
            from tools.argonia_world.routes import infra
            refs, bases, _ = infra.refs(alloc, world, resolver, GameGround().z)  # the final ground (f6177a7)
            from tools.argonia_world import map_markers  # 1.12: every placed place's marker, hidden until discovered
            over["persistentRefs"] = refs + border_wall_refs(alloc, GameGround().z) \
                + map_markers.refs(alloc, world, GameGround().z)
            recs += bases
        recs.append(over)
    return [Layer("base:regions", recs)]


CS_WEATHERS = "SKSE/Plugins/CommunityShaders/Weathers"


def cs_fog_files(alloc, world) -> list[dict]:
    """Community Shaders 1.9.1 per-weather files (`0x<local FormID>~<plugin>.json` under Weathers): none. Round 5 (sky A/B,
    lane 1.15-r5-cs-fog): the height fog is the feature's shipped defaults in the one global override, and a weather
    with no file takes it; the low mist is the weather records' own fog near/far."""
    return []


def sync_cs_fog(write: bool) -> list[str]:
    """Differences between data/dependencies.json's community-shaders per-weather files and cs_fog_files; with
    `write`, make them match (allocating new weathers' FormIDs) and save."""
    import json
    from pathlib import Path
    from tools.argonia_world.formids import Allocator
    from tools.argonia_world import db
    world = db.open()
    alloc = Allocator(world, frozen=not write)
    want = cs_fog_files(alloc, world)
    p = Path(__file__).resolve().parents[3] / "data" / "dependencies.json"
    deps = json.loads(p.read_text())
    row = next(d for d in deps["mods"] if any(f["path"].endswith("Argonia_ExponentialHeightFog.json")
                                               for f in d.get("files", [])))
    have = [f for f in row["files"] if f["path"].startswith(CS_WEATHERS + "/")]
    if have == want:
        return []
    if write:
        row["files"] = [f for f in row["files"] if not f["path"].startswith(CS_WEATHERS + "/")] + want
        p.write_text(json.dumps(deps, indent=1, ensure_ascii=False) + "\n")
        alloc.save()
    return [f"community-shaders per-weather fog files differ: {len(have)} laid, {len(want)} wanted"]


if __name__ == "__main__":
    import sys
    if sys.argv[1:2] == ["cs-fog"]:
        errs = sync_cs_fog("--write" in sys.argv)
        print("\n".join(errs) or "cs-fog: in step")
        sys.exit(1 if errs and "--write" not in sys.argv else 0)
