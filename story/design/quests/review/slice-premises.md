# Review loop: the slice's faction and local premises

The planner's triage (owner, 2026-11-06: the planner judges which findings matter and when the loop ends). Each
round: a fresh `quest-reviewer` per line, briefed with paths only; the planner rules each finding must-fix or noted;
one fixer applies only the must-fix list; rulings join "Settled". The loop ends when a round has no must-fix.

## Helstrom locals: LQ25, LQ30

### Round 1 (2026-11-06), planner's rulings

Must-fix:
- B1 LQ25: no arbitration and no "season of sharing" award. Restore the bait (the scaring crew dumps offal under the
  pier to fake kills); the player finds the bait points (sneak, or a swim under the pier), then faces the beast in
  its lair under the pier (blade, archery, magic) or lures it with the crew's own bait. Two endings: expose the crew
  to their rivals, or keep their secret for a price.
- B2 LQ25: the quest row's region, settlement and anchor to hist-heartland and Helstrom (bmv.dock5, the landing);
  LQ25 removed from the Vaunting and Threewater hooks.
- B3 LQ30: no report-back; the youth cornered at the shelter by one fixed-band creature (a creature_add row in place
  of the reed shelter). Choice 1: help the youth finish the walk-out unseen (sneak, combat). Choice 2: bring them back
  (saves them, shames them; the kin's reward differs). The two choices are the quest's whole budget.
- B4 LQ30: QA5 rewritten: the custom binds the tribe, not an outsider; "found by kin" deleted.
- B5 LQ30: settlement place.hist-heartland.helstrom; The Break cut (or made the shelter, with a climb); the city
  gate is one row owned by MQ05, which LQ30 reuses.
- N1: the LQ30 prerequisite on LQ25 deleted; LQ25's reason "the beast is not on the landing while MQ05's escorts
  stand there".
- N2: one band per quest, from the place where its scene stands.
- N3: LQ25's crew from BM&V's Helstrom placements (the boatman Namorine, villagers), not four new raft-polers;
  LQ30's added tree-minder cut (the kin is enough).
- N4: the beast is never called the Helstrom Crocodile (extinct); the crews are Agaceph with tail-poled rafts.
- N5: LQ30's "four hours ago" stays a line, not a timer.

Round 1: applied (commit e87457d4)

Settled: (none yet)

## Night-Reed: TG01, TG02

### Round 1 (2026-11-06), planner's rulings

Must-fix:
- B1 TG01: the thief runs when caught (a coward setting on his npc row, no script); harming him costs the reward and
  a line from Deep-In-Her-Cups, who still sends the player on: the line never dead-ends.
- B2 adaptation.md §5: the TG01 and TG02 summaries rewritten from the quest_adaptation premises (Deep-In-Her-Cups
  keeps the desk, the Khajiit trader is her front; Pusbottom is the repopulated slum, not the drowned quarter).
- N1 TG02: the canon ripper eels in the canal, slipped past by sneak and timing (eel-slime kept for TG10); Speech to
  draw out the lies; Lockpicking on the box. No new stage.
- N2 TG02: each client's lie written as one fact tied to its object; the "deed-stake" replaced by a sourced object
  (blue-jasper jewellery, material-culture.md).
- N3 TG02: the box is a container in the open beside a stilt house fallen from its stilts (not "sunk"), with a
  water-depth check row for the Pusbottom cell; no Riften or Nordic static (0006); the authored air pocket and
  escape either restored as a simple swim-out or their drop noted in `changed`.
- N4 TG02: Vasha gives the job; the ending is an act (hand the box to one client, or sell a lie back to its teller),
  at most three endings, none carried forward; THEFT is the primary shape (not DISPUTE).
- N5 TG01: the keepsake is named, sourced Argonian jewellery; watching the thief is a sneak where being seen makes him
  move it; the thief's round gets its package rows; the trip to Lilmoth is by the coast ship we.name.soulrest gives.

Round 1: applied (commit e87457d4)

Settled: Soulrest as one house on the wrong coast (a trade-off recorded in adaptation.md §4).

## Chainbreakers: BC01, BC02, BC03

### Round 1 (2026-11-06), planner's rulings

Must-fix:
- B1 BC01: no hearing, no road witnesses, no "take a month" ending. Never-Sold makes her point to the steward in one
  exchange. The estate's debt book is only a thing the player steals (sneak or lockpick, the vibe licenses books on a
  former Archein estate) and uses to bring the buy-out down. Cutting her loose is slipping her into the channel at
  night (she cannot drown, labour §1) while the player keeps the two estate men off her (sneak, blade, bow). One
  choice, two endings; no boat chase.
- B2 we.clean.road: add to its targets the Lurkers 060C61, 060C62 and the Dwemer ballistas 048FD0, 048FD1 (disabled);
  the boars 060C5E, 060C5F, 05D7DC, 05D7BD, 120D5C and Ja Tal 16BF58 at a fixed level. No new edit.
- B3: the quest rows of BC01-03 rewritten from quest_adaptation (settlement, region, anchors to the hosts); the shapes
  FRAUD, MISSING and RECKONING dropped; line_spirit_beat chainbreakers ord1 rewritten to the fire; Ussa-Rekh's npc row
  is the Soulrest broker, not an envoy at the Rose.
- B4 BC02: the place is the outer post's cells, not the Rose's lower levels; the sealed door and the old dead cut
  (they are BC04's Rose); the two heirs who go in cut; each cell reached by a skill (a lock, a collapsed way to climb,
  a flooded cell to dive); the way burns shut after the first is out, said plainly.
- B5 BC03: the side is taken by one act each: for the crew, take their owing tokens from his cabin (lockpick, sneak or
  pickpocket the key) so they break them before him (tokens, not ledgers); for him, face the crew in a standard
  brawl. Each side's cost is a concrete loss: his hire, or the crew's trade.
- N1: the line's promise becomes "by freeing its people and burying its dead"; the fire carries the line.
- N2: BC03 off a barge: Ussa-Rekh on Soulrest's open dock among the crews (no repeat of MQ01's barge or MQ03's
  bargain).
- N3: each choice changes only a greeting or a line later; the woman lives in every BC01 ending.
- N4: one start host per quest; the fire's cause stated or plainly left unsaid.
- N5: the crossing-keeper and his toll post cut; Never-Sold's npc row matches her host (BM&V's House).

Round 1: applied (commit e87457d4)

Settled: (none yet)

## After round 1

Applied (commit e87457d4). Planner's rulings on the fixer's judgement calls: LQ30 uses BM&V's own gate (08D5E9), and
MQ05 cites it rather than owning a row (MQ05's rework follows); one band per quest (LQ25 at the landing's band 1)
accepted; TG02's three lies are characters' claims inside the quest, not facts about the world, so they need no lore
source. Round 2 (a fresh reviewer per line) runs with the Act I round.


## Round 2 (2026-11-06), planner's rulings (all seven quests)

All five blocking and all five notes accepted, by subtraction or swap.
- B1 LQ25: Namorine and the placed rival pair dropped; the crew are the two villagers at -10,15 and -9,15; the rivals
  are BM&V's Boat Captain at -9,19.
- B2 LQ30 x MQ05: we.mq05.sweeper cut (one record, 01ArgonianSoldier2, behind ten placements); applied with MQ05's fixes.
- B3 TG01: we.tg01.doors widened to give 120E93, 0E971F and 039827 BM&V's Argonian door; no new row.
- B4 TG01/TG02: both quest rows rewritten from quest_adaptation (TG02 the fallen stilt house in the Pusbottom canal),
  each naming its settlement.
- B5 TG02: the eels are Slaughterfish (023AB8) at a fixed level, called ripper eels; the patrol path cut.
- N1 LQ30: the shelter's cell named, off MQ05's way in from the landing.
- N2 BC02/BC03: BC03's dock host is its start; BC02 starts with Never-Sold at the house (BC01's host reused).
- N3 BC03: one crew boss brawls; the other two and the pickpocket route cut.
- N4 BC01: Never-Sold's escort cut; she meets the player at the estate landing.
- N5 TG02: the job goes to an existing Chapter row (Vasha Half-Rent cut); the third pledge a different sourced object.

Round 2: applied (ab2cc1bf; B2 applied with MQ05).

## Round 3 delta (2026-11-06), planner's rulings

Not converging (blocking 5, then 6). The cause is the same as the main line outline's. These seven quests are
premise-level records: no stages, no journals. Yet they are reviewed at build depth (navmesh, enable parents, aliases,
model sources), and round 2's fixes added mechanisms (Never-Sold's second placement). Loop change (replace): premise
records are reviewed at premise level only. That covers the premise against the census and lore, hosts, prerequisites,
the branching budget, motifs, and clashes with other quests. Place fit is checked when a quest is written as a record,
and the known facts are listed below so they are not rediscovered.

Accepted at premise level:
- B3: the BC03 prerequisite's reason becomes "the crew know the player as the Chainbreakers' since BC01".
- B4: the six stale place_quest_hooks_provisions rows are deleted.
- B5: LQ25's rival trades from Helstrom; the crew want to scare her trade off the river; "on tail-poled rafts" is cut
  for her.
- B2, by subtraction: Never-Sold's second placement and its enable parent are cut. How she meets the player at the
  landing is a place-fit item.
- N7: the item is named "Kothringi Glass Beads".
- N8: the beads use a model already in the load order (no Monk Prayer Beads).
- N9: Bent-Spine's home is place.mercantile-coast.lilmoth; "(Under-Yard)" is cut.
- N11: BC01 and BC03 read "by its lock, unseen"; the lock is kept low.
- N12: BC03's crew wording is about the one boss.
- N13: "the gate's warden".
- N15: LQ25's prerequisite reason is rewritten.
- B6 and N14 are MQ05's: the warden is "his" and is called the levy warden, with no name.

### Places to fit at record time (known facts)
- LQ30: the shelter 0D7885 (-4,18) has no navmesh; 0D7883 (-5,18) has navmesh and no NPCs. The youth's cell is
  not set.
- BC01/BC02: Never-Sold has one placement (15635D). Bethesda's way to the 095465 landing is an alias travel package.
- LQ25: the crew bases show "Villager" (00FF4D) and "Aragonian Vliiager" (02A1EE). Name them through aliases, not
  base edits. we.lq25.crew needs 08D5EF as a target. The beast's lair has no cell.
- TG02: the beads (item.glass-bead-strand, in we.tg02.house's lockbox) take a silver amulet's model, not glass
  (round 4 N5).

Round 3: applied (0ef4f61e)

## Round 4 delta (2026-11-06), planner's rulings

Converging (blocking 6, then 1, a wording fix). All accepted:
- B1: LQ25's prerequisite reason reads "the player first meets the landing on MQ05's way in".
- N2: the unheld Under-Yard slot night-reed-fence is deleted; Bent-Spine's npc_source is re-pointed to Lilmoth; the
  stray " ." is cut.
- N3: "scare the Boat Captain's trade off the river ... expose the crew to her, their rival".
- N4: "The gate's warden, of the tribe's own levy".
- N6: "08D5E9, " is cut from MQ05's changed text.
- N7: a line here records that round 3 cut TG01's door re-base (BM&V's own doors are never re-modelled).
- N5 goes to "Places to fit at record time": the beads' model is a silver amulet, not glass.

Round 3 cut TG01's door re-base: BM&V's own doors are never re-modelled (N7).

Round 4: applied (fff0782b), 7 of 7.

## Full records, round 1 (2026-11-06): LQ25 and LQ30, the planner's rulings

Round 1 of new full records reads everything, so 9 blocking is expected. All accepted as worded, with these
choices:
- B1 LQ25: starts on reaching Okan-Tei (his cell 0D77AD); the beast is enabled at 20; journal 10 is rewritten.
- B2: the directions name the real spot; the rafts and the watching are cut.
- B3: the lie is a beast that takes boats in the deep channel.
- B4: the bucket is the evidence; the fact moves to 20 or 30 via k2; journal 40 says "the crew".
- B5: the lure is cut; shot or burnt from the pier; nonCombat reads "none needed".
- B6: one landmark line in journal 40; the unmeasured stair and boat are cut.
- B7: the failForward is deleted and both crew are protected.
- B8 LQ30: 92 when topicHeardFrom come-back or detectedBy the youth (block C-detected); journal 92 covers being
  seen.
- B9: present tense, as worded.
- N1 to N12, N14 and N15 accepted as worded. N5: cut stage 10 in each; merge LQ25's 20 and 30. N6: rebalance
  without adding. N14: LQ30's beast becomes a census creature other than a crocodile or a wasp, at fixed band 3.
- N13 (LQ22's shared reversal) waits until LQ22 is written; LQ22 is not in the slice.
- The lows are accepted as worded.

## Full records, round 1 (2026-11-06): TG01 and TG02, the planner's rulings

Blocking 11. All accepted as worded, with these choices:
- B1 and B2: TG01 starts on Deep-In-Her-Cups' topic.tg01-the-test at stage 0 (she is essential); stage 10 is cut in
  both quests; TG01 40/41 end on Bent-Spine's welcome topic, which chains TG02 at 20.
- B3: closed by B2.
- B4: stage 20 stays and is won by Sneak, gated on not detectedBy the thief (block C-detected, proved in Phase 3).
  The inZone completion is cut.
- B5: the necklace stays on him; the bedroll container is cut; the evening route is Pickpocket while he sleeps.
- B6: 30 merges into 40, and the settle topics are gated by C-item.
- B7: the house, the box and the clients sit under one enable parent turned on at TG02's start. Likewise TG01's
  thief and necklace are enabled at TG01's start.
- B8 to B11: as worded.
- Notes accepted as worded. Also:
  - the canal-depth need is measured at build;
  - NEGOTIATION is cut;
  - a budgetExceptions line goes in for THEFT twice;
  - the item names carry the tells, and journal 40's deductions are cut;
  - the directions use the Lilmoth Hist, the fallen house and the "Lilmoth Dock" marker;
  - the all-dead fail-forward uses the flat failure entry;
  - the hand-over gets a Speech 25 check;
  - swimming is named.
- Low notes: accepted as worded, except the Deep-In-Her-Cups name. It echoes a vanilla Skyrim name, so she is
  renamed from the roster's unused names (decision 0006, a name we add).

## Full records, round 1 (2026-11-06): BC01 to BC03, the planner's rulings

Blocking 16. All accepted as worded; nearly all of them are cuts. The planner's choices:
- B1: the taboo row is cut (it is "inferred"; buying Owings is Never-Sold's method).
- B2 and B3: stages 10 and 35 are cut, and so are the stage-20 topic gates. The act decides: the book in hand leads
  to e-bought-down (its journal: Never-Sold put the book before Hulm-Tei, and named him a slaver to his face, which
  is the lever, from the high note); Rows-For-Another in the channel at night leads to 91.
- B4: closed by B2.
- B10 and B11: Bethesda's way. On the first "come with me" the other two die in the fire (a kill in stage 40's begin
  fragment). The fall, the drain and the swim out are cut, and the one reached walks out through we.door.rose-jail.
- B5 to B9 and B12 to B16: as worded.
- High notes: all accepted as worded. The line gets a one-line budgetExceptions row for BONDAGE three times; the
  alteration opening is cut.
- Low notes: accepted as worded. Player-facing text uses Skyrim's UI skill names ("Speech").
