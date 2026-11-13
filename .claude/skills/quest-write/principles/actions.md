# Actions: what the player does, by skill

Read for every quest, with `general.md` (which holds the source tags' key). An action is a use of one of the
player's skills: Skyrim's eighteen (One-Handed, Two-Handed, Archery, Block, Heavy Armor, Light Armor, Smithing,
Destruction, Restoration, Alteration, Conjuration, Illusion, Enchanting, Alchemy, Sneak, Lockpicking, Pickpocket,
Speech) and Mysticism from Magic Expanded. Swimming and climbing are movement: they take the player somewhere and
never win a stage [OB skills]. The catalogue of uses, each one the quest form can deliver, is `skill-uses.yaml`.

## The principles

1. **A quest is a problem, not a puzzle, and has more than one way through**, each keyed to skills, things and
   people [AS P1; CD P1].
2. **Guide and attract; never chain.** Doing the only possible thing, then the next only possible thing, is not
   play [AS P4].
3. **Plan the ways through as a small fixed set**: two or three approaches at the crux, each on a different skill
   family, rather than open-ended freedom [AS P3].
4. **A check is a fixed threshold in the world, and failure keeps the game going.** A failed check closes that
   route with its own written refusal and leaves another open; a broken pick is another try; a check may stay
   closed until the player returns stronger [AS P7; SO P8; OB shape].
5. **Each quest teaches and rewards a way of playing** [AS P8].
6. **The game recognises how the player played**: a stored number set by the route is read by a later greeting or
   line [AS P2; AS P11].
7. **Two skill families at least in any quest bar a short job; no more than one pure-talk step in a row; two or three
   approach slots at the main problem** [AS V].
8. **Escalate along a line**: the first quest uses one family, middle quests combine two, late quests combine three
   and take away the player's safest tool [AS CP].
9. **A use the quest form cannot deliver is not written**: no spying on a routine, following, disguise, repairing a
   structure, a chase, a defence against arriving waves [AS A; MW §6.10].

## Patterns at the ceiling

A pattern is two to four uses from at least two families; fill it with a place, a cast and a stake [AS CP].

- **Gate and choice**: one goal, three ways in: pick the lock, lift the key from the person who carries it, talk or
  pay the keeper, or fight the one who stands in the way. Each costs something different [AS CP 1].
- **The swap**: get into an owned, locked place, take the thing and leave another in its place (a take moves the
  quest; the stage takes the false thing from the player) [AS CP 2; chainbreakers §3 BC01].
- **Dive and return**: learn from someone where the thing lies, cross deep water (Alteration's water-breathing or the
  player's own breath), open the box on the floor, and meet whoever waits on the bank [AS CP 5].
- **Trade the trade**: buy a thing, find it is not what was sold, recover the price by Speech or by force [AS CP 7].
- **Mirror**: two people want the same thing done by opposite means; the player chooses whose way [AS CP 10].
- **Gone ahead**: a person who must reach a place goes ahead and is found there; the danger of the road is a fight
  on the way [AS CP 6; MW §4.5].

## Drawing the plan

1. **Draw an action plan before the truth.** Run `python3 .claude/skills/quest-write/action_plan.py --profile <line
   key> --band <D0..D5> --shapes <SHAPE,...> --line <dir of records already in the line or packet>`. It proposes
   plans on the primary shape's beats (find, get there, the crux as two approaches, resolve) from `skill-uses.yaml`,
   weighted by the line's profile and away from what the line already uses. Pick one, adapt it or write your own
   from the catalogue; record it as `actionPlan` with the reason [AS V].
2. **Then write the truth so the actions follow from it**: a lock needs something worth locking and someone who
   carries its key; a fight needs someone with a reason to stand there [AS P5; OW M Plausibility test].
3. **Every stage that is not an ending has an action** (`skill`, `use`, target, setting) or approaches that each
   have one. Speech counts when it persuades, intimidates, bribes, shows a thing or accuses, not when it only
   listens. A stage whose only act is hearing the task, handing over what is held, reporting back or going through
   the door the journal names carries none [AS V; OB skills].
4. **Each use carries its world needs** (`skill-uses.yaml` `uses`): the hostile and its band, the lock and its level,
   the key and who carries it, the owner; they become `things` and `placements` rows, so the world holds them
   [AS A].

## Profiles

`profiles.yaml` holds one profile per line (`quest_line` row; key = the line id's last part) and the planned
`detectives`. A profile names the line's signature skills (most of its steps), its support skills, and what is rare
for it, so that a player could tell the faction from any three of its quests [AS FP]. A local quest takes `local`
and leans by its place: its danger band, its water and heights, its people's work.

## Anti-patterns

The fetch chain (talk, go, talk, go, report); a skill label with no skill used; a single required skill with no
other route; persuasion that is tried option by option until one works; one verb padded with twelve enemies instead
of one good fight; a consequence nobody sees [AS A].
