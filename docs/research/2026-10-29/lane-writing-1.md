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
