# Questlines: faction, main, local and Daedric lines

Read with `general.md` before any quest of a line. Evidence: `docs/research/2026-10-27/questline-design.md`
(its 14-step template and detectives' notes) and `quest-design-elder-scrolls.md`.

## The line record comes first

A line (faction, main or Daedric) is a **line record** before any of its quests is a quest record. Fill every
field; no job text before fields 1 to 9 are complete. The quests are then slices of it.

1. **Premise card:** the governing question, the governing verb, the cost of joining, what the faction wants
   from the player, what it lies about.
2. **Hidden spine:** the line's truth (culprit or truth, motive, timeline by day, the physical and spoken
   proofs, who knows what). Each quest's `truth` is a slice of it.
3. **Local root:** one local history and one contested ideal the faction embodies, and why it competes with
   each other guild. Grounded in the lore dossiers and the extrapolation, with sources.
4. **Rank ladder (5 to 7):** title, entry test (standing plus a skill, task or knowledge test; never time
   alone), what it unlocks, how many jobs, and **one new skill use per rank**, drawn from the line's profile
   (`profiles.yaml`) and combined with the earlier ones in later jobs. The top post comes only at the
   finale, with a cost (Skyrim's "leader in ten hours" is the anti-pattern).
5. **Job table:** id, rank, type (find, follow, question, scene, confront, deliver), the verb it teaches,
   places, clues planted, who appears. No two consecutive jobs share a type; one job per rank breaks the
   pattern (a scene-only case, an interview-only case, a case that cannot be fully solved).
6. **Cast sheet:** mentor, peer, inside rival, outside antagonist, informant, and the villain on screen by
   rank 2. Each speaks in at least three jobs before the turn and holds one contested belief.
7. **Rival-faction map:** for each other faction, its attitude, one shared case, one conflict case, the
   standing effect, any lockout and what makes it hostile.
8. **Seeding table:** for each finale conclusion, two clues in earlier jobs (one in a minor job, one in
   another faction's work), the decoy meaning, and a fair-play check: a player who read only the journal
   could reach it.
9. **Mid-line turn** at about half to two-thirds through: what it reverses and which earlier jobs it lets
   the player read again.
10. **A mid-ladder wrong-accusation branch** that costs standing but does not end the line.
11. **Finale:** a set piece using the line's verb in full; a choice with a cost; an ending where the truth and
    public justice diverge.
12. **Hub reaction:** for each rank and ending, the changed topics, prices, greetings and who avoids the
    player.
13. **Abandon path:** the world's state if the player stops at each rank.
14. **Authoring order:** spine, ladder, cast, seeding, job table, then each quest record, `quest-review` of
    the line and each quest, then briefs and dialogue.

## Line types

- **Faction lines:** as above. Joining one may close another only where the rival map says so; the line
  never forces the player to stay.
- **The main quest** ("The Eye and the Root"): urgency is stated in text and shown by consequence, never a
  timer; the prophecy or central question is answered in stages the player can follow without markers; the
  three endings (CUT, CLAIM, MEND) each change what the player meets afterwards.
- **Local quests:** one place's people and facts; a hook, two lines of enquiry, a revelation, a decision, a
  visible consequence; they never write anything a faction or main quest owns (tier protection).
- **Daedric and oddity lines:** `otherworldly.md`; each quest stands alone and expresses its patron.

## The detectives' line (decision 0025)

Designed at 4.1 §d from the old repo's quest foundation and faction designs (imported in 0.1 §f) and the
lore extrapolation; this file and `investigation.md` supply the principles, the foundation supplies the
structure. Ideas from the research pack (desks per rank, cases touching the rivals, a seeded finale) are
options to weigh against that foundation, not decisions.

## Record additions (line record)

`premise`, `spine`, `localRoot`, `ranks`, `jobs`, `cast`, `rivals`, `seeding`, `turn`, `wrongAccusation`,
`finale`, `hubReaction`, `abandon`.
