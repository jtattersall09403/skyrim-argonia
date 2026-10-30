# What is still owed in game (Part 1 and 2.W1–2.W4)

The one list of in-game checks still to pass before the 1.7 verdict. Journeys' status comes from the run history:
`python3 tools/run_batch.py --owed` (the source of truth; this file's journey table is its snapshot). Everything a
journey does not cover is listed by hand below and ticked here when proven, with the commit or report.

Snapshot: 2026-10-30 17:10 UTC. 10 journeys passed, 18 failing, 1 never run. The last two rounds proved nothing new:
the game ignored input after a save load (`lane-game-14.md`). The fix (a9a50dd) and the move to a g6 are in flight.

## Journeys

| Status | Journeys |
|---|---|
| Passed | attributes, claywater-walk, cosave, croc-den, lf83-endings, livia-sleep, quarantine, rest-is-the-only-save, w3-interior-sun, water-swim |
| Failing; fixes committed, re-run owed | claywater-look, combat-trial-a, dialogue-intercept, die-and-recover, fight-archetype, fight-damage-builds, fight-lock-on, fight-roll-burden (crash), first-place, grow-at-rest, lf83-components, menus-quit, quest-board, smoke (crash), suspend-save, ui-probe, ui-sweep, w3-crime, w3-weather-stills, world-sample (crash) |
| Never run | rest-respawn (built 4aabb98) |
| Drafts, not in the batch | nav-npc-walk, nav-sandbox-20, w4-veg-densest, water-budget, water-npc-swim (each needs an NPC travel order or a plugin swap; covered in part by world-sample) |
| Dropped | soak (owner), w3-road-hops (owner) |

## Not covered by a journey

| Item | From | Status |
|---|---|---|
| Input reaches the game after a save load | game-14 finding | owed: first g6 slot (game-15) |
| Frame times on the g6 against the revised bar (median ≥ 50, 95% ≥ 45, 1% lows 25–30) | #16 | owed: g6-migrate lane |
| Shaders-on and shaders-off Moonlight cards | owner | proven on the g4dn (lane-game-13); recheck on the g6 |
| Stream latency on a real device | 0.2 §d | build-VM emulated only (35.6 ms median); a real device is the owner's play |
| Distant terrain (xLODGen) restored, and a Claywater still judged | owner: keep xLODGen | owed: game-15 |
| The vastei pile: a still judged, and pickup works | owner | owed: game-15 |
| Respawn flags on the deserter (respawns) and the crocodile (never) | owner | owed: game-15 |
| The UI restyle in game (Pelagiad, palette, title, no compass): ui-sweep | 1.2 §a | owed (journey failing) |
| The M chart follows the old map | owner | in ui-probe's chart steps (failing) |
| Decision 0017's 1.2 §0 numbers (screen technology) | 1.2 | owed: from the g6 frame times |
| The world tour's 13 stops | owner | world-sample (crashing on travel; fix committed) |
| Claywater station house interior | owner: Nordic is fine | nothing owed |

## Then
The 1.7 packet to the owner (draft: `docs/research/2026-10-30/verdict-packet-draft.md`), with the numbers above.
