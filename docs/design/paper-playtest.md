# The paper playtest

A quest is played in words by a fresh player who knows nothing of it, thinking aloud at every step, before anyone
plays it in game. The paper game (`tools/playtest`) is a deterministic state machine over quest forms
([quest-form](quest-form.md)); the player is a separate headless Claude that can do nothing but send it commands.

## What it tests, and what it does not

It tests what a new player understands: whether the quest's progression, story, dialogue and people make sense as
they meet them, whether the objectives and markers lead them, and whether they want to go on. It does not test
navigation, visuals, combat, timing or anything a form cannot say: a walk is one `go`, a fight is the player's
choice of `win`, `lose` or `flee`, a lock is `win` or `fail`, and a persuasion is the character sheet's skill against
the line's threshold.

The game plays what the form says the game does, and nothing else. A condition or result word it does not know, a
quest a form names that the run did not load, a ref or item without a name the player would see: each stops the run
with a harness error naming it. Fix the cause (the form, or the names file); never work round it.

## The three moments

1. **The designed form, before dialogue is written** (`python3 -m tools.questform compile <quest>`): lines show as
   `[not yet written; the gist:]`. This catches a quest that does not hang together while changing it is cheap.
2. **After dialogue is written**: the same, with the words the player will read.
3. **Once on the built plugin**: the form read back from the plugin (`plugin.sh questform-read <dir>`), with the
   comparison first. `python3 -m tools.questform diff <designed> <built>` names every field the build changed and
   exits non-zero on any; a ref placed by an anchor is equal when the built position satisfies the anchor (within
   `NEAR_UNITS` of its reference, or in or near its place). Clear every difference, then play the built form.

Run again only when what the player meets has changed. The playtest is never part of `make check`: it is slow and
not deterministic. The game's unit tests and the comparison's are.

## What the player sees

| Command | Shows |
|---|---|
| `look` | the place's name; the people near, each with a word (hostile, dead); the things; the doors (locked) |
| `journal` | each quest's entries in order and its active objectives |
| `map` | the player's position; each active marker: what it marks (a person, thing, door, place), where, how far, which way; the places known |
| `go <marker N, person, thing, place>` | arrival, roughly how far it was, then the `look` |
| `talk <person>` | the greeting, then the topics open now |
| `say <topic, answer or number>` | the spoken words; what comes up (objective started or completed, journal entry, thing added or removed, message box); the topics now open, or the answers to a question |
| `take`, `use`, `fight`, `pick`, `pickpocket`, `persuade`, `wait` | what happens, as the game shows it |

A speaks-first line fires when the player arrives near its speaker at its stage. A must-live person's death fails
the quest; on a main or faction quest it also shows the main quest's message box once.

The people met are the forms' refs and every authored talker standing in the places the forms involve (the refs'
cells and their settlements), with each talker's topics gated as the build gates them. Names and places come from the
world database; a quest's new placements and items need a names file beside the form (`<quest>.names.json`:
`names` by id, `places` by cell with `name`, `interior` and an interior's `entrance`).

## Running it

    python3 -m tools.playtest run --forms <dir|files> --player careful|impatient|wanderer \
        [--model sonnet] [--know <earlier forms or a text>] [--names <file>] [--at <ref id>] [--source built]

Run the three players on each moment. `--at` is where the player stands when the game begins (default: the first
marker's target). `--know` gives a later quest's player what they would know by then, built from the journals of the
quests before. By hand: `python3 -m tools.playtest new ...`, then `do <session> "<command>" --think "..."`, then
`end <session> --take "..."` and `--answers "..."`.

The player runs from a new empty folder with its own system prompt, no setting sources, no MCP servers and one tool:
Bash allowed only to run the run's `play` wrapper; anything else is denied. `python3 -m tools.playtest probe`
proves it cannot read the repo (its stream is kept in `story/playtests/probe/`). Its brief is a role, not a checklist: who they are, how to play, the temperament,
when to stop, and to give an open take in their own words. The standing questions (what next, who they work for,
the most confusing moment, what they would tell the writer) come only after the take.

## Reading a run

Each run is a folder `story/playtests/<quest id>/<utc>-<player>-<designed|built>/`, committed:

| File | Holds |
|---|---|
| `transcript.jsonl` | one line per command: time, the player's think, the command, exactly what they saw, a state summary (stages, position, markers) |
| `take.md`, `answers.md` | the open take, then the answers |
| `stream.jsonl` | the model's whole stream (its own text between commands; its thinking where the stream carries it) |
| `brief.md` | the system prompt and first message the player got |
| `session.json` | the forms played, their hash, the world snapshot, the final state |
| `run.json` | quest, form source and hash, player, model, counts (commands, stalls, harness errors), how it ended, cost, minutes |

`python3 -m tools.playtest index` rebuilds `story/playtests/index.json`. A stall is a repeated command, a third
journal or map view running, or a think that says stuck.

Read the take first, then the thinks around each stall and each wrong guess: what did the player believe, and what
on screen made them believe it. Agreement across the three players is a finding; one player's taste is not.

## What to do with findings

- A player who did not know what to do next, or why: the journal entry or objective text is owed the missing fact,
  or a line must give it (quest-write). Change the record, compile, and play the moment again.
- A person whose role made no sense: their lines say who they are and why they care (dialogue-write).
- A line that contradicts what `look` shows: the line is wrong, never the world (quest-review).
- A harness error: the form or its names file is incomplete; never change the game to hide it.
- A difference in the comparison: the build is wrong, or the design is; fix the one that is, never both.

Record what changed and why in the quest's review notes; keep every run.
