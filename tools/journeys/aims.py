"""Aim overrides (owner 19:05 #41, decision 0036's amendment): when the reader judges a stop's scan and names the heading
that shows the subject, `python3 -m tools.journeys ledger aim <journey> <step> <heading> [--pitch P]` records it in
tests/journeys/aims.yaml (tracked: it survives a machine and is reviewed), with the stand's x, y at that moment.
Every generator applies it to that step's `player.setangle` lines (`apply_text`), keeping the stand; an override whose
stand has moved more than DROP_M from the recorded one is dropped on refresh (`prune`) and reported.
"""
from __future__ import annotations

import math

import yaml

from tools.argonia_world import skyrim_units as su
from tools.journeys import JOURNEYS, MOVETO, SETANGLE, SETPOS, steps_of

PATH = JOURNEYS / "aims.yaml"
DROP_M = 5.0
HEAD = ("# Aim overrides (tools/journeys/aims.py): a reader-named heading (and pitch) for one journey step, kept while\n"
        "# the stand stays within 5 m of the x, y recorded. Written by `python3 -m tools.journeys ledger aim`.\n")
DROPPED: list = []   # overrides apply_text found moved; `prune` removes them from the file


def load(path=None) -> list[dict]:
    p = path or PATH
    if not p.is_file():
        return []
    return (yaml.safe_load(p.read_text()) or {}).get("aims") or []


def _save(rows: list[dict], path=None) -> None:
    (path or PATH).write_text(HEAD + yaml.safe_dump({"aims": rows}, sort_keys=False))


def record(journey: str, step: str, heading: float, pitch: float | None, x: float, y: float, path=None) -> dict:
    row = {"journey": journey, "step": step, "heading": float(heading), "x": round(x), "y": round(y)}
    if pitch is not None:
        row["pitch"] = float(pitch)
    rows = [r for r in load(path) if (r["journey"], r["step"]) != (journey, step)] + [row]
    _save(rows, path)
    return row


def stand_of(blk: str, resolve_ref) -> tuple[float, float] | None:
    """The step block's stand: its setpos x, y, else its first moveto's ref (resolve_ref(edid) -> (x, y)) plus offset."""
    pos = {k: float(v) for k, v in SETPOS.findall(blk)}
    if {"x", "y"} <= set(pos):
        return pos["x"], pos["y"]
    for ref, off in MOVETO.findall(blk):
        r = resolve_ref(ref)
        if r:
            o = [float(v) for v in off.split()] if off else [0.0, 0.0, 0.0]
            return r[0] + o[0], r[1] + o[1]
    return None


def stand_in(journey: str, step: str, text: str, resolve_ref) -> tuple[float, float] | None:
    lines = text.splitlines()
    for name, a, z in steps_of(text):
        if name == step:
            return stand_of("\n".join(lines[a:z]), resolve_ref)
    return None


def apply_text(journey: str, text: str, resolve_ref=lambda edid: None, rows: list[dict] | None = None) -> str:
    """The journey's text with each step's override heading (and pitch) put on its setangle lines. An override whose
    stand moved more than DROP_M from the recorded one is left unapplied and queued in DROPPED."""
    mine = {r["step"]: r for r in (load() if rows is None else rows) if r["journey"] == journey}
    if not mine:
        return text
    lines = text.splitlines()
    for name, a, z in steps_of(text):
        r = mine.get(name)
        if not r:
            continue
        st = stand_of("\n".join(lines[a:z]), resolve_ref)
        if st is None:
            continue
        if math.hypot(st[0] - r["x"], st[1] - r["y"]) > DROP_M * su.UNITS_PER_METRE:
            if r not in DROPPED:
                DROPPED.append(r)
            print(f"aim override dropped: {journey} {name}: the stand moved "
                  f"{math.hypot(st[0] - r['x'], st[1] - r['y']) / su.UNITS_PER_METRE:.1f} m (more than {DROP_M:.0f} m)")
            continue
        ang = {"z": r["heading"], "x": r.get("pitch")}
        for i in range(a, z):
            lines[i] = SETANGLE.sub(lambda m: m.group(0) if ang[m.group(1)] is None
                                    else f"player.setangle {m.group(1)} {ang[m.group(1)]:.0f}", lines[i])
        print(f"aim override: {journey} {name} {r['heading']:.0f}")
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def prune(path=None) -> list[dict]:
    """Remove the dropped overrides from the file; the ones removed."""
    gone = list(DROPPED)
    DROPPED.clear()
    if gone:
        _save([r for r in load(path) if r not in gone], path)
    return gone
