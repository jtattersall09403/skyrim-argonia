"""The chart's source stamp is its own inputs (lane 1.15-r6-chart-stamp): a place or road changes it, a creature or
water record (not read) does not."""
from __future__ import annotations

import sqlite3

import pytest

from tools.argonia_world import db
from tools.chart import __main__ as chart_main


@pytest.fixture(scope="module")
def world():
    return db.open()


def _stamp_with(world, sql, params=()):
    """The stamp over a copy of the world's database, after one write."""
    mem = sqlite3.connect(":memory:")
    world.con.backup(mem)
    mem.execute(sql, params)

    class W:
        def query(self, q, *p):
            cur = mem.cursor()
            cur.row_factory = sqlite3.Row
            return cur.execute(q, p).fetchall()

    return chart_main.source_stamp(W())


def test_stamp_is_stable(world):
    assert chart_main.source_stamp(world) == chart_main.source_stamp(world)


def test_place_and_road_change_the_stamp(world):
    base = chart_main.source_stamp(world)
    assert _stamp_with(world, "UPDATE place SET position_m_x = position_m_x + 1 WHERE position_m_x IS NOT NULL") != base
    assert _stamp_with(world, "UPDATE road_point SET x_m = x_m + 1") != base


def test_unrelated_change_leaves_it(world):
    base = chart_main.source_stamp(world)
    tabs = [r[0] for r in world.query("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%creature%'")]
    if not tabs:
        pytest.skip("no creature table")
    col = world.query(f"PRAGMA table_info({tabs[0]})")[0]["name"]
    assert _stamp_with(world, f"UPDATE {tabs[0]} SET {col} = {col}") == base
