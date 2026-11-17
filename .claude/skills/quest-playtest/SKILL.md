---
name: quest-playtest
description: Play an Argonia quest on paper with a fresh headless player who knows nothing of it, milestone by milestone, to prove the player always knows what is going on, what they are expected to do next and what options they have. Run at three moments (the designed record before dialogue, after dialogue, the built plugin), grade each milestone against the record's information plan, send each miss back to the writer, and loop until a run passes. Use after quest-write writes or changes a record, after its dialogue is written, and after quest-build reads it back.
---

# Playing a quest on paper

A quest is played in words by a player who must say, at every milestone, what they think is going on and what they
will do next. The test is one thing: **does the quest give the player what they need, at the point they need it**,
so they can follow the plot, understand what is happening and choose their own next step. It never judges whether
the quest is good, fun or to anyone's taste, and the player plays as no persona: the owner judges those. It never
tests navigation, looks, combat or timing either; the owner does those in game. The path is in
[quest-system](../quest-system/SKILL.md). Before this: [quest-write](../quest-write/SKILL.md) (moment 1),
[dialogue-write](../dialogue-write/SKILL.md) and [text-review](../text-review/SKILL.md) (moment 2),
[quest-build](../quest-build/SKILL.md) (moment 3).

## 1. What a milestone is, and what is graded

A **milestone** is every point where the journal changes: the quest starts, a stage is shown, an ending is reached.
At each one the game stops the player and asks four questions before it lets them act:

1. What is going on? (who they work for, what has happened, why it matters, as far as they know)
2. What are you expected to do next, and where?
3. What options do you have for doing it? (the ways through they can see, and any choice in front of them)
4. Is there any word, name, person or thing you do not understand? Do you know how you could find out?

Each shown stage of the record has an **information plan** (quest-write §3a; `information` in
[quest-record](../quest-write/quest-record.md)): `going`, `next`, `ways`, written by the writer before any run. The
grade sets the player's answers beside it:

- **Pass** at a milestone: the answers to 1 to 3 hold every point of `going`, `next` and `ways` in substance (their
  own words; a detail they could look up in the journal is not required by heart), and nothing they believe is
  false. Every term they name under 4 is either explained on the path, or offered as a topic they saw and could
  pick.
- **Miss**: a point of the plan they do not have, a wrong belief, a next step they cannot name, a way through they
  did not see, or a term with no way to learn it.

A player who cannot say what the line's central things are (in the main quest, the Eye of Argonia and the Root)
or whom they work for misses, whatever the stage's plan says. A question the plot keeps open on purpose (why the
Unbound seal the trees, what the Eye truly does) is no miss when the player names it as open.

A run **passes** when every milestone on the way it played passes; a run that only completes has not passed until
each milestone is graded. The quest passes when a run passes on each way
through and at each choice (section 3).

## 2. The three moments

1. **The designed record, before dialogue**: `python3 -m tools.playtest record <record.yaml>`. The game plays the
   record's YAML view directly, so a record whose places are not yet in the story database (the new world's) plays
   too. Each topic's `intent` stands for its words, so `intent` says in plain words every fact the line will give.
2. **After dialogue**: the compiled form with the written lines: `python3 -m tools.playtest run --forms <dir|files>`.
3. **The built plugin**: the form read back (`bash tools/ArgoniaPlugin/plugin.sh questform-read <dir>`) after
   `python3 -m tools.questform diff <designed> <built>` shows no difference, played with `run --source built`.

Run a moment again only when what the player meets has changed. The playtest is never part of `make check`. Before
moments 2 and 3, `python3 -m tools.playtest reach <forms>` checks every stage and ending is reached by one of two
characters (one able in every skill, one new); an unreached stage is a finding before any player runs.

## 3. Run the player

    python3 -m tools.playtest record <record.yaml> [--know <notes.md>] [--way <approach id>] [--choose <ending id>] [--after <earlier.yaml>[@<ending>] ...]
    python3 -m tools.playtest run --forms <dir|files> [--after <quest id>...] [--know <notes.md>] [--source built]

- **One player, fresh each run**: a headless run of the `paper-player` agent's model and effort
  (`.claude/agents/paper-player.md`), which cannot read the repository and sees the game through one command. It is
  told to play as a new player who wants to understand the story and decide for themselves, and to pick topics only
  when it wants to know something, as a player would.
- **What the player already knows.** A quest of a line is played with `--know` the `notes.md` of the passing run of
  the quest before it in the line's order: the last thing a player writes at an ending is what they now know and
  have, in their own words, and it is all the next quest's player is told. A line's first quest runs with none. A
  later quest takes `--after` the records before it so their state carries, as the form game does. A
  form-based run of a later quest also takes `--after` the quests before it, so its state and things are loaded.
- **Ways and choices.** The player chooses freely. Where a stage has several ways through or the quest has a choice,
  one passing run per way and per ending is owed: a later run steers with `--way` or `--choose`, which tells the
  player which way the game expects of their build, never what to think of it.
- **Names.** A ref, item or place the player would see must have a name in the record or the world; the run stops
  on a thing without one, and the fix is in the record.
- **A harness error** (an unknown word, a quest not loaded, a thing without a name) stops the run: fix its cause in
  the record, never in the game.
- A run costs a few cents and a minute or two; run the ways of one quest at once, under `tooling/job_guard.sh` when
  there are many.

## 4. Grade the run

Each run is a folder `story/playtests/<quest id>/<utc>-<designed|written|built>/`: `transcript.jsonl`,
`milestones.md` (each milestone's plan from the record beside the player's four answers), `notes.md` (what the
player knew at the end), `run.json`.

1. Read `milestones.md` top to bottom and mark each milestone pass or miss (section 1), writing the grade into the
   run's `grade.md`: one line a milestone, and for a miss what the player lacked or believed.
2. For each miss, read the thinks before it in `transcript.jsonl`: what on screen gave the player that belief, or
   what they looked for and did not find.
3. Read `notes.md`: a wrong or missing fact there is a miss of the milestone where it should have been given.

## 5. Whose each miss is

| The player | It belongs to | Change |
|---|---|---|
| did not know what to do next, where, or how | the record (quest-write) | the journal entry, the objective's words or target, or a line on the path that gives the step |
| did not see a way through that the stage offers | the record | the journal names the ways ("I may fight them or slip past"), and a marker or a named thing shows each |
| did not know why they were doing it, or for whom | the record's lines on the path | the line on the path that gives the fact; never only an optional topic |
| met a word, name or person with nothing to explain it | the record's `terms` and topics | a plain gloss on the path at first use, and a topic the player can pick for more |
| believed something false | the line, entry or name that misled | its words (the record at moment 1, dialogue-write after) |
| could not tell a place or thing for what it is | the record's names and placements | the name the game shows on the door, container or thing; the place's need when it is a build matter |
| a difference between designed and built | the build or the design: fix the one that is wrong | quest-build, or quest-write |
| a harness error, or the game doing what Skyrim would not | the tool's lane | a report to the lead; never worked round |

The fix goes into the record's channels (journal, objective, marker, line, name, message), and the stage's
`information.carriers` says which channel now carries the missing point.

## 6. Loop until it passes

The writer answers every miss of a run as one set of changes, then a fresh player plays the changed quest with the
same `--know`. The loop ends when a run passes. A miss cleared by a change is recorded with its class (the table
above) for the lead to fold into the recipe that produced it ([quest-system](../quest-system/SKILL.md) "How the
skills learn"). When a quest's passing run changes what its player knew at the end, the next quest's run is made
again with the new `notes.md`.

## 7. Keep and report

- Commit every run folder; never delete one.
- Write in the lane's review notes (`story/design/quests/review/<lane>.md`) which runs passed and what each round
  changed.
- `python3 -m tools.playtest page` rebuilds the owner's page (`out/playtest/index.html`, every quest's milestones
  with each run's answers beside the plan) from the kept runs; republish it to its artifact after new runs.
