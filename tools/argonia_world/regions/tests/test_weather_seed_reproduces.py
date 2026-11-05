"""The seed (weather_seed.py via migrate --weathers-1-15) reproduces every weather row of the committed database."""
import json
import shutil
from pathlib import Path

from tools.argonia_world import db
from tools.argonia_world.regions import migrate

TABLES = ("image_space", "weather", "weather_colour", "weather_sky", "weather_realisation", "land_region_weather",
          "mist_regime", "mist_regime_season", "region_mist", "weather_mist_band", "climate")


def _rows(w, t):
    return sorted(json.dumps(dict(r), sort_keys=True) for r in w.query(f"SELECT * FROM {t}"))


def test_reseed_reproduces_database(tmp_path: Path):
    shutil.copytree(db.WORLD_ROOT / "world", tmp_path / "world", ignore=shutil.ignore_patterns("sources", "out"))
    w = db.open(tmp_path, cache=False)
    before = {t: _rows(w, t) for t in TABLES}
    migrate.weathers_1_15(w)  # in memory: save() would also run the slot checks, which the DB already passes
    for t in TABLES:
        assert _rows(w, t) == before[t], t
