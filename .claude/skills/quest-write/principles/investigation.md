# MURDER, MISSING, RECKONING (and every case the player must solve)

Read with `general.md`. Also used for THEFT and FRAUD the player solves (`crime-and-deceit.md`) and for every
case of the detectives' line (`questlines.md`). Evidence: `docs/research/2026-10-27/quest-shape-investigation.md`
(methods M1 to M8). An investigation is fair, mechanical and solvable from the player's side: simpler than a
novel, never a guess.

## The case

1. **Truth first:** one paragraph (killer or cause, method, motive, time, place, what was disturbed
   afterwards), then the final day's timeline with everyone's whereabouts.
2. **Every lie has one refuting thing.** Each cast member's column says what they know, saw and lie about, and
   why; the record names the thing or statement that refutes each lie.
3. **Conclusions with three clues by different channels** (a thing, a statement, a place or record); not two
   from one channel or one person. A clue is really four steps (visit, notice, identify, connect), so three
   clues are the minimum, never the target.
4. **Clues point to nodes** (people, places, things, organisations, events), not to the next clue. The start
   offers three leads; every node the player must reach has three leads in from different nodes; after any
   two nodes are visited, three leads to the rest remain. Five to nine nodes per cluster.
5. **Leads move the case; concept clues explain it.** Only leads count towards keeping it moving.
6. **Be permissive:** a sound way of investigating always yields something.
7. **Several plausible suspects:** shared means, shady habits, at least two with motive; two or three red
   herrings, each with its refuting clue; the culprit is met before the midpoint; no fact only the author
   knows; no out-of-world knowledge (no modern forensics: testimony, objects and records only).
8. **Keep clues few and relevant;** clutter the player cannot hold in memory is cut. No single clue may skip
   several steps.

## The player's side

9. **The journal is working memory** (within the imported journal design). It lists the open questions as sentences ("___ killed Naal-Ei with ___
   because ___") and records statements as facts attributed to people ("Haj-Tei says the courier left before
   dawn"), so contradictions can be seen.
10. **Lie and refute:** the player presents a fact or an item against a statement; disposition decides
    whether the speaker recants; the recanted line is new testimony.
11. **Accusation with evidence:** the player names a suspect, then presents exhibits (items or learned
    topics), each setting a conclusion flag; enough flags convict; too few give "bring me more" or a
    conviction that later unravels. A short closed run (who, with what, why) stops a lucky name winning. Long
    cases confirm in batches and give coarse feedback ("not all of that is right").
12. **A wrong accusation has a legible cost** in the world (a ruined name, flight, a death, lost standing) and
    the true culprit stays findable until a stated deadline stage.
13. **Endings:** right; right culprit with the wrong motive; wrong culprit; unsolved; and what the kin do. A
    condemn, absolve or stay-silent choice where the truth and justice diverge.
14. **No required fact sits behind high disposition only;** each has a second path (a bribe, a document,
    another witness).
15. **The engine cannot see what the player concludes,** so every conclusion is an explicit act: an exhibit
    presented, a journal blank chosen, a suspect named.

## MISSING

- Decide the fate and the reason first: alive and unwilling, alive and hidden, dead, or changed.
- A trail of three to five stops built as nodes, each trace explained by the next, with leads from more than
  the previous stop; one turn (a staged trail or a willing departure) recasts earlier stops.
- The fate is earned by a deduction, not a scene; a fate exists for every ending: found alive, found dead,
  never found, wrongly believed found.

## RECKONING (an old crime surfaces)

- The old crime as a timeline, with each party's role and what they have now.
- It surfaces through something physical: an object, a deathbed statement, a mismatch in records; reachable
  three ways.
- A guilty-party list (instigator, hand, beneficiary, silent witness) with different blame and a current life
  that justice would damage; justice and mercy each have a cost and a beneficiary; the wronged party may
  disagree with the law.

## The fairness test (run before review)

1. For each conclusion: three clues, distinct channels, not one person.
2. For each node: three leads from different sources.
3. Three blind routes reach an ending: one that misses the first clue everywhere, one that skips the richest
   person, one that starts at the last node.
4. No single clue bypasses steps by accident; the player does not grasp it all early and then stall on a
   detail.
5. The journal holds anything the player must remember beyond a handful of facts.
6. Someone who did not write the case reads only the journal and names each open question.

## Record additions (`shapeData`)

`timeline` (the final day, everyone's whereabouts), `lies` (speaker, false statement, refuted by),
`nodes` and `leads` (from, to), `redHerrings` (each with its refuter), `openQuestions` (journal sentences),
`accusation` (exhibits needed, flags, too-few outcome, closed run), `endings` (right, partial, wrong,
unsolved), and for MISSING `fate` and `trail`, for RECKONING `guiltyParties`.
