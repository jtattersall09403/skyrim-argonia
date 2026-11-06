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

### MQ01, round 1: fix by subtraction (planner's rulings; all accepted)

- B1: stages 11, 12, 13 and flag.mq01.manner-cooperated/-silent/-defied cut; all three stage-10 answers go to 20,
  the one broker approach moves into 20.
- B2: the rowboat rescue cut (stages 43 and 92, e-ties, flag.mq01.saved-ties, zone.mq01.boat-first): no boat
  system in the stack; Ties is a burnt survivor on the shore; MQ03 drops its saved-ties read and "from the water".
- B3: no timeOfDay gates or scene clock: 40 starts when the player reaches the fire after the clutch talk (as
  Helgen starts on arrival); the night fall-forward becomes inZone zone.mq01.shore to 44.
- B4: the stale clauses cut (the courier dies in the shallows as MQ03 has it; two cutters; one port hand, Ux-Xeek;
  the witnesses are camp families; n1-2 and n1-3 match thing.gang; no "MQ03 decides whether their months stand");
  the saved witness protected to stage 90, the three dawn fall-forwards cut, so 93's "alone" holds.
- N1: stage 30 completes on the reed handed to Sal-Sei; a-persuade cut.
- N2: the jars cut from MQ01's journals and fact.mq01.roots-cut (MQ03's reversal, MQ04's premise).
- N3: the leader's "fear of being named" and the witness clause cut from MQ01's cast.
- N4: at dawn only the clutch-dead line; e-sal leaves the player Sal-Sei's reed-knife (already in the world); no
  disposition-only rewards.
- N5: "Lilmoth's dock" in text, never Dock1; the hatching shed is the uxith (no "uxith goes dark"); Ux-Xeek's role
  matches (Wuleen-Sei reads the roll); the foundation lists both held-back forms (0BCC51, 0F0F3E).
Budget after the fix: 11 stage ids, 1 real choice, 3 endings.
Round 1: applied (commit c28a4e07): 11 stages, 1 choices, 3 endings

### Cross-quest rulings (planner, round 1)

- The courier, Mee-Tuja, dies at the camp's fire, as MQ01 stages it. His strap with the brass tag is torn off in the
  struggle and falls through the burnt boards into the shallows; MQ03's dive recovers it. (Overrides MQ01 B4's
  courier clause; MQ03 B3 stands.)
- No boats as a mechanic anywhere in Act I (no boat system in the stack): MQ01 B2, MQ04 B2.
- If Nesh-Deeka dies in MQ03, later quests say "The Reed sent me"; Never-Writes-Twice is the fallback handler
  (36-cast-roster §55): MQ03 B5, MQ04 N2.
- The jars of sap are cut from MQ01 (MQ01 N2), so MQ03's finding is a discovery again.

### MQ03, round 1: fix (planner's rulings; all accepted)

- B1: the dive is required; the activator's skill claim dropped; stage 20 completes when the survivor is shown the
  courier's tag (present-evidence) or passes a real skillAtLeast Speech check, so the dive's find opens the house.
- B2: the survivor choice cut (its two topics, the objective, the Speech 25 action, the flag, half of
  fact.witness-wanted); the survivor goes home by the Reed's people; stage 30 folds into 20: 6 stages, 1 choice (the
  oath, a plain yes or no).
- B3: as the cross-quest ruling; k6 re-pointed to c1 or cut.
- B4: we.mq03.barge-sails and the Soulrest clause cut; Wuleen-Sei marches the unhurt back to the barge at Lilmoth's
  dock; the hold's door locked under the dream parent.
- B5: as the cross-quest ruling; "Nesh-Deeka, if she lives," deleted from 91.
- N1: with MQ01's jars cut the reveal is MQ03's again; keep the shape the record can honour (drop RECKONING if its
  rules stay unmet), conclusion c1 only where a clue supports it.
- N2: shapeData.answer written (the voice is Cuts-the-Old-Knot); WONDER dropped from the shapes (the dream is the
  line's set piece).
- N3: stage 20 names the survivor by alias; the false "the one I pulled from the fire" cut.
- N4: the dream gets its fall-reset trigger and no fall damage in we.mq03.dream; the ring a build-check row; the move
  into the dream happens at night or after a rest, never mid-day "I slept".
- N5: grantHistStep as a stage action; Nesh-Deeka suspects, not knows, the courier's tag; t2.who matches the cast.
Round 1: applied (commit 7842f495): 5 stages, 1 choices, 2 endings

### MQ04, round 1: fix (planner's rulings; all accepted)

- B1: both the-jars topics and that failForward cut; the player pours the jars at the cut root (zone.mq04.root plus
  the item) and that moves to 91.
- B2: no poling; the hand-over to Carries-Both-Ways on the jetty; the ending disables the fence ref; journal 92 fixed.
- B3: no showing before witnesses and no Speech check to clear Pays-Late; e-exposed merges into e-minder (a man at
  the fence becomes a greeting variant and +5 standing): 2 endings; choice 2 is "the Reed or not".
- B4: both bypasses cut (the camp's-word skip at 10; "or shown the cut" at 30); the gift stays as 10's paid
  fallback; the-cut gated on the night at the root (time plus zone while his package runs); "unseen" dropped unless a
  detection block is proved in Phase 3.
- B5: the timeline: cut "the first work of it" and "first affected" from the foundation.
- N1: the knife goes in the jar bundle, so one take gets both.
- N2: as the cross-quest ruling.
- N3: fact.mq04.gum-origin moves to stage 30's learns; the false clauses cut; objective 30 reworded.
- N4: binding a man built from blocks (TR-activate + E-enable + C-stage); the cell men protected; Pays-Late's
  package only in stage 30, after the leeches are cleared.
- N5: the kaal's npc row loses the struck award; census.md's "Hatching Pools" line corrected; stage 10 gives the
  route from Lilmoth; journal 50 not conditional.
