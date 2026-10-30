# Lane writing-1: LF83 and the three Claywater people (1.4 content, 1.3 §b)

2026-10-29. Handed off at the context mark (planner's call at 349k).

## Hand-off: state and what is left, in order

**The quest, quest.local.lf83 "The Well and the Landing": recordStatus `design`, not yet `reviewed`.**
- Round 1 `quest-review` (fresh quest-reviewer agent): 13 findings (3 high, 6 medium, 4 low). All 13 are fixed or
  answered in the record's `review` section (rows `quest_review_finding`); one stays open as a db-lane debt (R12: the
  record view has no concept/lead column for clues).
- Round 2 review was launched on the fixed record and had not returned at hand-off. Its findings are lost with
  this context, so the next lane re-runs it.
- `brief.py` builds every brief from the current rows: 3 people, Gaius Vibius with 0 topics, and the journal.
  Output is in `out/briefs/lf83/` (git-ignored, rebuilt by the command below).

**Dialogue: nothing written yet for any of the three people.** The three chosen are Livia Varinius (the
well-keeper), Signs-For-The-Cargo (the landing's poler) and Takes-The-Short-Weight (n1-3). Why these three:
- The two keepers are the two sides of the negotiation.
- Takes-The-Short-Weight is the doubter the social principles require, the hook-giver, and the only Part 1 route
  to the crack clue.
- With these three the main path plays in Part 1 without the other four Claywater people.
- 0.4 §d should place these three. This is for the planner to confirm against the game lane.

**What is left, in order:**
1. Re-run quest-review round 2 on `quest.local.lf83`, with a fresh `quest-reviewer` that gets the same context
   note as round 1 (Part 1 systems, the three placed people, npcAlive reads creatures).
   - Fix every finding in the YAML view: `quest_record export quest.local.lf83 -o out/quests/lf83.yaml`, edit,
     then `import`.
   - Repeat until no finding is open. Then set `recordStatus: reviewed`, move R12 to an answered state, and
     re-import.
2. Objective text rows. The `quest_objective.text` keys `text.objective.lf83.{hear-station, hear-landing,
   why-failing, clear-bend, get-clay, terms}` have no `journal_entry` rows yet; only the imported old
   hear-landing and carry-terms rows exist.
   - Add them to `tools/argonia_world/content/lf83_things.py` as `journal_entry` rows.
   - The drafts are in the old record view: "Hear Livia Varinius at the well." / "Hear Signs-For-The-Cargo at the
     landing stage." / "Find out why the well at Claywater Station is failing." / "Bring the landing's clay basket
     back from the clay bend." / "Put terms to Livia Varinius and to Signs-For-The-Cargo." / clear-bend: "Kill the
     crocodile at the clay bend."
   - Delete the stale `text.objective.lf83.carry-terms`.
3. Rebuild the briefs with `brief.py quest.local.lf83 out/briefs/lf83` and `place_brief.py --person
   <id> --out out/briefs/place/<slug>.md`. The place briefs already exist for the well-keeper, the
   landing-s-poler and n1-3.
4. Run `dialogue-write` per person: three `dialogue-writer` agents, each given the place brief and the quest
   brief, with `corpus-find` over `~/argonia-private/dialogue/morrowind/groups/` and reports kept under
   `~/argonia-private/work/writing-1/`.
   - Output format: `tools/argonia_world/lines.py` YAML (its docstring). Ids are
     `line.claywater-station.<slug>.<topic-slug>[.<variant>]`; types are greeting, dialogue, goodbye.
   - Bands follow 1.3: `low` < 30, `words` 30–69, `high` ≥ 70. This conflicts with dialogue-write SKILL §4, which
     lists four bands; the skill needs a one-line fix to 1.3's three. Essential topics have no refusal band.
   - Each line carries its `facts`, `links` (hyperlinks), `available` conditions (questStage, flag, hasItem,
     dispositionAtLeast) and `onDelivered` actions. These are the record's takeGold 2 / takeGold 1 on the
     two-charges lines, setFlag ford-tasted / one-charge-* / ford-charge-bought / stop-charge-dropped, and
     takeItem clay-basket.
   - Each person also gets greeting variants after each ending (stage → greeting join) and a Goodbye line.
   - A fourth writer run covers the journal brief. Its journal text replaces `journalText` in the record.
5. `lines.py import out/lines/<slug>.yaml` per person. Then lint each file:
   `lines.py text F > t.txt; lint.py t.txt --race <race>`.
6. Run `text-review` with one `reader` over the lines and journal text, then the linter.
7. Post to the owner with `tooling/owner_inbox.py --post`: the record and the lines to read in their own time,
   how to reply, and the costs (`python3 tools/cost_report.py`).
8. Run `make check` once, then commit by pathspec.

**Reds:** none. 72/72 tests pass in `tools/argonia_world/tests/`, and `db check` is green. `make check` has not
been run: it was left for the final commit, per the memory guidance.

## What was built (committed)

**The record (rows).**
- LF83 was rebuilt from the imported skeleton: NEGOTIATION, cost tier raised from S to M, centrepiece COMBAT.
- Truth:
  - The stone well head, set in a moving clay bank, keeps cracking. A new crack opened on 5 Rain's Hand 4E 201,
    matching the station ledger's page.
  - The station charges for the stop. The landing charges walkers in answer.
  - A crocodile holds the clay bend where the landing digs its plaster clay.
- Three settlements:
  - one shared charge with a clay seal (stage 40);
  - buy off the ford charge (41);
  - the station drops its charge (42).
- A seven-day deadline (stage 90), and each keeper's death as its own resolution (92 and 93).
- Each keeper's charge is taken from the player in dialogue, so the premise is felt.
- Rewards are existing items and dispositions.

**New world rows**, through `tools/argonia_world/content/lf83_things.py`, which is idempotent:
- items `item.lf83.well-silt` and `item.lf83.clay-basket`;
- sockets `socket.claywater-station.lf83-{well-silt, clay-bend, clay-basket}` for hand placement in 0.4 §d / 1.4;
- local variants `lf83-well-clayed`, `lf83-well-closed` and `lf83-walls-unplastered`;
- topics `topic.lf83-{cracked-well, clay-bend, one-charge, ford-charge, stop-charge}`;
- `line_type goodbye`;
- the `verb_tag` lookup completed from skill-uses.yaml. It held only DIVE before.

**Directions, checked by hand against the db.** The route graph has no Claywater node.
- The station sits on `edge.route.road.gideon-blackwood-road.1087` at 584.8 m from Cartwright's Cross. That
  junction's signpost points to Gideon and to the Leyawiin exit.
- Going west, the station house lies north-west of the road vertex (364.65, 3117.38), which puts it on the right.
- Distances measured in place frame metres (x east, y south):

  | From → to | Measured | Written in the record |
  |---|---|---|
  | Well (323, 3062) → raft (348.3, 3007.9) | 59.6 m | "about sixty yards" |
  | Raft → clay bend (396, 3006) | 48 m | "about fifty yards" |
  | Raft → hut (339, 2968) | 41 m | "about forty yards" |

**Tools.**
- `tools/argonia_world/stage_walk.py` is the L2 stage-graph walker. Its rule: fail-forwards first, then
  successors. It builds witness states from each edge's condition, and flags shadowed edges, dangling or
  unreachable stages, and a named person with no death fail-forward (old 0138).
- `tools/argonia_world/lines.py` is the smallest lines importer and exporter. 2.5 owns the full one, and the db
  lane's report lists it as owed.
- Tests:
  - `test_stage_walk.py` (4 tests): every LF83 branch, including the deadline and both deaths from stages
    10/20/30; death overrides progress; and two tests that must fail, on a broken record, a dropped death
    fail-forward and a shadowed edge.
  - `test_lines.py` (8 tests): the round trip, re-import replaces, and the refusals.
  - `test_briefs.py::test_quest_brief_refuses_once_a_cited_fact_is_deleted`: brief.py refuses once
    `fact.claywater-station.vibe-condition-1` is deleted. This shows the refusal.
  - LF83 was added to `test_quest_record.py`'s round trip.

## Findings for other lanes and the planner
- **The schema doesn't fit three things the record needs (db lane):**
  - `quest_shape_data_items` has only investigation columns, so NEGOTIATION's sides, leverage, objections and
    aftermath are stored as speaker/says/refutedBy/from/to prose.
  - `quest_objective` has no objective-text column, so `objectiveText` in quest-record.md cannot import.
  - The `dialogue_line` comment promises a `status` column (imported versus written) that does not exist.
    Written lines are told apart by the `line.` id prefix.
- **The station house's interior host cell is `DawnstarBrinasHouse`,** a vanilla Nordic cell name. This is a 0012
  quarantine question for the place lane.
- **LF71 (Cartwright's Cross, 585 m east)** shares the charged-twice surface with LF83. When LF71 is rebuilt it
  should move off it.
- **World data conflict:** the station ledger says "the poler's wife came for water", while the landing's culture
  sheet says the landing does not drink the well's water. The record uses the ledger: the station charges the
  landing nothing.

## Round 2 review (arrived after hand-off; not yet applied: step 1 of the list is now "fix these", then round 3)

High
1. The crocodile fight may not be winnable in Part 1: `creature.crocodile` swims only (slaughterfish skeleton),
   flees and sinks at 20 %, respawns on rest, rests at the den by day. Hand the planner a crocodile override (held at
   the cut, flee 0, respawn held through the quest), prove the land fight at L4, latch the kill with a flag. (R3, R8
   not accepted.)

Medium
2. e-landing needlessly passes through stage 30 (crocodile and basket): open topic.lf83-stop-charge at 20 once the
   crack is known.
3. Journal 20 names the basket before anyone tells the player: Takes says it lies at the cut (not that he ran).
4. why-failing rests on one clue (the jar shows silt, not a crack): complete it when Livia admits the crack after
   being shown any of k1, k3, k4.
5. The rains timer starts before the player is told: put rains-close in the poler's and Takes's two-charges rows
   and in journal 10; consider gating the start on `seasonIs`.
6. Takes does not add up: her household's taboo forbids well water in the brine (and the record cites
   `culture.household.claywater-station.drying-racks`, which does not exist; find the real id); her stance avoids the
   well; she sends waders to the bend while fearing for them; she takes quarrels to the poler per the settlement
   norm. Re-ground how she tastes the water, have her turn waders back, give her silence to the poler a reason.
7. The settlement norm (each bank charges for its own half) is old custom; state the old charges (beds, carts by
   the wheel) and what is new.
8. Why the clay bend, and why nobody kills the crocodile: the bend is the only plaster-grade clay; Signs is the
   landing's only spear-hand.
9. Livia's motive in e-landing: the evidence shows stone cannot hold in that bank, so her charge buys nothing.
10. e-station: Takes's disposition should not drop; takeGold 100 is in both the topic and the ending (keep one);
    journal 41 states the crack even when the bribe comes at stage 10.

Low
11. topic.lf83-clay-bend (poler) both uses and hides basket-left (R12 not accepted).
12. Reveal order: charges-answer arrives in the poler's first line; leverage[2] gives Takes's k8 to the poler.
13. Missing rows: rumour_pool rows for rumour.lf83.*; the basket socket is owned by the poler (taking it is theft);
    the ledger counts only if taken; the crocodile can kill the poler (stage 93) (R10 not accepted).
14. Gaius Vibius is not placed in Part 1 yet argues the station's case and takes −15 in e-shared.
15. Rewards have no named giver; the shortspear is untied to the story (free raft crossings, the crocodile's hide).
16. Journal 10 says "I paid Livia" whatever the order; the ledger leaf has a stray "The roof shows it first." and
    an unmeetable "poler's wife" (place lane).

Accepted round-1 answers: R1, R2, R7, R9, R13; partly: R4, R5, R6, R11; not accepted: R3, R8, R10, R12.

## Continuation (2026-10-29, second context): the schema gaps, rounds 2 and 3, and the hand-off

**Committed.**
- `a55a367` Three 0030-section columns (planner ruling): `quest_objective.objective_text` (the record's
  `objectiveText`), `quest_clue.kind` (`concept` | `lead`, CHECK) and `dialogue_line.status` (`imported` | `written`,
  NOT NULL). All 2040 existing lines were migrated through db.py as `imported`. `lines.py` now selects and writes by
  `status`, and `quest_view.json` maps the two record fields. Tests: written lines are marked and a bad status is
  refused (test_lines); objectiveText and kind round-trip and a bad kind is refused (test_quest_record). The
  dialogue-write SKILL band line now reads 1.3's three bands.
- `852816b` Round 2 (fresh quest-reviewer: 4 high, 10 medium, 15 low, report
  `~/argonia-private/work/writing-1/review-r2.md`), every finding answered in the record (`R2-*` rows). The main
  changes:
  - The secret is now the yearly mending, not the crack.
  - The clay cut moved to the river's first swing below the ford. It is on the station bank, measured against
    `hydrology_reach_point` reach.169-1660.
  - Every settlement topic is granted, and Takes's clue is a taste test at her door.
  - The four objections are conditions, and the dry season is the deadline.
  - The quest is held to tier M: one variant, two approaches a stage, no rumours, no setWeather.
  - The six objective texts are in `objective_text`. `lf83_things.objective_entries` writes their `journal_entry`
    rows from it and deletes the stale `text.objective.lf83.carry-terms`.
  - `stage_walk.py` reads `seasonIs` (4/4 tests).
- `786cc01` Round 3 (fresh reviewer: 3 high, 8 medium, 20 low, report `review-r3.md`), every finding answered
  (`R3-*` rows). The main changes:
  - The yearly mending has three clues: k2, k15 (the mortar tub) and k16 (Takes, from the poler's wife, t10). It
    gates through objective `old-mending` at stage 30.
  - The seal is clay rammed behind the lining.
  - New item `item.lf83.well-water` (Livia's dipper) with its socket.
  - The ledger route is inside the station house, gated on the 0012 cell review.
  - The deadline is seasonIs wet. The terms have a figure (fact.lf83.terms-figure).
  - The e-shared and e-landing reward is the Drowning Gate ferry fare set to 0.
- Tests: 75/75 in tools/argonia_world/tests and .claude/skills. `db check` is green.

**Handed to the planner (the record names each).**
- 16a: a scour pool of 2.5 m or more under the cut at (281.5, 3058.5), and `socket.claywater-station.den-crocodile`
  moved there (it sits 55 m east of the raft, on marsh).
- 16b: activators that set `flag.lf83.crack-seen` (the well head) and `flag.lf83.tub-seen` (the mortar tub); a
  ledger-read hook (`flag.lf83.ledger-read`); and the crocodile den never respawning from the kill on.
- The Part 1 evaluator must cover seasonIs, topicHeardFrom, objectiveComplete, flag, npcAlive, hasItem, goldAtLeast
  and speakerDispositionAtLeast, and the actions takeGold, takeItem, giveItem, setFlag, grantTopic,
  applyLocalVariant, setPrice, changeDisposition and changeSettlementStanding.
- Confirm that the 4E 201 dry season holding Rain's Hand (the ledger's imported date) is at or after the game's
  start date.
- 0012: `DawnstarBrinasHouse` hosts the ledger. The ledger route stays closed until that cell is reviewed.
- 2.12 schema item: NEGOTIATION shapeData (sides, leverage, objections, aftermath) is still prose in
  `quest_shape_data_items`.
- Withdrawn: the round-1 claim that ford-mooring's water_id is a tarn 1.3 km away. body.221-1650 is the tarn at the
  ford.

**Round 4 and `reviewed` (`979cf55`).**
- Round 4 (fresh reviewer: 4 high, 4 medium, 15 low; report `review-r4.md`).
- The four high findings are fixed:
  - the crocodile's territory override is added to the 16a hand-off;
  - the basket socket is unowned;
  - stage 10's left and right are corrected, and its yards are converted from the measured metres;
  - the ledger host is reworded. Its re-hosting on a table is added to the 0012 pass.
- R4-M3 is fixed: the conditions read the evidence flags directly.
- The rest go into review row `R4-rest`, noted for 2.12 under the planner's convergence rule.
- `recordStatus: reviewed`. Briefs and place briefs are rebuilt.
- Next lanes, from R4-rest: the dialogue writers should know that R4-M2 (Signs's stage-10 clay-bend row still uses
  takes-doubts) and R4-M4 (Takes's cracked-well topic carries eight facts) stand. Write Signs's stage-10 line
  without the reprisal. Pace Takes's topic over two answers.

## Hand-off (second context, at the 250k mark): exact list for the next writing lane
1. Run three `dialogue-writer` agents in parallel, one per person, plus a fourth for the journal brief. Each gets
   the quest brief and the place brief:
   - Livia Varinius: `out/briefs/lf83/lf83-livia-varinius.md` and `out/briefs/place/well-keeper.md`.
   - Signs-For-The-Cargo: `out/briefs/lf83/lf83-signs-for-the-cargo.md` and `out/briefs/place/landing-s-poler.md`.
   - Takes-The-Short-Weight: `out/briefs/lf83/lf83-takes-the-short-weight.md` and `out/briefs/place/n1-3.md`.
   - The journal: `out/briefs/lf83/lf83-journal.md`.
   Briefs are git-ignored; rebuild them first with
   `brief.py quest.local.lf83 out/briefs/lf83` and `place_brief.py --person <id> --out out/briefs/place/<slug>.md`.
   - Output: `out/lines/<slug>.yaml` in lines.py format.
   - Ids: `line.claywater-station.<slug>.<topic-slug>[.<variant>]`.
   - Bands: 1.3's three (the fixed SKILL §4).
   - Gates: the terms written in each topic intent, as `available`.
   - Actions as `onDelivered`. Signs's ford-charge line needs goldAtLeast 100 and takeGold 100. Livia's
     two-charges pay line takes takeGold 2 and gives giveItem item.lf83.well-water. Takes's taste line takes
     takeItem item.lf83.well-water and sets setFlag ford-tasted and mending-heard. Signs's one-charge line takes
     takeItem clay-basket.
   - Every greeting links topic.claywater-two-charges at stage 0 in the dry season. Each person gets
     post-ending greeting variants and a Goodbye.
   - Reports go to `~/argonia-private/work/writing-1/`.
2. Import each file with `lines.py import out/lines/<slug>.yaml`, then lint it with
   `lines.py text F > t.txt; lint.py t.txt --race <race>`.
3. The journal text replaces each stage's `journalText` through `quest_record export/import`.
4. Run `text-review` with one `reader` over the lines and the journal text, then the linter.
5. Post the owner check-in with `owner_inbox.py --post check`:
   - plain English: what the quest is, who the three people are, where the record and lines live, how to reply,
     and that nothing waits on the read;
   - the cost line from `python3 tools/cost_report.py`;
   - no permission-drafts note (the planner dropped it: the permissions are already obtained).
6. Run `make check` once, then commit by pathspec.

## Dialogue (writing-3, 2026-10-30)

**Done.** The dialogue for the three placed Claywater people and the LF83 journal are written, imported and reviewed.
- Four `dialogue-writer` agents ran in parallel from rebuilt briefs (`brief.py`, `place_brief.py`). Their notes and
  fact requests are in `~/argonia-private/work/writing-3/{livia,signs,takes,journal}.md`.
- Lines imported with `lines.py import`, `status written`, 107 rows:
  - Livia Varinius (well-keeper): 39 lines;
  - Signs-For-The-Cargo (landing-s-poler): 30 lines;
  - Takes-The-Short-Weight (n1-3): 38 lines.
- Each person has three-band greetings, including the dry-season stage-0 greeting that links
  `topic.claywater-two-charges`. Each has every quest topic at its stages, every place topic, a greeting after
  each ending they live through, and a Goodbye.
- The journal text for stages 10, 20, 30, 40, 41, 42, 90, 92 and 93 replaced `journalText` through
  `quest_record export/import` (`world/db/quest_stage.jsonl`, 9 rows).
- Text review:
  - Round 1 (`reader`, report `~/argonia-private/work/writing-3/text-review.md`) found 52 itemised rows, plus
    206 comma-and joins and 67 uses of "citizen". All were applied in one fix pass.
  - The re-review covered only the changed bands (200 bands, report `text-rereview.md`). It found 28 rows, and all
    were applied.
  - After the fixes, `lint.py` gives 0 regex hits on all four texts (imperial, argonian, argonian; journal as
    imperial). A pattern count gives comma-and, nobody/somebody, only-one and rather-than 0 in every file, and
    "citizen" 26 (from 67).
- Rulings made in the fix pass:
  - At stage 40 the clay is already rammed in, as the `lf83-well-clayed` variant shows.
  - The e-shared and e-landing reward is the Drowning Gate ferry, not the raft. Journal 40 and 42 were corrected.
  - The poler's stage-30 lines no longer say the crocodile holds the cut.
  - Takes's mending clue names "a woman of the landing" (k16's "the poler's wife").
- Owner check-in: issue #14.

**Open, for the quest writer or planner (none blocks Part 1):**
1. Fact requests:
   - the about-onkobra, about-prison-road, about-gideon, about-helstrom and about-blackwood answers (what each
     is, where it is, how far);
   - directions from the station to Gideon and to Leyawiin;
   - where Gaius Vibius, Keeps-The-Second-Ledger, Abhuki and Mee-Seesh stand. The lines point to them without a
     place. Signs's Helstrom and prison-road pointers to Abhuki and Mee-Seesh need confirming;
   - Livia's training and bed and stable prices;
   - what each keeper knows after each ending (the greetings rest on the stage names);
   - a danger fact for Takes after the crocodile is dead.
2. Mechanism: the record's "player chooses to pay (takeGold 1)" at the ford has no line. `lines.py` has one
   `onDelivered` per line, so a choice needs its own line or a choice mechanism (2.5).
3. Quest topics answer only to stage 30. After an ending only greetings and place topics answer, and the brief
   lists no post-ending topic stages.
4. Doubts left from review:
   - Signs says the well stands at the station house door, while Livia puts her counter by that door.
   - The journal gives the free Drowning Gate ferry, but no spoken line does.
   - Journal 20's "I'm to kill the crocodile" is the objective gloss; no speaker says it.
   - "Gods keep the road dry" (Livia's goodbye) needs checking against the Imperial-fringe register.
   - Livia says "citizen" to every race. There are no listener variants yet.
5. Tooling:
   - The `lines.py` docstring shows `'>='`, but the `condition_op` lookup holds `≥ ≤ ≠`. The importer does not
     check the operator.
   - The style guide's prose linter (the comma-and, nobody-somebody, only-one table) has no implementation in
     the repo. `lint.py` does not catch comma-and, so the reader carried it.

## Follow-ups (writing-4, 2026-10-30)

**Done.** This closes the dialogue open list above for the owner's 1.7 verdict.
- **Persuasion route, by flag.** The vocabulary has no persuade action verb, so persuasion is a Speechcraft check
  on the line: `skillAtLeast speechcraft 30`, an authored threshold that is never rolled. Each keeper's
  `one-charge.argued` line sets `flag.lf83.livia-persuaded` or `flag.lf83.poler-persuaded`, and the agreement
  lines read the flag, never disposition.
  - Livia's persuasion answers her stone objection only, once the yearly mending is found. Her half-charge
    objection still needs the landing's promise.
  - Signs's persuasion answers his stone objection once the basket is back.
  - Review round 5 (record R5; report `~/argonia-private/work/writing-4/review-persuasion.md`) found 0 high and 5
    medium. M1 and M3 were fixed. M2, M4 and the lows are noted for 2.12.
- **Facts.** `tools/argonia_world/content/claywater_facts.py` adds 8 place facts, read off the route, hydrology,
  glossary and socket rows: the road to Gideon and to Leyawiin, Gideon, the Onkobra (the ford's stream is not the
  Onkobra), Helstrom, the Prison road, and where the household and the travellers stand. The record adds 8 more:
  one per ending, the free ferry, and the crocodile's death. The `about-*`, directions and people lines of all three
  people now state these facts and no longer send the player to the unplaced travellers.
- **Choice to pay.** It stands in until 2.5's choice buttons. Once the player has heard a keeper's side, asking
  `two-charges` again with the money pays, once only: Signs takes 1 drake and sets `flag.lf83.ford-paid`; Livia
  takes 2, gives the dipper and sets `flag.lf83.stop-paid`.
- **Post-ending topics.** Every quest topic of the three placed people answers at every ending they live through:
  44 new lines, each fixed to its ending's stage.
- **Tooling.** `lines.py` refuses any operator that is not a `condition_op` row, with two tests.
- **Tests.** `test_stage_walk.py` drives the lines in first-match id order through four checks:
  - the persuasion route reaches stage 40;
  - Speechcraft 29 gets the refusals;
  - persuading Livia alone leaves the half-charge objection open;
  - the pay choice happens once.
  It also checks that the post-ending answers cover every ending and topic.
- **Text review.** One `reader` pass over the 61 new and changed lines found 74 rows, and all were applied (see
  `~/argonia-private/work/writing-4/apply.md`). `lint.py` then gives 0 regex hits on all three people. Store::lint
  reports 0 findings on 0145.

**Open, for the planner:**
- Gaius Vibius (Imperial) shares the landing's household hut in the place build (`socket.claywater-station.npc-family`).
  This may be a slot artefact.
- The people lines name posts for Gaius Vibius, Keeps-The-Second-Ledger, Abhuki and Mee-Seesh. Only three people
  are placed in Part 1.
- The reader's fact doubts are in `~/argonia-private/work/writing-4/text-review.md`. They include the Drowning Gate
  as both a barrier and a ferry, and Livia hiding a reason that the other two state.
- The rest of the earlier list (training and bed prices, Livia's listener variants) stays open.
