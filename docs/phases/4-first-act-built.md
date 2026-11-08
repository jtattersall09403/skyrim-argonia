# Phase 4: the first story slice, built from the proven blocks

Status: [PROGRESS.md](../PROGRESS.md). The plan: [PLAN.md](../PLAN.md). Edit this file as the phase goes; it is the phase's whole brief.
Rewritten 2026-11-08 after the owner's third walk (tmp/walk-3-feedback.md, [owner-rulings](../owner-rulings.md)).

## Already done (do not redo)

- **The world map (block W-wrld-map)**: passed in the owner's walk 3 in Lilmoth, Thorn and Valenwood
  (`tools/ArgoniaPlugin/MapFix.cs`, `infra/gpu-box/lodsettings.py`).
- **Rooms without load doors**: the `bmv_shell` table (`tools/argonia_world/bmv_shell.py`), 1,889 building refs in 86
  settlements, classed A 86, B 114, C 166, D 595, X 928 by the navmesh inside each footprint
  ([census.md](../research/bmv/census.md#shells-rooms-without-load-doors)). The owner dropped the shell walk check;
  a quest or home cites a shell by its `bmv_shell.id` and reads its navmesh, never "a house".
- **Every block the slice uses is proved** (Phase 3, owner walks 2026-11-07 and 2026-11-08: steps 1 to 13 and checks
  A to D), and the talk block W-talk on Lilmoth's 30. Still owed in Phase 3: only the journal entry of
  `ARG_BlockTestEnd` (below).

## A. The walk-3 fixes (first; each lands with one owner check in docs/owner-walk-checks.md)

| Fix | Where it is recorded |
|---|---|
| Standing backstep: the clip itself cut at the end of its first push (not keys held while the clip plays whole) | Phase 1 |
| TrueHUD: the Player Widget's "Combined" preset as the base, the owner's tweaks on top | Phase 1 |
| Backstab like Dark Souls: behind a person, locked on or not, a normal attack plays Rim Parry's backstab and execution | Phase 1 |
| Skyrim's normal game music on in BM&V's worlds (Argonia music later) | Phase 1 |
| "Block Test, the end" listed among completed quests in the journal | Phase 3 |
| Talk recipe v2 (route directions, address by standing, facts true of BM&V, the naming rules) as the skill `talk-write`; Lilmoth's 30 redone with it | 4a and part B here |

## B. Names, topics and dialogue for everyone in the act's places

Owner, 2026-11-08: every person in every place the opening act and the slice visit is named, has their own
topics and talks, not only quest people. Recipe: the skill `.claude/skills/talk-write` (part A), then
[Phase 4a's loop](4a-talk-to-everyone.md) per settlement.

| Place (census settlement) | Visited by | Talkable (silent + service) | On the clean-up list | To write |
|---|---|---|---|---|
| Lilmoth, Hereguard Plantation, the Docks (Soulrest) | MQ01, MQ03, MQ05, TG01, TG02, BC03 | 30 | 9 | redo all 30 with recipe v2 |
| The village east of Lilmoth (`bmv.village`) | MQ04 | 6 | 0 | 6 |
| Helstrom's river landing (`bmv.dock5`) | MQ05, LQ25 | 8 | 3 | 5 |
| Helstrom (`bmv.helstrom`) | MQ05, LQ30 | 11 | 4 | 7 |
| The ship stop in Black Marsh North (`bmv.blackmarshnorth.thorn1`) | MQ05 | 33 | 0 | 33 |
| Blackrose (`bmv.blackrose`) | BC01, BC02 | 66 | 28 | 38 |
| Quest people we add (the broker, overseer, gang, the Veiled Reed, the Chapter, ...) | the quests | - | - | quest dialogue, part C |

**The clean-up and the talkers.** Nine of Lilmoth's 30 talkers (Looks-At-Books, two "New Order" soldiers now in the
Lilmoth council's pay, Deep-In-His-Cups and five more) are also `we.clean.*` targets from Phase 2. The talkers win:
the owner has walked them, and a talker's own base already fixes its level and name, which is what the clean-up was
for. Rule: a talker with a built `talker` row leaves the clean-up (its `world_edit_target` row is deleted with a
note); a clean-up target that is Nord, Thalmor, vanilla Imperial official or undead stays disabled and gets no
talker row. Clean-up targets are left out of the counts above.

## C. Build the slice

The opening act (MQ01 with the new-game flow and the opening scene, our Helgen, replacing Phase 1's lightest
opening; MQ03, MQ04, MQ05) and the chosen lines (BC01 to BC03 Chainbreakers, TG01 and TG02 Night-Reed, locals LQ25
and LQ30): 11 quests, records in the story data (`quest.main.mq01` ...), the clean-up and world edits in
`world_edit` and `world_edit_target`. Built from Phase 3's blocks only: every stage, trigger, condition and effect
is a copy of a proven block's shape (`docs/design/blocks.md`; the stage tables from
`python3 -m tools.argonia_world.slice_ledger.stage_blocks`); anything not a block goes back to Phase 2's method or
the quest is re-authored.

- **Code layout:** one C# file per quest (or per line) in `tools/ArgoniaPlugin/`, called from `Generate.cs` after
  the existing allocations so earlier form ids never move; Papyrus fragments in `papyrus/`, compiled on the play
  machine. `ARG_BlockTest` stays until the slice is built, then is removed with its forms.
- **Quest dialogue** for every speaker in the records, through `dialogue-write` and `text-review`, from the records.
- **Quest rumours:** each settlement's talkers gain a rumours topic for a quest that can start there (talk.md).

## D. The loop, then the owner

- **Loop**: read the files the game will consume (the ESP, the .pex, the staged ini files) and verify that
  everything intended is there and correct (`plugin.sh check`, `talk_check`, a per-quest read-back: every stage's
  journal, objective, fragment, alias and condition as the record says). If not, diagnose, fix and repeat. Never run
  the game; then pass to the owner.
- **Owner test:** play the slice from a new game: the new-game flow, the opening scene, the opening act and the
  chosen faction lines; talk to people in each place.

## Measured

(filled as the phase goes)

- **Clean-up built (2026-11-08).** `tools/ArgoniaPlugin/CleanUp.cs`, called after `Combat.Add` (overrides only, no new
  form ids): the eight slice clean-ups (lilmoth, hereguardplantation, dock2, dock5, helstrom, village, blackrose,
  blackmarshnorth.thorn1, whose three targets are in the coast ship's cell `0AA665`). Ten targets were built talkers and
  left the clean-up (rows deleted, the note on each `world_edit`): six at Lilmoth (Deep-In-His-Cups and five
  adventurers and thieves), three at Hereguard (the two New Order soldiers, Looks-At-Books) and the Dark Elf slave at
  Soulrest; none is Nord, Thalmor, Imperial official or undead. Built: 149 placements disabled, 12 templated placements'
  bases at a fixed level (the base's own, or 5 where it levelled with the player: talk.md's rule; no band-to-level
  table exists). Read-back `plugin.sh cleancheck`: all eight PASS (161 targets). `adaptation_check` counts a built
  talker as covered. Round trip clean, 558 YAML files.
- **MQ01 and MQ03 not built: block gaps.** (1) A trigger zone gated by a condition is not a proven block: MQ01 41 to 90
  and 42 to 91 (shore zone with `npcAtMark` and not `detectedBy`), MQ03 into 40 (house zone at night; and with
  `npcAlive` failing). (2) W-navmesh is unproven (Phase 3, risk 1) and MQ01 stands on `we.mq01.pier-mesh`. These stages
  go back to `quest-write` to be re-authored in proven shapes before the build.
- **BC03 re-authored, not built (2026-11-08, hand-off).** Round-1 rulings applied to the record (`quest.bc.bc03`): the
  tokens a Quest Object alias from stage 0 and "unseen" cut (F1); the yield split into `topic.bc03-yield-talk`
  (Speechcraft 30, ends at 91) and `topic.bc03-yield-pay` (50 gold, new end stage 92) (F2); the side topics granted by
  `topic.bc03-the-season` (F4); the token-breaking is Ussa-Rekh's own promise (F5); Ussa-Rekh and Heavy-Rope essential by
  the alias flag. `brief.py` refuses a record with no fail-forward, so stage 94 and its death triggers stay wired
  (unreachable while essential). F3 skipped. Briefs were rebuilt and both speakers' lines rewritten (Heavy-Rope 21, Ussa-Rekh 3;
  lint 0). Fact requests: the tokens and the promise in Ussa-Rekh's season line are cut (gap QA21, not lore); the Owing
  wording is kept, from labour-and-bondage.md §2. Navmesh: Dock2 (`02F35A`) is navmeshed by Black Marsh North.esp (`0A7784`, 225 triangles at dock height, x 47488..49152), not by Black Marsh.esm. An earlier note here said it had none: that was a misread of a truncated listing. The place stands. Still to do: the text-review pass, Chainbreakers.cs, the TIF/QF Papyrus, the read-back, then BC01 and BC02.
- **MQ01 and MQ03 re-authored to the blocks (2026-11-08, planner rulings).** Every zone is gated by its prerequisite
  stage only. MQ01: three shore boxes (90 from 41, 91 from 42, 93 from 40 under a parent that 41 and 42 turn off, as
  they turn off the other choice's zone); the saved one follows by alias package and is moved to the mark by the
  ending; Deesh-Duun's hut has a Novice-locked hatch (Lockpicking); `we.mq01.pier-mesh` dropped (no navmesh is
  added), the march starts from copies on Dock1 (`we.mq01.march`) swapped in by enable parents at 10 and 40. MQ03:
  stage 30 and its zone cut; the attack and the night set globals read by the oath answers; the answer, or
  Nesh-Deeka's death, sets 40 (the dream); the dream's end sets 90 or 91 on `flag.mq03.reed-sworn`; no night gate.
  One quest-review pass: 5 blocking, 3 major, 1 minor, all fixed (R6-1, R6-2 in each review). `brief.py` fixed to
  read Skyrim skill names, to exempt scene stages, and to accept things with no states. Briefs:
  `story/data/dialogue-writer/quest/mq01/` (11) and `mq03/` (6).
- LQ30 and LQ25 records re-authored to proven blocks (2026-11-08; each record's review finding B1): both Start Game
  Enabled with an opening topic; LQ30's gate zone unconditioned (prereq 40), detection and the reed trail cut, youth
  among the roots of 0D7883, a death fail-forward 93; LQ25's lair moved to the shallows under the crew's plank walk in
  0D77AF (0D7723 is a hillside), own bases for the crocodile and crew, a captain-death fail-forward 93.
- LQ30 and LQ25 built (`tools/ArgoniaPlugin/LocalQuests.cs`, after Combat; BlackMarsh2 0D6960 overridden there),
  dialogue from `story/data/quest_lines/` (dialogue-write, text-review: 10 rewrites applied, lint 0), Papyrus 7 new
  scripts compiled on the GPU box (16 of 16 .pex, 0 failed). Read-back `plugin.sh localcheck`: every stage, journal,
  objective, fragment and .pex, alias, topic gate and trigger PASS for both; round trip clean (497 yaml files). Open:
  LQ25's MQ05 >= 40 gate is added when ARG_MQ05 is in the plugin (the check prints a NOTE until then); the record's
  ledger rows we.lq30.trail, we.lq25.beast and we.lq25.crew still carry the pre-B1 wording (quest review, 2026-11-08).
- **TG01 and TG02 built** (2026-11-08, `tools/ArgoniaPlugin/NightReed.cs`, read-back `nightreedcheck`): 227 of 227
  checks pass on the seed's ESP through Spriggit YAML and back, with the 30 .pex compiled (30 of 30). 2 quests,
  21 lines in 14 topics, 11 people (plus 2 eels), 4 door locks and the trapdoor at Novice. Re-authored to proven
  blocks: TG01 starts Start Game Enabled with an empty stage 0 and Tilts-The-Jug's line gated on stage 0; 20 to 30's
  zone + night + unseen became an unconditioned zone at his bed (prereq 20) and the friend's line; TG02's "all three
  claims" and "all three sold" are hidden stages 21-23 and 43-45 with a guarded check; any client's death is the
  failed end 92 (three death aliases on one stage), replacing the 20-to-40 fail-forward. Measured: Pusbottom has no
  water deeper than 24 units, so the lockbox, the fallen house and the eels are in the deep water just north of Pusbottom
  (cell 5,0, floor about -700) by the Chapter's trapdoor, clients on its south bank (navmesh 07EDF2); Soulrest's
  docks have no navmesh at plank height, so the thief's round is on Soulrest's own navmesh 0A7785. Records: the
  re-authors are review findings B1-B4 in both, stage and journal text matches the build, and one quest-reviewer round
  ran (its 4 blocking findings applied as text and fact changes only; its notes 5-13 left open). Lines: one
  dialogue-writer per speaker (8) from brief.py's briefs, one reader pass (11 rewrites applied), lint clean;
  NightReed.cs builds all 21 from `story/data/dialogue-writer/quest/tg/nightreed.lines.tsv` (2026-11-08). The figurine is
  now vanilla HorkerTusk's ivory (03AD68), not the Companions totem CRTotem2 (decision 0006). Read-back 231 of 231 (the eel base read back as "Ripper Eel", ours; a
  new check: the figurine's model is not a totem), 37 of 37 .pex. Owed: the owner's in-game check.

- **BC03 built (2026-11-08).** `tools/ArgoniaPlugin/Chainbreakers.cs`, called after `LocalQuests.Add` (it reuses
  LocalQuests' kit, now internal, with `TopicV` for an info's variant lines). Ussa-Rekh, Heavy-Rope and his chest
  (vanilla StrongBox, Novice lock, owned by him) are snapped to Dock2's navmesh (Black Marsh North's `0A7784`), and both men are
  essential by alias flag. The tokens are a Quest Object alias created in the chest (F1). Hearing the season sets
  `ARG_BC03_SeasonHeard`, which gates the two side topics (F4). Yield-talk needs Speechcraft 30 (pass or fail line) and
  ends at 91; yield-pay needs 50 gold and ends at 92. A TR-death on each man sets 94. Lines: `story/data/quest_lines/bc03.json` (the words band
  of the TSVs). Papyrus: 8 new scripts (24 of 24 .pex, 0 failed). Read-back `plugin.sh bccheck`: 30 PASS, 0 FAIL;
  `localcheck` still PASS; round trip clean (679 yaml files). Open: the BC01 >= 90 gate is added when ARG_BC01 is
  built (the check prints a NOTE); the record's `changeStanding` (Chainbreakers +10) and `setFlag` effects have no
  global yet and are not built; the low and high bands are not built (one band, as LQ25 and LQ30).
- **MQ04 and MQ05 built (2026-11-08).** `tools/ArgoniaPlugin/MQ04.cs`, `MQ05.cs` on `QuestKit.cs` (the block test's
  shapes as helpers), fragments `papyrus/ARG_QF_MQ04.psc`, `ARG_QF_MQ05.psc` and seven TIFs (18 of 18 scripts compile).
  MQ04 has the quest-review's F1 to F8 applied: Pays-Late is essential and carries the gum pot (pickpocketed; his topic
  at 30 needs it, and sets 40), the way back has three leeches enabled at 45 and its own box (prereq 45 sets 91), the
  far-side objective and zones are cut, the camp is enabled at 40, the food is Salt Pile (034CDF; two on Lilmoth's fish
  barrel 02A1F6, at its bounds top). MQ05: the c2 conclusion gains a third clue (the grove's Hist whole); the ship's
  inner door pair (new block, owed an owner check); the evening quarrel and MQ04's set dressing are cut (review rows).
  Dialogue: 7 speakers, 51 `dialogue_line` rows, lint clean, one reader pass (11 of 14 hits applied). Read-back
  `plugin.sh mqcheck` (`MQCheck.cs`): 10 of 11 stages PASS; MQ05 20 FAILS, waiting on `ARG_NeshDeekaRef` from the
  MQ01/MQ03 lane (her topic is left out until that ref exists). MQ04 10 is set by MQ03 (that lane).
- **MQ01 and MQ03 built (2026-11-08, `tools/ArgoniaPlugin/MainQuest.cs`, read-back `plugin.sh mainquestcheck`):**
  476 of 476 checks pass from the seed's ESP (through Spriggit YAML and back) and the .pex (67 of 67 compiled on the GPU
  box, 13 new: `ARG_QF_MQ01`, `ARG_QF_MQ03`, 11 TIF). MQ101's override starts `ARG_MQ01` at a marker in the barge hold
  (0F9178, its 'Dainty Sload' location cleared); `ARG_MQ01` runs character creation, then 10; `ARG_Opening` keeps its forms,
  has no script and nothing starts it. 23 people (march copies on Dock1's navmesh 079823, the camp on 07990E at the
  paddy edge, -3750,1300; deep water west of -4400), 18 lines in 13 topics from `story/data/quest_lines/mq01.json` and
  `mq03.json` (the seven `*.lines.txt` normalised into these two, words band, no listener variants; reader pass: 9
  rewrites applied, 7 declined as against the record's facts). MQ03's endings start `ARG_MQ04` at 10 (looked up by editor id at the
  seed's end; checked); BM&V's 01Captain and Valenwood's two start quests are held back and started by MQ03's endings.
  **Re-authored to blocks:** the three scenes have no written lines, so the march ends at a fire zone (10 to 40, the march
  packages read the answer's global), the strike is stage 40's fragment (the courier killed, the two moved), and the dream
  ends at a zone at the hold door (40 to a hidden 45, which sets 90 or 91 on the sworn global); the taste is a hidden
  stage 11 (the sap's alias, on activate). **Cut:** disposition bands and race vocatives in the lines; the families' night
  schedules, the hut hatch (no door-into-water block: Deesh-Duun's huts are a water zone), grave-stakes, the cutting's
  light, the fog, the house doors' base swap and the screen; Nesh-Deeka named by the stranger (fact questions 2 and 4).
  **Fact questions answered:** Ties needs the tag or Speech 25 (the record's stage-20 action); the player knows
  Wuleen-Sei from MQ01; Salts-The-Catch keeps the house (t3, QA8); the boat goes when the player says so; no figure for
  the food months (labour-and-bondage §2 gives none); Ux-Xeek never reads the blank line. The house (0FE7F7) has no
  navmesh where its rooms are; its people stand 10 units over the tilted floor. Open: MQ05 looks `ARG_NeshDeekaRef` up before MainQuest allocates it, so its stage-10 topic is still left out; its lookup
  should move to a hook after `MainQuest.Add` (the MQ05 lane). Owed: the owner's walk from a new game.
