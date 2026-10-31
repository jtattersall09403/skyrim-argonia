# What is still owed in game (Part 1 and 2.W1–2.W4)

The one list of in-game checks still to pass before the 1.7 verdict. Journeys' status comes from the run history:
`python3 tools/run_batch.py --owed` (the source of truth; this file's journey table is its snapshot). Everything a
journey does not cover is listed by hand below and ticked here when proven, with the commit or report.

Snapshot: 2026-10-31 00:20 UTC (`run_batch --owed`, after lane game-17): 18 journeys passed, 14 failing, 3 drafts.
Report: `docs/research/2026-10-30/lane-game-17.md` (each red's state; diag5-g17.md the diagnosis).

## Journeys

| Status | Journeys |
|---|---|
| Passed | claywater-look, claywater-walk, combat-trial-a, cosave, croc-den, dialogue-intercept, fight-damage-builds, fight-lock-on, fight-roll-burden, first-place, lf83-endings, livia-sleep, quarantine, rest-is-the-only-save, rest-respawn, suspend-save, w3-crime, w3-interior-sun |
| Failing (state in game-17's report) | attributes, quest-board, world-sample, smoke, w3-weather-stills, water-swim (fixes in b7393c0, not yet deployed); die-and-recover (take-pile), fight-archetype (no swing), grow-at-rest (deserter dead after the rest), lf83-components (mortar-tub), menus-quit (pad in the Journal), ui-probe (close-dialogue), ui-sweep (sleep-wait), ui-review |
| Drafts, not in the batch | rest-respawn-cleared; w4-veg-densest and water-budget |
| Dropped | soak, w3-road-hops, nav-npc-walk, nav-sandbox-20, water-npc-swim |

## Not covered by a journey

| Item | From | Status |
|---|---|---|
| Input reaches the game after a save load | game-14 finding | proven (game-15) |
| Frame times on the g6 against the revised bar (median ≥ 50, 95% ≥ 45, 1% lows 25–30) | #16 | owed: g6-migrate lane |
| Shaders-on and shaders-off Moonlight cards | owner | proven on the g4dn (lane-game-13); recheck on the g6 |
| Stream latency on a real device | 0.2 §d | build-VM emulated only (35.6 ms median); a real device is the owner's play |
| Distant terrain (xLODGen) restored, and a Claywater still judged | owner: keep xLODGen | owed: installer step written (installer/steps/terrain-lod.md); restore and still not run |
| The vastei pile: a still judged, and pickup works | owner | owed: die-and-recover take-pile red (game-17) |
| Respawn flags on the deserter (respawns) and the crocodile (never) | owner | proven: rest-respawn passed 3 runs (game-16; the deserter now goes home, b5db19e) |
| Clearable place: respawns until wholly cleared, then never (LCTN cleared flag, survives save) | owner | owed: when a clearable place is built |
| The UI restyle in game (Pelagiad, palette, title, no compass): ui-sweep | 1.2 §a | owed (journey failing) |
| The M chart follows the old map | owner | in ui-probe's chart steps (failing) |
| The chart closes on B, Tab, M, touch Close (Esc by the os route) | game-16 | proven (game-17, live) |
| B closes the journal with no roll; B while moving rolls | #17 | proven (game-17, live, pad; touch not rerun) |
| Favourites on D-up (with a favourite set) | #17 | proven (game-17, live, pad UP and Q) |
| Decision 0017's 1.2 §0 numbers (screen technology) | 1.2 | owed: from the g6 frame times |
| The world tour's 13 stops | owner | world-sample (crashing on travel; fix committed) |
| Claywater station house interior | owner: Nordic is fine | nothing owed |

## Then
The 1.7 packet to the owner (draft: `docs/research/2026-10-30/verdict-packet-draft.md`), with the numbers above.
