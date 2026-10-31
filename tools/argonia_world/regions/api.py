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

Weather and image-space numbers are ours (decision 0003: no vanilla or Tropical Skyrim values are copied). They are
starting points for the look tuning (4.6), not a measurement: our fog tint and image tints, spread over the times
of day and the WTHR colour slots by the fixed ladder below. Only references (cloud texture paths, precipitation,
sounds, sky statics, the lens flare) come from each weather's template, and the C# writer reads those from the master.
"""
from __future__ import annotations

from tools.argonia_world import skyrim_units as su
from tools.argonia_world.regions.classify import weather_list

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


def mix(a, b, t: float) -> list[float]:
    return [x + (y - x) * t for x, y in zip(a, b)]


def scale(c, k: float) -> list[int]:
    return [max(0, min(255, round(v * k))) for v in c]


# slot -> brightness at (sunrise, day, sunset, night) over the time-of-day base colour
LADDER = {
    "skyUpper": (0.70, 0.80, 0.70, 0.15), "skyLower": (0.90, 1.00, 0.90, 0.20), "horizon": (1.00, 1.05, 1.00, 0.22),
    "fogNear": (0.90, 1.00, 0.90, 0.20), "fogFar": (0.85, 0.95, 0.85, 0.18), "ambient": (0.60, 0.75, 0.60, 0.25),
    "unknown": (0.60, 0.75, 0.60, 0.25), "sunlight": (1.10, 1.20, 1.10, 0.30), "sun": (1.30, 1.40, 1.30, 0.40),
    "effectLighting": (1.00, 1.00, 1.00, 0.40), "cloudLodDiffuse": (0.90, 1.00, 0.90, 0.20),
    "cloudLodAmbient": (0.50, 0.60, 0.50, 0.15), "skyStatics": (0.90, 1.00, 0.90, 0.30),
    "waterMultiplier": (1.00, 1.00, 1.00, 0.50), "sunGlare": (1.20, 1.30, 1.20, 0.00),
    "moonGlare": (0.00, 0.00, 0.00, 0.60),
}
WHITE = [255, 255, 255]
STARS = {"sunrise": [0, 0, 0], "day": [0, 0, 0], "sunset": [0, 0, 0], "night": [200, 210, 190]}
# state -> (flags, wind 0..1, cloud x/y speed, sun glare, sun damage, precipitation fade in/out, thunder freq)
STATE = {
    "clear-humid": ("Pleasant", 0.15, 0.02, 0.8, 1.0, (0.0, 0.0), 0.0),
    "ground-mist": ("Cloudy", 0.05, 0.01, 0.2, 0.0, (0.0, 0.0), 0.0),
    "dry-haze": ("Cloudy", 0.20, 0.02, 0.5, 0.5, (0.0, 0.0), 0.0),
    "monsoon-downpour": ("Rainy", 0.55, 0.05, 0.0, 0.0, (0.2, 0.9), 0.0),
    "sea-squall": ("Rainy", 0.80, 0.08, 0.0, 0.0, (0.1, 0.9), 0.3),
    "storm": ("Rainy", 0.70, 0.07, 0.0, 0.0, (0.1, 0.9), 0.6),
}
LIGHTNING = [214, 230, 190]  # a green-white flash, not blue


def tod_base(fog, images: dict, w) -> dict[str, list[float]]:
    """The base colour at each time of day: our fog tint carried towards the image space's tint."""
    tint = {t: rgb(images[i]["tint"]) for t, i in
            (("sunrise", w["image_dawn_id"]), ("day", w["image_day_id"]), ("sunset", w["image_dawn_id"]),
             ("night", w["image_night_id"]))}
    return {"sunrise": mix(fog, tint["sunrise"], 0.6), "day": mix(fog, tint["day"], 0.5),
            "sunset": mix(fog, tint["sunset"], 0.6), "night": tint["night"]}


def weather_colours(fog_hex: str, images: dict, w) -> dict[str, dict[str, list[int]]]:
    base = tod_base(rgb(fog_hex), images, w)
    out = {slot: {t: scale(base[t], k[n]) for n, t in enumerate(TOD)} for slot, k in LADDER.items()}
    out["stars"] = STARS
    return out


def ambient(colours: dict) -> dict[str, dict]:
    """Directional ambient per time of day: the ambient slot from above, a little darker from below and the sides."""
    out = {}
    for t in TOD:
        a = colours["ambient"][t]
        side, below = scale(a, 0.85), scale(a, 0.6)
        out[t] = {"xPlus": side, "xMinus": side, "yPlus": side, "yMinus": side, "zPlus": a, "zMinus": below,
                  "specular": [0, 0, 0], "scale": 1.0}
    return out


# --- the Argonia.esm records -------------------------------------------------------------------------------------
def climate_form_key(alloc) -> str:
    edid = alloc.world.values("SELECT edid FROM climate ORDER BY id")[0]
    return alloc.form_key(edid, "CLMT", "climate." + alloc.world.values("SELECT id FROM climate ORDER BY id")[0])


def weather_key(alloc, w) -> str:
    return w["form_key"] or alloc.form_key(w["edid"], "WTHR", f"weather.{w['id']}")


def _image_records(alloc, world) -> tuple[list[dict], dict]:
    images = {r["id"]: dict(r) for r in world.query("SELECT * FROM image_space ORDER BY id")}
    recs = []
    for i in images.values():
        i["formKey"] = alloc.form_key(i["edid"], "IMGS", f"image_space.{i['id']}")
        recs.append({"type": "IMGS", "edid": i["edid"], "formKey": i["formKey"],
                     "cinematic": {"saturation": i["saturation"], "brightness": i["brightness"],
                                   "contrast": i["contrast"]},
                     "tint": {"color": rgb(i["tint"]), "amount": i["tint_amount"]},
                     "hdr": dict(IMGS_HDR)})
    return recs, images


# HDR values of ours (a starting point for 4.6): a gentle eye adaptation and bloom for a bright, wet air.
IMGS_HDR = {"eyeAdaptSpeed": 1.0, "eyeAdaptStrength": 0.3, "bloomBlurRadius": 4.0, "bloomThreshold": 0.7,
            "bloomScale": 0.4, "receiveBloomThreshold": 0.6, "white": 4.0, "sunlightScale": 1.6, "skyScale": 1.6}


def _weather_records(alloc, world, images: dict) -> list[dict]:
    recs = []
    for w in world.query("SELECT * FROM weather WHERE template_form_key IS NOT NULL ORDER BY id"):
        flags, wind, cloud, glare, damage, (pin, pout), thunder = STATE[w["weather_state_id"]]
        col = weather_colours(w["fog_tint"], images, w)
        recs.append({
            "type": "WTHR", "edid": w["edid"], "formKey": weather_key(alloc, w), "template": w["template_form_key"],
            "flags": [flags], "colours": col, "ambient": ambient(col),
            "fog": {"dayNear": su.rounded(su.metres_to_units(w["fog_day_near_m"]), 2),
                    "dayFar": su.rounded(su.metres_to_units(w["fog_day_far_m"]), 2),
                    "nightNear": su.rounded(su.metres_to_units(w["fog_night_near_m"]), 2),
                    "nightFar": su.rounded(su.metres_to_units(w["fog_night_far_m"]), 2),
                    "dayPower": 1.0, "nightPower": 1.0, "dayMax": 1.0, "nightMax": 1.0},
            "images": {"sunrise": images[w["image_dawn_id"]]["formKey"], "day": images[w["image_day_id"]]["formKey"],
                       "sunset": images[w["image_dawn_id"]]["formKey"],
                       "night": images[w["image_night_id"]]["formKey"]},
            "clouds": {"speed": cloud, "colours": col["cloudLodDiffuse"],
                       "alpha": {"sunrise": 1.0, "day": 1.0, "sunset": 1.0, "night": 1.0}},
            "windSpeed": wind, "transDelta": 4.0, "sunGlare": glare, "sunDamage": damage,
            "precipitationFadeIn": pin, "precipitationFadeOut": pout, "thunderFrequency": thunder,
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
            over["persistentRefs"] = refs + border_wall_refs(alloc, GameGround().z)
            recs += bases
        recs.append(over)
    return [Layer("base:regions", recs)]
