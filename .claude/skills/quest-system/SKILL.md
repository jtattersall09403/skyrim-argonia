---
name: quest-system
description: The map of Argonia's quest skills. What a quest of ours is (the ceiling, the one quest form, who can die, markers, truth of the built world), the order of work from a story line to the owner's walk check with the skill for each step, who writes what, how review rounds converge and how the skills learn. Read it first, before writing, reviewing, playtesting or building any story line or quest.
---

# The quest system

Every quest skill is one step of one path. This page is the path; each step's skill holds the recipe for that step
and names the step before and after it. An agent entering at any step reads this page first.

## What a quest of ours is

**Data in one fixed form.** A quest is one JSON file in the quest form
([quest-form](../../../docs/design/quest-form.md)): its stages and journal entries, objectives with targets, the
people and things it places, its lines with their conditions and results, its triggers and who must live. It is
compiled from the quest's record in the story database, built into the plugin by one generic builder, read back from
the built plugin into the same form, and played on paper from that form. No quest has code of its own: a handful of
generic scripts, written once and proven once, carry out every result.

**The ceiling** is Morrowind's level of scripting: a journal number moved by talk and a few simple happenings, and
talk that depends on that number ([morrowind-level-scripting](../../../docs/research/morrowind-level-scripting.md)).
It is a closed list, and the form has no field for anything outside it:

| Kind | A quest may use |
|---|---|
| What moves a stage | a line the player picks (a topic, or an answer to a question); taking a named thing; using or reading a named thing (a door, a container, a book, a body); a named person or creature dying; another quest reaching a stage |
| What gates a line or a stage | a quest's stage; a stored number; faction and rank; a thing held, or gold; a skill; a person alive or dead; a person's regard for the player; the player's race or sex; who is speaking; whether they have spoken before |
| What a line or a stage does | the next stage, its journal entry and its objectives with markers; give or take things and gold; change a stored number, a faction or rank, a regard; switch a named person or thing on or off away from the player (in an interior other than the line's speaker's or the thing's, across the line between inside and outside, or 18,000 units from it outdoors); lock or unlock a door; give the player a container's contents; show a message box; start a quest; (a line only) turn its speaker hostile |
| A person speaking first | one person per quest, standing a step from where the player arrives, with a marker on them and the same line open as a topic |
| The world per quest | people placed standing where they are needed, at fixed levels; things on a measured surface or in a container (with a lock, a key and an owner where the play needs them); doors locked or unlocked |

In a quest's record a line only moves a stage, and the stage it moves to does everything else
([buildable.md](../story-line/buildable.md) §2). Nothing else exists: no stage moved by walking into an area, the clock, waiting or being seen; no scene; nobody who
walks, follows, leads or keeps a timetable for a quest; nothing appearing, vanishing or moving where the player can
see it; no music or weather; nothing built or moved in the world; no script of a quest's own. A step that seems to
need one is rewritten: [principles/general.md](../quest-write/principles/general.md) "What a quest may use" gives
the way each such dramatic job is done inside the ceiling.

**Six narrow additions**, each used only as stated here and only once its block is proven
([blocks](../../../docs/design/blocks.md), "Blocks owed"):

| Addition | Only for |
|---|---|
| one staged ending scene: a fade to black, the ending's music and named things switched in view, then messages | a line's ending vision (the main quest's three endings) |
| a choice on a message box's buttons, each button setting a stage | a line's final choice (the Eye's three endings) |
| a named ally called to the player's side by one power and sent away by another | an ending's reward (Cuts-the-Old-Knot in the Give ending) |
| a stage that kills one named person | an ending that costs that person's life (the Eye in the Use ending) |
| an objective with no marker until the player reaches its place, the journal then saying they guessed right | a side quest given as a riddle |
| a sick Hist's bark darkened by our recolour tool | the look of a sick Hist |

**Anyone can die.** No person of ours or of Black Marsh & Valenwood is made unkillable. A quest names the people it
cannot go on without; if one dies the quest fails with a journal entry, and a main or faction quest also shows its
kind's message once (load an earlier save, or go on in the world as it now is).

**Every objective has a marker**, save a riddle side quest's place before it is found. Every shown stage has an
objective with a target switched on; the quest becomes the tracked one with its first objective. Directions in words
are given as well, never instead.

**Everything said is true of the built world, by how it is made.** A quest never describes a world; it is written
onto one. Each step takes its facts from what exists at that step and passes on only what the next can keep:

- *A story* names places by what the world's data says they are. Anything physical it needs that the data does not
  hold (a locked house, a shrine, a wreck, a pen of beasts) is not written into the story as fact: it is listed as a
  **need of that place**, in words a place can be built to (story-line, "What each quest needs of its places").
- *A place's record* takes those needs as promises, and the place is built to them; the build checks each promise
  is there and reads as what it is called (`place-build`). A need the place cannot meet goes back to the story,
  which changes.
- *Reads as* is judged from the player's side. The player knows only what the game shows: what a thing looks like,
  the names the game puts on doors, rooms, map markers and things, what stands there, and what people have told
  them. Deciding in a record that a house is the hatching shed tells the player nothing. So every promised place
  and thing carries how the player will know it, and it is tested by sight: a fresh reader given only what the
  player would see and be told there (the surroundings sheet and the game's labels, never our own names for
  things) is asked what the place is; if they do not say it, the promise is not kept.
- *A quest record* is written only for places that are built, with every person and thing placed at a spot measured
  from the built place.
- *Dialogue* is written from the surroundings sheet of each speaker (what stands around them in the built place,
  each fact fixed or moving): lines describe only what the sheet holds and place things by what does not move.
- *The truth reader* (text-review) and the paper player's `look` are the last check, not the method.

So a story may be written before its places are built; a quest's record and its words may not. Journal entries say
only what the player has just done; nothing is said that the game's systems do not do.

## The order of work

| # | Step | Skill | Leaves behind |
|---|---|---|---|
| 1 | The story of the main quest or a faction's line | [story-line](../story-line/SKILL.md) | a line story read on paper: each quest an outline with its sketch, passing `python3 -m tools.questform sketch` |
| 2 | Each quest as a record that compiles to the form | [quest-write](../quest-write/SKILL.md) | the record in the database; its form passing `check` and `reach` |
| 3 | A fresh review of the record | [quest-review](../quest-review/SKILL.md) | findings; nothing blocking left |
| 4 | The designed quest played on paper | [quest-playtest](../quest-playtest/SKILL.md), moment 1 | runs kept; findings answered in the record |
| 5 | The quest's dialogue, then its review | [dialogue-write](../dialogue-write/SKILL.md), [text-review](../text-review/SKILL.md) (its style reader, and its truth reader against the speaker's measured surroundings) | lines in `story/data/quest_lines/`; review hits applied |
| 6 | The written quest played on paper | quest-playtest, moment 2 | runs kept; findings answered |
| 7 | Records into the game | [quest-build](../quest-build/SKILL.md) | the plugin seeded, read back, compared to zero, checked |
| 8 | The built quest played on paper | quest-playtest, moment 3 | runs kept |
| 9 | The owner's walk check, then deploy | quest-build, last steps | an owner check posted; deployed when no stream is live |

- **A minor quest** (one place's people, no line) starts at step 2 from a premise; steps 3 to 9 are the same.
- **A whole line** runs step 1 once, then steps 2 to 8 per quest in the line's order, so each later quest is played
  with the earlier ones' state (`--after`).
- **Going back.** A finding goes to the step whose output holds the fault (quest-playtest says whose each finding
  is), and every step after it is run again only where what the player meets changed.
- **Settlement talk** (everyone a player can walk up to, not only a quest's people) is [talk-write](../talk-write/SKILL.md),
  per settlement; a quest's people get their lines in step 5.

## Who writes what

- **Fable writes the overall story** of the main quest and of each major faction (step 1), knowing the ceiling, so
  nothing undeliverable is written.
- **Lanes build quests from it** (steps 2 to 8), one quest or one line per lane, each in its own worktree. A quest
  writer turns an outline into a record without inventing; a gap in the outline goes back to the story's author.
- **Readers and players are fresh agents** who see only what their step allows (quest-review: the record and the
  world; paper players: the game; story readers: the story as a player meets it), never the author's reasoning.
- **The owner judges look and fun in game**; agents never test in game.

## How rounds converge

Every review step (story readers, quest reviewers, paper players, text readers) runs in rounds, and rounds never
chase each other:

1. In one round every reader reads **the same version**.
2. The author gathers **all** their findings before changing anything.
3. The author makes **one coherent set of changes** that answers them together, inside the ceiling; no change is made
   for one reader's taste alone.
4. The next round's **fresh readers judge the set whole**.

Readers are evidence, not votes: agreement across readers is a finding, one reader's preference is not, and a
reader's call on look goes to the owner instead. Each persona is an honest player who is a little hard to please and
says so plainly, never a critic paid to find fault. A round ends the loop when it raises nothing blocking and
nothing new the author agrees with.

## Where the bar and the research live

- [owner-bar](../../../story/design/owner-bar.md): what the owner wants quests, story and writing to be. Every
  writer and reader reads it first.
- [province-vibe](../../../story/design/province-vibe.md): the province's mood, cited to the lore; `story/lore/`:
  the lore and the agreed extrapolation that every world call cites.
- **The quest design research** (`docs/research/writing/`: open-world RPGs, the Elder Scrolls, quest lines, actions
  and skills, five quest shapes) is distilled into [quest-write/principles/](../quest-write/principles/general.md),
  routed by quest shape ([shapes.yaml](../quest-write/shapes.yaml)). Each principle ends with its source tag, so it
  can be checked against its note; story-line, quest-write and quest-review all read the same files.

## How the skills learn

A finding from a paper player, a reader or the owner changes the work at once, but changes a skill only once a fix
has cleared it: the next players or the owner do not meet the fault again. Then the class of the fault is written into
the recipe that produced it (a principle file for a design fault, dialogue-write for a wording fault, quest-build for
a build fault) as a plain instruction of how to do it right, with its one-line reason. A finding not yet cleared
changes no skill. Every skill stays a clean recipe: the rule is stated, never the story of how it was learnt.

## Working as lanes

- One lane per quest, line or tool change, in its own worktree, landed by the lead.
- A lane keeps its scratch in a folder of its own (under the worktree's `out/`) and deletes only that folder, since
  lanes share the session's scratch space.
- Long jobs (a seed, a set of paper runs) run under `tooling/job_guard.sh`.
