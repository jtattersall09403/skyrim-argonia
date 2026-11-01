<!-- imported unchanged from elder-souls-argonia docs/research/vegetation/README.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Research — vegetation

How much vegetation, of what, where it stands and how it is anchored. Feeds the scatter compiler and the flora palettes.

**Land-tree level of detail is a count rule (owner ruling):** the nearest N1 trees (default 140) draw the full mesh, the next N2 (350) the medium mesh, the rest their card; `packages/game-core/src/vegetation/treeLodCounts.ts`, sliders in the studio Trees panel, persisted as `treeFull=` / `treeMid=`. It supersedes every distance or pixel table for trees in the notes below and in decisions 0075/0084 (which stay as records); non-tree plants keep the distance rings of `speciesRings.ts`.

| File | What it answers | Status |
| --- | --- | --- |
| [renderer-rewrite-baseline.md](renderer-rewrite-baseline.md) | The T2 renderer's numbers before the cell rewrite (jungle site: last-rebuild ms, pass split, draws, instances, triangles) and the culling micro-benchmark; rounds 1–2 add their rows. Decision 0082. | live measuring stick (vegetation renderer lane) |
| [vegetation-density-design.md](vegetation-density-design.md) | The design synthesis for density: legibility, local-geography dependence, within-region variance, mod reference. Read by `worldgen/scatter.py`, `compile_scatter.py`. | live design input |
| [tropical-vegetation-ecology-targets.md](tropical-vegetation-ecology-targets.md) | Real ecology numbers per stratum and per landscape type (stem densities, canopy, spatial pattern) with a game-translation table. Read by `worldgen/build_palettes.py`, `vegetation_ladder.py`. | live design input |
| [vegetation-composition-rules.md](vegetation-composition-rules.md) | How the source authors compose and anchor models (pivot offsets, co-occurrence) — the fix for floating vines and trees on tiptoes. Read by `worldgen/composition.py` and the studio vegetation runtime. | live design input |
| [mod-vegetation-micro-siting.md](mod-vegetation-micro-siting.md) | Where each species stands relative to the waterline, how density falls off away from shore, and how a dressed pool is structured ring by ring. Read by `worldgen/build_palettes.py`, `scatter.py`. | live design input |
| [groundcover-system.md](groundcover-system.md) | How Skyrim, the vault mods and shipped open worlds place and fade ground cover (the five shared mechanisms); the numbers behind the 16f ring rebuild. Read by `world/sources/flora/groundcover.json`, `packages/world-render/src/vegetation/Groundcover.tsx`. | live design input |
| [rock-placement-rules.md](rock-placement-rules.md) | Bethesda's own rock placement as rules with their mined evidence (sink, tilt, slope, water relation, clumping, the wet-rock family, open-backed shells). Read by `worldgen/rock_dressing.py`, `build_palettes.py`, `test_rock_rules.py`. | live design input |
| [openworld-vegetation-placement-architecture.md](openworld-vegetation-placement-architecture.md) | The macro→meso→micro placement pattern AAA open worlds use, how they dress water features, and the black-foliage/shadow fixes. Read by `worldgen/scatter.py`, `compile_scatter.py`. | research reference |
| [regional-variety-audit-2026-09-08.md](regional-variety-audit-2026-09-08.md) | Measured species variety per region. Its density figures are per dominant chunk and mis-attribute neighbours' trees. | species counts live; density figures superseded by `worldgen.vegetation_ladder.measure_delivered_by_region` |
