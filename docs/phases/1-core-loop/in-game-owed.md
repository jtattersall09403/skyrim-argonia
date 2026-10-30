# What is still owed in game (Part 1 and 2.W1–2.W4)

The one list of in-game checks still to pass before the 1.7 verdict. Journeys' status comes from the run history:
`python3 tools/run_batch.py --owed` (the source of truth; this file's journey table is its snapshot). Everything a
journey does not cover is listed by hand below and ticked here when proven, with the commit or report.

Snapshot: 2026-10-30 22:00 UTC (`run_batch --owed`, after lane game-16): 20 journeys passed, 11 failing, soak never
run (dropped). Report: `docs/research/2026-10-30/lane-game-16.md`.

## Journeys

| Status | Journeys |
|---|---|
| Passed | attributes, claywater-look, claywater-walk, combat-trial-a, cosave, croc-den, dialogue-intercept, fight-archetype, fight-damage-builds, fight-lock-on, fight-roll-burden, lf83-endings, livia-sleep, quarantine, rest-is-the-only-save, rest-respawn, w3-crime, w3-interior-sun, w3-weather-stills, water-swim |
| Failing (finding in game-16's report) | die-and-recover (earn: no vastei from blows), first-place (terms-with-signs: Signs' one-charge needs the objections answered first; the journey skips them), grow-at-rest (crash after the rest, at pending-level), lf83-components (stage-20: ArgoniaJournalNotice is sent but the bridge never sees it; code), menus-quit (quit-confirmed: no quit save line), quest-board (strike: Livia never under the crosshair), smoke (crash on its cow to Tamriel), suspend-save (in-combat-drop: the player is not in combat after the blow), ui-probe (frames-open: 0 frames with a menu open; the check is wrong), ui-sweep (map-closed: nothing closes the chart, not even view.close), world-sample (crash at the first cell change after the `teleport pos` probes of stop 1) |
| Drafts, not in the batch | rest-respawn-cleared (until Jungle Root Hollow is built); w4-veg-densest and water-budget (g6 frame measurement) |
| Dropped | soak, w3-road-hops, nav-npc-walk, nav-sandbox-20, water-npc-swim |

## Not covered by a journey

| Item | From | Status |
|---|---|---|
| Input reaches the game after a save load | game-14 finding | proven (game-15) |
| Frame times on the g6 against the revised bar (median ≥ 50, 95% ≥ 45, 1% lows 25–30) | #16 | owed: g6-migrate lane |
| Shaders-on and shaders-off Moonlight cards | owner | proven on the g4dn (lane-game-13); recheck on the g6 |
| Stream latency on a real device | 0.2 §d | build-VM emulated only (35.6 ms median); a real device is the owner's play |
| Distant terrain (xLODGen) restored, and a Claywater still judged | owner: keep xLODGen | owed: game-17 (not reached in game-16) |
| The vastei pile: a still judged, and pickup works | owner | owed: game-17 (not reached in game-16) |
| Respawn flags on the deserter (respawns) and the crocodile (never) | owner | proven: rest-respawn passed 3 runs (game-16; the deserter now goes home, b5db19e) |
| Clearable place: respawns until wholly cleared, then never (LCTN cleared flag, survives save) | owner | owed: when a clearable place is built |
| The UI restyle in game (Pelagiad, palette, title, no compass): ui-sweep | 1.2 §a | owed (journey failing) |
| The M chart follows the old map | owner | in ui-probe's chart steps (failing) |
| Decision 0017's 1.2 §0 numbers (screen technology) | 1.2 | owed: from the g6 frame times |
| The world tour's 13 stops | owner | world-sample (crashing on travel; fix committed) |
| Claywater station house interior | owner: Nordic is fine | nothing owed |

## Then
The 1.7 packet to the owner (draft: `docs/research/2026-10-30/verdict-packet-draft.md`), with the numbers above.
