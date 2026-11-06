# The block set: every engine mechanic the first story slice uses

Phase 2 ([brief](../phases/2-first-act-on-paper.md)). Derived from the act's quest records (`quest.main.mq01`,
`mq03`, `mq04`, `mq05`; adaptation in [adaptation](../../story/design/quests/adaptation.md) §5). A quest is QUST stages
joined by connectors: a **trigger** moves a stage, a **condition** gates a trigger or a line, an **effect** is what a
stage does, and a **world edit** is the record under them. Each block has one record shape (Spriggit YAML under
`plugin/Argonia`, built by `tools/ArgoniaPlugin`) and at most one Papyrus shape (a stage fragment, `QF_`, or a
dialogue fragment, `TIF_`). Precedent is counted in Skyrim.esm (decision 0034; the counts and how they were taken:
[quest-block-precedent](../research/skyrim/quest-block-precedent.md)). No block needs SKSE.

## Triggers (what moves a stage)

| Block | Record shape | Papyrus shape | Skyrim.esm precedent |
|---|---|---|---|
| **TR-topic**: a dialogue topic or choice | DIAL in the quest's branch; INFO with conditions; the choice is one INFO per answer | TIF_ `GetOwningQuest().SetStage(n)` | 5,540 INFOs with a fragment, in 475 quests |
| **TR-zone**: entering an area | ACTI trigger box (XPRM primitive) placed as REFR | the vanilla `defaultSetStageTrigScript` (properties: quest, stage, prereq stage); no script of ours | 327 refs carry it; 2,966 refs of 256 *Trig* bases |
| **TR-activate**: using or reading a thing | the thing is a forced-ref alias | the vanilla `defaultSetStageAliasScript` / `defaultSetStageActScript` | 119 quests use the alias set-stage family; 178 activate-script records; 6 read-book set-stage |
| **TR-acquire**: picking up an item | the item is a forced-ref alias | the vanilla `defaultSetStageOnPlayerAcquire` | 16 quests |
| **TR-death**: a death, or a group cleared | the actor (or each of the group) is a forced-ref alias | the vanilla `defaultSetStageOnDeathRefAlias`; for a group, `defaultCounterIncrementOnDeath` | 20 and 47 |
| **TR-chain**: another quest's stage | the next quest's QUST (not Start Game Enabled) | QF_ `NextQuest.Start()` / `SetStage(10)` at the ending stage | 86 quests read another quest's stage; 1,596 INFOs do |
| **TR-scene**: a scene finishing | SCEN owned by the quest | SCEN end fragment `SetStage(n)` | 577 scenes have fragments; 1,706 scenes in 1,378 quests |

## Conditions (what gates a trigger or a line), all CTDA on INFO, QUST or PACK

| Block | Function | Precedent (uses in QUST, INFO, PACK, SCEN) |
|---|---|---|
| **C-stage** | GetStage / GetStageDone (own quest or another's) | 8,029 / 4,175 |
| **C-global** | GetGlobalValue (settlement standing, owings) | 1,579 |
| **C-faction** | GetInFaction / GetFactionRank | 6,904 / 259 |
| **C-item** | GetItemCount | 678 |
| **C-skill** | GetActorValue on a skill (speech, sneak, alchemy...) | 150 on skills, of 543 |
| **C-time** | GetCurrentTime | 518 |
| **C-alive** | GetDead | 1,028 |

Flags in the records (`flag.mq*`) are not a block of their own: each is a stage done (C-stage) or a global
(C-global), whichever the record writes it as.

## Effects (what a stage does)

| Block | Record shape | Papyrus shape | Precedent |
|---|---|---|---|
| **E-stage**: the next stage, its journal entry and objective | QUST stage with log entry (CNAM) and QOBJ objective, no target | QF_ `SetStage`, `SetObjectiveDisplayed/Completed` | 726 log stages in 203 quests; 1,452 objectives in 396 |
| **E-enable**: show or hide a set of things | each set's refs carry XESP to one XMarker parent; the parent starts disabled or enabled | QF_ `Parent.Enable()` / `Disable()` | 23,239 refs with XESP; 911 initially disabled with one |
| **E-item**: give or take an item or gold | the item is a MISC/BOOK/WEAP record (fixed, never a levelled list) | QF_/TIF_ `Game.GetPlayer().AddItem/RemoveItem` | every vanilla reward; fragment bodies not counted (compiled) |
| **E-move**: place or move an actor or the player | an XMarker as the destination | QF_ `Ref.MoveTo(Marker)` | MQ101 and the vanilla dream quest DA16 do this; not counted |
| **E-faction**: join a faction or change rank | alias faction list (ALFC) on the alias, or a fragment | QF_ `AddToFaction/SetFactionRank` | 1,215 alias factions in 140 quests |
| **E-scene**: start a scene | SCEN owned by the quest, actors as aliases | QF_ `Scene.Start()` | 1,706 scenes |
| **E-package**: give an actor new behaviour | alias package list (ALPC: follow, travel, sandbox at a marker) | none: the alias filling applies it | 4,125 alias packages in 365 quests |
| **E-global**: change standing, owings, a remembered choice | GLOB record | QF_/TIF_ `Global.SetValue/Mod` | backs the 1,579 GetGlobalValue uses |
| **E-regard**: a person likes the player more or less | none | TIF_ `Actor.SetRelationshipRank(Player, n)` | the vanilla favour quests' `favorNPCDeathScript` set (46 quests) stand on it; not counted |

## World edits (the records under the blocks)

| Block | Record shape | Precedent |
|---|---|---|
| **W-npc**: a new person from a template, on existing navmesh | NPC_ with TPLT to a BM&V or vanilla base, our name, placed ACHR, persistent | 3,651 of 5,118 NPC_ have a template |
| **W-fixed**: a creature or enemy at a fixed level | NPC_ with the PC-level-mult flag off, a fixed level for its band (decision 0035) | 4,664 of 5,118 NPC_ are fixed level |
| **W-ref**: a new, moved or removed reference | REFR in a BM&V cell (our override of the cell's persistent/temporary group); a removal is the ref's own override set initially disabled (record flag 0x800), or a set under an enable parent that stays off, never a delete | 4,072 placements start disabled (2,682 REFR, 1,390 ACHR); 23,239 carry an enable parent (XESP) |
| **W-navmesh**: navmesh for a room that has none, so placed people can walk | NAVM in the interior CELL's group, made in the Creation Kit from the room's geometry | 583 of 590 interiors carry navmesh (1,519 NAVM); the seven without are test, preload or maze cells |
| **W-name**: a name for a place (an interior cell, or a map marker) | CELL FULL, or a map-marker REFR (XMRK) with FULL, overriding BM&V's | 583 CELLs carry FULL (all interiors); 397 map markers, every one named |
| **W-override**: a changed BM&V record (a lock, a door, a container) | the BM&V record overridden in Argonia.esp (Argonia.esp already does this for MQ101 and 182 others) | Update.esm overrides Skyrim.esm the same way; not counted |

Aliases are a rule of the blocks, not a block: every alias in an act quest is a **forced reference** to a persistent
ref we placed or a BM&V ref (2,687 forced-ref aliases in 425 vanilla quests), never "find matching".

## Dropped, and why

- **Waiting or sleeping as a trigger.** Vanilla has no alias script for it (0 quests) and only 10 records with a sleep
  script. MQ01's dawn and MQ03's dream were re-authored: the dawn is a topic with a C-time condition (talk to the
  survivor after five in the morning), and the dream is a bed the player activates (TR-activate, then E-move into
  `01Cavebig`).
- **Change Location story-manager starts.** 135 vanilla quests use them, but no act quest needs one: every quest
  starts from the one before (TR-chain), and arrival is a TR-zone at the settlement's edge.
- **Location conditions** (GetInCurrentLoc). BM&V has no LCTN records of its own (census), so a location condition
  has nothing to test; zones do the work.

## The induction note

**Why the base cases and one composite prove any quest built from the set.** A quest built from these blocks is a
graph of QUST stages; every edge is one trigger, gated by conditions, and every node fires effects over world edits.
The engine joins them only through the quest's stage: a trigger's whole output is `SetStage(n)`, an effect's whole
input is "stage n began", a condition's whole input is engine state (stage, global, faction, item, actor value,
clock, death). So a block proven once (the **base case**: it fires, or holds, in a quest of its own) behaves the same in
any quest, provided the joint is proven too. The **inductive step** is one composite quest in which every trigger
type moves a stage that fires every effect type, each trigger gated by every condition type. If a quest of k stages
works, adding a stage adds one edge of proven kinds through the proven joint, so the quest of k+1 stages works.

**Where the argument fails on this engine, and the guard for each.**

| Failure | Why it breaks | Guard (a rule of the block or a case in the composite) |
|---|---|---|
| Two triggers racing for one stage | MQ01 stage 40: two zones (the shed, the dock) could both fire; SetStage is not atomic with the read of the stage | Rule of TR-zone and TR-topic: every trigger carries a prerequisite (`GetStage == n`, the trigger script's prereq property), and the two outcomes are different stages (41, 42), each fragment disabling the other's trigger first. The composite has two zones that fire in the same frame. |
| Alias filling at quest start | a forced alias whose ref is disabled or in an unloaded cell fails to fill, and the quest refuses to start | Rule: forced refs only, every aliased ref persistent, aliases that may be gone marked Optional; no find-matching. The composite starts while its aliased refs are disabled and two cells away. |
| Persistent references | a non-persistent ref in an unloaded cell cannot be enabled, moved or filled | Rule of W-ref and W-npc: every ref a block names is persistent (in the cell's persistent group); the build check lists any quest-named ref that is not. |
| AI package priority | an alias package can lose to the actor's own (BM&V or template) package, or to combat | Rule of E-package: alias packages sit on the alias (which outranks the actor's own) and each has its conditions on the stage; a scene's actors are aliases of the scene's quest. The composite runs an escort while a hostile is enabled. |
| Save and reload mid-quest | a fragment running at the save is cut short; a trigger box that fired once may fire again; a scene in progress restarts | Rule of E-stage: fragments are short and idempotent (enable what should be enabled, never toggle); triggers carry the stage prerequisite so a refire does nothing; scenes are written to restart from their beginning. The composite is saved and reloaded at every stage. |

## Every stage of every act quest, mapped

Every stage of every act quest maps to the blocks above. Columns: the trigger that enters the next stage, the
conditions that gate it, the effects the stage fires, and the world edits it stands on. Record terms map to blocks so:
`topicHeardFrom` is TR-topic; `inZone` and `inSettlement` are TR-zone; `hasItem` as a trigger is TR-acquire, as a gate
C-item; `npcAlive` failing is TR-death; `counterAtLeast` and `placeCleared` are TR-death's counter; `questStage` and
`stageEverReached` are C-stage; `timeOfDay` is C-time; a record `flag` is C-stage or C-global; `npcAtMark` is
E-package (the actor's alias package puts them there) plus C-time; `grantTopic` is the topic's own C-stage condition;
`setFactionRank` and `grantServiceAccess` are E-faction; `changeStanding` and `changeSettlementStanding` are E-global;
`changeDisposition` is E-regard; `enableRef`/`disableRef`/`applyLocalVariant` are E-enable; `giveItem`/`takeItem`/
`giveGold`/`takeGold` are E-item; `moveRef` is E-move; `startScene` is E-scene. `goldAtLeast` is C-item (GetItemCount on Gold001, within the 678 GetItemCount uses counted in quest-block-precedent.md); `grantHistStep` is E-global (the hist-hearing GLOB raised by SetValue, never lowered; backs the 1,579 GetGlobalValue uses); `setDoorAccess` is E-item (the door locked to a key in its XLOC and the key given by AddItem, as Bethesda's bought houses are: the steward's house-purchase fragments hand the key; measured 2026-11-06 by the method of quest-block-precedent.md: of Skyrim.esm's 762 locked door refs, 398 name a key, and 36 quests' stage-fragment scripts (QF_) take a locked door or a key as a property, 22 a door and 18 a key, HousePurchase among them, while 25 dialogue fragments (TIF_) in 13 quests do, 43 quests in all; which stage of a quest runs it is in the compiled fragment and not counted). Skill uses named with Morrowind skills
in the vocabulary map to Skyrim actor values for C-skill (speechcraft and mercantile to Speech, security to
Lockpicking, sneak to Sneak or Pickpocket, marksman to Archery, the blades and spear to One-Handed or Two-Handed); swim,
dive and climb are movement (FreeClimb, water), never a check.

Generated from the records by `python3 -m tools.argonia_world.slice_ledger.stage_blocks` (2026-11-06, after review round 8); re-run it when a record changes (it writes this table from the story database, the one source). Trigger in is what enters the stage (its predecessors' successor and fail-forward conditions); an `npcAlive` failing is TR-death, and `objectiveComplete` is the stage's own objectives done. The world edits each quest stands on map to the world-edit blocks so: `npc_add` is W-npc with W-fixed, `ref_place` W-ref, `creature_remove`/`npc_remove` W-ref removal, `record_change` and `npc_change` W-override, `name_place` W-name, `navmesh_add` W-navmesh.

<!-- stage_blocks:begin (generated; do not edit) -->
| Quest stage | Trigger in | Conditions | Effects |
|---|---|---|---|
| MQ01 10 | the new-game start (ARG_Opening) | - | E-stage |
| MQ01 20 | TR-topic | - | E-package, E-stage |
| MQ01 30 | TR-zone | - | E-enable, E-stage |
| MQ01 40 | TR-topic, TR-zone | - | E-enable, E-scene, E-stage |
| MQ01 41 | TR-zone | C-stage | E-stage |
| MQ01 42 | TR-zone | C-stage | E-stage |
| MQ01 44 | TR-death, TR-zone | C-alive | E-stage |
| MQ01 50 | TR-zone | - | E-enable, E-stage |
| MQ01 90 | TR-topic | C-stage | E-enable, E-global, E-item, E-stage, TR-chain |
| MQ01 91 | TR-topic | C-stage | E-enable, E-global, E-stage, TR-chain |
| MQ01 93 | TR-death, TR-topic | C-alive, C-stage | E-enable, E-stage, TR-chain |
| MQ03 10 | TR-chain (the previous quest ends) | - | E-stage |
| MQ03 20 | TR-acquire, TR-death, TR-topic | C-alive, C-item | E-enable, E-global, E-move, E-stage |
| MQ03 40 | TR-death, TR-zone (objectives done) | C-alive, C-time | E-enable, E-move, E-stage |
| MQ03 90 | TR-topic, TR-zone | - | E-enable, E-faction, E-global, E-item, E-move, E-stage, TR-chain |
| MQ03 91 | TR-death, TR-zone | C-alive | E-enable, E-global, E-move, E-stage, TR-chain |
| MQ04 10 | TR-chain (the previous quest ends) | - | E-enable, E-stage |
| MQ04 20 | TR-death, TR-topic | C-alive | E-stage |
| MQ04 30 | TR-zone | - | E-stage |
| MQ04 40 | TR-death, TR-topic, TR-acquire | C-alive, C-item | E-stage |
| MQ04 91 | TR-acquire, TR-zone | C-item, C-stage | E-enable, E-faction, E-global, E-item, E-stage, TR-chain |
| MQ04 92 | TR-acquire, TR-zone | C-item, C-stage | E-enable, E-global, E-item, E-stage, TR-chain |
| MQ05 10 | TR-chain (the previous quest ends) | - | E-stage |
| MQ05 20 | TR-death, TR-topic | C-alive, C-item, C-skill | E-enable, E-stage |
| MQ05 40 | TR-zone | - | E-stage |
| MQ05 50 | TR-zone | - | E-stage |
| MQ05 91 | TR-death, TR-topic | C-alive | E-enable, E-global, E-regard, E-stage, TR-chain |
| MQ05 92 | TR-death, TR-topic | C-alive | E-enable, E-global, E-regard, E-stage, TR-chain |

- MQ01 stands on 13 ledgered world edits: `we.clean.hereguardplantation`, `we.clean.lilmoth`, `we.mq01.barge-crew`, `we.mq01.broker`, `we.mq01.camp`, `we.mq01.cell`, `we.mq01.families`, `we.mq01.gang`, `we.mq01.hold-location`, `we.mq01.no-valenwood`, `we.mq01.no-welcome`, `we.mq01.pier-mesh`, `we.mq01.start`.
- MQ03 stands on 12 ledgered world edits: `we.clean.hereguardplantation`, `we.clean.lilmoth`, `we.mq01.broker`, `we.mq01.camp`, `we.mq01.hold-location`, `we.mq03.door`, `we.mq03.dream`, `we.mq03.house`, `we.mq03.hurt`, `we.mq03.jar-marks`, `we.mq03.reed`, `we.mq03.rooms`.
- MQ04 stands on 7 ledgered world edits: `we.clean.village`, `we.mq04.cell`, `we.mq04.items`, `we.mq04.leeches`, `we.mq04.name`, `we.mq04.people`, `we.mq04.village`.
- MQ05 stands on 10 ledgered world edits: `we.clean.dock5`, `we.clean.helstrom`, `we.clean.lilmoth`, `we.clean.thorn1`, `we.mq05.grove`, `we.mq05.hall-name`, `we.mq05.people`, `we.mq05.ship-door`, `we.mq05.throne`, `we.mq05.way`.
<!-- stage_blocks:end -->

Every stage maps; no stage needs a block outside the set, and no block needs SKSE. The set is seven triggers, seven
conditions, nine effects and four world edits. The composite quest that proves the joints (Phase 3's first build)
needs one stage per trigger, each gated by one condition of each kind across the set and firing one effect of each
kind, plus the five guard cases above.

## The rest of the slice, mapped (phase 2, the first story slice)

The slice's other quests (adaptation §5) are written to the ledger, not yet as stage records; each is mapped here
from its premise and edits, and every mechanic falls inside the set above plus the two world-edit blocks added for
the slice (W-navmesh, W-name). No new trigger, condition or effect is needed.

| Quest | Triggers | Conditions | Effects | World edits |
|---|---|---|---|---|
| TG01 the keepsake | TR-topic (the desk, the trader), TR-zone (the thief's round), TR-acquire (the keepsake) | C-time (the round by day), C-skill (talk, pickpocket), C-alive (no harm) | E-stage, E-item, E-faction (the Chapter) | W-npc, W-ref (bedroll, drinking spot), W-override (two door pairs locked), W-name (Pusbottom) |
| TG02 the lockbox | TR-topic (the three clients), TR-acquire (the lockbox underwater) | C-item | E-stage, E-item, E-global (whose lie is kept) | W-npc, W-ref (sunk house) |
| BC01 the hearing | TR-topic (Never-Sold, the hearing), TR-activate (cut the boat loose) | C-item or gold (buy out), C-stage | E-stage, E-scene (the hearing), E-item, E-global (month taken on) | W-npc, W-ref (landing, book, toll post), W-name (the house) |
| BC02 the fire | TR-zone (into the smoke), TR-topic (whom first), TR-death (fail-forward) | C-alive, C-time (a timer as a scene: TR-scene) | E-stage, E-enable (smoke, burning, burnt), E-package (the heirs follow), E-item (the book) | W-npc, W-ref (cells, sealed door, stockade), W-override (door pair), W-navmesh, W-name |
| BC03 the refusal | TR-topic | C-stage | E-stage, E-regard (the side not taken) | W-npc, W-ref (barge, shelf) |
| LQ25 the river-beast | TR-topic, TR-death (the beast) | C-stage | E-enable (the beast's parent), E-stage, E-global (the award) | W-fixed (the beast), W-npc |
| LQ30 the walk-out | TR-zone (the shelter), TR-topic (the kin) | C-alive | E-stage, E-package (the youth walks home) | W-npc, W-ref (gate, trail, shelter) |
| The clean-ups (every place) | - | - | - | W-ref (each placement initially disabled), W-fixed (each templated actor kept) |

