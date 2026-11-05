<!-- imported unchanged from elder-souls-argonia docs/decisions/0153-quests-ship-as-data-over-one-world-record.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0153 Quests ship as data over one world record; the slice set is authored whole

**Decision (owner, 2.11 plan review).**

1. **What 2.11 proves is the recipe, not one quest.** Part 4 writes
   hundreds of quests by packet, so the risk is the writing recipe and
   the seams each shape crosses, not the state machine. Every quest that
   touches a slice place (derived from the build ledger and the anchors,
   never a hand list) is authored as data in 2.11. One wholly inside the
   slice plays end to end; one with an outside anchor plays to the stage
   that leaves the slice, shows that place's directions, and stops
   cleanly with its Part 4 packet named.
2. **One world record.** Every consumer of a world fact (directions,
   journal text, dialogue grounding, the quest validator) reads the place
   facts record, never the catalogue prose. Where the facts record cannot
   yet say it, the generator grows; a claim with no carrier is a red.
   The slice places' records and prose are audited against their built
   bundles before quests are written over them.
3. **The promise process goes one level down.** The two-way join between
   quest provisions and places stops at "the place exists". A stage-level
   validator checks the prose's claims against the world: a direction
   walks the route graph and arrives, a landmark is a real record in
   sight, a count exists in that area, the person to ask is there with the
   topic, and the first stage is reachable at the place's stance at that
   moment (its baseline, a flip an earlier stage can meet inside the
   slice, a clear on a clearable place, or an approach from outside the
   hostile scope). It gates authoring and runs over every record.
4. **Logic apart from text.** Stages, conditions, actions and objectives
   are data that reference text keys. Journal entries and quest lines are
   catalogue text written through the dialogue pipeline, so a better
   writing skill rewrites the text and re-runs the validator without
   touching a quest's logic. Directions are generated from the route
   graph and only restated in prose.
5. **The exemplar is judged by play.** No mid-phase owner read: the
   exemplar is written first, gated by the validator and a critic panel,
   the other quests follow in the same phase, and the owner judges it at
   the walk. A ruling from that play becomes a fix round over the rest.
6. **MQ01 is the opening's, whole.** The camp build already carries the
   barge, its roll and courier posts, the scene marks, the clutch and the
   witness sockets and the scene-state key; MQ01's stages, its attacked
   and aftermath variants and its play from new game and character
   creation are 3.4's, so the opening is tested end to end once and with
   the lessons of the simpler quests behind it. MQ01 stays in the
   validator set.
7. **Joining and stance are the runtime's.** Faction joining and rank
   grants, and the stance flips the catalogue hostility blocks declare,
   are interpreted at runtime from quest state, standing, gold and deeds;
   greetings, the answered-violence runtime and the travel predicates
   read the derived stance.
8. **The quest panel observes.** Under 0149 the studio shows a quest's
   stage, flags, objectives and journal and sets nothing; a journey's
   start state lives in capture tooling, and every journey reaches one of
   its states through the player's flow.
9. **Journeys are loops.** An end-to-end journey exists to surface
   defects: its strip is read, the findings fixed at source, the journey
   rerun, until the reader finds nothing a slice player would stumble on;
   the planner writes the exit judgement. Four journeys form a covering
   set over every verb kind the authored quests use, which is why four
   strips stand for the rest; the headless driver and the validator carry
   every quest.
10. **The UI is swept before it is built.** A thorough crawl of what the
    phase needs against what the UI package and the ui-lab hold, with
    file evidence either way, precedes any new screen; the gaps are built
    in the UI system on the three viewports.

**Why.** The phase brief assumed a blank slate (no map, no journal, a
single quest) when the dialogue package, the UI and the economy already
held most of the runtime's edges, and its single-quest scope would have
left the writing recipe, the hostile-place entries and the consistency of
prose with the world unproven until Part 4. The owner's standing
requirement is that a quest's directions take the player there and that
nothing in the world contradicts what the player was told, which only a
validator over one record can hold at scale.

**Consequences.** `packages/narrative` holds the quest and journal
stores, the applier, the flip evaluator, markers, the overlay runtime and
the driver; `standing.ts` gains join, expel and rank grants; the quest
record gains `stages`; `worldgen.quests --check` gains the stage-level
rules; the facts generator grows; the 3.4 brief owns MQ01 whole; the
production sequence's "World Studio narrative debugger" is an observe-only
panel; the data model gains the save families.
