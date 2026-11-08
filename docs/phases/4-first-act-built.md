# Phase 4: the first story slice, built from the proven blocks

Status: [PROGRESS.md](../PROGRESS.md). The plan: [PLAN.md](../PLAN.md). Edit this file as the phase goes; it is the phase's whole brief.
Rewritten 2026-11-08 after the owner's third walk (tmp/walk-3-feedback.md, [owner-rulings](../owner-rulings.md)). **Status 2026-11-08: built, read back and deployed; the owner's walk is owed (docs/owner-walk-checks.md sections 5 to 7).**

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

- **Clean-up built (2026-11-08).** `tools/ArgoniaPlugin/CleanUp.cs`, called after `Combat.Add` (overrides only, no new
  form ids): the eight slice clean-ups (lilmoth, hereguardplantation, dock2, dock5, helstrom, village, blackrose,
  blackmarshnorth.thorn1, whose three targets are in the coast ship's cell `0AA665`). Ten targets were built talkers and
  left the clean-up (rows deleted, the note on each `world_edit`): six at Lilmoth (Deep-In-His-Cups and five
  adventurers and thieves), three at Hereguard (the two New Order soldiers, Looks-At-Books) and the Dark Elf slave at
  Soulrest; none is Nord, Thalmor, Imperial official or undead. Built: 149 placements disabled, 12 templated placements'
  bases at a fixed level (the base's own, or 5 where it levelled with the player: talk.md's rule; no band-to-level
  table exists). Read-back `plugin.sh cleancheck`: all eight PASS (161 targets). `adaptation_check` counts a built
  talker as covered. Round trip clean, 558 YAML files.
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
- **Chainbreakers BC01, BC02, BC03 built (2026-11-08).** `tools/ArgoniaPlugin/Chainbreakers.cs` (after `LocalQuests.Add`;
  LocalQuests' kit), all in BM&V's BlackMarsh. The line's standing is the global `ARG_ChainbreakersStanding` (E-global):
  BC01 90/91, BC02 91/92/93 and BC03 90 each add 10. BC01 and BC02 were re-authored to the proven blocks (planner
  rulings), one quest-review pass each (BC01 4 blocking, BC02 4 blocking, all applied with the cheap minors), briefs,
  one dialogue-writer per speaker (8), one reader pass (44 line fixes, 10 record and 1 book fix). **BC01 Four Months
  for a Boat:** Start Game Enabled; Never-Sold (our base, placed once in BM&V's House 15635D) sets 10 by her estate
  topic; stage 10's fragment puts the debt book (a BOOK) in Hulm-Tei's Apprentice-locked, owned chest on the landing
  navmesh at 31,-12 (095465, Black Marsh North's 0ACD06; no shed); her alias's sandbox package takes her to the
  landing; the book in hand on her bring-down topic sets 90 (her page torn out, the first price left in the chest,
  Rows-For-Another moved by the house). Rows-For-Another's channel topic sets 40 only at night (C-time) and unseen by
  Hulm-Tei and both estate men (C-detected, review F1), else a day line; she then follows by package to an
  unconditioned zone where the channel leaves the estate (prereq 40, sets 91). TR-death on either woman to 94.
  **BC02 One Out of the Smoke** (retitled, review F12): after BC01 >= 90, Never-Sold's fire topic sets 20 (smoke and
  the three held enabled); the room is BM&V's walk-in keep 01cyKeep at 30,-15 (navmesh 0ACB8C; 01BlackRoseJail has
  none), Tsaxi at the 'Black Rose Jail' marker; his Speech 25 topic or the zone inside the keep sets 30; each 'come
  with me' sets 31/32/33, whose fragment disables the other two (each under its own enable parent; no kill); the
  chosen follows by package; three exit zones at Tsaxi (prereq 31/32/33) or his Speech 25 let-by topic (review F1)
  set 91/92/93; any held's death from 30, or Tsaxi's/Never-Sold's, to 94. QA4 and QA20 now place the post in the
  keep. BC03's opening topic is gated on BC01 >= 90. Papyrus: 58 of 58 .pex, 0 failed (13 new scripts). Read-back
  `plugin.sh bccheck`: 96 PASS, 0 FAIL (BC01, BC02, BC03); `localcheck` PASS; round trip clean (812 yaml files);
  `make check` green. Open: the low and high bands are not built (one band, as BC03); positions on the landing and in
  the keep are by navmesh height band, unwalked; the freed one's after-state greeting (review minor F5/F7) is not built.

- **Integrated and deployed (2026-11-08, d15555cb).** Every lane merged on main and the plugin re-seeded once: 2,167
  records, round trip clean (1,730 YAML files), the records listing 0 errors (it now knows MQ01's held quests). Read-backs
  on the one ESP and the 80 compiled scripts: clean-up all PASS, blocktest every step PASS, main quest 476/476, local
  quests PASS, Chainbreakers 96 PASS, MQ04/MQ05 all stages PASS, Night-Reed 231/231; `talk_check` 119 talkers in four
  worlds, 0 problems; `make check` green. Fixed at integration: MQ05's Nesh-Deeka topic built after MainQuest places her
  (MQ05.AddNesh); MQ05's two travel packages shared editor ids with their markers. Deployed to argonia-play (DEPLOY OK).
  Owner checks: docs/owner-walk-checks.md sections 5 to 7.
- **Quest rumours built (2026-11-08):** 11 settlement talkers rumour 5 quests that can start (LQ30, LQ25, TG01, BC01,
  BC03; BC02 and TG02 start from their line's earlier quest, so no rumour). Each rumour INFO (`Talk.Rumours`, at the
  seed's end) is gated to the talker's ref and copies every GetStage condition of the giver's opening line (BC03's
  BC01 >= 90 with it). `talk_check` reads each back: quest in the plugin, Start Game Enabled from its start-up stage,
  the opening line found, the gate matched, no talker one of the quest's own people: 5 rumours, 0 problems; every
  read-back PASS.
- **Wording bands and after-quest greetings (2026-11-08):** the Chainbreakers' written low and high bands are built as
  extra INFOs, warm on GetRelationshipRank with the player >= 1 and cool below 0, the default taking rank 0 (exclusive by
  condition, since Spriggit's YAML does not keep INFO order): BC01 6/6, BC02 11/11, BC03 9/9 warm/cool; no race form is
  written in any brief's lines. After-quest Hello topics (written, reader-checked): Rows-For-Another (BC01 90/91, 3),
  the one out of the smoke (BC02 91/92/93, 3 each), Sei-Wan at the gate (LQ30 91/92, 2 each). bccheck and localcheck
  read every band and greeting back (PASS).
- **Wording bands for the act's quests (2026-11-08):** warm and cool bands written per speaker (one dialogue-writer
  each, one reader pass applied: 41 rewrites) and built as BC's (warm on GetRelationshipRank with the player >= 1, cool
  < 0, the default the complement; each band INFO keeps its gates and fragment, so no Papyrus changed): warm/cool MQ03
  10/10, MQ04 7/7, MQ05 8/8, TG01 10/10, TG02 11/11, LQ25 4/4, LQ30 4/4. MQ01 is left on one band: it is the opening on
  the barge, where no one can yet hold a rank with the player. Pays-Late's rows spoke all three old bands with
  [low]/[words]/[high] markers in one INFO; the middle is now the words band with the directions, and the race macro
  left in two MQ05 bands is gone. mainquestcheck, mqcheck, nightreedcheck and localcheck read every band's condition
  and text back (498/498, all stages, 275/275, PASS); cleancheck, blocktest, bccheck PASS; talk_check 119/0 with 5
  rumours; `make check` green. Bands live in `story/data/quest_lines/mq03.json`, `lq25.json`, `lq30.json`
  (`lines@low`/`lines@high`), `dialogue_line` `variants_low`/`variants_high` (MQ04, MQ05) and
  `story/data/dialogue-writer/quest/tg/nightreed.lines.tsv` (`<key>@<band>.<n>`); the writers' files are `*.bands.tsv`.
- **Known gaps, for the owner walk or later:** positions at BC01's
  landing, BC02's keep and the Reed's house (BM&V's tilted sinking cabin) were picked from navmesh, never walked; some
  routes still have short or long legs (084A86 goes east before west; one Hereguard leg is 1,043 paces).
