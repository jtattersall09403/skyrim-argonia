# Lane 1.15-r6-ground-roads (hand-off note; in progress)

## Measured: Skyrim.esm's riverbed edge share (the bar, 0034)
`python -m tools.argonia_world.vanilla.measure q11` (Tamriel LAND, 8.20 M dry vertices; LTEX LRiverbedEdge01):
- share of all dry land 0.32 %; within 16 vertices of water 2.51 %; beyond 16 vertices 0.06 %
- 83.8 % of the edge's area lies within 16 vertices; 10.6 % of dry land is within 16 vertices
- per 8x8-cell shore window (78 windows), share within 16 v: p10 0, p50 0, p75 2.9 %, p90 6.1 %

Bar for our province: within-16 share at most 6.1 % (vanilla window p90), beyond-16 share at most 0.06 %.

## State
- Done: q11 in vanilla/measure.py.
- Next: derived textures (mips, normals with vanilla alpha) as an install step; check-materials prints the share;
  roads census on a fresh generate; rock booth framing.
