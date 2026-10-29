# Lane 2.W4-navmesh: report (first context, handed off at the context mark)

## Hand-off

**Done, committed in `2db09f8`:** `tools/navmesh/` (inputs, the DotRecast job `ArgoniaNav`, the seam stitch, the
NVNM/NVMI codec, L1 checks, the vanilla proof, 9 unit tests), `tools/ArgoniaGen/NavmeshRecords.cs` (NAVM per cell
and the NAVI override through Mutagen's own parser), the hooks in `LandWorld.cs` (3 lines) and `Program.cs`
(`world --navmesh`, `navmesh roundtrip`), `pipeline.py navmesh` and `navmesh_sample()` in `check`,
`tools/navmesh/sample-manifest.json`, DotRecast 2026.3.1 (zlib) in `data/sourcing-register.json`, the journal
`docs/research/journals/navmesh.md`, the L4 drafts, `infra/gpu-box/navmesh_ck.ps1` (not run). The `make navmesh`
target went in with another lane's commit `d0d7cc8`, which swept up the Makefile hunk.

**Left, in order:**
1. **Province numbers.** Job `nav-province-1` was still running at hand-off (in the stitch, 19 of 126 rows). Its
   log is `~/.argonia/jobs/nav-province-1.log` (`/usr/bin/time -v`: wall time and Maximum resident set size), and
   its results are `out/navmesh/province/build.json` and `check.json`. Measured so far: inputs about 15 s; Recast
   about 18 min (about 8.8 s a row on 4 threads, ArgoniaNav at 369 MB RSS); the Python process at 114 MB at the
   last read. Then put the time, the peak RSS and the check results here.
2. **The determinism hash on two builds.** It is proved on the four-cell sample: sha256 `5eed6ffd…`, the same
   before and after the inputs rewrite. ArgoniaNav's raw output is identical across a serial and a 4-thread run.
   Still owed: a second Claywater build compared against `53c94d0c…`/`8462392c…` (the hash changed with the cs-16
   and snap fixes; rebuild twice now), and a second province build.
3. **`make navmesh` end to end** (`pipeline.py:navmesh`). It has not been run. It writes ArgoniaWorld.esm with
   every NAVM and runs `checks.verify_esm`, which is proven on the sample: 4 of 4 identical, NAVI 4. Measure its
   peak RSS: the ESM writer holds every NAVM in memory, on top of the 1.08 GB the LAND write already takes.
4. **`make check` in full.** Only the parts this change reaches have run: ruff clean, `pytest tools/navmesh
   tools/ArgoniaGen` 9 passed, `navmesh_sample()` green, guard and links ok. plugin-check now also builds the
   four cells (about 5 s).
5. **Owed in game (L4):** `tests/scenes/nav-claywater.json`, `tests/journeys/nav-npc-walk.yaml` (0.4 §d),
   `nav-paths-200.yaml` and `nav-sandbox-20.yaml` (2.W4 §b). Unmeasured: whether the engine accepts a NAVI override
   that holds only our NVMI and an empty NVPP.
6. **The CK comparison:** `infra/gpu-box/navmesh_ck.ps1`. Its UI Automation names are unproven. The build-VM side
   of the comparison (reading `ArgoniaWorld-ck.esm` with `esm.py`/`nvnm.py`) is not written.

**Reds:** none known in the committed tree. The open edge: Claywater's islands (see below) are reported, not fixed.

## Province result (job `nav-province-1`, after the hand-off was written)

- **The build: done.** 23 min 32 s wall time. Peak RSS was 856 MB, under the 2 GB bar. Inputs took 17 s, Recast
  1,031 s, the stitch 270 s and the checks 94 s. It wrote 12,083 NAVM: 4,299,037 triangles, 303,494 edge links,
  745,814 water triangles and 37,155 road triangles. Records sha256 `b90943f471c1…`.
- **L1: RED (exit 1)**, on one check.
  - Heights: 57 vertices over 32 units, max 46. The likely cause is seam-split interpolation in steep cells, not
    yet diagnosed.
  - Links: 303,494, with 0 asymmetric, 0 bad targets and 0 bad geometry.
  - NAVI: 12,083 of 12,083, with 0 errors.
  - Road samples on the navmesh: 98.4%.
- **Islands:** 7,390 apart from the main component (33.3 km²), 2.36 km² in all. 1,335 are over 100 m²; the largest
  is 1.14 km². These are reported, as the brief allows.
- **Next step:** snap seam-split vertices to the ground, or measure them against the band, then re-run.

## Numbers

- **Vanilla (Skyrim.esm, read only):** the codec decodes and re-encodes 14,447 of 14,447 NVNMs byte-identical.
  The 20-NAVM round trip (17 with links, 5 water, 7 Preferred, 5 doors, 16 cover, up to 1,257 triangles) goes
  through NavmeshRecords.Parse and the Mutagen writer and comes back with NVNM 20/20 and subrecords 20/20
  byte-identical, all compressed. Rules measured: the grid divisor by triangle count (12,817/12,817), the NVMI
  location at the vertex mean (12,815), NVMI edge links equal to the NVNM's neighbours (12,817), every triangle
  CCW, water triangles on the bed (depth median 126 units, p99 953).
- **Claywater block** (cells -60,8 to -53,15, from the place row and `su.province_to_skyrim`): 64 NAVM, 38,230
  triangles, 1,776 edge links. L1 green:
  - heights: 0 vertices over 32 units (max 18, at seam splits); triangle centroids p99 19 units;
  - links: 0 asymmetric, 0 with a bad target, 0 with bad geometry;
  - NAVI: 64 entries, 0 missing, 0 errors.
  - Measured beyond L1: 97.5% of road samples lie on the navmesh. Walkable dry ground is covered 97.6% under 30°,
    77.5% at 30–40° and 23.7% at 40–45°. There are 113 islands: 21 over 100 m², the largest 923 m², 8,550 m² in
    all against a main component of 154,363 m². Steeper than 45°: 1,131 ground triangles, 970 m² (0.8%).
  - Wall time 9.8 s, peak 251 MB.
- **Key finding:** at a 32-unit voxel, Recast's ledge filter cuts the walkable slope to atan(32/64) = 26.6°, which
  lost 42% of the walkable ground. At 16 units the cut is 45°.
