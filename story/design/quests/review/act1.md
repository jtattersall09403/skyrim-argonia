# Act I review loop: state

The planner runs the loop (quest-review §0; owner-rulings, 2026-11-06). The record format has no `review.settled`
field, so the settled rulings for each quest are kept here, in that quest's "Settled" list; reviewers read this file
with the record.

## MQ03 A Dead Prisoner's Use (M)

- Stages: 7 (10 camp, 20 house, 30 the offer, 40 the dream, endings 90 and 91).
- Choices: 2 (the survivor goes home or stays as the Reed's witness; the Reed's oath taken or refused).
- Endings: 2 (e-sworn, e-unsworn; Nesh-Deeka's death fails forward to e-unsworn).
- Skills by stage: alchemy (taste) and swimming (dive); speech; speech; climbing.
- MQ04 starts the same after either ending.

### Settled

(none yet)

## MQ04 The Tree That Turned Its Face (M)

- Stages: 8 (10 root-herald, 20 the cut root, 30 the tree-minder, 40 the trail and the camp, 50 the return, endings
  90, 91 and 92).
- Choices: 2 (take a cell man alive or not; a bound man brought before the village or handed to the Reed).
- Endings: 3 (e-exposed, e-minder, e-reed); every ending reaches stage 90 or more, so MQ05 starts the same.
- Skills by stage: speech; blade; sneak; swimming with sneak or blade; a boat or speech.

### Settled

(none yet)

## Rounds

- Round 0: rework done, awaiting review.

## Round 1 (2026-11-06): fresh reviewers on all four records; the planner's rulings

### MQ05: rework whole (as MQ03 and MQ04 were), not patch

Must-fix, all five blocking accepted:
- B1: no seated dispute, verdict or settlement as the climax or resolution (rule g); the dispute may stay as colour.
- B2: every stage the player plays is won with a skill (skillAtLeast and speakerDispositionAtLeast exist in
  condition_term; MQ04 stage 50 uses a Speech check); the hollow approaches cut. MQ05 does NOT absorb LQ25's
  river-beast: that is LQ25's own centre; MQ05 needs its own skill moment.
- B3: no voyage stage on BM&V's moored ship interior; the directions name which of its doors is Helstrom's.
- B4: the two public Reed escorts cut (they break the "voice the Reed can deny"); the basin warning comes from LQ30's
  gate soldier (08D5E9) and the landing's people.
- B5: journal 10 rewritten to what the player knows at MQ04's end ("I'm to take what I found back to Nesh-Deeka").
Notes accepted: the budget (about 8 stages, at most 3 endings; deaths by the standard fail-forward; no hidden trust
meter); the city gate cites we.lq30.trail; no unsourced "thorned causeway" (helstrom.md: the marsh is the wall) unless
BM&V's terrain shows one; rewards with real rows or cut; tree-minder as a village office, Helstrom's Hist a grove,
the npc and fact rows corrected. MQ05's place in the line (the spirit: Helstrom behind its thorns, past the empty,
swept Scalded Throne) is kept; make it exciting and Black Marsh-y.

Settled: (none yet)

## The whole main line, round 1 (2026-11-06): the planner's rulings

All five blocking findings and all five notes accepted. Fix at outline level (Acts II to V have no records yet);
the authored story/design/quests/30-main-quest.md stays as history, with a header note pointing to the adapted
outline, which becomes the source.
- B1: no multiplying choices down the line: §20's trust variables and paths, §24b's reward tracks and tier locks,
  §24.4's "offers only what accumulated state has enabled", §21b.3's wrong-mark lead, MQ15's variant per lead city,
  the carry-forward clauses of MQ20, MQ25 and MQ27 all cut; rewards fixed per quest; the second Hist in one fixed
  place; Cuts-the-Old-Knot opposes at the door on every path; only the finale's CUT, CLAIM or MEND carries forward;
  Act I's flags (flag.mq05.reed-exposed, flag.mq04.adopted) colour only or cut.
- B2: no procedure resolves an act: MQ22's two reports cut (the lie becomes MQ21's last choice, its victim the raid
  the player stands in); MQ20 a break-in and rescue (no files, no copy/alter/leak menu); MQ25's council background
  only; MQ26's archive not a desk; evidence weakens the Last Warden (MQ29) but never releases it; MEND an act at the
  Root, custodians only in the epilogue.
- B3: MQ05 as ruled above.
- B4: no living Shadowscales hunting the player (the last dies in 4E 201): the single vanished survivor the player
  tracks, or MQ23's manhunt cut.
- B5: homes only where the world has them: MQ14 (Archon's lighthouse) dropped from the beats (three leads: MQ07,
  MQ09, MQ10); Gideon and Stormhold homes struck from §21; the sunken Xanmeer (MQ16) and the Lost City (MQ29)
  recorded as needs before Act III is fitted.
- N1: Act II opens on MQ07's false Eye; MQ06 cut; the triangulation is the last stage of the third lead.
- N2: Helstrom freed of most main quests (by the cuts above); one MQ23 route chain; no main quest in a faction seat or a
  slice quest's place (MQ13 vs TG02's Pusbottom, MQ09 vs BC02's cells, MQ04's village vs the Many-Root hub).
- N3: talk-only quests cut or given skill stages.
- N4: the act split in §22 matches the line spirit.
- N5: MQ04 stage 10's journal has a sender line for when Nesh-Deeka died in MQ03; the Eye's two statements in
  eye-of-argonia.md reconciled (the Eye "grants no kingship" vs CLAIM's coronation).
