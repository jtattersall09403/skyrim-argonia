# The paper playtest

A quest is played in words by a fresh player who knows nothing of it, thinking aloud at every step, before anyone
plays it in game. The paper game (`tools/playtest`) is a deterministic state machine over quest forms
([quest-form](quest-form.md)); the player is a separate headless Claude that can do nothing but send it commands.

## What it tests, and what it does not

It tests what a new player understands: whether the quest's progression, story, dialogue and people make sense as
they meet them, whether the objectives and markers lead them, and whether they want to go on. It does not test
navigation, visuals, combat, timing or anything a form cannot say: a walk is one `go`, a fight is the player's
choice of `win`, `lose` or `flee`, a lock is `win` or `fail` (with lockpicks held, and only a lock the sheet's
Lockpicking could plausibly manage), being seen stealing is the player's choice of `unseen` or `seen`, and a
skill check is the character sheet's skill against the line's threshold.

The game plays what the form says the game does, and nothing else. A condition or result word it does not know, a
quest a form names that the run did not load, a ref or item without a name the player would see: each stops the run
with a harness error naming it. Fix the cause (the form, or the names file); never work round it.

## The three moments

1. **The designed form, before dialogue is written** (`python3 -m tools.questform compile <quest>`): lines show as
   `[not yet written; the gist:]`. First `python3 -m tools.playtest reach <forms>`: every stage and every ending must
   be reachable; one that is not is a finding before any player runs. This catches a quest that does not hang
   together while changing it is cheap.
2. **After dialogue is written**: the same, with the words the player will read.
3. **Once on the built plugin**: the form read back from the plugin (`plugin.sh questform-read <dir>`), with the
   comparison first. `python3 -m tools.questform diff <designed> <built>` names every field the build changed and
   exits non-zero on any; results compare in order (the engine runs them in order); a ref placed by an anchor is
   equal when it is built in the designed `at`'s cell within `PLACED_UNITS` of it (or, with no `at`, satisfies the
   anchor). Clear every difference, then play the built form.

Run again only when what the player meets has changed. The playtest is never part of `make check`: it is slow and
not deterministic. The game's unit tests, the comparison's and `reach` are: `make check` compiles every staged quest
that fits the form and plays it with `reach` (below), unless it is listed with its reason in
`tools/playtest/reach_owed.json` (a list that only shrinks).

## What the player sees

| Command | Shows |
|---|---|
| `look` | the place's name; the people near, each as who they are where the form or the world says (an Argonian woman) and hostile or dead; the things on the ground and the containers; the doors; each locked one with its level, each owned one marked; two of one name are told apart as `<name> 1` and `<name> 2` |
| `journal` | each quest's entries in order and its active objectives |
| `map` | the player's position; each active marker: what it marks (a person, thing, door, place), where, how far, which way; the places known |
| `go <marker N, person, thing, place>` | arrival, roughly how far it was, then the `look`; into another interior only when a door of the run leads there that is unlocked or whose key is held (else the door's locked words). The transcript row says how the player knew the way: `marker`, `in sight`, `known place`, or `name only` (flagged on the page) |
| `talk <person>` | who they are (Nesh-Deeka, an Argonian woman), the greeting (the first whose conditions hold; the first conversation makes "spoken before" true), then the topics open now |
| `say <topic, answer or number>` | the spoken words: one entry per prompt (a prompt with a check carries its label, as the built topic does: "(Persuade)", "(Alchemy)", "(20 gold)"), and saying it speaks the first line of that prompt whose stage window and conditions hold, a failed check the record's own fallback words; what comes up (objective started or completed, journal entry, thing added or removed, message box); the topics now open, or the answers to a question (by the same rule) |
| `use <container>` | its lock and level if locked (it opens with its key held, no crime), else what is in it (its `contents` and the things placed in it); opening an owned one is no crime, and it says that what is taken from it is stolen |
| `use <door>` | through it, or locked with its level; its key held unlocks it; a lock with no key and nothing that unlocks it stays shut; a door a result unlocks starts locked, key only |
| `use <thing>` | a thing with `text` is read as a book or note; a dead person's body is searched |
| `take <thing> [unseen\|seen]` | one thing from the ground (its whole `count`), an opened container, a pocket or a body (the whole stack), counted by the form's item id; a container cannot be taken; an owned thing, a thing from a container another owns, or a pocket asks `unseen` or `seen` (a key does not make a container's things the player's; a `give_ownership` result does) |
| `pick <lock> win\|fail [unseen\|seen]` | needs lockpicks (a failure breaks one); a key-only lock cannot be picked; a level above `LOCK_SKILL` for the sheet's Lockpicking is beyond the player; a picked container opens |
| `pickpocket <person>` | what they carry; `take` then takes one |
| `fight`, `wait` | what happens, as the game shows it |

Every command counts towards the run's limit, one the game refuses too. Stages are by done, as the engine has them
([quest-form](quest-form.md)): a stage already done is never set again; a trigger is open while its prerequisite is
done, its stage is not and the quest's stage is below its `until`; a condition's `not: true` turns it round. An ending closes every objective still shown.
Regard stays between -4 and 4. A speaks-first line fires when the player arrives near its speaker at its stage. A
must-live person's death within the row's window (its `from` stage done, the stage at most its `to`) fails the quest if
it runs, and on a main or faction quest that has not ended shows its kind's message box; a who-must-live person, or a
death trigger's person, already dead as the quest starts moves it at once. A crime that is `seen` says what Skyrim
would do (the owner or a guard confronts the player: a fine or a fight) and goes no further; either way the thing is
held.

The people met are the forms' refs and every authored talker standing in the places the forms involve (the refs'
cells and their settlements), with each talker's topics gated as the build gates them. A name comes from the form
first (its `names`, `places` and `texts`, a ref's `name`, a door's `destination` as "Door to ...", a marker's
`name` as its cell's place name), then from a names file (`<quest>.names.json`: `names` by id, `places` by cell with `name`, `interior` and an
interior's `entrance`, `people` by id with `race` and `sex`), then from the world database, which also says who a
person is. Each id a names file had to give is listed in the run's `run.json` (`names_from_file`): what the form
still lacks.

Items are held and matched by the form's item id (a unique thing by its ref id, a stock thing by its base; Skyrim's
lockpick and gold under one id whichever way the form names them): a take trigger, a hand-in, a condition and a
stage's `set_stage` `if_held` all count the same item. One take moves each quest by the triggers open as it happens,
never by one the stage it set has just opened.

## Running it

    python3 -m tools.playtest run --forms <dir|files> --player careful|impatient|wanderer \
        [--model sonnet] [--after <quest id>...] [--know <a text>] [--names <file>] [--at <ref id>] [--source built]

Run the three players on each moment. `--at` is where the player stands when the game begins (default: the first
marker's target). A later quest is played with `--after` and the earlier quests' forms loaded beside it: the game
first plays each named quest to a completed ending by itself along a shortest path (the walker,
`tools/playtest/walk.py`), so the player starts with the state, items, gold and rank they leave, and knows what the
journal entries met on that path say; a quest no path completes stops the run with a harness error, itself a
finding. `--know` adds a text of its own. By hand: `python3 -m tools.playtest new ...`, then
`do <session> "<command>" --think "..."`, then `end <session> --take "..."` and `--answers "..."`.

`python3 -m tools.playtest reach <forms>` (and `make reach` on every compiled quest) proves, for each quest and each
way through the quests it waits on (each completed ending of each), that every stage and every ending is reached by
one of two characters, each with 1,000 gold: one able in every skill and a new character; and that each character
who can take that way through completes the quest. It names each stage or ending no character reaches, with the
stages reached; a search cut at its limit (`MAX_STATES`) says so and is never read as "no path". The walker acts on
the walked quest's own references first (every loaded one only when that leaves something unreached), takes and uses
everything, and can fight anyone a condition, a trigger or a who-must-live row names. `make reach` takes about 12
seconds for the eight quests that fit the form today.

The player runs from a new empty folder with its own system prompt, the project's setting sources only, no MCP
servers and one tool: Bash allowed only to run the run's `play` wrapper, a Python script that passes the player's
words to the game as arguments with no shell between; anything else is denied. `python3 -m tools.playtest probe`
proves it cannot read the repo, trying at least five ways (a shell substitution inside a `play` argument and a
redirection among them; its stream is kept in `story/playtests/probe/`). A silent player is killed at the run's
timeout; three refused attempts end the run, keeping the last attempt's folder. Its brief is a role, not a checklist: who they are, how to play, the temperament,
when to stop, and to give an open take in their own words. The standing questions (what next, who they work for,
the most confusing moment, what they would tell the writer) are asked as a separate final turn after the take is stored,
numbered, and whatever comes back is kept as `answers.md`. A run ends when every loaded quest that has started has ended
and none is waiting to start, or the player is stuck, or the command limit is reached; the player is told more may
follow after a quest completes.

## Reading a run

Each run is a folder `story/playtests/<quest id>/<utc>-<player>-<designed|built>/`, committed:

| File | Holds |
|---|---|
| `transcript.jsonl` | one line per command: time, the player's think, the command, exactly what they saw, a state summary (stages, position, markers) |
| `take.md`, `answers.md` | the open take, then the answers |
| `stream.jsonl` | the model's whole stream (its own text between commands; its thinking where the stream carries it) |
| `brief.md` | the system prompt and first message the player got |
| `session.json` | the forms played, their hash, the world snapshot, the final state |
| `run.json` | quest, form source and hash, player, model, counts (commands, stalls, harness errors), how it ended and how each quest stands, why the player stopped (`stopped`: result, error, timeout or no result, with the result's `subtype` and any `player_error`), cost (the questions turn's included), minutes |

`python3 -m tools.playtest page` writes the owner's page for exploring the runs (`out/playtest/index.html`, one
self-contained file, published as a private

artifact): every quest's stages with each run drawn along them, the takes and answers side by side, and each run step
by step with its thinking, the screen, the state and a map of where the player went. It is made wholly from the run
folders; make it again after new runs are kept. A stall is a repeated command, a third
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
