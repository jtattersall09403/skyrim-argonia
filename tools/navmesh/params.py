"""The navmesh job's numbers, each with where it comes from (docs/research/journals/navmesh.md).

Units are Skyrim units unless named. The CK's own generator defaults are tes4skyrim's reading of the CK's
`[Recast]` settings (docs/commentary/ck_navmesh_generation.md, commit 2abe3ce); the vanilla figures are measured on
Skyrim.esm by `python -m tools.navmesh vanilla`.
"""
from __future__ import annotations

MAX_SLOPE_DEG = 45.0  # the CK's fRecastAgentMaxSlope and fMaxWalkableAngle: Skyrim's walkable angle
AGENT_HEIGHT = 128.0  # fRecastAgentHeight
AGENT_RADIUS = 32.0  # fRecastAgentRadius
AGENT_CLIMB = 32.0  # fRecastAgentMaxClimb
EDGE_MAX_LEN = 512.0  # fRecastEdgeMaxLen
CELL_SIZE = 16.0  # voxel width (the CK's 8 is for placed meshes): Recast's ledge filter refuses a span whose
# reachable neighbours (one voxel each way) differ by more than the climb, a slope cut of atan(climb / 2 cs): 45
# degrees at 16, the walkable angle (at 32 it was 26.6 and dropped 42% of the walkable ground, measured on Claywater)
CELL_HEIGHT = 8.0  # fRecastCellHeight
EDGE_MAX_ERROR = 1.3  # fRecastEdgeMaxError, in voxels as Recast reads it
REGION_MIN_SIZE = 50  # uRecastRegionMinSize, spans
REGION_MERGE_SIZE = 20  # uRecastRegionMergeSize, spans
VERTS_PER_POLY = 6  # Recast's default; the detail mesh triangulates every polygon
DETAIL_SAMPLE_DIST = 6 * CELL_SIZE  # Recast's sample-demo default (6 voxels)
DETAIL_SAMPLE_MAX_ERROR = 2 * CELL_HEIGHT  # the detail mesh keeps within two voxel heights of the ground
SNAP_MAX = 64.0  # a vertex within this of the ground is put back on it (Recast heights are voxel tops)
WELD_Z = 16.0  # detail vertices at one plan position within this height are one vertex
BORDER_SAMPLES = 2  # the ground read beyond each cell edge (256 units, 8 voxels), so erosion and ledges see across
WATER_MAX_DEPTH = 1000.0  # deeper water has no navmesh: vanilla water triangles lie on the bed, 99% within 953
TOLERANCE_Z = 32.0  # L1: a vertex within this of the ground (two detail errors), or of the water surface
SEAM_DZ = 64.0  # a cross-cell edge pair links when both its ends are within this height
ISLAND_REPORT_M2 = 100.0  # L1: every island (a component apart from the main one) larger than this is listed, m^2


def recast() -> dict:
    """The parameters ArgoniaNav reads from grid.json."""
    return {"snapMax": SNAP_MAX, "cs": CELL_SIZE, "ch": CELL_HEIGHT, "maxSlopeDeg": MAX_SLOPE_DEG, "agentHeight": AGENT_HEIGHT,
            "agentRadius": AGENT_RADIUS, "agentClimb": AGENT_CLIMB, "edgeMaxLen": EDGE_MAX_LEN,
            "edgeMaxError": EDGE_MAX_ERROR, "detailSampleDist": DETAIL_SAMPLE_DIST,
            "detailSampleMaxError": DETAIL_SAMPLE_MAX_ERROR, "waterMaxDepth": WATER_MAX_DEPTH, "weldZ": WELD_Z,
            "borderSamples": BORDER_SAMPLES, "regionMinSize": REGION_MIN_SIZE,
            "regionMergeSize": REGION_MERGE_SIZE, "vertsPerPoly": VERTS_PER_POLY}
