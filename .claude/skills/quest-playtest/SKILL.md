---
name: quest-playtest
description: Play an Argonia quest on paper with fresh headless players who know nothing of it, at its three moments (the designed form before dialogue, after dialogue, the built plugin), read the runs, decide whose each finding is, answer them as one set and confirm. Use after quest-review clears a record, after its dialogue is written, and after quest-build reads it back from the plugin.
---

# Playing a quest on paper

A quest is played in words, by a player who thinks aloud at every step, before anyone plays it in game. The paper
game (`tools/playtest`) plays exactly what the quest form says the game does; its reference, with every command and
what the player sees, is [paper-playtest](../../../docs/design/paper-playtest.md). The path is in
[quest-system](../quest-system/SKILL.md). Before this: [quest-review](../quest-review/SKILL.md) (moment 1),
[dialogue-write](../dialogue-write/SKILL.md) and [text-review](../text-review/SKILL.md) (moment 2),
[quest-build](../quest-build/SKILL.md) (moment 3). After this: the next step of the path, once the findings are
answered.

The playtest tests what a new player understands: whether the progression, story, lines and people make sense as
they meet them, whether objectives and markers lead them, whether they want to go on. It never tests navigation,
looks, combat or timing; the owner does those in game.

## 1. The three moments

1. **The designed form, before dialogue** (`python3 -m tools.questform compile <quest id> --out <dir>`): lines show as
   their gists. A quest that does not hang together is caught while changing it is cheap.
2. **After dialogue**: compiled again, with the words the player will read.
3. **The built plugin**: the form read back (`bash tools/ArgoniaPlugin/plugin.sh questform-read <dir>`), after
   `python3 -m tools.questform diff <designed> <built>` shows no difference.

Run a moment again only when what the player meets has changed. The playtest is never part of `make check`.

## 2. First the fast check

`python3 -m tools.playtest reach <forms>`: for each way through the quests it waits on, every stage and ending is
reached by one of two characters (one able in every skill, one new; each with 1,000 gold), and each who can take that
way completes the quest. An unreached stage is a finding before any player runs. A search cut at its limit says so
and is never read as "no path". `make reach` runs it over every compiled quest.

## 3. Run the players

    python3 -m tools.playtest run --forms <dir|files> --player careful|impatient|wanderer|gainer \
        [--model sonnet] [--after <quest id>...] [--know "<text>"] [--names <file>] [--at <ref id>] [--source built]

- **The temperaments**, each a fresh headless player with one tool: *careful* reads every line and journal entry;
  *impatient* skims and follows markers; *wanderer* talks to everyone and pokes at everything; *gainer* (below, for
  a choice) chooses by what each side gives. Moments 1 and 2 run the first three; moment 3 runs one careful player. Add a second impatient run where a quest opens with much optional talk
  (a join, a briefing), since that player shows whether the step can be found without it.
- **A choice is tested by players who value different things.** The three temperaments differ in patience, not in
  what they want, and one model's players tend to make one choice. Where a quest turns on a choice, add runs whose
  `--know` text gives the player a person to be with reasons of their own (out for power; loyal to their own people
  above outsiders; true to whoever hired them; trusting no institution), on different models (`--model`), and in the
  closing questions ask each for the strongest honest case for the option they did not take. One run is always the
  *gainer* temperament (`--player gainer`), who chooses purely by what each side gives in play. Every player
  choosing alike under one persona is not a finding; an option no persona takes and none can argue is, and so is
  the gainer finding one side better in every way.
- **After a choice the closing questions ask** what the player thinks they gained and gave up in what they can now
  do, get or reach (the game's own words for it: `Learned:`, `Added:`, a door, a trader), and whether they would
  choose differently for the reward. A player who can name no gain, or only what people said, shows an outcome that
  is only words: a finding for the record (quest-review (j)).
- **A later quest of a line** runs with `--after` the quests before it, their forms loaded beside it: the game first
  plays each to a completed ending along a shortest path, so the player starts with the state, things, gold and rank
  they leave and knows what those journal entries said. `--know` adds a short text of its own.
- **Names.** At moment 1 a new thing or person may still lack a name the player would see. A ref, item or place the player would see must have a name in the form or the world database; a names
  file (`<quest>.names.json`) is the stop-gap, and each id it had to give (`names_from_file` in `run.json`) is owed
  to the record.
- **A harness error** (an unknown word, a quest not loaded, a thing without a name) stops the run: fix its cause in
  the record or the names file, never in the game.
- The player is a separate Claude run that cannot read the repository (`python3 -m tools.playtest probe` proves it).
  A run costs a few cents and about a minute; run the three of a moment at once, under `tooling/job_guard.sh` when
  there are many.

## 4. Read a run

Each run is a folder `story/playtests/<quest id>/<utc>-<player>-<designed|built>/` (`transcript.jsonl`, `take.md`,
`answers.md`, `stream.jsonl`, `run.json`).

1. Read `take.md` first: did they understand, was it fun, do they want the next quest, what made no sense.
2. Then the thinks around each **stall** (a repeated command, a third journal or map view running, a think that says
   stuck) and each **wrong guess**: what did the player believe, and what on screen made them believe it? Set it
   against the truth of the record.
3. Then the rows where the player found the way by `name only` rather than a marker, a place in sight or a known
   place.
4. `answers.md`: what they think comes next, whom they work for, the most confusing moment, what they would tell the
   writer.

Agreement across players is a finding; one player's taste is not.

## 5. Whose each finding is

| The player met | It belongs to | Change |
|---|---|---|
| not knowing what to do next, where, or why | the record (quest-write) | the entry, the objective, its target, or a line that gives the missing fact |
| a person whose role or stake made no sense | the record's cast and topics, then the lines | a topic that says who they are and why they care; the lines rewritten (dialogue-write) |
| a name or local word before it was given; a line pointing to a topic in other words than the topic's | the lines (dialogue-write) | the wording |
| a line or entry that contradicts what `look` shows | the line or entry; the world is right | the line (dialogue-write) or the record (quest-write) |
| a choice everyone makes the same way | the record's choice | each side argued by its own person, its cost named before it |
| a difference between designed and built | the build or the design: fix the one that is wrong, never both | quest-build, or quest-write |
| a harness error, or the game doing what Skyrim would not | the tool's lane | a report to the lead; never worked round |

## 6. One set of changes, then confirm

Gather every finding of the moment's runs before changing anything. Make one coherent set of changes that answers
them together (a record change goes through quest-write's own loop; a line change through dialogue-write and
text-review), then run fresh players on the changed quest. A finding is **cleared** when the next players are no
longer lost, bored or misled at that point. A finding a change did not clear stays open with the run that shows it.

## 7. Keep and report

- Commit every run folder; never delete one.
- Write in the lane's review notes (`story/design/quests/review/<lane>.md`) what each round's players said, what
  changed as one set, and which findings cleared; a change to the record is also answered in its `review` section
  like a reviewer's finding.
- `python3 -m tools.playtest page` rebuilds the owner's page (`out/playtest/index.html`, every quest's stages with
  each run drawn along them, takes side by side) from the kept runs; republish it to its artifact after new runs.
- **For the skills**: a cleared finding is recorded with its class of fault and the change that cleared it, for the
  lead to fold into the recipe that produced it ([quest-system](../quest-system/SKILL.md) "How the skills learn").
