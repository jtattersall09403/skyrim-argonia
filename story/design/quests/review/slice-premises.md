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

