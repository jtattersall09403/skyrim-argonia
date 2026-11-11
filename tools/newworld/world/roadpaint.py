"""How a road or a path is painted into the land: the one rule the world's roads (world/texture.py), a place's paths
(tools/places/build.py plan_paths) and the place studio (tools/places/studio/web/js/path_paint.js) all follow.

Measured (docs/research/nw-02-walk5-ground.md, section 1):
- Skyrim paints the ground under a road with one dirt LTEX whose weight stays >= 0.97 to 3 m from the spine and
  falls to 0.76 at 5 m, 0.56 at 6 m, 0.36 at 8 m (the road mesh's surface edge is at 3.45 m): a ramp of about 2.5
  vertices. Expressed from the surface edge (e = distance - half width, m): 0.97 at -0.45, 0.90 at 0.55, 0.76 at
  1.55, 0.56 at 2.55, 0.36 at 4.55; ours reaches 0 at 8.55 m. A minor road or a path keeps the same shape at 0.8
  scale (it never gets narrower than 2 vertices of ramp).
- A quadrant shows at most six textures (base + five alpha layers): the landscape shader has six texture slots
  (Community Shaders Lighting.hlsl TexColor + TexLandColor2..6, two float4 blend weights of which six are used) and
  Skyrim.esm piles up at six distinct textures (7,506 quadrants) with only 337 at seven; BM&V and KoTM never pass six.
- Our road has no road mesh over it, so the land is the road: a track core and a verge. The core material hands to the
  verge over 4.5 m (2.5 vertices), never in one vertex; two track materials of the road's set vary along it (noise at
  60 to 240 m, each always 15 % or more of the core), so a change of material along a road is a long blend, never a
  join.
"""
from __future__ import annotations

import numpy as np

M_PER_UNIT = 1 / 70.0
VERTEX_M = 128 / 70.0
# the land weight a road gives its own materials, by distance from the surface edge (m, + outward)
PULL_E = (-0.45, 0.55, 1.55, 2.55, 4.55, 8.55)
PULL_W = (0.97, 0.90, 0.76, 0.56, 0.36, 0.0)
CORE_IN, CORE_OUT = -3.0, 1.5  # core share 1 inside -3 m of the edge, 0 from 1.5 m out (ramp 4.5 m)
SCALE = {"major": 1.0, "minor": 0.8}
HALF_M = {"major": 3.45, "minor": 2.0}
# a place path's style -> its class (the reach of its ramp)
STYLE_CLASS = {"road": "major", "street": "major", "path": "minor", "dirt": "minor", "track": "minor", "boardwalk": "minor"}
TRACK_MIN = 0.15  # each of a road set's two track materials keeps at least this share of the core


def pull(edge_m, scale: float = 1.0) -> np.ndarray:
    """The road's total weight at a distance (m) from its surface edge: 1 on the surface, the measured ramp beyond."""
    e = np.asarray(edge_m, np.float64) / scale
    p = np.interp(e, PULL_E, PULL_W)
    return np.where(e <= PULL_E[0], np.clip(PULL_W[0] + (PULL_E[0] - e) * 0.03 / 1.5, PULL_W[0], 1.0), p)


def reach_m(scale: float = 1.0) -> float:
    """How far beyond the surface edge a road paints at all."""
    return PULL_E[-1] * scale


def core_share(edge_m, scale: float = 1.0) -> np.ndarray:
    """Of the road's weight, the share of its track core (the rest is the verge)."""
    e = np.asarray(edge_m, np.float64) / scale
    return np.clip((CORE_OUT - e) / (CORE_OUT - CORE_IN), 0, 1)


def track_mix(t) -> np.ndarray:
    """Along-road noise in [-1, 1] -> the share of the set's first track material, kept in [TRACK_MIN, 1-TRACK_MIN]."""
    s = 0.5 + 0.5 * np.tanh(1.6 * np.asarray(t, np.float64))
    return TRACK_MIN + (1 - 2 * TRACK_MIN) * s


def road_weights(edge_m, scale: float, mix) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """-> (pull, track A weight, track B weight, verge weight), each a fraction of the vertex (they sum to pull)."""
    p = pull(edge_m, scale)
    c = core_share(edge_m, scale)
    m = track_mix(mix)
    return p, p * c * m, p * c * (1 - m), p * (1 - c)


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
    "clay": ("earth_track", "mud_track", "clay_verge"),       # red clay mounds and flood plains
}
ROAD_MATERIALS = sorted({m for s in ROAD_SETS.values() for m in s})
