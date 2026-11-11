"""How a road or a path is painted into the land: the one rule the world's roads (world/texture.py), a place's paths
(tools/places/build.py plan_paths) and the place studio (tools/places/studio/web/js/path_paint.js) all follow, with no
smoothing after it: the rule is soft by itself, so all three paint the same numbers.

Measured (docs/research/nw-02-walk5-ground.md, section 2):
- Skyrim paints the ground under a road mesh with the region's dirt LTEX. Over six holds' straight road pieces its
  mean weight is 0.91 to 0.99 at 3 m from the spine (the mesh's surface edge is at 3.45 m) and falls to 0.39 to 0.78
  at 8 m; the steepest metre of any hold's mean ramp is 0.17 (Whiterun, 5 to 6 m), 0.31 a vertex. Ours is one straight
  ramp from 0.97 at 0.45 m inside the surface edge to 0 at 8.55 m outside it: 0.108 a metre, 0.20 a vertex (0.25 for
  a minor road or a path, whose ramp is 0.8 as long), between Whiterun's and Falkreath's.
- A quadrant shows at most six textures (base + five alpha layers): the landscape shader has six texture slots
  (Community Shaders Lighting.hlsl TexColor + TexLandColor2..6, two float4 blend weights of which six are used) and
  Skyrim.esm piles up at six distinct textures (7,506 quadrants) with only 337 at seven; BM&V and KoTM never pass six.
- Our road has no road mesh over it, so the land is the road: a track core and a verge. The core is whole on a major
  road's spine and falls to nothing over 6.5 m (3.6 vertices: 0.28 a vertex), the same on every class, so a path's
  spine is four fifths track, and the verge holds the rest of the road's weight; two track materials of the road's
  set vary along it (noise at 60 to 240 m, each always 15 % or more of the core), so a change of material along or
  across a road is a ramp, never a join.
- No road material grows grass, and the road holds 0.97 or more to 3 m from a major spine and 1.6 m from a minor one:
  no grass-bearing ground reaches a spine.
"""
from __future__ import annotations

import numpy as np

M_PER_UNIT = 1 / 70.0
VERTEX_M = 128 / 70.0
# the land weight a road gives its own materials, by distance from the surface edge (m, + outward)
PULL_E = (-0.45, 8.55)
PULL_W = (0.97, 0.0)
CORE_IN, CORE_OUT = -3.45, 3.05  # core share 1 on a major spine, 0 from 3.05 m outside the edge (ramp 6.5 m)
SCALE = {"major": 1.0, "minor": 0.8}
HALF_M = {"major": 3.45, "minor": 2.0}
# a place path's style -> its class (the reach of its ramp)
STYLE_CLASS = {"road": "major", "street": "major", "path": "minor", "dirt": "minor", "track": "minor", "boardwalk": "minor"}
TRACK_MIN = 0.15  # each of a road set's two track materials keeps at least this share of the core


def pull(edge_m, scale: float = 1.0) -> np.ndarray:
    """The road's total weight at a distance (m) from its surface edge: 1 on the surface, its straight ramp beyond."""
    e = np.asarray(edge_m, np.float64) / scale
    p = np.interp(e, PULL_E, PULL_W)
    return np.where(e <= PULL_E[0], np.clip(PULL_W[0] + (PULL_E[0] - e) * 0.03 / 1.5, PULL_W[0], 1.0), p)


def reach_m(scale: float = 1.0) -> float:
    """How far beyond the surface edge a road paints at all."""
    return PULL_E[-1] * scale


def core_weight(edge_m) -> np.ndarray:
    """The most the track core can hold at a distance (m) from the surface edge: 1 on a major spine, a straight ramp
    to 0 at CORE_OUT, the same on every class (the verge has the rest of the road's weight)."""
    e = np.asarray(edge_m, np.float64)
    return np.clip((CORE_OUT - e) / (CORE_OUT - CORE_IN), 0, 1)


def track_mix(t) -> np.ndarray:
    """Along-road noise in [-1, 1] -> the share of the set's first track material, kept in [TRACK_MIN, 1-TRACK_MIN]."""
    s = 0.5 + 0.5 * np.tanh(1.6 * np.asarray(t, np.float64))
    return TRACK_MIN + (1 - 2 * TRACK_MIN) * s


def road_weights(edge_m, scale, mix) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """-> (pull, track A weight, track B weight, verge weight), each a fraction of the vertex (they sum to pull). The
    core is the lower of its own ramp and the pull, so no material of a road changes faster than the steeper of the
    two ramps."""
    p = pull(edge_m, scale)
    c = np.minimum(p, core_weight(edge_m))
    m = track_mix(mix)
    return p, c * m, c * (1 - m), p - c


def layer_opacities(edge_m, scale: float, mix=0.0) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """The same weights as three alpha layers laid over any ground, bottom first (verge, track B, track A): the
    opacities whose composite is road_weights exactly (o_top = w_top, each lower = w / what is left above it)."""
    p, a, b, v = road_weights(edge_m, scale, mix)
    oa = a
    left = 1 - oa
    ob = np.where(left > 1e-9, b / np.maximum(left, 1e-9), 0)
    left = left * (1 - ob)
    ov = np.where(left > 1e-9, v / np.maximum(left, 1e-9), 0)
    return np.clip(ov, 0, 1), np.clip(ob, 0, 1), np.clip(oa, 0, 1)


# Road sets: the two track materials and the verge of a road, by the ground it crosses (texture.py MATERIALS ids).
# Colours of the diffuses as the NewWorld profile resolves them (mean RGB, luminance; contrast = luminance std):
#   gravel_track  BM&V dirtroad01            (81,69,51)  lum 70  contrast 13.6  grey-brown gravel
#   earth_track   TS Tundra02                (112,84,46) lum 87  contrast 14.4  dry ochre earth with tufts
#   mud_track     TS RiverMud                (85,68,47)  lum 70  contrast 12.7  fine brown mud
#   sand_track    BM&V Sand06                (91,74,53)  lum 76  contrast 12.2  rippled brown sand
#   verge         TS DirtSnowPath01          (88,74,47)  lum 75  contrast 13.6  trodden earth with grass in it
#   clay_verge    TS FieldGrass01            (121,89,58) lum 94  contrast 8.8   pale sandy earth
# (the old road: BM&V dirtroad01 core and vanilla LDirt02 skirt, which the NewWorld profile shows as Tropical
# Skyrim's dirt02: (52,36,23), lum 39, contrast 9.0, the darkest flat ground we painted.)
ROAD_SETS = {
    "marsh": ("mud_track", "gravel_track", "verge"),       # wet lowland: mud and gravel through a grassy verge
    "forest": ("gravel_track", "mud_track", "verge"),      # forest and swamp hummock: gravel first
    "upland": ("earth_track", "gravel_track", "clay_verge"),  # dry ridges, mesas and scrub
    "coast": ("sand_track", "gravel_track", "clay_verge"),    # sandy coasts and grassland
    "clay": ("mud_track", "gravel_track", "clay_verge"),      # red clay mounds and flood plains
}
ROAD_MATERIALS = sorted({m for s in ROAD_SETS.values() for m in s})
# Every set carries COMMON_TRACK (at least TRACK_MIN of its core), so wherever a road has a core, every quadrant round
# it can keep one road material in common however few texture slots it has.
COMMON_TRACK = "gravel_track"
