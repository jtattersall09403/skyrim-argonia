"""L1 (lane 1.15-r6-fog-yellow, owner #41 19:05: "I don't want that smoggy yellow ever"): no weather a region list
draws paints a fog or sky slot yellow or olive (hue 30-80 deg, saturation over 0.25) at any time of day unless
the template it was seeded from does there, and no rain, storm or overcast image space tints the screen. Judged on the
colours the record is written with: the sky paint (upper, lower, horizon) is always the resolved template's, every
colour of a clear (Pleasant) weather is, the rest are our rows; a referenced Tropical Skyrim weather is judged on its
own record. Skipped without game data (the templates are the game's)."""
import colorsys
import os
from pathlib import Path

import pytest

from tools.argonia_world import db
from tools.argonia_world.regions import api

GAME = Path(os.environ.get("ARGONIA_GAME_ROOT", Path.home() / "games/skyrimse")) / "Data"
SLOTS = ("fogNear", "fogFar", "skyUpper", "skyLower", "horizon")
SKY = ("skyUpper", "skyLower", "horizon")


def yellow(rgb: bytes) -> bool:
    h, s, _ = colorsys.rgb_to_hsv(*(c / 255 for c in rgb[:3]))
    return 30 <= h * 360 <= 80 and s > 0.25


def test_yellow_catches_the_tundra_storm_fog_and_passes_slate():
    assert yellow(bytes.fromhex("D7BC22")) and yellow(bytes.fromhex("666242"))  # SkyrimStormRainTU day fog
    assert not yellow(bytes.fromhex("6E7D6B")) and not yellow(bytes.fromhex("727A71"))  # wet-rain's slate fog


@pytest.mark.skipif(not (GAME / "Skyrim.esm").exists(), reason="no game data")
def test_no_listed_weather_paints_a_yellow_sky_its_template_does_not():
    w = db.open()
    listed = set(w.values("SELECT DISTINCT weather_id FROM land_region_weather"))
    errs = []
    for r in w.query("SELECT w.id, w.form_key, w.template_form_key, s.classification FROM weather w LEFT JOIN "
                     "weather_sky s ON s.weather_id = w.id ORDER BY w.id"):
        if r["id"] not in listed:
            continue
        if r["form_key"]:  # a referenced weather draws its own record: none of its slots may be yellow by day
            own = api.template_colours(r["form_key"])
            errs += [f"{r['id']} {s} day {own[(s, 'day')].hex()}" for s in SLOTS if yellow(own[(s, "day")])]
            continue
        tpl = api.template_colours(r["template_form_key"])
        ours = {(x["slot"], x["tod"]): bytes.fromhex(x["rgb"]) for x in
                w.query("SELECT slot, tod, rgb FROM weather_colour WHERE weather_id = ?", r["id"])}
        for s in SLOTS:
            for t in api.TOD:
                sky = s in SKY and r["id"] not in api.NEUTRAL_SKY
                drawn = tpl[(s, t)] if sky or r["classification"] == "Pleasant" else ours[(s, t)]
                if yellow(drawn) and not yellow(tpl[(s, t)]):
                    errs.append(f"{r['id']} {s} {t} {drawn.hex()} (template {tpl[(s, t)].hex()})")
    assert errs == []


def test_rain_storm_and_overcast_images_keep_our_untinted_grade():
    w = db.open()
    graded = api.template_graded(w)
    for r in w.query("SELECT w.id, w.image_day_id d, w.image_dawn_id a FROM weather w JOIN weather_sky s ON "
                     "s.weather_id = w.id WHERE s.classification != 'Pleasant'"):
        for i in (r["d"], r["a"]):
            if i in graded:
                continue  # a clear weather's own image (dawn), the template's grade by lane 1.15-r6-light
            row = w.query("SELECT tint_amount FROM image_space WHERE id = ?", i)[0]
            assert row["tint_amount"] == 0.0, (r["id"], i)
    assert not graded & {"rain", "storm", "overcast"}


def test_grade_ab_twin_is_clear_dry_on_skyrims_own_clear_light_and_grade():
    """The owner's noon-cast A/B (lane 1.15-r6-water-look-2): clear-dry-neutral is clear-dry but for its day image
    space, and both resolve to Skyrim.esm's own records (SkyrimClear, ISSkyrimClearDAY_FF), in no region's list."""
    from tools.argonia_world import db
    from tools.argonia_world.formids import Allocator
    w = db.open()
    a, b = (dict(w.query("SELECT * FROM weather WHERE id = ?", i)[0]) for i in ("clear-dry", "clear-dry-neutral"))
    assert {k for k in a if a[k] != b[k]} == {"id", "edid", "image_day_id", "why"}
    assert b["image_day_id"] == "day-neutral" and a["image_day_id"] == "day"
    col = "SELECT slot, tod, rgb FROM weather_colour WHERE weather_id = ? ORDER BY slot, tod"
    assert [tuple(r) for r in w.query(col, "clear-dry")] == [tuple(r) for r in w.query(col, "clear-dry-neutral")]
    assert not w.query("SELECT 1 FROM land_region_weather WHERE weather_id = 'clear-dry-neutral'")
    imgs, _ = api._image_records(Allocator(w, frozen=True), w)
    by = {r["edid"]: r for r in imgs}
    n, t = by["ARG_ImageSpace_day_skyrim"], by["ARG_ImageSpace_marsh_day"]
    assert n["template"] == t["template"] == "10A1EE:Skyrim.esm" and n["gradeFromTemplate"] and t["gradeFromTemplate"]
    assert n["templatePlugin"] == "Skyrim.esm" and t["templatePlugin"] == "Tropical Skyrim.esp"
    wx = {r["edid"]: r for r in api._weather_records(Allocator(w, frozen=True), w, _)}
    assert wx["ARG_Weather_clear_dry_neutral"]["templatePlugin"] == "Skyrim.esm"
    assert wx["ARG_Weather_clear_dry_neutral"]["formKey"] == "000F03:Argonia.esm"
    assert wx["ARG_Weather_clear_dry_neutral"]["lightFromTemplate"]


# --- the olive lint (lane 1.15-r6-storm-grey, owner #41 19:05: "I don't want that smoggy yellow ever") -------------
LINT_SLOTS = ("skyUpper", "skyLower", "horizon", "fogNear", "fogFar", "ambient", "dalcUp", "dalcSide", "dalcDown",
              "cloudLodDiffuse", "cloudLodAmbient")
# The one exception list: (weather, slot, time of day) -> why. Every other drawn sky, fog, ambient or cloud slot of
# every weather we write is outside hue 40-100 deg or at saturation 0.12 or under.
_TS = "the template's own (Tropical Skyrim's SkyrimClear, taken whole by r6-light; the owner's A/B #43 rules it)"
_DAWN = "ours: a dry or mist weather's warm dawn and ground light (ambient, directional), not a rain family; " \
        "this lane fixes the rain and storm family only, the rest is owed to the planner (lane 1.15-r6-storm-grey §6)"
_GOLD = "ours by design: tannin-haze's brown-gold air (climatology §4), a dry haze"
EXCEPT = {
    **{(w, "fogNear", "day"): _TS for w in ("clear-dry", "clear-dry-neutral")},
    **{(w, "cloud28", "sunset"): _TS for w in ("clear-dry", "clear-dry-neutral")},
    ("wet-rain", "cloud9", "sunrise"): "SkyrimOvercastRainFF's dawn cloud layer 9 (636549), as on every vanilla "
    "overcast rain (0034); the writer copies cloud layers whole from the template",
    **{(m, s, t): _DAWN for m in ("mist", "mist-20m", "mist-25m", "mist-2m", "mist-49m", "mist-6m")
       for s, t in (("ambient", "sunrise"), ("dalcSide", "sunrise"), ("dalcDown", "sunrise"), ("dalcDown", "night"))},
    **{("monsoon-overcast", s, t): _DAWN for s, t in (
        ("fogFar", "sunrise"), ("ambient", "sunrise"), ("ambient", "sunset"), ("dalcUp", "sunset"),
        ("dalcSide", "sunrise"), ("dalcSide", "day"), ("dalcDown", "sunrise"), ("dalcDown", "day"))},
    **{(m, s, t): _DAWN for m in ("montane-haze", "montane-haze-68m") for s, t in (
        ("ambient", "sunrise"), ("ambient", "sunset"), ("dalcUp", "sunset"), ("dalcSide", "sunrise"),
        ("dalcSide", "sunset"), ("dalcDown", "sunrise"), ("dalcDown", "night"))},
    **{("tannin-haze", s, t): _GOLD for s, t in (
        ("ambient", "sunrise"), ("ambient", "day"), ("cloudLodDiffuse", "day"), ("cloudLodAmbient", "day"),
        ("dalcUp", "day"), ("dalcSide", "day"), ("dalcSide", "night"), ("dalcDown", "night"))},
}


def olive(rgb: bytes, sat: float = 0.12) -> bool:
    h, s, _ = colorsys.rgb_to_hsv(*(c / 255 for c in rgb[:3]))
    return 40 <= h * 360 <= 100 and s > sat


def test_olive_catches_the_storm_fog_and_passes_its_grey():
    assert olive(bytes.fromhex("5D6355")) and olive(bytes.fromhex("44503C"))  # storm noon fog far and ambient, r6
    assert not olive(bytes.fromhex("737373")) and not olive(bytes.fromhex("677C83"))  # grey; the slate noon zenith


def _cloud_layers(form_key: str) -> dict:
    """The template's drawn cloud layer colours {(cloudN, tod): rgb}: the layers NAM1 leaves on (its bits are the
    disabled layers), as the writer copies them (coloursFromTemplate)."""
    import struct
    from tools.argonia_world.water.layer import top_group
    p, fid = api.template_plugin(form_key), int(form_key.split(":")[0], 16)
    r = next(x for x in top_group(GAME / p, b"WTHR") if x.formid & 0xFFFFFF == fid)
    off = struct.unpack("<I", r.first("NAM1")[:4])[0] if r.first("NAM1") else 0
    pn = r.first("PNAM") or b""
    return {(f"cloud{k}", t): pn[k * 16 + i * 4:k * 16 + i * 4 + 3] for k in range(len(pn) // 16)
            if not off >> k & 1 for i, t in enumerate(api.TOD)}


@pytest.mark.skipif(not (GAME / "Skyrim.esm").exists(), reason="no game data")
def test_no_weather_we_write_draws_an_olive_sky_fog_ambient_or_cloud_slot():
    w = db.open()
    errs, used = [], set()
    for r in w.query("SELECT w.id, w.template_form_key t, s.classification c FROM weather w JOIN weather_sky s ON "
                     "s.weather_id = w.id WHERE w.template_form_key IS NOT NULL ORDER BY w.id"):
        tpl = api.template_colours(r["t"])
        ours = {(x["slot"], x["tod"]): bytes.fromhex(x["rgb"]) for x in
                w.query("SELECT slot, tod, rgb FROM weather_colour WHERE weather_id = ?", r["id"])}
        pleasant = r["c"] == "Pleasant"
        drawn = {}
        for s in LINT_SLOTS:
            if s.startswith("dalc") and pleasant:
                continue  # the template's own directional ambient (ambientFromTemplate)
            for t in api.TOD:
                from_tpl = pleasant or (s in SKY and r["id"] not in api.NEUTRAL_SKY)
                drawn[(s, t)] = tpl[(s, t)] if from_tpl else ours[(s, t)]
        drawn.update({k: v for k, v in _cloud_layers(r["t"]).items() if any(v)})
        for (s, t), c in sorted(drawn.items()):
            if olive(c):
                if (r["id"], s, t) in EXCEPT:
                    used.add((r["id"], s, t))
                else:
                    errs.append(f"{r['id']} {s}@{t} {c.hex().upper()}")
        if r["id"] in api.NEUTRAL_SKY:  # the rain and storm sunlight is a warm-neutral grey
            errs += [f"{r['id']} sunlight@{t} {ours[('sunlight', t)].hex().upper()}" for t in api.TOD
                     if colorsys.rgb_to_hsv(*(c / 255 for c in ours[("sunlight", t)]))[1] >= 0.15]
    assert errs == []
    assert set(EXCEPT) - used == set(), "an exception no longer needed: drop it"
