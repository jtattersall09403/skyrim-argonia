<!-- imported unchanged from elder-souls-argonia docs/research/phase16/README.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Research — Phase 16 evidence (closed)

Phase 16 is closed ([0135](../../old-decisions/0135-phase-16-closes-the-world-is-leg-work-now.md)).
This folder keeps the evidence still read as reference: the five read-only
audits (`file:line` against commit `34bec0ed`; none of them changed
anything), the 16g plot reviews and remedy plan, the catalogue-wide steps
audit, the hand-offs and the 16k research notes. The chunk ledgers, the 16g
mining and the place-builder method reviews are provenance and live in
[../archive/phase16-evidence/](../archive/phase16-evidence/README.md). The plan
they served is [the Phase 16 README](../../phases/16-foundation-and-places/README.md).

| File | What it answers | Status |
| --- | --- | --- |
| [audit-water-runtime.md](audit-water-runtime.md) | Why the deployed sea looks static: swell, whitecaps, shore break, hard edges, hovering sheets, doming and seams, traced to the runtime code. | evidence |
| [audit-hydrology-data-model.md](audit-hydrology-data-model.md) | What water entities exist, where the level comes from, which stages feed terrain and water back into each other, and why trees stand in rivers. | evidence |
| [audit-chain-and-terrain.md](audit-chain-and-terrain.md) | The terrain chain's dependency graph and its feedback cycles, local patches, the border and the cliffs. | evidence |
| [audit-settlements-delivered.md](audit-settlements-delivered.md) | The shipped settlements measured against the rules: hollow buildings, wrong kits, orientation, doors, floating pieces, missing paths. | evidence |
| [audit-routers-and-context.md](audit-routers-and-context.md) | Whether the doc routers have broken and what important context sits unused; broken links across all 360 `.md` files. | evidence |
| [16e-road-paint-census.md](16e-road-paint-census.md) | Generated census of road paint per material code on the shipped land cover (`worldgen.road_paint_census`). | evidence (generated) |
| [16g-remedy-plan.md](16g-remedy-plan.md) | The reasoning behind `world/sources/sites/plot-remedies.json`, from the eight review packs. | plan (applied) |
| [16g-review/dunmer-north.md](16g-review/dunmer-north.md) | 16g plot review of `dunmer-north`. | evidence |
| [16g-review/hist-heartland.md](16g-review/hist-heartland.md) | 16g plot review of `hist-heartland`. | evidence |
| [16g-review/imperial-fringe.md](16g-review/imperial-fringe.md) | 16g plot review of `imperial-fringe`. | evidence |
| [16g-review/imperial-penal-south.md](16g-review/imperial-penal-south.md) | 16g plot review of `imperial-penal-south`. | evidence |
| [16g-review/mercantile-coast.md](16g-review/mercantile-coast.md) | 16g plot review of `mercantile-coast`. | evidence |
| [16g-review/naga-kur-deeps.md](16g-review/naga-kur-deeps.md) | 16g plot review of `naga-kur-deeps`. | evidence |
| [16g-review/pirate-freeholds.md](16g-review/pirate-freeholds.md) | 16g plot review of `pirate-freeholds`. | evidence |
| [16g-review/saxhleel-coast.md](16g-review/saxhleel-coast.md) | 16g plot review of `saxhleel-coast`. | evidence |
| [16h-catalogue-wide-steps-audit.md](16h-catalogue-wide-steps-audit.md) | Which steps from 16h part 2 to Phase 15 run over a whole catalogue, measured counts, the sample-first shape for each, and the tools with no place selector. | evidence |
| [16h-handoff-2026-09-25.md](16h-handoff-2026-09-25.md) | The Codespaces migration hand-off: every lane's state at the cut, what was mid-flight, the line that relaunches it. | hand-off (history) |
| [16k-handoff-2026-09-25.md](16k-handoff-2026-09-25.md) | 16k hand-off at the planning session's close: the owner rulings 1–6 that 0099 and the 16k brief carry. | hand-off (history) |
| [16k-fire-system-research.md](16k-fire-system-research.md) | 16k fire technique: why flames were invisible by day and white by night (physical exposure vs display-referred additive sprites), the WebGL shader rule now and the WebGPU hero path later; decision 0107. | research |
| [16k-path-paint-and-studio-gpu.md](16k-path-paint-and-studio-gpu.md) | Why the path paint drew blocky, dark and unhazed (CSM wiped its shader patch), the CSM hook-chain gate, the paint harness numbers; places out of range wait for their ground by event; what the studio uploads to the GPU and why about 150 MB is expected. | research |
