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
  If the person belongs to a major quest (the main quest or a faction's line; owner, 2026-11-12), a message box
  appears once, in our words after Morrowind's ("the thread of prophecy is severed"), saying the player may load an
  earlier save or go on in the world as it now is. A minor side quest only ends as failed, with its journal entry
  and no message. One always-running quest holds every major-quest person so the message also shows before their
  quest has begun.

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

| Lane | What | State (2026-11-13 00:40 UTC) |
|---|---|---|
| R1 | Research: Morrowind-level scripting in practice | done: [morrowind-level-scripting](../research/morrowind-level-scripting.md) |
| R2 | The post-mortem of walk 6 | done: [walk-6-post-mortem](../research/walk-6-post-mortem.md) |
| R3 | Engine facts: markers, force-greet, mortality, generic scripts | done: [quest-form-engine-facts](../research/skyrim/quest-form-engine-facts.md) |
| A | The quest form: schema, compiler, checks, the gate's ratchet | done: [quest-form](../design/quest-form.md) |
| O, D1 | The opening (MQ01) and the quest after it (MQ03) re-authored, with dialogue, played on paper | done |
| Q1 to Q4 | MQ04, MQ05; the Chainbreakers' three; the Night-Reed's two; the two local quests: re-authored to the form | done (11 of 49 staged records fit) |
| S | The 38 unbuilt staged records rowed back; the lines-and-factions review | done: story/design/quests/review/walk6-ceiling.md |
| K | The generic builder, generic scripts (68 of 68 compiled), reader, mortality, markers on, the block test as forms | done |
| H, H2, H3 | The paper game, the runner, the comparison, the owner's page | done: [paper-playtest](../design/paper-playtest.md), https://claude.ai/artifact/QjrYTSBXYjMrCvz56V5uDP |
| D2a to D2c | Dialogue for the other nine quests, played on paper | running |
| I1 | Compiler and record gaps the eleven quests found (locks, owners, carried things, a failed check's own words, the chain) | running |
| I2 | Old per-quest builders retired; every quest built from its form; read-back and comparison at zero | running |
| H4 | The paper game: containers, locks, theft, starting a later quest from true state, a reach check | running |
| C | Code review of the new tools (Fable 5.2) and its fixes | todo |
| W | The skills restructured as one set with the cleared findings; the owner's walk check posted; deploy when no stream is live | todo |

## The skills as one system, learning from the paper players (owner, 2026-11-12)

- **The loop.** Each paper player's finding is kept with the run. When a fix clears it (a later player is no longer
  confused or bored at that point), the class of fault is written into the recipe that produced it, as a plain
  instruction of how to do it right; a finding that is not yet cleared changes nothing in a skill. The findings and
  what each became are listed in "Measured" below until they are folded in.
- **The quest design research is part of the set, visibly.** Ten research notes on quest design (open-world RPGs,
  the Elder Scrolls, quest lines, actions and skills, five quest shapes: `docs/research/writing/`) are distilled
  into `quest-write/principles/` and routed by quest shape (`shapes.yaml`); quest-review reads the same files. Found
  2026-11-13: only one principle file names its research; nothing at the level of a whole story line pointed to it;
  the principles predate the ceiling (a `deadline`, an `escape`, `checkpoints`); and the sections `shapes.yaml`
  makes a record hold are themselves bureaucratic (`ledger`, `voteLedger`, `records`, `bondageSheet`), which pushes
  every writer towards ledgers. Lane W re-distils each principle file against its research note, the ceiling and
  [owner-bar](../../story/design/owner-bar.md), links each to its source, and renames or drops those sections.
- **Lines true of the built world** (owner, 2026-11-13; lane T, with lane W). Three guards, each in the recipe:
  the writer's brief holds only facts measured from the built world around the speaker (what stands there and what
  it reads as, by fixed landmarks; what the speaker's routine actually has them doing; what the game's systems do),
  each marked as fixed or as moving with someone's routine, and a line may place a thing only by fixed things; a
  truth reader, separate from the style reader, is given each line beside the measured facts of its speaker's
  surroundings from the read-back of the built plugin and lists every claim about the world the facts do not
  support; and the paper game's `look` shows the player what is really there, so a line that describes something
  absent is caught by the player too.
- **The skill set, restructured** (lane W, after the builder and the first built playtests): the quest skills become
  a connected set, each a clean recipe that names the skill before it and after it, so an agent entering at any
  point knows the whole path. Planned shape, to be settled by what this phase teaches: `quest-system` (the map of the
  set, the ceiling, the quest form, which skill to use when); `story-line` (the overall story of the main quest or a
  faction line, written by Fable inside the ceiling); `quest-write` split by kind of quest where the kinds really
  differ (a talk-and-choice quest, a fetch or theft, a hunt, an induction into a faction); `quest-review`;
  `quest-playtest` (the paper playtest: when, how to read a run, what to do with a finding); `quest-build` (records
  to the form, the generic builder, the comparison, the owner's check); `dialogue-write` and `text-review` as they
  are, linked in. [quests-on-a-world](../design/quests-on-a-world.md) stays the one overview and points at them.

## After this phase (owner, 2026-11-12)

Once everything above is delivered, its lessons learned and the skills updated, this session also owns and delivers
the new world phase that is the first pass of fitting the authored quests to the new world, using the updated
skills. Its brief is minimal, so its plan is built out in its own phase file first (the owner's words kept as
written, detail appended below them).
The owner's bar for it: the quests and story must not feel "patched or shoehorned" into the new world but
"really naturally and deeply integrated with it", keeping the factions and the spirit; there is creative licence to
rewrite and re-author so it reads as "a really nicely written exciting story throughout that any elder scrolls fan
would fall in love with"; and every quest uses in-game skills, which is "really key to the fun".
The overall story of the main quest and of each major faction is written by Fable, knowing the quest rules and the
ceiling, aiming at what Morrowind achieved inside minimal scripting: storytelling, deep world building, compelling
lines, moral ambiguity and real conflict of several kinds.
Before any quest of it is written, the story itself is read on paper (the owner's idea, 2026-11-12): fresh readers are
taken through it one quest at a time as a player would meet it, saying at each step what they think is going on, whom
they trust, what they expect and what they would choose; new readers every round; a separate reader checks each
chapter can be built at the ceiling. Readers are evidence, not votes. The loop stops when a round can retell the
story, wants the next chapter, splits on the conflicts meant to be ambiguous, and raises nothing new the author
agrees with.
Rounds never chase each other (owner, 2026-11-12): in each round every reader reads the same version (the players
and the deliverability reader together), the author gathers all their findings and makes one coherent set of changes
that answers them at once inside the ceiling, and the next round's fresh readers judge that set whole. No change is
made for one reader alone. Each reader's persona is an honest player who is a little hard to please and says so
plainly, not a critic paid to find fault.
The vibe binds the rewrite (owner, 2026-11-12; [province-vibe](../../story/design/province-vibe.md)): tallies, rolls,
ledgers, paperwork, hearings and procedure are rare, kept for the few people, factions and places they truly belong
to (the lead's judgement); quests lean on doing things, of many kinds, anchored on the variety of
the game's skills, not only fighting. Any build can finish the main quest; each faction's line leans on its own
skills.

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

- **Why no marker could be followed:** our own stack setting wrote `bShowQuestMarkers=0` and
  `bShowFloatingQuestMarkers=0` (a 2026-11-07 setting, "Morrowind's way"); no HUD mod hides them; no quest of ours
  made itself the tracked one. Both are reversed in the build.
- **The paper playtest, first use (the designed opening, three players, before dialogue):** all three followed the
  chain and wanted to know why they were spared; all three said joining the Reed "felt hollow" and that people
  showed under template names. After the join was given six optional topics and the lines were written, the
  confirming player asked four of them and could say who the Reed are and why they joined. A run costs about
  $0.04 to $0.07 and under a minute.
- **What the paper game caught that reading did not:** MQ03's jar, key and lockpicks were not in the form at all;
  a failed persuade showed the success line; a gated start line had an ungated copy; MQ04 was no longer started by
  MQ03; placements nothing named were dropped (MQ05's wasps).
- **Skills lost for now, to be restored once the form carries locks and owners:** the Chainbreakers' three quests
  turn only on Speech or gold (their thefts were cut because the form had no owner or lock).

### Cleared findings waiting to be folded into the skills (lane W)

Each was raised by a paper player, fixed, and not raised by the next player.

- (MQ01) Before a player is asked to join anything, lines they can choose tell them what it is, whom it serves, what
  it wants of them and why them, what it pays, and one true reason to hesitate; "not yet" stays open and free.
- (MQ01) The first person to speak tells a new player where they are and what the local words mean, in their own
  voice and a few sentences.
- (MQ04, MQ05) After an ending, a person greets with their own view of it and its cost, never "I have nothing to add".
- (MQ04, MQ05) A choice between people is named before it is made: the brief or journal says what each does.
- (MQ04) A line that points to a topic ("ask me who...") uses the words the next topic answers.
- (MQ04, MQ05) Only the name the player already has is used in lines, prompts and journal (the player says "the
  cutters" until told otherwise).
- (MQ04, MQ05) Each person's first line says who they are in a clause and glosses our words the first time.
- (all) A speaker's brief gives every person's sex.
- (tools) A lane keeps its scratch in a folder of its own and deletes only that; lanes share the session's scratchpad.
- (BC01) A talked route is an argument that settles the matter itself, never a promise the player must then keep.
- (BC01, BC02) A line names only where its speaker stands as the player sees it: no room or wall the placement lacks.
- (BC02, BC03) Each option of a choice is argued by the person it concerns, with a reason of their own, held as a
  record fact before the lines are written; each side states what the other side winning would cost.
- (BC01) A choice offered by a later person is named by the quest-giver first, or players never find it.
- (BC01 to BC03) A hand-in or greeting shared by several routes or endings says only what is true of all of them.
- (not cleared, held open) Four of four players made the same choice in BC02: a choice everyone makes one way is not
  yet a choice. The Chainbreakers' rewrite owes it.

