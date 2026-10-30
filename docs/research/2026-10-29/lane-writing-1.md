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
