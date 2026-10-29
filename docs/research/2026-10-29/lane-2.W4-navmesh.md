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

## Continuation (second context, 2026-10-29)

**The province's first run was red.** `nav-province-1` ran for 23:32 and peaked at 856 MB. It failed on two counts.
- **Degenerate triangles:** the `invalid value in divide` was 7 zero-area triangles out of 4,299,037: 6 with a
  repeated corner and 1 with three corners on one line, in cells (-55,56), (28,-18) and (-15,-51). The cause was in
  `stitch.split_open_edges`. Recast's detail mesh leaves slivers, where a corner lies within EPS (0.5 units) of the
  opposite edge in plan. The T-junction repair split that open edge at the sliver's own corner.
  - Fix 1: `drop_slivers` removes those triangles before the repair. The repair then splits the neighbours' edges at
    the corner: 1,077 dropped on the province, 8 on Claywater.
  - Fix 2: a split never uses the triangle's own corner, and uses each point once.
  - Fix 3: the first rebuild (`nav-province-2`) still had 3 degenerate triangles, from split points a unit or two
    from a corner that lay on the line to the far corner, in cells (-41,-8) and (6,-38). `fan_points` now leaves
    out any split point that would make a fan triangle under `MIN_PLAN_AREA` (0.125 units²).
  - **The L1 check:** `checks.degenerate` (a repeated corner, or zero plan area) is part of `green`. It **failed
    once on purpose** on the pre-fix province (count 7), and again on `nav-province-2` (3). Unit tests: a test that
    reproduces the province's pattern on the old `stitch.py` (2 degenerate), the sliver drop, the fan filter and the
    mask (12 passed).
- **Heights:** 57 vertices were 65–208 units above the ground, left unsnapped by `SNAP_MAX` 64. At a cliff edge,
  Recast's detail mesh takes a vertex's height from the column beside it. The ground is the only collision so far,
  so `SNAP_MAX` is now 256. Heights over tolerance: 0 (vertex max 30).

**1. The province (`make navmesh`'s build, with every fix):**
- Run: 12,083 NAVM, 4,298,892 triangles, 2,821,202 vertices, 303,494 links. Times: inputs 7.7 s, Recast 1,051 s,
  stitch 335 s, check 119 s.
- **L1 green:** degenerate 0; heights over 0 (centroid p99 20.0, max 363); links 0 asymmetric, 0 bad target, 0 bad
  geometry; NAVI 12,083 entries, 0 missing, 0 errors.
- Measured: road 98.4 % on the navmesh; walkable coverage 98.8 % under 30°, 72.1 % at 30–40°, 19.2 % at 40–45°.
- Islands: 7,416 (1,337 over 100 m²; 2.36 M m² in all) against a main component of 33.3 M m². The largest island
  is 1.14 M m².
- `python -m tools.navmesh build --province` (`nav-province-2`): 21:03 wall, peak RSS 854 MB.

**2. Determinism:**
- Claywater: `45ad2a5f59690bbb…`, the same on four builds (two before the fan filter, two after; the filter did not
  change it). Wall 7.5–17 s, peak 199–218 MB.
- Sample: still `5eed6ffd…` (the manifest is unchanged).
- Province: `31e0537c5eabbed8…` from `make navmesh` (4 threads), and `31e0537c5eabbed8…` again from `nav-province-3` (2 threads; 30:08 wall, peak 857 MB): identical.

**3. `make navmesh` end to end:** 26:37 wall, **peak RSS 1.56 GB** (≤ 2 GB, so no streaming is needed). The plugin
write alone, measured separately on `nav-province-2`, took 98 s at a 1.565 GB peak. ArgoniaWorld.esm is 195.6 MB,
sha256 `0f7f0e2a…`. `verify_esm`: 12,083 of 12,083 NVNM byte-identical, 0 extra, NAVI 12,083.

**4. `make check`:** CHECK GREEN in full, 1:58 wall, peak 635 MB (pytest 203 passed, ctest 21 of 21, plugin twice identical, Spriggit byte-identical, both sample hashes as the manifests).

**The voxel width:** production `CELL_SIZE` is 16. On Claywater:

| Voxel width | Walkable dry ground covered | Under 30° | 30–40° | 40–45° | Road | Main component |
|---|---|---|---|---|---|---|
| 16 | 83.2 % | 97.6 % | 77.5 % | 23.7 % | 97.5 % | 154,363 m² |
| 32 | 58.3 % | 89.2 % | 7.1 % | 0.1 % | 91.4 % | 73,818 m² |

At 32 there are also 232 islands (52 over 100 m²).

**The islands:**
- Claywater's 21 islands over 100 m² are all dry ground: 0 % water, 0 % road, and no roofs (the ground is the only
  collision so far). They lie on the block's mountain rows, at z 4,500–12,200.
- None joins the main component on the whole province.
- 31–81 % of the ground around each one is steeper than 45°: these are real unreachable shelves.
- Claywater Station itself is on the main component, so no fix is needed. Details are in the journal.

**Still owed:** item 5 (L4: `tests/scenes/nav-claywater.json`, `tests/journeys/nav-*.yaml`, and whether the engine
accepts our NAVI override) and item 6 (the CK comparison, `infra/gpu-box/navmesh_ck.ps1`). The drafts are kept. The
province also has 7,416 islands, which have not been classified; Claywater's say they are mountain shelves, but
that is not measured province-wide.
