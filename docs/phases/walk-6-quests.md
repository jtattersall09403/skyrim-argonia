# Walk 6 (quests): the quest system cut back to Morrowind level

Status: [PROGRESS.md](../PROGRESS.md). The owner's feedback in their own words and the deliverables it asks for:
[walk-6-quests-handover.md](walk-6-quests-handover.md). This file is the plan and is edited as the work goes.
Written 2026-11-12 by the planner session the owner asked for.

## What went wrong, in one paragraph

The owner's walk of the rebuilt opening was "a complete mess": a journal entry described a fire and a rescue that
never happened, people stood still or walked the wrong way, a hut sat sunk in the dock and later turned into a
house, and a new player could not tell what was going on. The quests asked the engine for staged set pieces (people
marching on cue, scenes, areas that fire a stage when walked into, things switched on in the player's sight), and
each of those can go wrong in ways that reading the files never shows. The fault of each thing the owner saw is
written up in [walk-6-post-mortem](../research/walk-6-post-mortem.md) (lane R2).

## The plan, critically

The handover's reading is kept where it holds and changed where a simpler shape does the same job.

1. **The ceiling is a closed list, and the tools cannot express anything outside it.** A rule in a document is not
   enough: the last build broke rules that were written down. A quest becomes **data only**: its stages, journal
   entries, objectives and their markers, its lines with their conditions and results, its things and people. That
   data is one small file per quest in one fixed form (the *quest form*, below). There is no place in the form to
   write a scene, a march, a walk-in area or a script, so a quest above the ceiling cannot be written down, let
   alone built. The gate (`make check`) refuses a quest record that does not fit the form.
2. **No quest has code of its own.** Today each quest line has its own builder program and its own small scripts
   (80 compiled scripts for 11 quests); that is where "built wrong" came from. One generic builder turns any quest
   form into game records, and a handful of generic scripts, written once, carry out the results a line or a stage
   may have (set a stage, give or take a thing, switch a thing on or off, change a number, a faction or a regard,
   show a message). Proving those few scripts once in game proves them for every quest, which is the confidence the
   owner asked for without playing every quest.
3. **The paper playtest plays the game's own records.** A reader turns the built plugin back into the same quest
   form, and the paper game runs on that. Because the designed form and the built form are the same kind of file,
   comparing them names every place the build differs from the design; because the form holds nothing the reader
   cannot model, the paper game never tells the playtester something the real game would not do. The same paper
   game runs on the designed form before anything is built, so a confusing quest is caught while changing it is
   cheap. The playtest is a step of writing a quest, never part of the gate.
4. **A stage's journal entry says only what the player has just done.** Stages move when the player talks to
   someone, takes or uses a thing, or kills something; never because the player walked somewhere or because the
   world was meant to act. A journal entry therefore cannot describe events that did not happen.
5. **What is cut is cut everywhere**, not only in the opening: escorts, people led or leading, events timed by the
   clock, "do it unseen" checks, scenes, music changes, and anything switched on or off where the player can see it.
   A quest that leaned on one of these is re-authored to keep its spirit (the event has already happened and is
   found, is told by a witness, or happens somewhere the player is not).

### The ceiling: what a quest may use

Morrowind's quests are a journal number moved by talk and by a few simple happenings, and talk that depends on that
number. Research note with what Morrowind actually did and Skyrim's matching record for each:
[morrowind-level-scripting](../research/morrowind-level-scripting.md) (lane R1). The closed list:

| Kind | Allowed | Cut |
|---|---|---|
| What moves a stage | a line the player picks (a topic or an answer to a question); taking a named thing; using or reading a named thing (a door, a lever, a book, a body); a named person or creature dying; another quest's stage | walking into an area; a scene ending; the clock; waiting or sleeping |
| What gates a line or a stage | a quest's stage; a stored number; faction and rank; a thing held, or gold; a skill; a person alive or dead; the person's regard for the player; who is speaking | time of day; being seen or unseen; where the player stands |
| What a line or a stage does | the next stage, its journal entry and its objectives with markers; give or take things and gold; change a stored number, a faction or rank, a regard; switch a named thing or person on or off **away from the player** (another cell, or out of sight by distance, checked from the positions); move the player through a door; show a message box; start or end a quest | scenes; any package that makes a person walk, follow, lead or keep a timetable for a quest; moving a person in view; music; weather; anything a script must watch for over time |
| A person speaking first | one person may greet the player by walking up and starting their own line (Skyrim's force-greet, which Morrowind also had), only where the person stands a few steps from where the player must appear, and always with a marker on them and the same line open if the player speaks first | |
| World edits per quest | people placed standing where they are needed; things placed on a read surface; a door locked or unlocked; nothing built, nothing moved, no structure added | new structures, docks, huts, fires, crowds |

### The quest form (the one contract between the tools)

One JSON file per quest, made from the story database's quest record (`tools/questform`, lane A). It holds, and can
hold only: the quest (id, name, kind, how it starts); **stages** (number, journal text, whether it ends the quest and
how, results); **objectives** (text, shown and completed at which stages, and one or more **targets**: a person, a
thing, a door or a place marker); **people and things** (each a placed reference: who or what, where, on or off at
the start, mortal always; a thing may sit in a container); **lines** (speaker, the player's prompt, the spoken text
or, before dialogue is written, its gist, conditions from the allowed list, results from the allowed list, a first
and a last stage); **triggers** (take, use, death, another quest's stage: each names its thing and the stage it
sets, with a prerequisite stage); **who must live** (the people whose death fails the quest, and whether the death
also shows the main quest's message). Results and conditions are closed vocabularies; an unknown word is an error.

### Markers, deaths, the message

- **Markers.** Every objective has a target and the build already refuses one without; the owner still saw none he
  could follow. Lane R3 finds why from the files (the quest not being the tracked one, the compass or the floating
  marker hidden by the HUD mods, a target not switched on) and how Bethesda does it; the kit then makes every quest
  tracked when it gives its first objective and gives every thing to fetch or use a target of its own. Directions
  in dialogue stay.
- **Anyone can die.** No person of ours, and none of Black Marsh & Valenwood's, is essential or protected. A quest
  names the people it cannot go on without; if one dies the quest ends as failed with a journal entry that says so.
  If the person belongs to the main quest, a message box appears once, in our words after Morrowind's ("the thread
  of prophecy is severed"), saying the player may load an earlier save or go on in the world as it now is. One
  always-running quest holds every main-quest person so the message also shows before their quest has begun.

### The opening, small

The player wakes in the barge's hold (kept as it is: the owner liked it) and makes their character. Outside the
hold's door stands the man with the work roll. He speaks first: the player's name is not on his roll, they owe
nobody here, and he wants them off his pier; if they want work he names a place in Lilmoth and a person there. That
person takes the player into the Veiled Reed, the faction that carries the main quest. The quest is three steps
(speak to the man, find the person, be taken in), each with a marker. Removed from the world: the extra dock and its
rope fence, the hut that sat in the water, the burning huts, the camp's march and every person placed for them. The
camp's burning becomes something the player hears of and can go and see the day after, not something staged. The
named place and person are chosen from what Black Marsh & Valenwood's Lilmoth already holds and the story's cast
(lane O, through the quest-write skill), and reported on the owner's issue.

### The paper playtest

- **The game on paper** (`tools/playtest`, lane H): plain code with unit tests. It loads quest forms (designed or
  read back from the built plugin) and the talk of everyone standing in the places involved, keeps the state a
  save would (stages, things carried, numbers, factions, who is alive, what is switched on), and answers a small set
  of commands: look around, open the journal, open the map (the player's position, each active marker's position and
  what it marks), go to a marker, a person or a named place, talk to someone, pick a topic or an answer, take or use
  a thing, fight someone (the playtester chooses to win, lose or walk away; a lock, a pickpocket and a persuasion
  work the same way against the character's skills), wait. Each answer is exactly what the player would see: spoken
  lines, the objective text that comes up, journal entries, things gained or lost, message boxes.
- **The player** is a fresh, separate Claude run started by the tool in an empty folder, able to do nothing but
  send those commands. It is told only that this is an Elder Scrolls game set in Argonia and that it has played
  Skyrim (for a later quest, also a short "what you know so far" built from the journal of the quests before). Its
  brief is a role, not a checklist: play, think aloud at every step, and at the end give its own open take (how it
  felt, whether it understood, whether it was fun, whether it wants to know what happens next, what made no sense);
  a few standing questions come only after that. Three players by temperament: a careful reader, an impatient one
  who skips talk, a wanderer. Its private reasoning and every command and answer are kept as a transcript beside the
  quest.
- **In the recipe, three moments:** on the designed form before dialogue is written (lines shown as gists); after
  dialogue; once on the built plugin, with the designed-against-built comparison. Run again only when what the
  player meets has changed. The comparison and the form check are fast and in the gate; the playtest never is.
- **The owner's page** (lane H2): a private artifact that shows each run as a track through the quest (stages
  reached, where the player went, who they spoke to, where they stalled or guessed), the player's thinking beside
  each step with what the game showed, the closing take, and runs of one quest side by side. It reads the kept
  transcripts, so new runs appear without the page being rewritten.

### Every quest and line authored so far

- **The 11 built quests** (the opening MQ01; MQ03, MQ04, MQ05; the Chainbreakers' BC01 to BC03; the Night-Reed's
  TG01 and TG02; the two local quests LQ25 and LQ30) are re-authored to the ceiling with quest-write and
  quest-review, rebuilt by the generic builder, and played on paper. Their old builders, checks and scripts are
  deleted.
- **The 38 other quest records that have stages** are compiled to the quest form; each that does not fit is
  re-authored on paper to fit (records only).
- **The lines and factions** (the main line's outline, the faction lines, the roughly 660 quests that are only a
  premise): one review that lists every premise and set piece that needs more than the ceiling and writes its
  rowed-back version into the outline, so nothing above the ceiling is waiting to be written later.
- **The recipes**: quest-write, quest-review, [blocks](../design/blocks.md) and
  [quests-on-a-world](../design/quests-on-a-world.md) are rewritten whole as clean recipes at the ceiling, with the
  paper playtest as a step.

## The lanes

Delivery lanes are Opus 5.5 at medium effort; code review is Fable 5.2 at medium. Each lane works in its own
worktree and is landed by the lead. Nothing is tested in game by an agent; nothing is deployed while the owner
streams.

| Lane | What | After | State |
|---|---|---|---|
| R1 | Research: what Morrowind-level scripting is in practice, and Skyrim's record for each piece | - | todo |
| R2 | The post-mortem: the cause of each fault the owner saw in walk 6 | - | todo |
| R3 | Research: why no marker could be followed; how Bethesda tracks a quest and marks things; force-greet; how many people are essential or protected | - | todo |
| A | The quest form: its schema, the compiler from a quest record, the form check in the gate, the report of which of the 49 staged records fit | R1 | todo |
| O | The opening re-authored as a record (quest-write, quest-review), with its place and person | R1, R2 | todo |
| K | The generic builder and the generic scripts; markers; mortality and the message; force-greet; the block test quest rebuilt on them; old builders and scripts removed as quests move over | A, R3 | todo |
| H | The paper game, the plugin reader, the designed-against-built comparison, the player runner and transcripts | A | todo |
| H2 | The owner's page for playtest runs | H | todo |
| Q1 to Q4 | The other ten built quests re-authored and moved to the form (main quest; Chainbreakers; Night-Reed; locals), each played on paper as designed | A, O | todo |
| S | The 38 unbuilt staged records fitted to the form; the lines-and-factions review | A | todo |
| D | Dialogue for what changed (dialogue-write with the Morrowind find step, text-review) | O, Q | todo |
| I | Integration: one build of the merged tree, scripts compiled, every read-back, the comparison at zero differences, playtests on the built plugin, fixes | all | todo |
| C | Code review of the new tools (Fable 5.2) and its fixes | K, H | todo |
| W | The recipes rewritten; the owner's walk check posted; deploy when no stream is live | I, C | todo |

## What the owner will be asked to check

Kept short, in [owner-walk-checks](../owner-walk-checks.md) when posted: the generic scripts' block test (each
result happens once); the opening from a new game (the man speaks first; three steps; a marker each); a marker on
the compass and the map for an objective and for a thing to fetch; killing a main-quest person shows the message;
one re-authored quest of each line. Everything else rests on the gate, the comparison and the paper playtests.

## Rulings by the planner (not the owner's; challenge any on the issue)

- Walk-in areas no longer move any quest, although the engine does them reliably: with them gone, no journal entry
  can run ahead of what the player did, and Morrowind's quests did without them.
- Escorts and "follow me" are cut, although Morrowind had them: they were its weakest quests, and ours failed twice.
- The playtester is a separate Claude run with one tool, not a sub-agent, so that it truly cannot read the story or
  the code. Sonnet 5.5 by default for cost; any model can be named per run.
- Old saves are not kept working across this change: quests are rebuilt from nothing and a new game is needed.

## Measured

(filled in as lanes land)
