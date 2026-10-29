"""The chart's gate tests (L1, on the synthetic sample; the real render's checks run under `make chart`)."""
from __future__ import annotations

import pytest

pytest.importorskip("PIL")

from tools.chart import checks, render, sample


@pytest.fixture(scope="module")
def font():
    p = render.font_path()
    if not p.exists():
        pytest.skip(f"Pelagiad not fetched ({p}): python -m tools.chart fetch-font")
    return p


@pytest.fixture(scope="module")
def chart(font):
    return sample.render_sample()


def test_sample_hash_is_pinned_and_deterministic(chart):
    a = sample.sample_hash()
    assert a == sample.sample_hash(), "two renders of the sample differ"
    assert a == sample.pinned(), "the drawing changed: look at the stills, then re-pin sample-manifest.json"


def test_cities_at_db_position_and_inked(chart):
    f = sample.features()
    rep = checks.run_all(chart, f)
    rows = rep["cities"]["rows"]
    assert len(rows) == 7 and all(r["position_ok"] and r["on_land"] and r["inked"] for r in rows)
    assert rep["rivers"]["ok"] and rep["roads"]["ok"], (rep["rivers"], rep["roads"])
    assert rep["no_player_marker"]["ok"]


def test_y_runs_south_no_flip(chart):
    """A place further south (larger y_m) is lower on the chart; further east is further right."""
    pl = chart.index["places"]
    soulrest, stormhold = pl["place.mercantile-coast.soulrest"]["px"], pl["place.dunmer-north.stormhold"]["px"]
    assert soulrest[1] > stormhold[1] and soulrest[0] < stormhold[0]


def test_every_cell_in_one_tile(chart):
    t = chart.index["tile"]
    for tx, ty, x, y, w, h in chart.index["cells"].values():
        assert int(x // t) == tx and int((x + w - 1e-6) // t) == tx
        assert int(y // t) == ty and int((y + h - 1e-6) // t) == ty


def test_layers_shapes(chart):
    s = sample.SIZE
    assert chart.base.shape == (s, s, 3) and chart.ink.shape == (s, s, 4) and chart.revealed.shape == (s, s, 4)
    assert chart.ink[..., 3].any() and chart.revealed[..., 3].any()
