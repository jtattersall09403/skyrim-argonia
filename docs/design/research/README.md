<!-- imported unchanged from elder-souls-argonia docs/research/README.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# docs/research/ — index

Reusable research findings, one topic per file, grouped into themed folders
(one level only). Filenames are the map: scan a folder's listing before
starting a new file, and add new work to the folder it belongs in, never
at the top level. Route into research from [../README.md](../README.md) (the
task router).

| Folder | What lives there |
| --- | --- |
| [world-terrain/](world-terrain/) | Terrain, climate, hydrology, geomorphology, coasts, islands, the land beyond the border. Start here for "does this place really have the water that it claims": [place water facts vs the shipped water](world-terrain/place-water-facts-vs-shipped-water.md). |
| [vegetation/](vegetation/) | Flora ecology targets, composition rules, density design, placement architecture and micro-siting. |
| [rendering/](rendering/) | Presentation systems: sky and light, water, waterfalls, weather, terrain splatting, scatter instancing, ground/shore materials, ambient audio, and the [fable5-world-demo audit](rendering/fable5-world-demo-audit.md) (what we take from an external WebGPU world). |
| [placement-settlements/](placement-settlements/) | Where things go and what they are made of: place distribution and siting, approach and wayfinding, settlement morphology and form evidence, kit level design, [building depth and variety](placement-settlements/building-depth-and-variety.md) (how a house is assembled), [type recipes](placement-settlements/settlement-type-recipes.md) (the digest of `type-recipes.json`), shipped placement rules, kit sourcing, asset inventory and deliverability audits, content density. |
| [phase11/](phase11/) | What remains live from Phase 11: the adversarial critique set ([phase11-critique/](phase11/phase11-critique/)), the vibe-sheet asset audit, and the travel-cost isolation study cited by decision 0041. The round papers (gap plan, proposals, reviews, walkthrough, promise ledger) are archived under [archive/phase11-rounds/](archive/phase11-rounds/). |
| [phase16/](phase16/README.md) | Closed with Part 1 ([0135](../old-decisions/0135-phase-16-closes-the-world-is-leg-work-now.md)). The Phase 16 evidence still read as reference: the five read-only audits ([water runtime](phase16/audit-water-runtime.md), [hydrology data model](phase16/audit-hydrology-data-model.md), [delivered settlements](phase16/audit-settlements-delivered.md), [chain circularity, local patches, borders, cliffs](phase16/audit-chain-and-terrain.md), [routers and unused context](phase16/audit-routers-and-context.md)), the 16g plot reviews and remedy plan, the catalogue-wide steps audit, the hand-offs and the 16k fire and path-paint research. Its ledgers, mining and method reviews are archived. |
| [text-and-voice/](text-and-voice/) | How the game's prose sounds: AI-writing tells, Morrowind speech register, the Morrowind dialogue corpus (voice-review yardstick). |
| [combat-and-systems/](combat-and-systems/) | Playable systems: poise, diceless resolution, stats/progression references, swim/climb/boat implementation, navmesh ambient AI, bow-aim camera, source-game crosscheck, build-out systems audit. |
| [ui/](ui/) | The interface: the reference images behind 2.2 ([reference/](ui/reference/README.md): the restyled Morrowind pause screen that seeds the look, the title concept for Part 3) with their written descriptions. |
| [infrastructure/](infrastructure/) | The development machine: the Codespaces migration plan, the vault snapshot in R2 and the tiered restore. The operating doc is `tooling/bootstrap/README.md`. |
| [quests-and-cast/](quests-and-cast/) | Quest and narrative research: cast structure, faction/quest rewards, opening hours and start area, boss options. |
| [lore-facts-audit/](lore-facts-audit/README.md) | The 170 loading-screen facts audited against the game: what each implies, what exists, what was ruled (0157). |
| [lore/](lore/) | Lore-grounding notes that back world decisions: minority enclaves, creature asset availability, watercraft. |
| [agent-ops/](agent-ops/README.md) | How our coding agents spend tokens: the `cost-review` skill's log (decision 0079). |
| [agents/](agents/README.md) | Where agent routing is decided (0079, 0118); no live research. |
| [process/](process/README.md) | Where the way work is run is decided (0106, 0131, the hooks); no live research. |
| [engine/](engine/) | Engine and stack choices: [Godot 4 migration assessment](engine/godot-migration-assessment.md) (stay on the browser stack, finish WebGPU). |
| [archive/](archive/) | Superseded workstream material and decision-record round logs, provenance only. Never a live design source. Holds `phase10-rounds/`, `phase11-rounds/`, `water-8b-rounds/`, `weather-8c-rounds/` (history split out of decisions 0036, 0041, 0025, 0032), `water-round-2-2026-09/` (the round-2 water handoff, quality contract and evidence ledger), `water-overhaul-2026-09/`, `workstream-s/` `phase16-evidence/` (the Phase 16 chunk ledgers, the 16g mining and the place-builder method reviews), `agent-process-reviews/` (the instruction-surface, agent-tree and workflow cost reviews behind 0079, 0106 and 0118) and `phase16-retired-briefs/` (the 16i and 16j briefs, retired by 0099; their live items are in the [polish backlog](../phases/P-polish/backlog.md)). |
