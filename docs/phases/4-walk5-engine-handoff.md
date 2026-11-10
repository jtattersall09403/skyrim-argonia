# Walk 5, engine lane: hand-off (stopped at the usage limit)

The engine lane's brief (the lead's, 2026-11-10): fix the first act's quests in BM&V from the engine review
(`4-walk5-engine/review-engine.md`, sections A to F) and the builder-side items of the writing review
(`4-walk5-engine/review-writing.md`, section A), under the lead's eight rulings (MQ01 re-hosted beside the dock on
navmesh island 079823; one island per walk; a walk starts in view; Run Once and endings that stop and disarm; one quest
kit; `plugin.sh questcheck`; bands untouched; the recipe docs). Nothing of the fixes is in the plugin yet.

## Done
- Committed with this note: `inspect aliaspack` in tools/ArgoniaPlugin/Inspect.cs (the lead's read of alias packages).
- Measured (off game, `plugin.sh inspect navpath` / `navnear` on the built plugin): every MQ01 spot of the new host is
  within 150 units of a triangle of 079823 and joined to the plank's foot (5350,-7800) on that one mesh, nothing else
  nearer: fire 5900,-4700 CONNECTED (104 triangles reached); shed 6150,-4450 (153); cutting 6100,-4300 (154);
  shore end 4350,-4450 (165); water's edge 4500,-5150 (137); landfall 5300,-5200 (62); plank end 4900,-5450 (139);
  Deesh-Duun's hut end 4850,-5650 (3 triangles within 150). So the march, the shed route, both follows and the shore
  endings lie on one island once the builder uses these spots.
- Clutter in the footprint to disable through the clean-up (world_edit_target rows the data lane must add, edit
  `we.clean.hereguardplantation`, `what` "disabled: ... (MQ01's camp beside the dock)"), all `Black Marsh North.esp`:
  barrels 11AD83 to 11AD94 (18), grain sacks 11ADC7, 11ADC8, 11ADC9, lamp post and lanterns 14162E, 14162F, 141630,
  141631, 141632. CleanUp.cs needs the cell lookup for non-person placements first (in the patch below).

## Written, not proven (kept as a patch, the tree restored)
`4-walk5-engine/papyrus-and-cleanup.patch` (apply with `git apply`): every quest script's endings disarm a `Zones`
array and stop the quest (MQ04, MQ05 gain `Stop()`); one-ending guards in MQ03 20 and 40, MQ05, TG01, TG02; MQ01's
march: stage 30 enables the march copies and disables the hold's (one of each person), `StartMarch()` sets hidden
stage 32 once the five walkers' 3D is loaded (once a second, bounded at 60), `Fragment_32` evaluates each walker's
package, the strike puts any walker more than 400 from the fire at it before the courier dies, character creation
guarded by `started`; Fragment_35 and `March()` gone; MQ03 unlocks the Reed's house door at 20 and at the ending (A1),
the taste completes objective 10 (A14); CleanUp.cs reads a static's cell from the load order. It needs the builder
changes (Zones and HouseDoor properties, stage 32, no stage 35) in the same commit, and the lead's Papyrus compile.

## Left (in order)
1. The one kit: `4-walk5-engine/kit-port.md` (a zero-diff port of every builder onto QuestKit.cs; acceptance there).
   A child started it and was stopped; no builder file was changed.
2. questcheck: unfinished on branch `worktree-agent-a04c1ea806410c17d`, commit f59d3bc7 (worktree
   .claude/worktrees/agent-a04c1ea806410c17d), not merged: QuestCheck.cs with the loader, a .psc parser and nine
   rules; Program.cs and plugin.sh wired. Open: rule 1 reads navmesh vertices in the wrong order (most starts reported
   off navmesh); a QC_DEBUG block to delete; `--selftest` is a stub; tools/tests/test_questcheck.py not written; the
   acceptance run of `4-walk5-engine/questcheck.md` not done. Rule 7 skips same-base pairs; RunOnce is checked only
   on quests with an ending: lift both.
3. The fixes: `4-walk5-engine/fixes.md` is the checklist (kit additions, MQ01 re-host with its zones and targets,
   MQ03 at the new camp, MQ04 meshes from the winner 0C7102, MQ05's dead packages, Word topic, bounds and deaths,
   LQ25's MQ05 gate in a finish step, BC01/BC02 follows on the kit's Follow and Never-Sold kept at home, deaths per
   person, offers bounded, exclusive fallbacks, objective targets for all 42 objectives, TG02's pledges as quest
   objects). Then seed, round trip, placecheck, questcheck, the per-quest read-backs; `make check`.
4. The docs: `4-walk5-engine/docs.md` (blocks.md rows and quests-on-a-world.md sections 4, 5, 8), after 3 lands.
5. The report owed to the lead: the text keys the writing lane must change (MQ01 journals and objectives naming the old
   camp; MQ03 objectives 10 to 12 and the oath refusal; MQ05 Word under the `speech` gate as the one line; BC01
   objective and journal 10 with Never-Sold at home; BC01 after-greeting `after90`; the cool bands of A8), the stages
   that disappear (none planned: deaths kept as Protected for BC01's Rows-For-Another, BC02's Tsaxi, BC03's two; death
   triggers removed from MQ03's officer and Never-Sold), and the form ids that move (from BC01's PatronAtLanding
   onward, once the fixes land).
