# Round 6 of 1.15: every open row closed (owner, 07:36, 08:06 and 08:11, #37)

The owner refused the round-5 hand-over (open findings listed) and ruled: no hand-over with known gaps, loop until
complete; the oddly coloured trees root-caused and fixed, never dropped; loop fast, the slow derived steps last and
only for what changed; every loop as fast as it can be, made to stick, with a retrospective at each round close.

## Lanes (briefs in briefs/, reports in lane-1.15-r6-*.md)
mesh-patcher (install-time NIF patcher, 19 meshes, LOOK_DROP empty), light (records byte-equal to Tropical's, volumetric
links from Update.esm, shafts re-enabled), claywater-water (pads with 1.0 m freeboard, 30 reds to 0), ground-roads
(riverbed share under Skyrim's bar, derived landscape textures, roads against Skyrim's measured road bar), water-steps
(123 hanging pieces re-seated, still water without drift), creatures (plan-check, spots framing actors), navmesh-lodkey
(navmesh on the final ground, LOD keyed per half), journeys-harness (stands clear of canopy, reach keys), fast-loop-2
(the stage table, keyed deploy steps, chain.sh, round_retro.py), batch-one-load, gate-by-reach, plugin-per-region.

## The batch
tests/journeys/batches/1.15-round-6.yaml on the existing LOD; the tree booth list beside it; readers on the stills; the
ledger rows move with the verdicts. Then the LOD halves whose inputs moved, the saves, and the retrospective below.

## Retrospective
(appended by tooling/round_retro.py at the close)

## Where the time went (tooling/round_retro.py)

23 logs (r6-chain*)

| stage | n | median s | p90 s | total s | share |
|---|---|---|---|---|---|
| round total | 3 | 53 | 5565 | 5638 | (sum) |
| batch: per journey run | 18 | 158 | 527 | 5585 | 32.1 % |
| round: batch | 3 | 50 | 5096 | 5163 | (sum) |
| round: deploy | 6 | 462 | 763 | 3432 | (sum) |
| prebatch: gate | 8 | 335 | 364 | 2694 | 15.5 % |
| prebatch: journeys | 10 | 323 | 370 | 2668 | 15.3 % |
| deploy total | 4 | 462 | 763 | 1897 | (sum) |
| prebatch: plugin | 11 | 90 | 193 | 1186 | 6.8 % |
| deploy: skse build | 4 | 263 | 360 | 1042 | 6.0 % |
| deploy: stack push | 6 | 51 | 92 | 776 | 4.5 % |
| deploy: launch | 4 | 100 | 114 | 397 | 2.3 % |
| prebatch: plugin-check | 3 | 116 | 128 | 335 | 1.9 % |
| deploy: make plugin | 12 | 13 | 41 | 324 | 1.9 % |
| round: up | 2 | 148 | 291 | 296 | 1.7 % |
| prebatch: chart4k | 8 | 44 | 45 | 281 | 1.6 % |
| capacity wait ((tries-1) x 60 s) | 10 | 0 | 0 | 240 | 1.4 % |
| prebatch: chart | 8 | 22 | 46 | 231 | 1.3 % |
| prebatch: vegetation | 8 | 21 | 22 | 215 | 1.2 % |
| deploy: base save | 4 | 28 | 125 | 205 | 1.2 % |
| prebatch: plugin-ids | 8 | 12 | 26 | 137 | 0.8 % |
| deploy: send ESMs and helpers | 6 | 12 | 14 | 114 | 0.7 % |
| deploy: mesh patches | 6 | 15 | 16 | 96 | 0.6 % |
| deploy: ground textures | 6 | 13 | 13 | 78 | 0.4 % |
| deploy: theme | 7 | 9 | 9 | 62 | 0.4 % |
| deploy: lod | 6 | 9 | 9 | 55 | 0.3 % |
| deploy: chart | 9 | 1 | 1 | 53 | 0.3 % |
| prebatch: roads | 8 | 5 | 7 | 46 | 0.3 % |
| deploy: chart 4k | 8 | 0 | 1 | 44 | 0.3 % |
| prebatch: water | 8 | 4 | 6 | 40 | 0.2 % |
| deploy: views | 8 | 4 | 8 | 32 | 0.2 % |
| prebatch: sample | 8 | 4 | 5 | 31 | 0.2 % |
| deploy: machine up | 10 | 3 | 4 | 30 | 0.2 % |
| deploy: perks | 7 | 3 | 4 | 18 | 0.1 % |
| prebatch: navmesh | 5 | 3 | 4 | 16 | 0.1 % |
| deploy: game down | 16 | 1 | 1 | 15 | 0.1 % |
| deploy: shader cache save | 4 | 2 | 8 | 15 | 0.1 % |
| deploy: stack stage | 7 | 2 | 2 | 14 | 0.1 % |
| deploy: shader cache | 5 | 1 | 8 | 13 | 0.1 % |
| deploy: send scenes | 4 | 2 | 4 | 11 | 0.1 % |
| deploy: controls | 6 | 1 | 1 | 7 | 0.0 % |
| deploy: papyrus | 6 | 0 | 0 | 0 | 0.0 % |

| wait or LOD half | lines |
|---|---|
| capacity: no spot capacity lines | 74 |
| interrupts | 1 |
| locks: queued behind | 42 |
