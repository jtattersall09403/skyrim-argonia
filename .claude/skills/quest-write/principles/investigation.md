# MURDER, MISSING, RECKONING (and every case the player must solve)

Read with `general.md` (which holds the source tags' key). Also used for a THEFT or FRAUD the player solves
(`crime-and-deceit.md`) and for every case of the detectives' line (`questlines.md`). A case is fair, mechanical and
solvable from the player's side: simpler than a novel, never a guess. The investigating is done with skills: a lock
picked to reach the body, a key lifted from a suspect, a sample read with Alchemy, a witness persuaded or frightened,
a culprit fought.

## The case

1. **Truth first**: one paragraph (killer or cause, method, motive, place, what was disturbed afterwards), then the
   last day as a sequence of events with where everyone was [IN M1].
2. **Every lie has one refuting thing.** Each person's column says what they know, saw and lie about, and why; the
   record names the thing or statement that refutes each lie [IN M1; IN M5].
3. **Three clues per conclusion, by different channels** (a thing, a statement, a place or a body), never two from
   one person. A clue is four steps (reach it, notice it, know what it is, connect it), so three is the least, never
   the aim [IN P1; IN P2].
4. **Three ways past each chokepoint**, not only three clues: the vital door has a key someone carries, a lock, and a
   person who will open it [IN P3].
5. **Clues point to nodes** (people, places, things, groups, events), not to the next clue. The start offers three
   leads; every node the player must reach has three leads in from different nodes; after any two nodes are visited,
   three leads to the rest remain. Five to nine nodes to a cluster; a harder case adds a second cluster linked by a
   different kind of lead [IN P4; IN M2].
6. **Leads move the case; concept clues explain it.** Only leads count towards keeping it moving [IN P5].
7. **Be permissive**: a sound way of investigating always yields something [IN P6].
8. **Several plausible suspects**: shared means, shady habits, at least two with motive; two or three red herrings,
   each with its refuting clue; the culprit met before the midpoint; no fact only the author knows; no out-of-world
   knowledge (testimony and things only) [IN P14; IN P15; IN M1; IN A].
9. **Keep clues few and relevant**; clutter the player cannot hold in mind is cut, and no single clue skips several
   steps [IN P12; IN P10].
10. **Facts are fixed; the reading is the player's.** Identity comes from what people wear, carry and say, never from a
    label handed over [IN P16].

## The player's side

11. **The journal carries the case**: each entry holds what the player has learnt as facts said by named people
    ("Haj-Tei says the courier left before dawn"), so a contradiction can be seen, and ends on the open question
    [IN M4; IN P19].
12. **Lie and refute**: the player shows a thing held or a fact learnt against a statement; a Speech check or the
    thing itself makes the speaker recant, and the recanted line is new testimony [IN M5; IN P17].
13. **The player asserts the answer from a closed set**: names the suspect, then shows the exhibits, each a thing
    held or a fact learnt (a stored number); enough of them convicts, too few gives "bring me more". A short closed
    run of questions (who, with what, why) stops a lucky name winning; a long case confirms in batches and says how
    many are right, not which [IN P7; IN P8; IN M3].
14. **A wrong accusation has a legible cost** in the world (a ruined name, a death, lost standing), and the true
    culprit stays findable until the confrontation ends the quest [IN P13].
15. **Endings**: right; right culprit with the wrong motive; wrong culprit; unsolved; and what the kin do. Where truth
    and justice part, the player chooses to condemn, absolve or keep silent [IN M1; IN M3].
16. **No required fact sits behind a high check alone**: each has a second path (a price, a thing to take, another
    witness) [IN P6; IN M8].
17. **The engine cannot see what the player concludes**, so every conclusion is an act: a thing shown, a name
    chosen in a line [IN P7].

## MISSING

1. **Decide the fate and the reason first**: alive and unwilling, alive and hidden, dead, or changed [IN M6].
2. **A trail of three to five stops built as nodes**, each trace explained by the next, with leads from more than the
   previous stop; one turn (a staged trail or a willing departure) recasts the earlier stops [IN M6].
3. **The fate is earned by a deduction, and found**: the person standing where they went, or their body, or their
   things; a fate exists for every ending: found alive, found dead, never found, wrongly believed found [IN M6;
   MW §4.5].

## RECKONING (an old crime surfaces)

1. **The old crime as a sequence of events**, with each party's part and what they have now [IN M7].
2. **It surfaces through something physical**: a thing, a body, a dying person's words; reachable three ways
   [IN M7].
3. **The guilty parties** (who planned it, whose hand, who gained, who saw and kept quiet), each with different
   blame and a present life that justice would damage; justice and mercy each have a cost and someone who gains; the
   wronged may disagree with the custom [IN M7].

## The fairness test (run before review)

1. For each conclusion: three clues, distinct channels, not one person [IN M8].
2. For each node: three leads from different sources [IN M8].
3. Three blind routes reach an ending: one that misses the first clue everywhere, one that skips the richest person,
   one that starts at the last node [IN M8].
4. No single clue bypasses steps by accident; the player does not grasp it all early and then stall on a detail
   [IN M8; IN P10].
5. The journal holds whatever the player must remember beyond a handful of facts [IN M8].
6. A paper player who did not write the case reads only the journal and names each open question [IN M8; OB made].

## Record additions (`shapeData`)

`timeline` (the last day: everyone's whereabouts), `lies` (speaker, false statement, refuted by), `nodes` and
`leads` (from, to), `redHerrings` (each with its refuter), `openQuestions` (the questions the journal carries),
`confrontation` (the exhibits needed, how many convict, what too few gives, the closed run), `endings` (right,
partial, wrong, unsolved); for MISSING `fate` and `trail`; for RECKONING `guiltyParties`.
