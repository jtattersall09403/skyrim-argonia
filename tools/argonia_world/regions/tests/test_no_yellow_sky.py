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
                drawn = tpl[(s, t)] if s in SKY or r["classification"] == "Pleasant" else ours[(s, t)]
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
