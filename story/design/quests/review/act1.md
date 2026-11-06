# Act I review loop: state

The planner runs the loop (quest-review §0; owner-rulings, 2026-11-06). The record format has no `review.settled`
field, so the settled rulings for each quest are kept here, in that quest's "Settled" list; reviewers read this file
with the record.

## MQ03 A Dead Prisoner's Use (M)

- Stages: 5 (10 camp, 20 house, 40 the dream, endings 90 and 91).
- Choices: 1 (the Reed's oath taken or refused).
- Endings: 2 (e-sworn, e-unsworn; Nesh-Deeka's death fails forward to e-unsworn).
- Skills by stage: Alchemy 25 (the phial); the tag or Speechcraft 25 (Ties).
- MQ04 starts the same after either ending.

### Settled

- Round 3: Ties-The-Loose-Plank is essential, with his own ref (ref.mq01.ties) enabled by MQ01's endings, moved to the mat at stage 20 and disabled by both endings; ref.mq03.house-hurt, c2, k5 and k7 are cut; journals 10, 20, 90 and 91 and t2's timing are as ruled; topic.mq03-the-boat uses fact.mq03.satchel-hers.

## MQ04 The Tree That Turned Its Face (M)

- Stages: 4 (10 the root-herald, 20 the cut root, 30 the tree-minder or the egg-tender, 40 the trail, the camp and the
  return), ending 91.
- Choices: 0 (the jars are poured at the root in every play).
- Endings: 1 (e-minder 91), so MQ05 starts the same.
- Skills by stage: 10 Speech 25 or two portions of food; 20 One-Handed or Destruction; 30 Sneak unseen (not detectedBy Pays-Late,
  C-detected) or Speech 25; 40 swimming, then Sneak or One-Handed.

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

Round 1: applied (commit 341a5dae): 5 stages, 1 choices, 2 endings

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

### The whole main line, round 2 (2026-11-06): fresh read of main-line-outline.md; the planner's rulings

All accepted, each fixed by subtraction or a place swap; nothing else in the outline is reopened (settled stays settled).
- B1: the Lost City is open ground; the Eye opens only the Root's door.
- B2: MQ07's boat tail cut; the buyer's mark names the cave.
- B3: MQ07's places re-chosen from the census (no Bandit Dock as Murkwood; no 01CabinInt2).
- B4: MQ20 uses 01cabinintDUPLICATE002, not 01Tower (a copy of vanilla Darklight Tower).
- B5: the second Hist is a recorded tribal tree, not the Murkwood Verge coast wonder.
- N1 and N3 together: MQ18's door swap targets the temple's front door (BM2 13,25); the bait is the Eye brought to that door.
- N2: Ahnjazzi cut from MQ10 (she never leaves her Soulrest desk; "salvage rights" is a permits motif).
- N4: MQ16's divers race in the dry chambers.
- N5: Swampy Cave's back-water route runs inside its one cell; 01Cavebig in place of the occupied 01Cavern; the
  reed-cutters' camp gets a census id or is dropped; the old Rose's walls confirmed on the map data.
Round 2: applied (main-line-outline.md): B1 to B5, N1 to N5; reed-cutters' camp dropped (no census id); old Rose cells confirmed (BlackRoseold 7 refs, gg 17, no actors or doors; statics not itemised in the census).

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
Round 1: applied (commit 34ceef35): 5 stages, 2 choices, 2 endings

### MQ03, round 2 (2026-11-06): the planner's rulings

All five blocking and all five notes accepted, each by swap or subtraction.
- B1: we.mq03.dream locks the hold's inner door 0F9399, not the exterior door 005AB4.
- B2: Ties-The-Loose-Plank is protected while the hurt enable parent is on.
- B3: "with a dry anger that passed" cut from the 90 and 91 journals.
- B4: k6 deleted from c2.clues.
- B5: t4.who is Cuts-the-Old-Knot; fact.mq03.barge-gone dropped from topic.mq03-the-boat's uses.
- N1: stage 20's fail-forward on Nesh-Deeka's death is all(dead, inZone house, night).
- N2: the activator's Hist grant is deleted from we.mq03.jar-marks; the taste (then stage 20) brings the dream.
- N3: stage 20's journal keeps "I'm to tell her..." and loses the offer sentences.
- N4: k7 cut from c2.
- N5: Salts-The-Catch's look_body matches her sex (argonian-female).

### MQ03, ruling #50 rework (2026-11-06)

- Skills per stage: 10 Alchemy (taste) and swimming or Alteration Waterbreathing (the dive); 20 the tag (swimming) or
  Speech 15 for Ties; 40 climbing on the dream's root ledges (placed statics, no tree). Athletics gone from the record.
- The dive is plain: journal, objective, directions and topic.mq03-the-boat all say off the end of the burnt boards, on
  the bottom, for the courier's brass tag, to show whose man he was.
- Cut: stage 10's "go down to the strangers" objective and its topic gate (holding phial and tag ends the stage); the
  premise's procedure words. Settled rulings above stand. Still 5 stages, 1 choice, 2 endings; recordStatus design,
  a quest-reviewer round to follow.

Round 2: applied (b05cf519).

### MQ04, round 2 (2026-11-06): the planner's rulings

All three blocking and all five notes accepted, by subtraction; plus the planner's own call on the boat.
- B1: the topic successor to 92 cut; the hand-over sets flag.mq04.handed-over only; the pour at the root is the only
  exit (92 if the flag, 91 if not); "withdrawn (e-reed)" and "or with the Reed" cut from the thing states.
- B2: journal 40 and objective 30 say only what both routes give (strangers by the north reeds; go north to the leech
  water); gum-trail dropped from stage 30's learns.
- B3: "dry at the cut" cut from fact.mq04.root-cut and we.mq04.village.
- N1: fact.mq04.minder-washes added to topic.mq04-the-village's uses; "after dark" in journal 30.
- N2: e-reed's +10 Reed standing names the existing Reed gate it meets; no new reward.
- N3: "unseen" cut from the sneak/spy reason.
- N4: "expose the cell before the village" cut from the foundation's Kept list; act1.md's MQ04 summary regenerated.
- N5 and the boat (planner): the bound man is at the jetty only ("fence" cut from ref names and seen text) and is
  handed over on the jetty to Zaren-Ish, who walks him off; no boat. gum-origin listed in topic.mq04-the-cut's uses.
- Round 2: applied (4915a86f).

### MQ01, round 2 (2026-11-06): the planner's rulings

All four blocking and all five notes accepted, by subtraction or a flag.
- B1: the saved one is essential (not protected) to stage 90.
- B2: the barge clauses cut from t1 and t3; Mee-Tuja dropped from the hold and joins at the plank; journal 20 "walks with us".
- B3: one place for the families: Deesh-Duun at the fire for the reading, into the huts at the strike; the other two
  clauses cut.
- B4: "the roots were cut" cut from 91 and 93; the clutch-dead changes move from stage 90 to 50, with Deesh-Duun's row.
- N1: Wuleen-Sei, Mee-Tuja and Sal-Sei essential until stage 40 (Helgen's Hadvar and Ralof); their four failForwards cut.
- N2: the hour words cut from journals 40 and 50 and the dawn topic intents.
- N3: "always on the left hand" cut from stage 20.
- N4: a-keep-alive and heal-the-sick ("tend the hurt") cut; the saved one placed in ref.mq01.survivors at stage 50.
- N5: zone.mq01.plank, the ref.mq01.zone-*-first disables, "whichever of the three", journal 44's "neither in time",
  journal 50's "from whoever I saved" and we.mq01.camp's islet clause all cut.

Round 2: applied (112479fc).

### MQ05, round 2 (2026-11-06): the planner's rulings

All three blocking and all five notes accepted, by subtraction.
- B1: stage 10 fails forward to 20 on Nesh-Deeka's death alone; the reed-officer's topic row, successor clause and
  "keeps the house" line cut.
- B2: stage 30 merged into 40 (20→40 on inZone zone.mq05.grove); journal 30's hall lines become colour in 40;
  zone.mq05.gate, 30's objective, both skill gates and a-admire cut. The climb at 40 is the quest's skill.
- B3: the other person's reaction cut from 91 and 92; 91's fail-forward keeps topic.mq05-tell-minder heard (minus the
  Speech clause); the fail-forward to 92 only when both are dead.
- N1: the ship's landing door given by its place in the ship (measured at build); door pairs cited 0AA664↔0AA837 and
  0830A8↔23D496; the list of other doors cut.
- N2: Names-The-Late-Guest cut, with k1, topic.mq05-the-way and the prep hint.
- N3: the Speech gate on Kaska-Meen dropped; the ending is a free choice.
- N4: the disposition clause cut from topic.mq05-tell-minder; shapeData.prize reworded (no "hearing").
- N5: the rescue clause and "nobody turns back" cut; both keep their posts all day, only the quarrel is evening.
- Round 2: applied (ab2cc1bf).

### The whole main line, round 3 (2026-11-06): the planner's rulings

All five blocking and all five notes accepted, by subtraction.
- B1: 01Ship cut from MQ07; the sale and the strongroom on the Bandit Dock's own ground (Murkwoodext).
- B2: MQ09's interior and its new door pair dropped (the tablet lies in the old Rose's ruin cells); MQ18's undercroft
  keeps 01aundergroundcell with a we.clean row disabling its 10 placements.
- B3: MQ23's Shadowscale is an old retired one, not "the last" (Veezara is canon's last, in Skyrim); "last" and "the
  order's last living member" cut from MQ23 and the Act IV hook. No one hunts the player.
- B4: the 10 stale quest rows retired (MQ06, 11, 12, 13, 14, 15, 19, 22, 25, 32); stale settlements and titles cleared.
- B5: the MQ20 and MQ21 group escorts cut; freed captives leave on their own.
- N1: on MQ21's lie no raid comes; the volunteers are left behind.
- N2: MQ26's guardian is the existing Grevious Twilight, fought in 01Underdarkmiddle; no new actor.
- N3: MQ08's alchemy and back-water route cut.
- N4: "opens the Lost City" struck from eye-of-argonia.md; the Tear marker phrase struck.
- N5: MQ07's "speech to buy a look" and MQ10's "at night" cut.
- MQ05 addendum (slice round 2, B2): we.mq05.sweeper cut; the broom stays in we.mq05.throne.

Round 3: applied (9567fb28).

### Reconciliation after round 2 (2026-11-06): the planner's calls

- MQ05: topic.mq05-the-seat cut (its speaker was the cut sweeper; the throne lines live in journal 40). The fail-forward
  to 91 also needs Kaska-Meen alive, so with both dead only 92 matches.
- MQ05 ship doors: 0AA837 (x 2924) and 23D496 (x 6038) sit in one cell 0AA665; prove from the cell's navmesh that one
  walkable section joins them. If not, add one door pair inside the ship joining the two sections (block W-ref), the
  lightest edit that keeps Lilmoth → Helstrom walkable.
- MQ04: Zaren-Ish waits on the jetty itself (no boat anywhere: journal 10, fact.mq04.officer-waits, ref.mq04.guarded,
  the npc notes).
- MQ03: k7's support row for c2 deleted (quest_clue_supports); k6 and k7 left only where they still support.
- Blocks: goldAtLeast, grantHistStep and setDoorAccess map to a block in blocks.md (an existing one, or a new one with
  its Skyrim.esm precedent counted), so every stage maps.
- Generator: slice.py's rebuild must reproduce the committed rows exactly; every hand edit since round 1 (we.clean
  .abondedtemple, the MQ01-05 and slice edits) is carried into slice_rows.py.
Reconciliation: applied (f34c6cba):
seat topic cut and fail-forward 91 gated on Kaska-Meen alive; ship navmesh 0AA666 (353 triangles, one component) reaches
0AA837 but nothing within 2954 units of 23D496, so we.mq05.ship-door adds one inner door pair; Zaren-Ish on the jetty;
k7's c2 support deleted; goldAtLeast C-item, grantHistStep E-global, setDoorAccess E-item; the generator retired: the
story database is the one source, edited through db.py or quest_record export and import.

### MQ04, round 3 delta (2026-11-06): the planner's rulings

Not converging (round 2: 3 blocking; round 3: 5). Cause: the Reed hand-over branch. Every fix to it left copies
(boat, walk-off, go-between, a superseded §24b citation), and it gives the player almost nothing over e-minder. Ruling,
by subtraction: cut the branch. MQ04 has one ending (the pour at the root, e-minder). Zaren-Ish, the hand-over topic,
flag.mq04.handed-over, e-reed, journal 92, the bound-at-jetty refs, ref.mq04.guarded, fact.mq04.officer-waits, t7, L6
and Carries-Both-Ways' row (used by no quest) all go. The captured cell man stays the village's (e-minder's text).
The 1 choice left is MQ04's route (talk or night watch); 1 ending. QA9 keeps its lore but loses the MQ04 citations.
Also accepted: B5 (the root-herald believes minder-washes; t5 says the village sees him go down at night); N1
(objective 30 "Learn what Pays-Late or the egg-tender saw."); N2 (gum-trail into stage 40's learns); N3 (minder-hid cut
from stage 30's learns).
Loop change (replace, not add): B5 and N2 are mechanical (a topic uses a fact its speaker does not know; a fact used
that nobody can learn). They become adaptation_check rules, and quest-review's checklist items 4 and 23 shrink to
pointers.

Round 3: applied (e5e9ceea; gap-register QA9/QA15 and this line in the next commit).

### The whole main line, round 4 delta (2026-11-06): the planner's rulings

Not converging (blocking 6, 5, 8 over rounds 2-4). Cause: the outline names cells, doors and in-cell mechanics for
Acts II to V. Each place swap brings new census facts (occupants, navmesh, doors, models) that a reviewer then
checks at build level, long before those quests are written as records. Loop change (replace): the outline is reviewed
at line level only (spirit, act beats, lore, motifs, branching, carry-forward). Place fit is checked when each quest
becomes a record. In the outline, each Act II-V quest keeps its settlement or region and the kind of place. Cell ids,
door ids and in-cell mechanics move to one list, "Places to fit at record time", which records the known facts
(round 4 B1-B3, B7, B8; MQ18's back door; MQ10's landing door) so they are not rediscovered.
Accepted at line level: B5 (the stale premise and spirit rows of MQ09, 10, 18, 20, 23, 26, 27 and 29 replaced by
the outline's first sentence); B6 (MQ21's "someone pays on screen" and its fire escort clause cut); MQ23 note ("He
dies this year either way" cut; "found dying" becomes "found"); the Act IV hook ("a hand that knows the wards");
MQ10's "the same night" cut and one wording for Tear; MQ21's lie needs a motive or a gain, or the choice goes (the
fixer picks the smaller change, from the outline's own beats). B4 (MQ04) is closed by MQ04's round 3 cut.
Slice: MQ05's new door pair (we.mq05.ship-door) takes 1DE5DF in its own row.

### MQ01, round 3 delta (2026-11-06): the planner's rulings

Not converging (blocking 4 then 4). Causes: three of four are stale copies the round 2 fixer left (it ran before the
"a cut is a search" rule), and one is a cross-quest Helgen case the checker does not see. All four blocking and all
seven notes accepted, as the reviewer worded the fixes (B2: Deesh-Duun into the huts and Sal-Sei to the shed at the
strike; N10: cut clutch-dead from Deesh-Duun's and Dives's rows; N11: Wuleen-Sei essential to 90, hold door 0F9399).
Loop change: the checker's helgen rule extends across quests. A person a later quest's stage needs is protected
from their first appearance in any quest until that stage, or has a fail-forward there.

Round 3: applied (8ae52554).

### MQ03, round 3 delta (2026-11-06): the planner's rulings

Converging (blocking 5 then 3). All three blocking and all six notes accepted as worded:
- B1: Ties is essential, not protected, while the parent is on.
- B2: ref.mq03.house-hurt is cut. Ties's own ref is acted on: MQ01 stage 50 enables him outside the survivors parent,
  MQ03 stage 20 moves him to the mat, and both endings disable him. MQ03 stage 20's onEnter disables
  ref.mq01.survivors during the fade.
- B3: 0F9399:Black Marsh.esm is written with its plugin and added as a target of we.mq01.doors on base 1DE5DF.
- N4 to N9 as worded.
- The stale act1.md MQ03 header and the Settled list are brought up to date.
Loop change: adaptation_check normalises a form id written without its plugin. B3's door was missed because the id
lacked ":Black Marsh.esm".

Round 3: applied (8ae52554). The 0F9399 door-base part of B3 is skipped under the MQ05 round 3 ruling.

### MQ05, round 3 delta (2026-11-06): the planner's rulings

Diverging (blocking 3 then 7). Causes:
- The reconciliation added mechanisms: a door re-model and a named warden. Each brings fresh rows to check.
- Our door rule reached further than decision 0006. 0006 binds what we add; BM&V's own doors are BM&V's world as its
  authors made it (decision 0038, owner: "BM&V stays as it is").
Ruling, by subtraction:
- We do not re-model BM&V's own doors anywhere. we.mq05.ship-door-base is cut, and so are the door-base swaps in
  we.tg01.doors and we.mq01.doors (and the MQ03 B3 addition of 0F9399). A door we add takes 1DE5DF.
- adaptation_check's vanilla_door rule applies only to doors we add.
Accepted:
- B1: the inner pair takes 1DE5DF; "ship door statics" cut.
- B3: "named and given her post by the quest" cut. The soldier speaks through a reference alias on 08D5E9 and is
  "his".
- B4: failForward[1] cut, and e-minder.when's Ei-Tuja-dead clause with it.
- B5: One Who Has Fire Hands' clauses cut.
- B6: the watch's stranger clause cut; "Tell" replaces "Convince".
- B7: each stale clause cut; the ledger lists we.mq05.ship-door.
- N1: the hints point at topic.mq05-the-word and k3; the merchant hint is dropped; pointOfNoReturn reads "none: the
  way can be walked back".
- N2: the gift takes 40 gold (takeGold).
- N3: journal 20 reads "The Reed wants...".
- N4: Ei-Tuja is essential to 92, and both stage 50 fail-forwards are cut (Helgen).
- N5: c1 cut; k6's c2 support cut.
- N9: "every day" cut.
- N10: one clause on the inner door in stage 20's directions, measured at build.
Not taken:
- N6: the +20 rewards stay.
- N7: moot once ship-door-base is cut.
- N8: the pair stays, cheaper than a build-time collision check.
Loop change: a fix may not add a mechanism (a new edit, alias, door or name). If a fix needs one, the planner rules
on it first.

Round 4: applied (11ed07df; the database rows in 0ef4f61e and e5e9ceea)

Round 3: applied (e5e9ceea)

### The whole main line, round 5 delta (2026-11-06): the planner's rulings

Converging (blocking 8, then 4). All four blocking and all five notes accepted, by subtraction:
- B1: "keeps the cult's trust" is cut from MQ21, beat ord 2 and changed item 12. The truth branch reads "her raid burns
  the house and its stock".
- B2 and N2: the name Tear is dropped everywhere ("the north-east coast's ship landing").
- B3: MQ05's foundation reads "MQ05 starts the same after MQ04's ending (91)".
- B4: MQ01's premise loses the doubled clause; "aboard" becomes "among them".
- N1: the spirit rows of MQ10, MQ18, MQ26 and MQ29 each become one sentence carrying the quest's turn, taken from
  the outline's own text.
- N3: "flooded lower ground".
- N4: "his blade (given, or taken)".
- N5: the garbled parenthesis is cut from MQ04's foundation.
- The Places section drops its door re-base notes (BM&V's own doors are never re-modelled).

Round 5: applied (150b818f), 9 of 9; the line_spirit_beat rows in the database are the older text and held neither phrase.

### MQ01, round 4 delta (2026-11-06): the planner's rulings

Flat (blocking 4, then 4), but the findings are now one kind: who is present, and under which enable parent, as
round 3's cross-quest move of Ties left it. Each finding is answered by a cut, so nothing new is wired. All four
blocking and notes N1 to N6 accepted:
- B1: Ties is cut from journal 30 and from the families lists. His one ref first appears, burnt, on the shore at 50.
- B2: "(ref.mq01.survivors)" is cut from the foundation; thing.mq01.survivors reads "Ties-The-Loose-Plank beside them
  on his own ref".
- B3: the same fix as the main line's round 5 B4.
- B4: MQ03's t2 reads "him", not "his barge".
- N1: the courier stands outside the broker's enable parent; the two states are scoped to the broker.
- N2: the hold door's lock is cut.
- N3: "Deesh-Duun said...".
- N4: we.mq01.hold-location is listed in the ledger and in the changes.
- N5: "the player brings the saved one (stages 41, 42)".
- N6: "until an MQ03 ending disables him".

Round 4: applied (2791e6f7), 10 of 10 (B3 with the main line's B4 in 150b818f).

### MQ04, round 4 delta (2026-11-06): the planner's rulings

Converging (blocking 5, then 2: both leftover copies of the cut branch). All accepted, by cuts:
- B1: the quest_adaptation premise is cut from "or hands" to the end.
- B2: "and bound" is cut from stage 40's note.
- N1: the drips clause is cut from topic.mq04-the-cut's intent and from stage 30's note.
- N2: the cell-man npc notes point at we.mq04.cell.
- The QA9 citation is cut from recordSources.lore.
- This file's MQ04 summary is brought up to date (one ending).

Round 4: applied (e2c6fd4c), 6 of 6 (N5, the foundation's parenthesis, in 150b818f).

### MQ03, round 4 delta (2026-11-06): the planner's rulings

B1 and B2 are MQ01's round 4 B2 and N1 seen from MQ03's side; MQ01's fixes answer them (Ties on his own ref; the
courier outside the broker's parent). Accepted:
- B3: "already" and "and the families" are cut from t2 and we.mq03.reed; "at dawn" and "and the families" are cut
  from fact.mq03.barge-gone.
- N1: "once both are answered" is cut from stage 20's directions.
Act I is converging: 7 unique blocking findings this round across MQ01, MQ03 and MQ04, against 19 in round 3.

Round 4: applied (3d5c90e7), 2 of 2 (B1, B2 and MQ01's B4 in 2791e6f7).

### MQ05, round 4 delta (2026-11-06): the planner's rulings

Converging (blocking 7, then 3). All accepted as worded, by cuts or restores:
- B1: the cast changes go back to 91 and 92. The fact is cut from the uses of the two tell topics, because the player
  says it and the speaker needs no knowledge of it.
- B2: the broom clause is restored in we.mq05.throne.
- B3: the foundation's MQ04-ending clause is cut.
- N4: the depth-stick and held-fast clauses are cut everywhere.
- N5: the levy-warden-01 row is marked as 082C96's occupant with nothing built; the name and look are dropped.
- N6: marsh-way is listed in topic.mq05-the-word's uses and Nesh-Deeka's knowledge; the warden clause is cut from
  the hint.
- N7: "it sends no escort".
- N8: the watch's question is cut.
- N9: takeGold goes into topic.mq05-the-word's intent.
- N10: "until the quest ends (91 or 92)".
- N11: "tells".
- N12: "his;" is cut.
- N13: thing.mq05.ship's source names we.mq05.ship-door.
- N14 is the slice's round 4 B1.

Round 4: applied (830f4fd1), 11 of 14 here; B3 in 150b818f (the main line's B3), N14 with the slice's B1. Not
applied: N11 ("tells"), whose row the ruling does not name.
- MQ05 round 4 N11, pointer: the row is quest.main.mq05's foundation, the B1 clause "the player convinces one
  person". It becomes "tells". Applied in round 5.

### MQ01, owner ruling #50 rework (2026-11-06)

The ruling overrides round 1 B3 ("after the clutch talk") and N1 (stage 30 completes on the reed): the camp stage
(30) and the bedding-reed chore are cut, stage 20 ends at the fire and the strike starts there; the clutch talk is
optional at stage 20. Every stage names a Skyrim skill: 10 Speechcraft; 20 Sneak or Speechcraft; 40 Sneak or
swimming; 41 OneHanded, Destruction or Sneak; 42 swimming and Sneak; 44 swimming; 50 Speechcraft. Every other
settled ruling stands; no MQ03-cited row id changed.

### The whole main line, round 6 delta (2026-11-06): the planner's rulings

Converging (blocking 4, then 3). All accepted:
- B1: MQ29's spirit row ends at "fought on every path".
- B2: the six-actor sentence is cut from MQ01's changed text.
- B3: flag.mq05.reed-exposed is cut from line 18.
- N4: MQ09 "a fight with, or a sneak past, what nests there".
- N5: the parenthesis is cut.
- N6: "behind its thorns" is cut.
- N7: "(given, or taken; row needed)".
- N8: "rounds 1 to 6".
- Outside the delta, also accepted:
  - the database's line_spirit and line_spirit_beat rows for quest.line.main are replaced by the outline's For the
    data block (pending since round 1);
  - the old spirit and premise rows of MQ21, MQ31, MQ16, MQ07 and MQ03 take the outline's first sentence;
  - MQ05's foundation reads "tells".

### MQ03 and MQ04, the delta after the #50 rework (2026-11-06): the planner's rulings

Both found 3 blocking. Most of them are a new kind, caused by the #50 rework, not stale copies: skill routes that
are labels only. Examples are a check of 15 that every new character passes, a branch already forced by the stage
before, and "unseen" with no detection check. Loop change (replace), applied in the skills, the checker and the
blocks:
- principles/actions.md lists Skyrim's skills, not Morrowind's. The stale names came from there.
- A skill route counts only if it can be failed: a skill check of 25 or more (Bethesda's easy level), or a fight,
  lock, dive or spell the player must do. skill_routes counts the first stage too.
- Sneak that must go unseen uses the existing condition term detectedBy, as a block C-detected (GetDetected, with
  Skyrim.esm's count) proved in Phase 3. Sneak that only passes enemies without a fight needs no check, as in
  vanilla.
MQ03, all accepted:
- B1: the boards are at the camp's fire, in the reviewer's wording.
- B2, option (i): Ties is won by the tag (the dive, swimming) or by Speech 25. The tag is cut from stage 10's
  successor, and both water-breathe rows are cut. The owner's #50 overrides round 1 B1's required dive.
- B3: the stranger's errand is cut from the intent, the directions, the foundation and the premise.
- N1: a need row: the water below the boards is swimming depth, measured at build.
- N2: accepted as is.
- N3: "In the hatching shed at the camp's far end".
- N4: "the courier Mee-Tuja's brass tag"; "on the water side" is cut.
- N7: this file's MQ03 header is rewritten to match the record.
MQ04, all accepted:
- B1: the night watch is won by Sneak gated on not detectedBy Pays-Late (C-detected); "unseen" stays.
- B2: as worded.
- B3: actionPlan and both summaries are rewritten to the stage skills; the hand-to-hand row is cut.
- N1: Sneak is cut from stage 20.
- N2: the gift is gold, in the topic's intent (takeGold), and the journal says "pay her".
- N3 to N6: as worded.
- N8: stage 30 fails forward on Pays-Late's death alone.
- N10: this file's MQ04 summary is rewritten to match the record.

### MQ05, the delta after the #50 rework (2026-11-06): the planner's rulings

Blocking 4, from new material (the wasps' nest), not stale copies. All accepted, with the planner's choices:
- B4 and N9: stages 20 and 30 merge. Stage 20 completes on zone.mq05.grove. The nest is met on the way: a fight
  (OneHanded, TwoHanded, Block, or Marksman, Destruction) or a Sneak past on the root at night (no detection check,
  as in vanilla). zone.mq05.bend, objective "bend" and journal 30's nest lines are cut.
- N1: the drowned channel, its swimming rows, the channel clause in fact.mq05.wasps, L14 and the swim need are cut.
- B2: the bmv need names the nest's cell on the way (from we.mq05.way's wasp placement, 166381), measured at build.
- B1: LQ25 starts on MQ05 ≥ 40.
- B3: "and FreeClimb" is cut.
- N4: invisibility is cut. N5: the flint-vine cites are cut. N6: the wasp base is 166381.
- N7: "walks out through the hall" is cut. N8: "north-east" and "by the first street, on the left inside the gate"
  go into the journals.
- N3: a pure choice stage (who is told) is exempt from the skill rule, as an ending is. The skill rule says so in
  place (loop change).

### MQ01, the delta after the #50 rework (2026-11-06): the planner's rulings

Blocking 5. Cause: the rework labelled stages with skills, but few of those skills decide an exit (the same cause
as MQ03 and MQ04; the stricter skill_routes rule now catches labels). All five blocking findings and N1 to N10 are
accepted, by cuts:
- B3: stage 20 is cut. The march is a follow scene after the answer (Helgen's cart). Stage 10 gets "follow Wuleen-Sei
  to the camp's fire", the fire zone sets 40 from 10, and the plank and pier talk stay as colour.
- B4: stage 50 is cut. The shore zone in 41, 42 and 44 sets 90, 91 or 93. 50's onEnter moves into the endings'
  worlds. topic.mq01-dawn is cut. thing.mq03.hurt reads "by MQ01's endings".
- B5: topic.mq01-the-clutch is cut. gang-hist moves to 40's learns. Journal 40 reads "at the families' Hist
  cutting, over their clutch".
- B1: stage 40's Sneak row is cut. The huts are entered only from the water, and the cutters stand between the
  fire and the shed.
- B2: "shallows" becomes the deep water under the plank boards (measured at build; the same need as MQ03's dive).
  42's Sneak row is cut.
- N1: the reading names Sal-Sei, keeper of the clutch, and Deesh-Duun aloud (Helgen's roll call); beats.liminal
  matches.
- N2: as worded.
- N3: huts-first sits inside the huts.
- N4: hide in the reeds until the cutters leave.
- N5: closed by B4.
- N6: the shed-wall knife is cut; the reward knife stays.
- N7: the player overhears her guess and he does not deny it.
- N8: noted.
- N9: "saves one of them"; the serial comma is fixed.
- N10: the review rows that cite stage 30 are marked as cut by #50.
MQ01 is now the hold, the strike, three rescue branches each won by a skill (blade, Destruction or reeds; the dive
from the huts; the swim), and the endings.

### MQ04, the leftovers of the #50 fix (2026-11-06): the planner's rulings, spelt out

The fixer could not apply "as worded" rulings whose wording lived only in the review message. Loop change: from
now on every ruling spells out its fix in this file.
- B2: cut fact.mq04.strangers-seen and fact.mq04.gum-origin from stage 30's learns. Journal 40's first sentence
  becomes "A root of Low-Reed Village's Hist was cut and its sap drawn off." we.mq04.village's drips clause says
  what fact.mq04.gum-trail says: drips from the workshop to the leech water.
- N3: cut "in a crowd or a market" from stage 30's Speech setting.
- N4: cut the two-handed, bow and Destruction clauses folded into the OneHanded notes of stages 20 and 40.
- N5: "two cells out" becomes "past the last stilt house, where the reeds bend".
- N6: cut "where he found it" from journal 91.
- Self-review B3 (gold against the village's barter lore): the gift becomes food, not coin. Two portions of any
  common food (C-item on the food keyword, then E-item to take them); the journal says "bring her food".
- Self-review N3: Turns-The-Clutch's protection until stage 40 stays (the Helgen rule needs it).

### The slice's last checker warnings, and how the loop ends (2026-11-06): the planner's rulings, spelt out

Checker calls (skill_routes):
- Pickpocket counts as a route that can fail (it fails on detection, as in vanilla).
- A Speech check of 25 or more with a gold or food alternative counts as a route, as Bethesda's persuade or bribe
  does.
- A pure choice stage is one whose successors are only distinct choice topics, whatever they lead to. BC03's stage
  10 (stand with Ussa-Rekh or Heavy-Rope) is one.
BC02:
- Stage 20, the gate, is won by Speech 25 with Third-Born Tsaxi, or by Sneak, not detectedBy Tsaxi (C-detected).
- Stage 40 merges into 30. Reaching the chosen prisoner and walking out are one stage, and the endings fire on
  npcAtMark at we.door.rose-jail.
How the loop ends: the planner rules, as the owner gave. The Act I and slice loop closes when:
- adaptation_check prints no warning for the slice quests;
- a last delta review raises nothing blocking that a single cut or rewording cannot answer;
- those cuts are applied without another review.

### MQ01 stage 10 and MQ03 stage 40 (2026-11-06): the planner's rulings, spelt out

- MQ01 stage 10, the hold: it is the new game's opening scene, Helgen's cart. A stage that completes on a scene's
  end (TR-scene) and cannot be failed is a scene stage, exempt from the skill rule as a choice stage is. The hold's
  talk plays as the scene (the roll call reading Sal-Sei and Deesh-Duun aloud, the answer). Stage 10 completes on
  the scene's end, and the march follows as before.
- MQ03 stage 40, the dream: the root-ledge climb is cut (the owner: climbing in trees is pointless and buggy, and a
  climb that resets on a fall cannot fail). The dream is a short vision scene to the door (TR-scene), exempt as a
  scene stage. The placed root-ledge statics are cut.
- adaptation_check: skill_routes skips a stage whose only successor is a scene's end.
- MQ01's place_hostility_flips rows that test the cut stages 30 and 60 are re-pointed at stage 40.
