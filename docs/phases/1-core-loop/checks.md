# Part 1 check ledger (1.1 to 1.7, and the world track's 2.W1 to 2.W4)

Every check from the running game (L4 to L6) that a Part 1 or 2.W1–2.W4 brief owes, with what proved it. It
replaces the hand-made in-game-owed list. The format is fixed (`tools/check_ledger.py` checks it in `make check`;
`tools/run_batch.py` rewrites each `journey:<id>` row at the end of every run, a `#<prefix>` row from those steps
alone). Status: owed, proven or dropped. A proven row carries its run, report line or commit; a dropped row its
owner-brief date. The mapping from each brief's acceptance lines is in `docs/research/2026-10-31/ledger-audit.md`.

## 1.1 The game-state seam

| Check | From | Level | Status | Evidence |
|---|---|---|---|---|
| Every co-save family round-trips through a save, a quit and a reload | 1.1, 1.3 §b, 1.4, 1.5 | L4 | proven | journey:cosave pass out/batch/g17/20261030T225900 |
| A view opened from the schema shows live data in game | 1.1 | L4 | proven | journey:ui-probe pass out/batch/adhoc/20261031T041115 |
| The scene-reset path leaves no state behind (a before and after read of every family) | 1.1 | L4 | owed | no journey reads it |

## 1.2 The UI, stage one

| Check | From | Level | Status | Evidence |
|---|---|---|---|---|
| The sweep of every menu from the first place: Pelagiad, our palette, the Argonia title, no compass, no marker | 1.2 §a, 0.2 §c | L4 | owed | journey:ui-sweep fail out/batch/adhoc/20261031T112117 |
| A reader's Nordic-tells pass on the sweep's stills is clean | 1.2 §a | L4 | owed | waits on ui-sweep |
| The owner sees a before-and-after still of the main menu and one menu | 1.2 §a | L6 | owed | no check-in on record |
| Text readable on the folded Magic V5 (drive.sh v5-folded and v5-unfolded) | 1.2, 1.2 §d | L4 | owed | docs/research/2026-10-31/lane-game-21.md:28 (not run) |
| Our dialogue window opens on talking, shows live topics, closes back to play; no vanilla Dialogue Menu | 1.2, 1.2 §b, 1.1 | L4 | proven | journey:dialogue-intercept pass out/batch/g17/20261030T225900 |
| Our screens in play: the dialogue topics, a long answer, the HUD notice, the journal's quest entry | 1.2 §b, §c | L4 | owed | journey:ui-review fail out/runs/ui-review/20261031T002055 |
| The dialogue and journal open and close hand-offs, a clip | 1.2 §b, §c | L5 | owed | no clip made |
| B closes the journal with no roll; B while moving rolls (pad) | 1.2 §c | L4 | proven | docs/research/2026-10-30/lane-game-17.md:15 |
| Touch B closes the journal | 1.2 §c | L4 | owed | docs/research/2026-10-31/lane-game-21.md:28 (not run) |
| The HUD's states and the vanilla HUD hidden; the chart opens and reveals | 1.2 §d, §e, 1.6 | L4 | proven | journey:ui-probe pass out/batch/adhoc/20261031T041115 |
| Our HUD is hidden over the loading screens | 1.2 §d | L4 | owed | docs/research/2026-10-31/lane-game-21.md:41 |
| The chart closes on B, Tab, M and touch Close | 1.2 §e | L4 | proven | docs/research/2026-10-30/lane-game-17.md:11 |
| Favourites open on D-up with a favourite set | 1.2 §a | L4 | proven | docs/research/2026-10-30/lane-game-17.md:17 |
| Quit from the menus writes the suspend save and returns to the main menu | 1.2 §a, 1.5 | L4 | owed | journey:menus-quit fail out/batch/adhoc/20261031T112117 |
| The screen technology's numbers (decision 0017, 1.2 §0) from the play machine's frame times | 1.2 §0 | L4 | owed | waits on the 0.2 §d frame times |

## 1.3 Talk and carry

| Check | From | Level | Status | Evidence |
|---|---|---|---|---|
| Every attribute equals its mirror AV, set and clamped, through a rest and a load | 1.3 §a | L4 | proven | journey:attributes pass out/batch/g18a/20261031T003055 |
| Every derived value read for 5 test characters matches the formulas | 1.3 §a | L4 | owed | no journey reads 5 characters' derived values |
| A topic learned from one person is asked of a second | 1.3 §b | L4 | proven | journey:first-place pass out/batch/g17/20261030T225900 |
| Low and high disposition show different variants; an essential topic answers at disposition 0 | 1.3 §b | L4 | owed | no run on record |
| Each slot stacks in a still of the paperdoll and on the body; take, equip, read the book | 1.3 §c | L4 | owed | no journey |
| A swing trains Long Blade, not One-handed | 1.3 §c, 1.6 | L4 | proven | journey:fight-damage-builds pass out/batch/g17/20261030T225900 |

## 1.4 One quest through the journal

| Check | From | Level | Status | Evidence |
|---|---|---|---|---|
| LF83 starts in dialogue the real way; the fail-forward | 1.4 | L4 | proven | journey:quest-board pass out/batch/g18a/20261031T003055 |
| Each stage set by its real path; the journal shows the entry and the stage | 1.4 | L4 | proven | journey:lf83-components pass out/batch/adhoc/20261031T032802 |
| The four endings | 1.4 | L4 | proven | journey:lf83-endings pass out/batch/g18a/20261031T003055 |
| The assault is reported to the victim's crime faction | 1.4, 2.W3 | L4 | proven | journey:w3-crime pass out/batch/g17/20261030T225900 |
| A reader confirms no marker at any point (stills at three steps) | 1.4 | L4 | owed | no reader report on record |

## 1.5 Grow, die, rest, save

| Check | From | Level | Status | Evidence |
|---|---|---|---|---|
| Skill uses, a pending level, rest, the sitting opens, spend, values change | 1.5 | L4 | proven | journey:grow-at-rest pass out/batch/adhoc/20261031T041115 |
| Die with vastei, wake at the camp, walk to the pile, take it, the amount equal | 1.5 | L4 | owed | journey:die-and-recover#take-pile fail out/batch/adhoc/20261031T112117 (passed in b1, docs/research/2026-10-31/lane-game-21.md:19) |
| A second death replaces the pile | 1.5 | L4 | owed | journey:die-and-recover#second-death (never passed) |
| A still of the pile judged by a reader (the 51-vastei pile) | 1.5 | L4 | owed | no reader report on record |
| The archetype respawns after rest; the crocodile does not | 1.5, 1.6 | L4 | proven | journey:rest-respawn pass out/batch/adhoc/20261030T202908 |
| A clearable place respawns until wholly cleared, then never | 1.5 | L4 | owed | journey:rest-respawn-cleared (draft, not in the batch: no clearable place built) |
| Rest is the only save: no quicksave, wait or travel autosave | 1.5 | L4 | proven | journey:rest-is-the-only-save pass out/batch/g17/20261030T225900 |
| The suspend save on a stream drop, in and out of combat | 1.5 | L4 | proven | journey:suspend-save pass out/batch/adhoc/20261031T000000 |
| The rest-to-sitting hand-off, a clip | 1.5 | L5 | owed | no clip made |

## 1.6 Fight on the tuned stack

| Check | From | Level | Status | Evidence |
|---|---|---|---|---|
| Group A wired and loaded: the sheet, the burden perk lock, the roll event, lock-on | 1.6 | L4 | proven | journey:combat-trial-a pass out/batch/g17/20261030T225900 |
| Lock on by R3 near the deserter | 1.6, 0.2 §c | L4 | proven | journey:fight-lock-on pass out/batch/g17/20261030T225900 |
| The roll is locked when overloaded and given back | 1.6, 1.3 §c | L4 | proven | journey:fight-roll-burden pass out/batch/g17/20261030T225900 |
| The deserter's record values and our outfit reach the actor | 1.6 | L4 | proven | journey:fight-archetype pass out/batch/g18b/20261031T011830 |
| The crocodile is placed, alive, in its pool, and stays dead | 1.6 | L4 | proven | journey:croc-den pass out/batch/g17/20261030T225900 |
| Guard, parry and riposte, kill and loot as one fight in an arena | 1.6 | L4 | dropped | owner-brief:2026-10-30 (no arena; the four fight checks simplified; modders' work is not judged) |
| A five-minute duel loop with no crash or growing script lag | 1.6 | L4 | dropped | owner-brief:2026-10-30 (the soak is dropped) |

## 1.7 The verdict

| Check | From | Level | Status | Evidence |
|---|---|---|---|---|
| The first-place walk-through: arrive, camp, talk, learn, ask, take LF83, finish it | 1.7 | L4 | proven | journey:first-place pass out/batch/g17/20261030T225900 |
| The whole batch (all.yaml) green in one pass, crash-prone last, the memory climb per loop measured | 1.7, Part 1 exit | L4 | owed | the reds are ui-sweep, menus-quit, die-and-recover (docs/research/2026-10-31/lane-game-21.md:45) |
| No Nordic element the owner meets outdoors (the immersion rows, a reader) | 1.7 | L4 | owed | no reader report on record |
| The Moonlight cards launch Argonia, shaders on and off | 1.7 | L4 | proven | dcccfa1 |
| The owner plays the shaders-on and shaders-off cards and calls the machine (#16) | 1.7 | L6 | owed | the packet |
| The stream latency measured on the owner's own device, printed on the packet | 1.7, Part 1 exit | L6 | owed | the packet |
| The owner plays `bat first-place` and gives the five answers | 1.7, 1.2, 1.4, 1.6, Part 1 exit | L6 | owed | the packet |
| The 60-minute soak | 1.7 | L4 | dropped | owner-brief:2026-10-30 |

## 2.W1 Terrain, apron and edges

| Check | From | Level | Status | Evidence |
|---|---|---|---|---|
| Stop 1: heights on the road in at Claywater match the heightfield within 0.5 m | 2.W1 §a, 0.4 §d | L4 | proven | journey:world-sample#s01 pass out/batch/adhoc/20261031T103633 |
| Stop 2: the steepest limited cliff | 2.W1 §a | L4 | proven | journey:world-sample#s02 pass out/batch/adhoc/20261031T103633 |
| Stop 3: a four-cell corner on a slope | 2.W1 §a | L4 | proven | journey:world-sample#s03 pass out/batch/adhoc/20261031T103633 |
| A reader finds no obvious texture tiling in the sample's vantage stills | 2.W1 §a | L4 | owed | no reader report on record |
| Stop 9: the player cannot leave by a border segment or an exit gate; the closed-road message | 2.W1 §b, 2.W3 §b | L4 | proven | journey:world-sample#s09 pass out/batch/adhoc/20261031T103633 |

## 2.W2 Water

| Check | From | Level | Status | Evidence |
|---|---|---|---|---|
| Stop 4: a stepped river reach with rapids | 2.W2 | L4 | proven | journey:world-sample#s04 pass out/batch/adhoc/20261031T103633 |
| Stop 5: a waterfall seated on its step | 2.W2 | L4 | proven | journey:world-sample#s05 pass out/batch/adhoc/20261031T103633 |
| Stop 6: a marsh basin at its designed level | 2.W2 | L4 | proven | journey:world-sample#s06 pass out/batch/adhoc/20261031T103633 |
| Stop 7: a lake shore and a coast, the apron through the haze | 2.W2, 2.W1 §b | L4 | proven | journey:world-sample#s07 pass out/batch/adhoc/20261031T103633 |
| The plane budget's frame time in game | 2.W2 | L4 | owed | journey:water-budget (draft, not in the batch) |
| Mist stills | 2.W2 | L4 | owed | no run on record |
| The player swims (water-swim) and NPCs swim | 2.W2 | L4 | dropped | owner-brief:2026-10-30 (base-Skyrim behaviour is not checked) |

## 2.W3 Regions, weather, light and roads

| Check | From | Level | Status | Evidence |
|---|---|---|---|---|
| Stop 10: a signpost's text and arms at a junction | 2.W3 §b | L4 | proven | journey:world-sample#s10 pass out/batch/adhoc/20261031T103633 |
| Stop 11: the weather cycles over a 7-day skip at Claywater | 2.W3 §a | L4 | proven | journey:world-sample#s11 pass out/batch/adhoc/20261031T103633 |
| A reader panel on 12 weather stills | 2.W3 §a | L4 | dropped | owner-brief:2026-10-30 (w3-weather-stills dropped) |
| The interior sun at four hours in two interiors | 2.W3 | L4 | proven | journey:w3-interior-sun pass out/batch/g17/20261030T225900 |
| Each road leg end to end by teleport hops | 2.W3 §b | L4 | dropped | owner-brief:2026-10-30 (the road walk dropped; 2.W3's Outcome names w3-road-hops) |
| Tear Road Stage against the traced Tear road's exit (3.4 km apart) | 2.W3 | L4 | owed | docs/phases/1-core-loop/2.W3-regions-roads.md:84 |

## 2.W4 Vegetation, navmesh and LOD

| Check | From | Level | Status | Evidence |
|---|---|---|---|---|
| Stop 8: the densest vegetation cell's frame time against the bar | 2.W4 §a | L4 | proven | journey:world-sample#s08 pass out/batch/adhoc/20261031T103633 |
| The densest 10 cells' frame time and a reader on 20 vantage stills: no Nordic flora, no vanilla rocks | 2.W4 §a | L4 | owed | journey:w4-veg-densest (draft, not in the batch) |
| Stop 12: 20 path requests across the block, a door link and a swim path | 2.W4 §b | L4 | proven | journey:world-sample#s12 pass out/batch/adhoc/20261031T103633 |
| 20 NPCs on sandbox packages never stand still for 60 s | 2.W4 §b | L4 | dropped | owner-brief:2026-10-30 (NPC movement is not checked in game) |
| Stop 13: the distant view's stills from a high point | 2.W4 §c | L4 | proven | journey:world-sample#s13 pass out/batch/adhoc/20261031T103633 |
| Distant terrain (xLODGen) restored on the play machine and a Claywater still judged: no missing tiles | 2.W4 §c | L4 | owed | docs/research/2026-10-31/lane-game-21.md:27 |
| The near-to-LOD hand-off, a clip | 2.W4 | L5 | owed | no clip made |

## 1.8 A play machine you can rely on

| Check | From | Level | Status | Evidence |
|---|---|---|---|---|
| The owner has ruled on the machine from an evidence-based call (interruption bands, placement scores, prices, latency), and it is built | 1.8, owner play test 12 | L6 | owed | evidence in docs/research/2026-10-31/1.8-machine-evidence.md; the owner chose A on #30 (owner-brief:2026-10-31): g6.2xlarge spot in London; owed: built from the fresh Paris image |
| A simulated spot interruption (the metadata mock) writes the suspend save | 1.8 | L4 | owed | being built (lane-1.8-watch) |
| The play page retries a refused start for 2 minutes, showing "starting…" | 1.8, #29 | L4 | owed | the owner said yes (owner-brief 2026-10-31); being built (lane-1.8-watch) |
| The baked image boots to the Argonia menu with no first-boot fix by hand | 1.8 | L4 | owed | not built |
| `machine_inventory.sh` shows nothing unarchived on London and on Paris | 1.8, docs/machine-moves.md | L4 | owed | London: 6 MO2 folders unarchived (docs/research/2026-10-31/lane-records.md) |
| `saves.sh backup` succeeds at a stop | 1.8 | L4 | proven | docs/research/2026-10-31/1.8-session-1.md; run.sh stop backed up 26 saves each: s3 argonia-saves saves/20261031T122540Z.zip (argonia-play) and saves/argonia-play-london/20261031T122615Z.zip (2026-10-31) |
| wake.yml's "play" comment starts the Paris machine | 1.8, #27 | L6 | dropped | owner-brief:2026-10-31 the "play" comment switch removed |

## 1.9 The front door and loads

| Check | From | Level | Status | Evidence |
|---|---|---|---|---|
| Loading `argoniabase` and two other saves reaches play (a state read: the player can move) | owner play test 3 | L4 | owed | black screen with the HUD, nothing works (docs/research/2026-10-31/owner-playtest-1.md) |
| No scrolling tree/desert bar on the main menu or behind the loading screens | owner play test 1 | L4 | owed | the owner saw it |
| No blank parchment screen between the Bethesda intro and the main menu | owner play test 2 | L4 | owed | the owner saw it |
| A reader over 3 load stills: our picture, our frame (no Celtic knot), readable unsquashed text, no HUD | owner play test 7, 8; game-22 reader | L4 | owed | knot frame from loadingmenu.swf (docs/research/2026-10-31/lane-game-22.md) |

## 1.10 The player character

| Check | From | Level | Status | Evidence |
|---|---|---|---|---|
| A reader over front, side and back full-body stills: an Argonian head, no Nord features, natural hair and tint | owner play test 6; game-22 reader | L4 | owed | a Nord head on an Argonian body; neon yellow-green hair |
| The same from `argoniabase` and from a fresh base save | 1.10 | L4 | owed | — |

## 1.11 Our HUD, rebuilt from the old game's

| Check | From | Level | Status | Evidence |
|---|---|---|---|---|
| The old HUD's inventory: every element built or dropped with a reason | owner play test 5 | L1 | owed | not done |
| A reader over calm, fight and low-health stills: no flat primary bars, vastei top left, nothing overlapping | owner play test 5 | L4 | owed | flat primary bars; vastei bottom right |
| The owner says the HUD looks right | owner play test 5 | L6 | owed | — |

## 1.12 Menus

| Check | From | Level | Status | Evidence |
|---|---|---|---|---|
| The system menu (settings, load, quit) opens from play by pad, keyboard and touch | owner play test 11 | L4 | owed | the owner found no way to open it |
| The pause menu: sentence-case labels and our proportions (a reader) | owner play test 10 | L4 | owed | all caps; squashed horizontally |
| Favourites open by Q and D-up with a favourite set | game-22 | L4 | owed | `dev-favorite` misses weapons by editor id (docs/research/2026-10-31/lane-game-22.md) |

## 1.13 The chart

| Check | From | Level | Status | Evidence |
|---|---|---|---|---|
| Full zoom-out shows the whole province, nothing cut off | owner play test 9 | L4 | owed | bottom cut off |
| The player marker shows at the player | owner play test 9 | L4 | owed | none |
| The area around the player reveals as they explore, and holds after a save and load | owner play test 9 | L4 | owed | not revealed |
| The chart's art is the old project's hand-drawn map (or its design) | owner note (tmp/owner-message.md) | L3 | owed | unconfirmed |
