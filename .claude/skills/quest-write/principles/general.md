# General principles (every quest)

Binding for `quest-write` and `quest-review`. Each principle ends with its source in brackets, so it can be checked:

| Tag | Source | Section names used in tags |
|---|---|---|
| OB | [owner-bar](../../../../story/design/owner-bar.md): the owner's rules | `bar`, `skills` (Action and the player's skills), `vibe`, `shape` (Shape of a quest and a line), `truth` (Truth and lore), `talk` (People and talk), `made` (How the story is made) |
| MW | [morrowind-level-scripting](../../../../docs/research/morrowind-level-scripting.md) | `§1` to `§6` and the item number |
| OW | [quest-design-open-world-rpg](../../../../docs/research/writing/quest-design-open-world-rpg.md) | `P` Principles, `M` Methods (by name), `A` Anti-patterns, `R` Reviewer checklist |
| ES | [quest-design-elder-scrolls](../../../../docs/research/writing/quest-design-elder-scrolls.md) | `P` Principles, `WS` What the sources establish, `A` Anti-patterns |
| QL | [questline-design](../../../../docs/research/writing/questline-design.md) | `P` Principles, `F` Method fields, `A` Anti-patterns, `D` Notes for the detectives' line |
| AS | [quest-actions-and-skills](../../../../docs/research/writing/quest-actions-and-skills.md) | `P` Principles, `CP` Combination patterns, `FP` Faction action profiles, `V` Variety measures, `A` Anti-patterns |
| CD | [quest-shape-crime-and-deceit](../../../../docs/research/writing/quest-shape-crime-and-deceit.md) | `P` Principles, `MA` to `MF` Methods A to F, `A` Anti-patterns |
| SO | [quest-shape-social](../../../../docs/research/writing/quest-shape-social.md) | `P` Principles, `M1` to `M14` Methods in the order listed, `A` Anti-patterns, `C` Checklists |
| IN | [quest-shape-investigation](../../../../docs/research/writing/quest-shape-investigation.md) | `P` Principles, `M1` to `M8` Methods, `A` Anti-patterns, `D` Notes for the detectives' line |
| TJ | [quest-shape-threat-and-journey](../../../../docs/research/writing/quest-shape-threat-and-journey.md) | `P` Principles, `M` Methods (by shape), `D` Writing directions, `A` Anti-patterns |
| OT | [quest-shape-otherworldly](../../../../docs/research/writing/quest-shape-otherworldly.md) | `P` Principles, `M1` to `M7` Methods, `A` Anti-patterns |
| CC | [choice-and-consequence](../../../../docs/research/writing/choice-and-consequence.md) | `P` Principles, `WS` What the sources establish, `K` The kinds of consequence, `SM` Spellmaking |
| GK | [outcome-kinds](../../../../docs/research/skyrim/outcome-kinds.md) | the table's rows, by kind |

## What a quest may use

A quest is one number moved by what the player does, and talk that depends on that number [MW §1; MW §6.1]. The
closed list is the quest form ([quest-form](../../../../docs/design/quest-form.md)); a step that needs anything
else is rewritten, never scripted [MW §6.10; OB shape].

- **A stage moves** when the player picks a line, takes a named thing, uses or reads a named thing (a door, a lever,
  a book, a body), when a named person or creature dies, or when another quest reaches a stage [MW §6.1].
- **A line or a stage is gated** by a quest's stage, a stored number, faction and rank, a thing held or gold, a skill,
  a person alive or dead, a person's regard, the player's race or sex, and who is speaking [MW §3].
- **A line or a stage does** the next stage with its journal entry and objectives (each with a marker), gives or
  takes things and gold, changes a stored number, a faction, a rank or a regard, locks or unlocks a door, turns its
  speaker hostile, shows a message box, starts a quest, and switches a named person or thing on or off away from the
  player [MW §4.6; MW §6.7].
- **The world per quest** is people placed standing where they are needed, things placed on a surface or in a
  container (with a lock level, a key and an owner where the play needs them), and doors locked or unlocked.
  Nothing is built or moved for a quest [MW §6.8; OB shape].
- **One person per quest may speak first**, standing a few steps from where the player arrives [MW §6.6].

Cut, everywhere: walking into an area, the clock and waiting, being seen or unseen as a quest's own check, scenes,
people who walk, follow, lead or keep a timetable for a quest, anything appearing, vanishing or moving where the
player can see it, music and weather [MW §3; MW §4.4; MW §4.5]. Each dramatic job those did is done like this:

| The job | How it is done |
|---|---|
| a deadline, pressure, "before it is too late" | a state the player finds already true (the boat half sunk, the eggs already dead), said by the people who live with it; and a choice whose cost is named before it is made [ES P13; TJ P6] |
| suspense in a theft or a break-in | an owned, locked thing whose key a person carries: Skyrim's own crime system supplies being seen, the bounty and the guard, and the quest never checks it [CD P11; MW §6.3] |
| a chase, a fight that "breaks out" | a hostile person or creature standing where the player must go, whose death moves the quest; or a line whose result makes its speaker attack [MW §4.6; MW §6.7] |
| an escort, someone who must come along | the person says they will go ahead and is found there; they are switched off where they stood and on at the destination, each away from the player (another interior, or 18,000 units outdoors); the road's danger is a fight on the way [MW §4.5] |
| "find the place" | a named thing at the place that the player uses, reads or takes (a body, a marker stone, a note) [MW §4.4] |
| an event the story needs (a fire, a rising, a raid) | it has already happened and is found, it is told by a witness, or it happens where the player is not and its aftermath is found [MW §6.8] |
| a hand-over, a fetch, a report | a line gated on the thing being held, however it was got [MW §6.3] |
| a finale or a set piece | a hard choice with a named cost, or a hard place (a locked box among armed keepers), never a staged sequence [QL P2; OB shape] |
| timed aftermath ("after three days...") | what the player finds next time: a person gone, a greeting changed, a topic, a door locked, a price; and a later quest's line reading a stored number [OW P9; OB shape] |

## The owner's bar, as craft

1. **Every quest is something the player does with named in-game skills**, and the record names which (One-Handed,
   Two-Handed, Archery, Block, Heavy Armor, Light Armor, Smithing, Destruction, Restoration, Alteration,
   Conjuration, Illusion, Enchanting, Alchemy, Sneak, Lockpicking, Pickpocket, Speech, and Mysticism from Magic
   Expanded). Never talk-to-X-then-Y, never a chore. Why: using the character's skills is the fun [OB skills;
   AS P4; AS A].
2. **A main quest has at least two ways through by different skills**, each able to go wrong in its own interesting
   way, and none is the only way. Why: any build can finish the main quest [OB skills; AS P1; CD P1].
3. **A faction's quests lean on the faction's skills** (`profiles.yaml`), and each faction has drama and tension of
   its own kind: what it fights, who it fights, what it costs. Why: the guild feels real only when its work uses its
   craft [OB skills; OB bar; AS P6].
4. **Action, danger and discovery come before law, custom, procedure and records.** Law and custom are background;
   a climax or a resolution is never a hearing, a ruling, a trial or a negotiation at a table. Why: Black Marsh is
   not a bureaucratic place [OB skills; OB vibe].
5. **Paperwork is rare, kept to the few people and places it truly belongs to** (an outsider's papers, an
   ex-Imperial household's count), **and then it is a thing to steal, burn, swap or alter, never the play.** No
   stage is won by reading, counting, filing or comparing. Why: ledgers and tallies drag every quest towards a desk
   [OB vibe]. The Chainbreakers' count in
   [chainbreakers](../../../../story/design/quests/lines/chainbreakers.md) §3 is the pattern: a leaf in a locked box,
   lifted or swapped.
6. **Morrowind's virtues**: moral ambiguity, each side arguable with a reason of its own, and the world built
   through what people say and want. Why: that is what made Morrowind's stories worth playing [OB bar; ES WS;
   SO P1].
7. **A new player can always tell what is going on**, as it happens. Why: a quest nobody understands is not played
   [OB bar].
   - The first person to speak tells a new player where they are and what the local words mean [OB bar].
   - Before the player is asked to join anything, lines they can choose say what it is, whom it serves, what it
     wants of them and why them, what it pays, and one true reason to hesitate; "not yet" stays open and free
     [OB bar].
   - Prompts and journal entries use only the names the player has been given ("the cutters" until told otherwise)
     [OB bar].
   - A choice between people is named before it is made: the journal or a line says what each option does [OB bar].
   - A choice that a later person will offer is named by the quest-giver first [OB bar].
8. **Everything said is true of the built world.** Why: the world, the places, the dialogue and the quests are one
   thing to the player [OB truth].
   - A thing's place is told by things that do not move, never "next to us" [OB truth].
   - Nothing is described that is not there to see; a place is named for what it is only where something built
     reads as that; a person's stated work is work they are seen to do [OB truth].
   - Nothing is said that the game's systems do not do (no tides) [OB truth; OB shape].
9. **Nothing is levelled.** Danger, thresholds and rewards are fixed numbers; a fight is paired with a reward in
   proportion to its difficulty [OB shape; OB skills; TJ P11].
10. **Anyone can die.** Every line reads sensibly with each named person dead, or the quest names them as one it
    cannot go on without: their death fails it with a journal entry, and a main or faction quest also shows its
    message [OB shape; MW §6.9].

## The premise and the truth

11. **Believable people.** Say the premise in one sentence, then for each person ask what they know and what a
    sensible person in their place would do; if they would act otherwise, change the truth [OW M Plausibility test;
    ES A].
12. **Truth first, as physical events**: who, where, when, how, why, before any stage. Every clue, rumour and lie
    follows from it [OW M Hidden-truth record].
13. **Prepare a situation, not a plot.** The truth and the cast's knowledge are the situation; stages are states the
    player can reach in more than one order [AS P5].
14. **One honest account, and false ones that clues refute.** No key person betrays the player or lies after being
    honest; at most one coincidence [ES P11; ES WS].
15. **Every giver has a motive** from the nine: knowledge, comfort, reputation, serenity, protection, conquest,
    wealth, ability, equipment; record it in `cast[].wants` [OW P6].
16. **Each person speaks from their own column of knowledge**: knows, believes, suspects, hides (and why) [OW M
    Knowledge matrix].
17. **Each option of a choice is argued by the person it concerns**, with a reason of their own held as a record
    fact before any line is written; each side says what the other side winning would cost [OB bar; SO P1].

## The trail

18. **Three clues per conclusion**, in at least two forms (a line, a thing, a place, a body), never fewer because
    one seems obvious [OW P1].
19. **Concept clues say what happened; leads say where to go next.** Tag each clue; every stage the player reaches
    offers leads out, so the player is never stuck [OW P3; OW P4].
20. **Three ways past every chokepoint** (a locked door, a name, a person who must be met), of different kinds: a
    key someone carries, a lock to pick, a Speech check, a price, a fight, a second person who knows [OW P2;
    OW M Chokepoint list].
21. **The player deduces or decides; nobody hands over the answer** [OW R; ES A].
22. **The player can always act on what they have worked out, and always knows why they are asked to act**
    [OW P12].
23. **Topics carry the thread.** A clue is a word another person can answer; topics open by stage, so a
    conversation unfolds rather than dumps; a spent topic answers briefly [ES P4].

## The world and the player

24. **The world does not wait.** Quest people and things stand in the world before the quest starts and can be met,
    killed or taken early; a hand-in is gated on the thing held, so a player who already has it, bought it, stole it
    or took it from a body goes on [ES P5; OW P16; MW §6.3].
25. **Every objective has a marker on its target, and directions are also given in words**: a route by landmarks the
    world really has, a bearing, a word for how far, never a count. A giver who does not know the way names someone
    who does, and the objective points at that person first. A riddle side quest's place alone has no marker until
    the player finds it ([quest-system](../../quest-system/SKILL.md), "Six narrow additions") [OB shape; OB talk;
    ES P1; ES P2; TJ D].
26. **One stage, one step.** Each entry says, first person and past tense, what the player has just done, carries
    forward the names and places still needed, and gives the one step now owed; it never tells a later step or an
    event that did not happen [MW §6.2; ES P3; OB shape].
27. **Urgency is told and found, never timed**: say in a line why this matters now, and let the state the player
    finds show it [ES P13; QL P10].
28. **Danger is fixed and warned of**: two independent signs before any place above the band around it (a person's
    fear, remains, a body) [TJ P11; TJ P3].
29. **A shortcut is flagged** in its prompt, so it is never taken by accident and never strands the player [ES P7].
30. **No pointless lock**: a lock has a reason in the story and a key that someone carries [ES P8].
31. **A talked route settles the matter itself**: a persuasion ends the problem in the line, never with a promise
    the player must then go and keep [OB bar].
32. **A plausible reaction is not always a good one**: if a branch always ends in "kill them", reshape it [ES P10].

## Choices, consequences, rewards

33. **No single right answer**: at least two endings, each with a virtue and a cost [OW P8]. A quest with a choice
    or more than one ending also reads [choices.md](choices.md): what each outcome gives and costs in play.
34. **Stake the choice before it comes, and offer the obvious option, then make it cost** [OW P10; SO P7].
35. **Consequences are things to use**: every ending changes what the player can do or reach (a power, a thing, a
    trader's stock, a trainer, a door, a bed, the next job) and says where the player will meet it; a greeting or a
    stored number is how it is shown and kept, never the whole of it. The delayed kind is a later quest's line
    reading a stored number [OW P9; OW M Choice and consequence table; CC P1].
36. **After an ending, each person left standing greets with their own view of it and its cost**; a greeting or a
    hand-in shared by several endings says only what is true of all of them [OB bar].
37. **The player's method is acknowledged**: a later line names how they did it (the lock, the fight, the word)
    [AS P2; AS P11].
38. **Rewards serve choice, mastery and belonging**: they fit the route taken, prove competence or bind the player to
    people; fixed, proportionate to the risk and tied to the story [OW P18; ES P14].
39. **Signal over noise**: the important fact arrives in one focused moment; no three people repeat one summary;
    detail that does no work is cut [OW P11; OW P19].
40. **No plain fetch, kill or delivery** without a discovery or a turn [OW A; AS A].
41. **Vary the places**: no two quests stage in the same room; each gets a place, a thing or an enemy of its own
    from what the world holds [ES P12].
