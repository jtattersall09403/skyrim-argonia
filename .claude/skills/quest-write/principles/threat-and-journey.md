# PREDATOR, CONTAMINATION, EXPEDITION

Read with `general.md` (which holds the source tags' key). A threat is fixed: its band, its place and its reward
never scale to the player [OB shape; TJ A].

## PREDATOR

1. **A puzzle about knowledge before a fight.** Write the creature's habit first (its territory, what draws it, what
   it eats, what it fears; never an hour or a tide, which no step may depend on); the fight is the last stage and the
   clues decide how well the player enters it [TJ P1; TJ M].
2. **Traces, account, lair**: traces in the world (a body, a torn net, a bait bucket: placed things the player can
   use or take), the community's account with one wrong belief, and the lair that confirms it [TJ M].
3. **Every clue changes a choice**: which skill to bring, where to fight it, whether to fight at all, whom to tell.
   Record "clue, where, the choice it changes, who else knows"; drop a clue with no choice [TJ P2; TJ M].
4. **Say why it is unsolved, and declare a fair twist**: the wrong culprit, a creature provoked, someone feeding it, a
   solution that is not killing, a remedy that is a trade [TJ M].
5. **A way that is not a fight** whenever the creature is above the band the player is likely to be ready for: the
   people who feed it faced, the bait taken away, a keeper paid [TJ M].
6. **A weak sample of the threat**, placed on the way, that the player meets unprepared and survives; it teaches the
   habit [TJ M].
7. **Warn, then let the player choose**: remains and people's fear before the lair [TJ P3].

## CONTAMINATION

1. **Source, spread, sign, cure**, all in the truth [TJ M; TJ P5].
2. **The place shows it before anyone says so**, by what is placed there to see (the dead fish on the bank, the sick
   lying in their beds, a jar of the bad water) [TJ M; OB truth].
3. **First ill, last well**: an order of households in the truth, consistent with exactly one way it spread [TJ M].
4. **A misdiagnosis**: two plausible sources, one confirmed by a test the player can make (a sample read with
   Alchemy, a thing taken from upstream); each side favours the wrong cause that suits it [TJ M].
5. **The pressure is found, never timed**: the sick are already sick and the dead already dead when the player
   arrives; what worsens follows the player's own choices, named before they are made [TJ P6; ES P13].
6. **The cure needs gathering, a journey or a trade** (often an EXPEDITION inside it), and the changed world stays:
   a person who recovers stands up, one who did not is gone [TJ M].

## EXPEDITION

1. **Rumour, route, gate, prize, return**, each a stage [TJ M].
2. **Preparation hints from three sources**: someone who went before, the threshold itself (the remains of an earlier
   party, a body to search), and a trader who will not sell without a warning [TJ M; TJ P3].
3. **Choose ground whose approach hides the goal**: a large landmark at the far end, something midway that blocks the
   view, small obstacles for tempo; never the goal in a straight line from the start [TJ P8; TJ A].
4. **The point of no return is flagged twice**: in a line before, and by the place itself [TJ M].
5. **Failure is not only death**: a thing lost, a way closed, a person left behind [TJ M].
6. **The return changes something** in the world or in a person [TJ M].
7. **Leads chain**: each find names where the next can be found, because players read out of order [TJ P7; TJ M].

## Directions

Every place to reach has a marker and, in words: a starting point the player has seen, a bearing in the world's
terms, a word for how far (never a count), one hard-to-miss landmark on the way and one that confirms arrival, a sign
of going too far, and the other way if water or a climb changes it. From the destination, one named landmark is in
sight [TJ D; OB talk].

## Anti-patterns

A creature whose only clue is its location; a contamination cured by fetching one named thing with no cause shown;
a warning that is only the word "dangerous"; danger with no earlier sign; a twist made by reversing a person's
earlier true statement; a hidden timer; dialogue that repeats the journal [TJ A].

## Record additions (`shapeData`)

- PREDATOR: `habit`, `whyUnsolved`, `twist`, `clueChoices` (clue, where, choice, who else knows), `nonCombat`,
  `weakSample`.
- CONTAMINATION: `source`, `spread`, `sign`, `cure`, `firstIllLastWell`, `misdiagnosis`, `stakes` (what the player
  finds already lost, and what each choice will cost).
- EXPEDITION: `rumour`, `route` (in words), `gate`, `prize`, `return`, `prepHints` (three), `pointOfNoReturn`,
  `nonLethalFailure`.
