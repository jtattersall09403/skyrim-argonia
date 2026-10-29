"""Skyrim's unit facts, the only place they live (decision 0009 §4; CLAUDE.md "Skyrim unit facts live only in
the units module"). Every other module converts through these names; a literal 70.03, 4096 or 0x800 elsewhere
is a bug the gate's grep finds (tests/test_skyrim_units.py).

World frame: metres, x east, y north, z up, yaw degrees clockwise from north (the imported records' frame).
Skyrim frame: units, same axes, rotations in radians applied Z then Y then X (Euler ZYX, extrinsic).
"""
from __future__ import annotations

import math

# --- distance -------------------------------------------------------------------------------------------------
UNITS_PER_METRE = 70.03  # 0009 §4; the heightfield's 1.828 m sample is 128 units
VERTEX_SPACING_UNITS = 128  # LAND vertex spacing
CELL_UNITS = 4096  # an exterior cell's side
LAND_VERTS = 33  # LAND vertices per cell side (32 quads + the shared edge)
LAND_QUADRANT_LAYERS = 6  # texture layers per quadrant, the base layer excluded
VHGT_STEP_UNITS = 8  # one VHGT signed byte step
CELL_METRES = CELL_UNITS / UNITS_PER_METRE  # 58.49 m


def metres_to_units(m: float) -> float:
    return m * UNITS_PER_METRE


def units_to_metres(u: float) -> float:
    return u / UNITS_PER_METRE


def cell_of(x_units: float, y_units: float) -> tuple[int, int]:
    """The exterior cell grid coordinate holding a Skyrim-frame point."""
    return math.floor(x_units / CELL_UNITS), math.floor(y_units / CELL_UNITS)


def cell_origin(cx: int, cy: int) -> tuple[int, int]:
    """South-west corner of a cell, in units."""
    return cx * CELL_UNITS, cy * CELL_UNITS


# --- rotation -------------------------------------------------------------------------------------------------
def yaw_to_rot(yaw_deg: float) -> tuple[float, float, float]:
    """A world-frame yaw (degrees clockwise from north) as Skyrim's (rx, ry, rz) radians.

    Skyrim's z rotation is clockwise seen from above with 0 facing north (+y), the same sense as the world frame,
    so only the unit changes; it is normalised into [0, 2π) as the CK writes it.
    """
    return 0.0, 0.0, math.radians(yaw_deg) % (2 * math.pi)


def rounded(v: float, places: int = 4) -> float:
    """Positions and angles are written at a fixed precision so regeneration is byte-stable."""
    r = round(v, places)
    return 0.0 if r == 0 else r  # no -0.0


# --- FormIDs and plugins --------------------------------------------------------------------------------------
FORMID_FIRST = 0x800  # the first object id a plugin may allocate (lower ids are the engine's)
FORMID_LAST = 0xFFFFFF  # the last for a full (non-light) master
LIGHT_LAST = 0xFFF  # the last for an ESL-flagged plugin
EDITOR_ID_MAX = 99  # the CK's limit; voice paths take only the first 25 (gotcha in prior-art §3)

# The runtime's own masters, in load order (decision 0012's context); Creation Club masters follow from
# Skyrim.ccc for those present, then the dependency plugins (data/dependencies.json), then ours.
OFFICIAL_MASTERS = ("Skyrim.esm", "Update.esm", "Dawnguard.esm", "HearthFires.esm", "Dragonborn.esm")
ENGINE_MARKER_HEADING = "000034:Skyrim.esm"  # XMarkerHeading: the engine's own heading marker
