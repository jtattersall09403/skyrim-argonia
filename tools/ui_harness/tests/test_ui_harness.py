"""The gate's part of 1.2's L3 harness: the smoke subset (300 topics, the wiring, one still per view on the folded
Magic V5) and the chart fixture's agreement with out/chart's index. The full run is `make ui-stills`."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from tools.ui_harness import chart_fixture

CHROMIUM = list((Path.home() / ".cache" / "ms-playwright").glob("chromium_headless_shell-*"))


@pytest.mark.skipif(not chart_fixture.INDEX.exists(), reason="out/chart not rendered (make chart)")
def test_chart_fixture_agrees_with_the_index():
    fx = json.loads(chart_fixture.FIXTURE.read_text())
    assert chart_fixture.made(fx, json.loads(chart_fixture.INDEX.read_text())) == fx, \
        "run python -m tools.ui_harness.chart_fixture"


@pytest.mark.skipif(importlib.util.find_spec("playwright") is None or not CHROMIUM,
                    reason="Playwright or its headless shell not installed (infra/build-vm/toolchain.lock)")
def test_smoke(tmp_path):
    from tools.ui_harness.harness import run

    r = run(smoke=True, out=tmp_path, shoot=False)
    assert r["fails"] == [], r["fails"]
    t = r["stills"]["dialogue/threeHundredTopics@v5-folded"]["topics"]
    assert t["fails"] == [] and t["visibleRows"] >= 8
    assert len(r["stills"]) >= 4
