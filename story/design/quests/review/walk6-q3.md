# Walk 6, lane Q3: the Night-Reed Chapter's TG01 and TG02 at the ceiling

These are the two built quests of the Night-Reed Chapter's line. Each is re-authored as a quest record at the
Morrowind-level ceiling ([walk-6-quests](../../../../docs/phases/walk-6-quests.md), "The ceiling"). Each compiles to a
quest form that passes `python3 -m tools.questform check`, and each is off `story/data/questform_owed.json`. The
records live in the rows; export them with `quest_record export quest.tg.tg01` or `quest.tg.tg02`.

This file holds:
- the story calls, with their lore sources;
- what was cut, and what replaced it;
- the world edits that remain;
- the review round;
- the dialogue lines the change made stale.

## TG01 A Dry Hand in a Wet City

**Steps.**
- Stage 0 is hidden and runs from a new game. S'Tabi's line sends the player to Tilts-The-Jug (stage 10), or her own
  line gives the test at once.
- 10: speak to Tilts-The-Jug inside the house on Soulrest's dock, behind the door beside S'Tabi.
- 20: get the Blue Jasper Necklace. She gives three lockpicks with the test. The player takes the necklace out of
  Keeps-What-Floats's strongbox (a take), or gets his key from him instead: Speech 35 on one prompt (stage 21), or
  60 gold on another (stage 22). With the key, the player takes the necklace from the box.
- 30: bring the necklace to Tilts-The-Jug. The hand-in is gated on holding it. If he lives, stage 50 and a hundred
  gold; if he is dead, stage 51 and no pay.
- 50/51: take the coast ship to Lilmoth, go down the trapdoor north of Pusbottom and speak to Bent-Spine.
- 90: the player is taken in as a Lookout. This starts TG02, and Tilts-The-Jug greets the player afterwards.
- Failed endings: 97 (Tilts-The-Jug dead) and 98 (Bent-Spine dead). Each shows the faction line's message.

**Cut, and what it became.**
- **His round and the walk-in area.** The thief had a round of three schedule packages (the dock by day, a bench in
  the evening, a bedroll at night), and a walk-in area at his bed moved stage 20. Now he stands on the dock west of
  the house door all quest, with Sits-By-The-Water beside him. The necklace is in his own strongbox under the eaves
  north-west of the house, and he keeps its key on him. Following him (Sneak) has no substitute, because the ceiling
  has no way to move a stage by watching.
- **The lift off his body (Pickpocket).** The form cannot hold a thing carried by a person, so the quiet-hand route
  is the strongbox: Lockpicking, as a theft. Speech 35 and 60 gold now buy his key, on two prompts, so paying is
  always the player's choice.
- **Sits-By-The-Water's gate.** Her answer about where he sleeps was behind Speech 25 or 10 gold. Now Tilts-The-Jug
  names the strongbox, and Sits-By-The-Water's free line gives the levers: he runs from a fight, and he would let it
  go to a good talker or for sixty gold.
- **The locks.** The Novice lock on the trapdoor is cut: it was the only way down, and the form carries no lock
  level. The three lockpicks move from the pay to the test, where TG01's own lock is met. The two door pairs of the
  house that were locked with no key are cut too.
- **The enable parent and the lookouts.** The parent used to switch people on at stage 20; the people now stand from
  the start. The two lookouts are cut. Only the strongbox is switched on, by Tilts-The-Jug's line, while the player
  is inside the house.
- **The endings.** The two completed endings (clean and harmed) became one. The pay and her regard are settled at the
  hand-in (stages 50 and 51), so the one ending is true either way.

**World edits left.**
- Five people placed standing: S'Tabi, Tilts-The-Jug, Keeps-What-Floats, Sits-By-The-Water and Bent-Spine. Each is
  placed near a named door on its cell's navmesh.
- One strongbox on the boards (base 09424C:Skyrim.esm, the old build's), with the necklace in it, lock Novice, opened
  by his key.
- The ledger matches: `we.tg01.thief` is rewritten; `.round`, `.doors` and `.trapdoor` are deleted; `.chapter`,
  `.dock` and `.trader` are rewritten as standing people.

## TG02 The Drowned Lockbox

**Steps.**
- 10: TG01's ending starts the quest. Ask Bent-Spine about the work.
- 20: dive to the drowned merchant's lockbox in the deep water north of Pusbottom, pick its Novice lock and take what
  is inside. Taking any of the three pledges moves the quest on. Bent-Spine gives three lockpicks, and three more
  once, on a line (stage 21).
- 30: settle the pledges on the bank. One way is to give all three to one client, on a hand-in gated on holding all
  three. Each client has their own ending (90, 91 or 92): 120 gold, that client warms, and the other two cool. The
  other way is to sell Neeta-Haj the figurine she claims, at its fair price (Speech 30; stage 41).
- 41: sell Okan-Tei the charm. With Speech 30 he pays its full worth (stage 42); without it he haggles the price down
  (stage 43).
- 42/43: sell Dar-Zeel the beads, again at full price (stage 95) or haggled down (stage 96).
- Bent-Spine greets the player after either kind of ending.
- Failed endings: 97 (Bent-Spine dead) and 98 (any client dead). Each shows the faction line's message.

**Cut, and what it became.**
- **The fallen stilt house.** It was a structure: BM&V's house static laid on its side on the floor. Now the merchant
  drowned crossing the deep water with his lockbox, and only the lockbox lies on the floor.
- **The ripper eels.** These were two slaughterfish placed in the water. The form names only what a stage, line or
  objective needs, and no eel moved or gated anything. Bent-Spine no longer speaks of eels, and sneaking past them
  has no substitute.
- **The joint hidden stages.** "All three claims heard" (stages 21 to 23) and "all three sold" (43 to 45) are cut:
  - each client's claim is their own line, open from the job on;
  - the hand-over is one line per client, gated on holding all three;
  - the sales run one client after another, each its own step.
- **Okan-Tei's gate on his claim.** It was Speech 30 or 20 gold, and it set a flag. The claims are now free.
- **The sale prices.** Each sale is now at the pledge's fair price, its item value: 40, 90 and 55 gold. A sale is not
  a price for silence (the Chapter's taboo on blackmail). Speech 30 is needed only for the first sale, where the
  hand-over is still open. On the second and third sales, Speech 30 gets the full price, and without it the client
  haggles the price down, so no failing check stands on the only way forward.
- **The enable parent.** Bent-Spine's job line now switches on the lockbox and the three clients, while the player is
  below in the Chapter (on the other side of the interior line).

**World edits left.**
- Four people placed standing: Bent-Spine in the Chapter's inner room, and Neeta-Haj, Okan-Tei and Dar-Zeel on the
  south bank, near the trapdoor 16BF7F.
- One lockbox on the floor of the deep water (base 09424C:Skyrim.esm), with the three pledges in it, lock Novice.
- The ledger matches: `we.tg02.house` and `.eels` are deleted, and `.clients` is moved to cell 0059FB.

## Story calls and their lore

| Call | Source |
|---|---|
| The Night-Reed Chapter is native and meets under Lilmoth by Pusbottom; its way down is BM&V's trapdoor north of Pusbottom | story/lore/topics/guilds-and-orders.md §3 (native; Pusbottom the criminal underground); story/lore/lilmoth.md (Pusbottom); BM&V trapdoor 16BF7F, dungeon 16BF81 |
| Tilts-The-Jug keeps the Chapter's desk at Soulrest, inside the house; Bent-Spine is its fence under Lilmoth | story/design/quests/36-cast-roster.md §56; 40-factions.md §32 (Desks); npc rows |
| A Khajiit trader on Soulrest's dock sends people to the desk | story/design/province-vibe.md §8 (Khajiit at Soulrest); npc row S'Tabi |
| The test is restraint: a Chapter Lookout's necklace comes back with no harm to the thief, or there is no pay | culture.faction.night-reed-chapter (value Skill and restraint; norm Take from those who can bear it) |
| A dock thief who keeps his takings in a strongbox, and his drinking friend | story/lore/soulrest.md (a port of crews and dockside trade); backstories marked invented |
| The keepsake is a necklace of polished blue jaspers | story/lore/topics/material-culture.md (jewellery; polished blue jaspers) |
| The coast ship runs from Soulrest to Lilmoth | story/lore/extrapolation/settlement-register.md §2 Soulrest; BM&V doors 039827/0AA6C9, 0AA837/0AA664 |
| Pay is in coin, and nothing written proves anything | story/design/province-vibe.md §5 (coin at the ports and cities), §9 |
| A merchant who took pledges drowned in the deep water north of Pusbottom with his lockbox | story/lore/lilmoth.md (a merchant city of stilts and canals); the drowning is an event inside the quest |
| The pledges are a worn bone figurine, a Neesak charm newly set in silver, and Kothringi glass beads from the cairns | story/lore/topics/material-culture.md (bone-workers, carved figurines, Neesak of Scrying, silver and glass); item row Kothringi Glass Beads |
| Selling each client their pledge at its fair price is a sale, not a price for silence | culture.faction.night-reed-chapter (taboo Blackmail as a trade) |
| The clients' claims are lies inside the quest | slice-premises.md, the planner's ruling after round 1 (characters' claims need no lore source) |

## The review round (quest-reviewer, 2026-11-12, one round per quest)

### TG01: two blocking findings, both fixed

- **B1, the world-edit ledger.** It still held the round, the necklace carried on the thief, the locked trapdoor,
  the house's locked doors and the stage-20 parent. Fix: `.thief` is rewritten; `.round`, `.doors` and `.trapdoor`
  are deleted, with their links; `.chapter`, `.dock` and `.trader` now describe people standing from the start.
- **B2, stage 20 could not be tried by a new character.** The lock was the only way open, with no picks, no gold and
  no Speech 35. Fix: Tilts-The-Jug gives three lockpicks with the test, and the lock is Novice.

The high and medium findings, all fixed:
- The talk and coin routes gave a second necklace while the first stayed in the box. They now give his key (stages
  21 and 22), and the take moves the quest on.
- One prompt could spend sixty gold without the player choosing to. There are now two prompts.
- "Its one open door" was wrong; the text now says "the door beside S'Tabi".
- The ship's door was ambiguous. The ship door 039827 is now an objective target, and the directions say "the door at
  the far end of the hold".
- The thief robbed a sleeping Chapter Lookout, so "no harm" now has a stake.
- Tilts-The-Jug has a greeting after the ending.
- Stages 97 and 98 no longer change anyone's regard; they set a flag.

Left for the planner:
- A new player finds S'Tabi only by asking about work. The faction is found by exploring.
- `we.name.soulrest` and `we.tg01.pusbottom` rename BM&V places. Renaming is not on the ceiling's list of world
  edits, but the journal uses those names.
- TG01 and TG02 both centre on opening a box.

### TG02: four blocking findings, all fixed

- **B1, the lock was the only way to the pledges.** Fix: the lock is Novice, Bent-Spine gives three picks, and he
  gives three more once (stage 21).
- **B2, the ledger.** It still held the fallen house and the eels. Fix: both rows are deleted, and `.clients` is moved
  to cell 0059FB.
- **B3, hollow stages.** Stages 41 and 42 asked no skill. Fix: on each, Speech 30 gets the full price, and without it
  the client haggles the price down (stages 42/43, 95/96), so both ways move the quest on.
- **B4, the fail-forwards did not match the form.** Fix: stages 20 to 43 carry the same deaths (Bent-Spine, any
  client), and stage 10 carries Bent-Spine's only.

The high and medium findings, all fixed:
- There was no reaction to the outcome. The hand-over now has one ending per client: the one who got the pledges
  warms and the other two cool. Bent-Spine has a greeting after each kind of ending.
- The sale prompts assumed the player had heard the claims. Each prompt now states the claim itself.
- The sales read as blackmail. Each is now a sale at the item's own value, and Dar-Zeel's fear of exposure is gone.
- The prices were wrong. The sales are now 40, 90 and 55, or a haggled 45 and 30, and the hand-over pays 120.
- The centrepiece was STEALTH; it is now DIVE.
- Journal 30 now explains the Neesak charm ("a green scrying crystal").

Left for the build:
- The lockbox base must be placed as an emptied copy that does not respawn.
- The figurine needs a bone mesh, not the silver-amulet mesh.

## The paper playtest (designed forms, careful player, Sonnet)

The runs are in `story/playtests/quest.tg.tg01/` and `quest.tg.tg02/`. Our people's names had to go in a names file,
because without it the game showed their template's name ("Argonian Boat Captain", "Flaa Heet"). The first TG01 run
had no names file and is kept.

**TG01.** The quest completed in 18 commands with no stalls; the stages ran 0, 10, 20, 30, 50, 90.
- The player found the flow and the markers clear.
- The player said the strongbox was unlocked, so the lockpicks and the key routes were pointless, and the "no harm"
  rule had no weight. This is the form's missing lock level, not the record's.
- The rest of the confusion was the unwritten lines (the gists). The player asked for more on why the Chapter sets a
  test, which is for the dialogue lane.
- The game listed the necklace "in Strongbox" at the new game, before the strongbox is switched on. That is the paper
  game showing a switched-off container's contents.

**TG02.** The run stopped on a harness error at stage 30: `speechcraft is not a skill`.
- The records use `speechcraft` throughout, and so do eight other quests. The paper game's sheet says `Speech`.
- This is a mismatch between the record vocabulary and the paper game, which lanes A and H must settle. It is not
  worked round here.
- Up to that stop, the player understood the brief, the dive and the choice. Again the lockbox read as unlocked.

No record change came from the playtest: every finding is the form's missing lock level, a harness fault, or unwritten
dialogue.

## Dialogue lines now untrue or without a stage (for the dialogue lane)

The written lines are in `story/data/dialogue-writer/quest/tg/nightreed.lines.tsv`, by key. A key's `@high` and
`@low` band lines go with it. 110 keys are stale in all.

**TG01: 57 keys. Every TG01 key except the 7 of `ARG_TG01_TopicDoor_0*`, which are still true.**
- `ARG_TG01_TopicTest_0*` (7): tells the player to follow his round.
- `ARG_TG01_TopicBed_0*`, `_1*` and `_fallback` (13): the topic `topic.tg01-his-bed` is cut. It is replaced by
  `topic.tg01-his-habits`, which is not yet written.
- `ARG_TG01_TopicGiveBack_0*`, `_1*` and `_fallback` (13): he now hands over his key, not the necklace, and the coin
  route is its own prompt (`topic.tg01-buy-it`).
- `ARG_TG01_TopicReturn_0*` and `_1*` (15): these name lockpicks in the pay and a locked trapdoor.
- `ARG_TG01_TopicWelcome_0*` and `_1*` (12): "you opened the trapdoor with your own hand"; the trapdoor is no longer
  locked.

**TG02: 53 keys. Every TG02 key except the 10 of `ARG_TG02_TopicClaimFigurine_0*` and `ARG_TG02_TopicClaimBeads_0*`,
which are still true.**
- `ARG_TG02_TopicJob_0*` (9): these speak of the fallen stilt house and the eels.
- `ARG_TG02_TopicClaimCharm_*` (11): the gate on his claim is cut.
- `ARG_TG02_TopicHandOver{Neeta,Okan,Dar}_0*`: these say eighty gold; the hand-over now pays 120.
- `ARG_TG02_TopicSell{Figurine,Charm,Beads}_0*` and their fallbacks: these say fifty gold and name the Speech check;
  each is now a fair-price sale, and the later two sales can be haggled.

**Lines still to write:**
- TG01: `topic.tg01-his-habits`, `topic.tg01-buy-it` and `topic.tg01-after`.
- TG02: `topic.tg02-more-picks`, `topic.tg02-after-hand` and `topic.tg02-after-sell`, plus the refusals for a player
  who is not holding the thing.

## Limits of the form met here

- The form holds no lock level, no key and no owner for a container. The Novice locks, the strongbox's key and the
  thief's ownership (which makes the take a theft the crime engine sees) are written only in the records' `things`
  and the ledger, and the generic builder needs them.
- The form holds no thing carried by a person, so nothing can be a pickpocket target.
- The compiler used to take one target per objective. It now reads the record's comma-separated `target` as several
  targets; eight records already wrote targets that way. A stage whose routes run through different references needs
  several targets to pass `asked-is-target` and `completes-on-target`.
- `adaptation_check`'s `helgen` rule still asks for essential or protected people. The records state, person by
  person, that nobody is either (the ceiling), and that wording satisfies the rule's text test.

## Dialogue (lane D2c, 2026-11-13)

The lines are in `story/data/quest_lines/tg01.json` and `tg02.json` (topic, speaker, `infos` by variant: `main` when
the conditions hold, `fail` or `nothing` for a refusal, `dead` or `haggle` for a second outcome). One
`dialogue-writer` per speaker from the generated briefs, each with its Morrowind find step, then one `text-review`
pass over all four quests' lines by place, journals and objectives included. S'Tabi's door line was still true and
is kept word for word. Every one of the 110 stale keys of `nightreed.lines.tsv` is replaced by these files; the TSV
files under `story/data/dialogue-writer/quest/tg/` and the old briefs in `tg01/`, `tg02/` stay only because
`tools/ArgoniaPlugin/NightReed.cs` (the old builder) still reads them, and go with it.

Record changes made with the dialogue:
- TG02: the hand-over and the sale were one topic id shared by three clients, and the compiler takes one speaker's
  words per topic id. Each client now has their own (`topic.tg02-hand-over-neeta`, `-okan`, `-dar`;
  `topic.tg02-sell-figurine`, `-charm`, `-beads`).
- TG02: Neeta-Haj's sale was the only fair route and stood on a failing Speech 30 check; both first players had 15
  and were pushed into the hand-over. She now haggles like the other two (new stage 40, twenty gold), and the
  objective says Speech 30 is for the full price.
- TG01: Keeps-What-Floats has a greeting once his strongbox is empty (stages 30 to 51), so the "no harm" rule has a
  face.

Paper runs after dialogue: five chained TG01 then TG02 runs (careful and wanderer, then a confirming careful), all
completing both quests with no harness errors. Players could say who the Chapter is (take from those who can bear
it, harm no one, sell no silence), what each client lied about, and how the box was settled. Left for the tool lanes:
the paper game shows the `main` words for every condition copy of a line, so a haggled sale reads as a full-price
one while the journal and the gold say half; the locks show as open; two copies of a persuade prompt are listed.
